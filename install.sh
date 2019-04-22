#!/bin/sh

cd ~/broker

sudo apt update

sudo apt install python3-pip -y

sudo apt install python3-venv -y

python3 -m venv venv

source venv/bin/activate

pip3 install -r requirements.txt

echo "
#!/usr/bin/env bash
source ~/broker/venv/bin/activate
cd ~/broker
python3 broker.py
" > broker.sh

sudo chmod +x broker.sh
sudo mv broker.sh /bin/broker

sudo touch /etc/systemd/system/broker.service
sudo chmod 775 /etc/systemd/system/broker.service
sudo chmod a+w /etc/systemd/system/broker.service

sudo echo "
[Unit]
Description=broker
[Service]
User=pi
ExecStart=/bin/bash /bin/broker
Restart=on-failure
WorkingDirectory=/
StandardOutput=syslog
StandardError=syslog
[Install]
WantedBy=multi-user.target
" > /etc/systemd/system/broker.service

sudo systemctl enable broker.service
sudo systemctl daemon-reload
