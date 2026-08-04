Simple Raspberry Pi webcam monitoring.


1. Install using systemd autostart:

Requirements:
- python

Clone repository
git clone  
`https://github.com/aasiop/XYZ.git`

Enter repository  
`cd XYZ`

Set up systemd autostart  
`sudo nano /etc/systemd/system/record_rpi.service`

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
`crontab -e`

Paste into another line   
`0 6 * * * /usr/bin/python3 /PATH_TO_REPOSITORY/record_rpi.py >> /PATH_TO_REPOSITORY/logs.log 2>&1`







2. Install using docker