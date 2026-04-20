# AirController for Linux

**AirController** is a tool that automatically switches your AirPods between mono and stereo modes.

> 🐧 **Note**: AirController is designed to work on **Linux** systems using **PulseAudio/PipeWire** and **pactl**. It is not compatible with Windows or macOS.

## Features

- 🔄 **Automatic audio sink switching** - No manual intervention needed
- 🎵 **Mono/Stereo detection** - Intelligently detects when one AirPod is removed or charging
- 🔌 **AirPods connection monitoring** - Real-time status tracking
- 🧹 **Safe cleanup on exit** - Removes virtual sinks when shutting down
- ⚡ **Lightweight** - Minimal resource usage
- 🚀 **Service ready** - Can run as systemd service or desktop autostart

## Requirements

- Python 3.8 or higher
- PulseAudio **or** PipeWire with pipewire-pulse
- `pactl` command-line tool (comes with PulseAudio/pipewire-pulse)

---

## Installation

### Method 1: Quick Install

```bash
# Clone the repository
git clone https://github.com/bondarenko-g/AirController
cd AirController

# Install dependencies
pip install -r requirements.txt

# Run AirController
python main.py

### Method 2: System-wide Installation
```bash
# Clone and install
git clone https://github.com/bondarenko-g/AirController
cd AirController
sudo ./scripts/install-service.sh
```

## Running as a service

### Systemd Service (Auto-start on boot)
```bash
# Install the service
sudo ./scripts/install-service.sh

# Check status
sudo systemctl status aircontroller@$USER

# View live logs
sudo journalctl -u aircontroller@$USER -f

# Restart the service
sudo systemctl restart aircontroller@$USER

# Stop the service
sudo systemctl stop aircontroller@$USER
```

### Desktop Autostart (Starts when you log in)
```bash
# Install desktop autostart
./scripts/install-autostart.sh
```

### Manual run
```bash
# Run in foreground
python main.py

# Run in background
python main.py &
```


1. **Clone the repository**:
```bash
git clone https://github.com/mofumii/AirController
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```


## Configuration
- You can customize timeouts and sink names by editing variables in config.py
- Default polling interval: 3 seconds.

## Troubleshooting
- Make sure pactl and PulseAudio/PipeWire are installed.
- Ensure your user has permission to acces bluetooth devices.
- Check if your AirPods are visible via bluetoothctl or similar tools.

## Contributing

Pull requests are welcome!

If you encounter any issues or bugs, feel free to [open an issue](https://github.com/bondarenko-g/AirController) or contact me directly

Thank you for your input!

## Used materials
- Some code from [delphiki/AirStatus](https://github.com/delphiki/AirStatus)

## License

This project includes code from the [AirStatus project](https://github.com/delphiki/AirStatus) (GPLv3).  
Therefore, this project is licensed under the GNU General Public License v3.0. 
See the [LICENSE](./LICENSE) file for details.
