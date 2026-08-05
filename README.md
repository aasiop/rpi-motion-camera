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
- python
- ffmpeg

---

## Installation:

Install ffmpeg
```bash
sudo apt install ffmpeg
```

Clone repository
```bash
git clone https://github.com/aasiop/rpi-camera-motion-recorder.git
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
sudo nano /etc/systemd/system/record_rpi.service
```

Paste  
```
[Unit]
Description=Camera autostart

[Service]
ExecStart=/usr/bin/python3 /srv/NAS/monitoring/record_rpi.py
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```
Change user=pi to your account username

### Setup file merge time using crontab

Enter crontab configuration  
```bash
crontab -e
```

Paste into another line   
```bash
0 6 * * * /usr/bin/python3 /PATH_TO_REPOSITORY/record_rpi.py >> /PATH_TO_REPOSITORY/logs.log 2>&1
```

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
```

| Variable | Description                                    |
|----------|------------------------------------------------|
| `PROJECT_PATH` | Path to store recordings                       |
| `TEMP_DIR` | Directory where files are temporary merged     |
| `RESOLUTION_X` | Screen width                                   |
| `RESOLUTION_Y` | Screen height                                  |
| `SENSITIVITY` | higher value = less sensitive motion detection |
| `BUFFER_TIME` | time after detecting a movement                |
| `AFTER_DETECTION_TIME` | time before detecting a movement               |

## License
This project is licensed under the MIT License.