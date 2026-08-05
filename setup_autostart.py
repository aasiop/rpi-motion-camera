import os
import sys
import subprocess
from pathlib import Path

# must have sudo permissions
if os.geteuid() != 0:
    print("Run this script with sudo.")
    sys.exit(1)

project_dir = Path(__file__).resolve().parent #gets project path

env_file = project_dir / ".env" #check for .env configuration
if not env_file.exists():
    print("Missing .env file. Create it from .env.example")
    sys.exit(1)

#gets user
user = os.environ.get("SUDO_USER", "pi")

#interpreter running script
python = sys.executable

service = f"""[Unit]
Description=RPI Camera Motion Recorder autostart
After=multi-user.target

[Service]
Type=simple
WorkingDirectory={project_dir}
ExecStart={python} {project_dir / "record_rpi.py"}
Restart=always
RestartSec=5
User={user}

[Install]
WantedBy=multi-user.target
"""

service_path = Path("/etc/systemd/system/rpi-motion-camera.service")

service_path.write_text(service)

subprocess.run(["systemctl", "daemon-reload"], check=True)
subprocess.run(["systemctl", "enable", service_path.name], check=True)
subprocess.run(["systemctl", "start", service_path.name], check=True)

print("Service installed successfully.")