# RPI webcam motion monitoring

Simple Raspberry Pi webcam monitoring. It records before and after detecting movement, then combines the clips into continuous daily recordings. Ideal for indoor motion detection.

---

## Features

- Motion-triggered recording
- Pre-motion recording buffer
- Lossless video merging
- Automatic systemd setup

---

## Requirements

Requirements:
- sudo privileges
- python >= 3.10
- python-dotenv
- opencv-python
- ffmpeg
- V4L2 compatible camera

---

## Structure

```text
PROJECT_PATH/
├── merged/
│   ├── merged_2026-08-20.mp4
│   ├── merged_2026-08-21.mp4
│   └── ...
├── recordings/
│   ├── .tmp/
│   │   ├── rec_2026-08-22_12-15-23.mp4
│   │   └── ...
│   ├── rec_2026-08-22_12-12-34.mp4
│   ├── rec_2026-08-22_12-12-59.mp4
│   └── ...
└── logs/
```

## Installation:

Install requirements: python, ffmpeg and v4l-utils
```bash
sudo apt install python3 python3-pip ffmpeg v4l-utils
```

Clone repository
```bash
git clone https://github.com/aasiop/rpi-motion-camera.git
```

Enter repository  
```bash
cd rpi-motion-camera
```

Install requirements: python libraries
```bash
pip install -r requirements.txt --break-system-packages
```

Create your configuration file:  
```bash
cp .env.example .env
```

Change permissions:
```bash
chmod 600 .env
```

Edit the configuration:  
```bash
nano .env
```

Set up systemd autostart  
```bash
sudo python3 setup_autostart.py
```

Setup file merge using crontab
```bash
python3 setup_merging_time.py
```

---

## Configuration

Create a `.env` file from `.env.example`.

Example:
```env
PROJECT_PATH            = /mnt/camera
TEMP_DIR                = /tmp/merge
RESOLUTION_X            = 1920
RESOLUTION_Y            = 1080
SENSITIVITY             = 65
BUFFER_TIME             = 4
AFTER_DETECTION_TIME    = 8
MERGE_TIME              = 6:00
```

| Variable | Description                                  |
|----------|----------------------------------------------|
| `PROJECT_PATH` | Path to store recordings                     |
| `TEMP_DIR` | Directory where files are temporary merged   |
| `RESOLUTION_X` | Screen width                                 |
| `RESOLUTION_Y` | Screen height                                |
| `SENSITIVITY` | Higher value = less sensitive motion detection |
| `BUFFER_TIME` | Seconds recorded before motion detection     |
| `AFTER_DETECTION_TIME` | Seconds recorded after motion stops          |
| `MERGE_TIME` | Daily merge time (24h format)        |

#### WARNING: Recording FPS is not configurable. It depends on your Raspberry Pi's processing performance, camera and selected resolution. Higher resolutions increase CPU usage and may reduce the achievable FPS.

---

## Usage

Check program status:
```bash
sudo systemctl status rpi-motion-camera.service
```

Stop program:
```bash
sudo systemctl stop rpi-motion-camera.service
```

Start program:
```bash
sudo systemctl start rpi-motion-camera.service
```

Disable autostart:
```bash
sudo systemctl disable rpi-motion-camera.service
```
Enable autostart:
```bash
sudo systemctl enable rpi-motion-camera.service
```

---

## Uninstallation

Stop and remove systemd service:
```bash
sudo systemctl stop rpi-motion-camera.service && \
sudo systemctl disable rpi-motion-camera.service && \
sudo rm /etc/systemd/system/rpi-motion-camera.service && \
sudo systemctl daemon-reload
```

Enter cronjob:
```bash
crontab -e
```

Remove line with merge.py:
```text
0 6 * * * /usr/bin/python3 /path/to/merge.py >> /path/to/logs.log 2>&1
```

Then delete the remaining files in rpi-motion-camera and recordings folder

---

## License
This project is licensed under the MIT License.