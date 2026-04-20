# AirController - Automatic stereo/mono switching for AirPods on Linux (PulseAudio / pipewire-pulse)
# Author: bondarenko-g
# Version 1.0
# If something does not work DM me or create an Issue

import logging
import shutil
import signal
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

import airpods_status as pods_status
import AirController.logging_config as logging_config
from AirController.config import STATUS_CHECK_FREQUENCY, TIMEOUT


class AudioStatus(IntEnum):
    DISCONNECTED = 0
    MONO = 1
    STEREO = 2


# ============================================================================
# EXCEPTIONS
# ============================================================================


class AudioError(Exception):
    """Custom exception for audio-related errors"""

    pass


# ============================================================================
# ENUMS & DATA CLASSES
# ============================================================================


@dataclass
class AudioConfig:
    """Configuration for audio sink"""

    channels: int
    channel_map: str
    description: str

    @classmethod
    def stereo(cls, model_name: str) -> "AudioConfig":
        return cls(
            channels=2,
            channel_map="front-left,front-right",
            description=f"{model_name} (Stereo)",
        )

    @classmethod
    def mono(cls, model_name: str) -> "AudioConfig":
        return cls(
            channels=1,
            channel_map="mono",
            description=f"{model_name} (Mono)",
        )


# ============================================================================
# AUDIO MANAGEMENT
# ============================================================================


class AudioSinkManager:
    """Manages PulseAudio sink operations"""

    def __init__(self, sink_name: str, timeout: int = TIMEOUT):
        self.sink_name = sink_name
        self.timeout = timeout

    @contextmanager
    def _subprocess_run(self, cmd: list, error_msg: str):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.timeout, check=False
            )
            yield result
        except subprocess.TimeoutExpired:
            raise AudioError(f"Timeout after {self.timeout}s: {error_msg}")
        except subprocess.SubprocessError as e:
            raise AudioError(f"Subprocess error: {error_msg}: {e}")
        except UnicodeDecodeError as e:
            raise AudioError(f"Encoding error: {error_msg}: {e}")

    def delete_sink(self) -> bool:
        """Delete existing audio sink if it exists"""
        logging.info(f"Deleting sink '{self.sink_name}'")

        try:
            with self._subprocess_run(
                ["pactl", "list", "short", "modules"], "Failed to list modules"
            ) as result:
                if result.returncode != 0:
                    logging.error(f"pactl list failed: {result.stderr.strip()}")
                    return False

                modules_found = False
                for line in result.stdout.splitlines():
                    if self.sink_name not in line:
                        continue

                    parts = line.split()
                    if not parts or not parts[0].isdigit():
                        logging.warning(f"Invalid module line format: {line}")
                        continue

                    module_id = parts[0]
                    logging.debug(f"Unloading module {module_id}")

                    with self._subprocess_run(
                        ["pactl", "unload-module", module_id],
                        f"Failed to unload module {module_id}",
                    ) as unload_result:
                        if unload_result.returncode != 0:
                            logging.error(
                                f"Failed to unload {module_id}: {unload_result.stderr.strip()}"
                            )
                            return False

                        modules_found = True
                        logging.info(f"Successfully unloaded module {module_id}")

                if not modules_found:
                    logging.debug(f"No module found for sink '{self.sink_name}'")
                return True

        except AudioError as e:
            logging.error(str(e))
            return False

    def create_sink(self, config: AudioConfig) -> bool:
        """Create a new audio sink with specified configuration"""
        logging.info(f"Creating {config.channel_map} sink for {self.sink_name}")

        if not self.delete_sink():
            logging.warning("Could not delete existing sink, continuing anyway")

        cmd = [
            "pactl",
            "load-module",
            "module-remap-sink",
            f"sink_name={self.sink_name}",
            "master=@DEFAULT_SINK@",
            f"channels={config.channels}",
            f"channel_map={config.channel_map}",
            f'sink_properties=device.description="{config.description}"',
            "latency_msec=2",
        ]

        try:
            with self._subprocess_run(cmd, "Failed to create sink") as result:
                if result.returncode != 0:
                    logging.error(f"Failed to create sink: {result.stderr.strip()}")
                    return False

                # Set as default sink
                with self._subprocess_run(
                    ["pactl", "set-default-sink", self.sink_name],
                    "Failed to set default sink",
                ) as set_result:
                    if set_result.returncode != 0:
                        logging.warning(
                            f"Could not set as default sink: {set_result.stderr.strip()}"
                        )

                    logging.info(
                        f"Successfully created and set {config.channel_map} sink"
                    )
                    return True

        except AudioError as e:
            logging.error(str(e))
            return False


# ============================================================================
# STATUS MODEL
# ============================================================================


class AirPodStatus:
    """Represents current AirPod status"""

    def __init__(self, data):
        self.is_connected = data.status == 1
        self.model = data.model or "AirPods"
        self.left_charge = data.charge.get("left", -1)
        self.right_charge = data.charge.get("right", -1)
        self.left_charging = data.charging_left
        self.right_charging = data.charging_right

    @property
    def should_use_mono(self) -> bool:
        """Determine if mono audio should be used"""
        # Missing earbud or charging
        if self.left_charge == -1 or self.right_charge == -1:
            return True
        # Earbud is charging
        if self.left_charging or self.right_charging:
            return True
        return False


# ============================================================================
# CONTROLLER
# ============================================================================


class AirController:
    def __init__(self):
        self.status = AudioStatus.DISCONNECTED
        self.model_name: Optional[str] = None
        self.sink_manager: Optional[AudioSinkManager] = None

    def _update_model_info(self):
        try:
            data = pods_status.get_data()
            self.model_name = data.model
            if not self.sink_manager:
                self.sink_manager = AudioSinkManager(self.model_name)
        except Exception as e:
            logging.error(f"Failed to get model info: {e}")

    def switch_to_stereo(self) -> bool:
        if not self.model_name:
            self._update_model_info()

        logging.info(f"Switching to stereo audio for {self.model_name}")
        config = AudioConfig.stereo(self.model_name)
        return self.sink_manager.create_sink(config)

    def switch_to_mono(self) -> bool:
        """Switch to mono audio configuration"""
        logging.info(f"Switching to mono audio for {self.model_name}")
        config = AudioConfig.mono(self.model_name)
        return self.sink_manager.create_sink(config)

    def update_audio_status(self) -> AudioStatus:
        try:
            airpods_data = pods_status.get_data()
            status = AirPodStatus(airpods_data)

        except Exception as e:
            logging.error(f"Failed to retrieve AirPods status: {e}")
            return self.status

        if not status.is_connected and self.status != AudioStatus.DISCONNECTED:
            logging.info("AirPods disconnected")
            if self.sink_manager:
                self.sink_manager.delete_sink()
            self.status = AudioStatus.DISCONNECTED
            return self.status

        if not self.model_name and status.model:
            self.model_name = status.model
            self.sink_manager = AudioSinkManager(self.model_name)

        if status.should_use_mono:
            target_status = AudioStatus.MONO
            switch_func = self.switch_to_mono
        else:
            target_status = AudioStatus.STEREO
            switch_func = self.switch_to_stereo

        if self.status != target_status:
            logging.info(f"Switching from {self.status.name} to {target_status.name}")
            if switch_func():
                self.status = target_status
            else:
                logging.error(f"Failed to switch to {target_status.name}")

        return self.status


# ============================================================================
# UTILITIES
# ============================================================================


def check_dependencies():
    """Verify all required system dependencies are available"""
    dependencies = {
        "pactl": "pulseaudio-utils or pipewire-pulse",
        "python3": "Python 3.6+",
    }

    for cmd, package in dependencies.items():
        if cmd == "python3":
            continue
        if shutil.which(cmd) is None:
            logging.critical(f"{cmd} is not installed or not in PATH")
            logging.critical(f"Please install: {package}")
            sys.exit(1)


def validate_config():
    """Validate configuration values"""
    if STATUS_CHECK_FREQUENCY < 0.1:
        logging.warning("STATUS_CHECK_FREQUENCY is very low, may cause high CPU usage")
    if TIMEOUT < 1:
        logging.warning("TIMEOUT is very low, may cause frequent failures")


class GracefulExiter:
    """Handle graceful shutdown on signals"""

    def __init__(self, sink_manager: Optional[AudioSinkManager] = None):
        self.sink_manager = sink_manager
        signal.signal(signal.SIGINT, self._handle_exit)
        signal.signal(signal.SIGTERM, self._handle_exit)

    def _handle_exit(self, signum: int, frame) -> None:
        """Handle exit signals gracefully"""
        logging.info("Shutting down AirController...")

        if self.sink_manager:
            success = self.sink_manager.delete_sink()
            if not success:
                logging.error("Failed to delete sink on exit")
                sys.exit(2)

        exit_codes = {
            signal.SIGINT: 130,  # Ctrl+C
            signal.SIGTERM: 143,  # systemd kill
        }
        sys.exit(exit_codes.get(signum, 0))


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def parse_arguments():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    logging_config.setup_logging(args.verbose)
    # check_dependencies()
    validate_config()

    controller = AirController()
    exiter = GracefulExiter(controller.sink_manager)

    logging.info("AirController started")

    try:
        while True:
            controller.update_audio_status()
            time.sleep(STATUS_CHECK_FREQUENCY)
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt")
    except Exception as e:
        logging.critical(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
