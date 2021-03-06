#!/bin/sh

if [[ $# -eq 2 ]]
    then
        echo "username will be $1"
        echo "password will be $2"
    else
        echo "username and password must be provided as arguments"
        exit 1
fi

cd /home/pi/broker

sudo apt update

sudo apt install python3-pip python3-venv dbus libdbus-glib-1-dev libdbus-1-dev python-dbus -y


python3 -m venv venv

source venv/bin/activate

pip3 install -r requirements.txt

echo "
#!/usr/bin/env bash
cd /home/pi/broker
source venv/bin/activate
python3 broker.py $1 $2
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
User=root
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
