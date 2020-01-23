#!/usr/bin/env bash

NAME=$1

# set the timezone
sudo timedatectl set-timezone America/New_York

# update the hostname
sudo hostnamectl set-hostname $NAME
sudo sed -i "s|raspberrypi|${NAME}|g" /etc/hosts

# patch the system and do setup
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y git puppet
sudo rm -f /etc/puppet/hiera.yaml
source /etc/profile.d/puppet-agent.sh
sudo puppet module install puppetlabs-vcsrepo
sudo puppet module install puppet-python
sudo puppet module install camptocamp-systemd

sudo puppet apply /home/pi/PiWeatherRock/setup.pp
