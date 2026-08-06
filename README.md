# RPI webcam motion monitoring

Simple raspberry pi webcam monitoring. It records before and after detecting movement. Mainly made for indoors movement detections.

---

## Features

- Lightweight
- Motion-triggered recording
- Pre-motion recording buffer
- Lossless video merging

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

## Installation:

Install requrements: python, ffmpeg and v4l-utils
```bash
sudo apt install python3 python3-pip ffmpeg v4l-utils
```

Install requirements: python libraries
```bash
pip install -r requirements.txt
```

Clone repository
```bash
git clone https://github.com/aasiop/rpi-motion-camera.git
```

Enter repository  
```bash
cd rpi-camera-motion-recorder
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

---

## Uninstallation

Stop and remove systemd service:
```bash
sudo systemctl stop rpi-motion-camera.service
sudo systemctl disable rpi-motion-camera.service
sudo rm /etc/systemd/system/rpi-motion-camera.service
sudo systemctl daemon-reload
```

Remove cronjob:
```bash
crontab -l
```

Remove line with merge.py:
```text
0 6 * * * /usr/bin/python3 /path/to/merge.py >> /path/to/logs.log 2>&1
```

Then delete the remaining files in rpi-motion-camera folder

---

## License
This project is licensed under the MIT License.