#!/bin/bash
set -x

# Adjust these two lines to include your desired hostname
sudo hostnamectl set-hostname tart
sudo sed -i 's|raspberrypi|tart|g' /etc/hosts

sudo apt-get update
sudo apt-get dist-upgrade -y
sudo apt-get install -y --no-install-recommends xserver-xorg lightdm realvnc-vnc-server git libgl1-mesa-dri awesome lxterminal vim puppet x11-xserver-utils

mkdir /home/pi/bin
echo '#!/bin/bash' > /home/pi/bin/xhost.sh
echo 'xhost +' >> /home/pi/bin/xhost.sh
chmod a+x /home/pi/bin/xhost.sh

sudo sed -i 's|#display-setup-script=|display-setup-script=/home/pi/bin/xhost.sh|' /etc/lightdm/lightdm.conf
grep -e '^display-setup-script' /etc/lightdm/lightdm.conf

# Install Distelli Agent
curl -sSL https://pipelines.puppet.com/download/client | sh
echo 'Enter your Access Token from Puppet Pipelines and press enter:'
read -s DistelliAccessToken
echo 'Enter your Secret Key from Puppet Pipelines and press enter:'
read -s DistelliSecretKey
cat << EOF |sudo tee /etc/distelli.yml > /dev/null
DistelliAccessToken: "$DistelliAccessToken"
DistelliSecretKey: "$DistelliSecretKey"
EOF
sudo /usr/local/bin/distelli agent install -conf /etc/distelli.yml
sudo /usr/local/bin/distelli agent status
sudo usermod -G gpio distelli

cat << EOF > /home/pi/config.pp
service { 'vncserver-x11-serviced':
  ensure => running,
  enable => true,
}

\$disabled_services = [
  'bluetooth',
  'triggerhappy',
]

service { \$disabled_services:
  ensure => 'stopped',
  enable => 'false',
}
EOF

sudo -i puppet apply /home/pi/config.pp

sudo reboot
