# post notice if not Raspbian 10 or newer
unless ($facts['os']['name'] == 'Debian') and
  ($facts['os']['distro']['id'] == 'Raspbian') and
  (versioncmp($facts['os']['release']['major'], '10') == 0) {
  notice('This manifest has only been tested Raspbian 10 (buster)')
}

$main_packages = [
  'git',
  'libgl1-mesa-dri',
  'lightdm',
  'realvnc-vnc-server',
  'tmux',
  'x11-xserver-utils',
  'xserver-xorg',
  'vim',
]

$piweatherrock_packages = [
  'libjpeg-dev',
  'libportmidi-dev',
  'libsdl1.2-dev',
  'libsdl-image1.2-dev',
  'libsdl-mixer1.2-dev',
  'libsdl-ttf2.0-dev',
  'libtimedate-perl',
  'python3-pip',
]

package { [ $main_packages, $piweatherrock_packages, ]:
  ensure          => latest,
  install_options => [
    '--no-install-recommends',
  ],
}

# if using Raspbian Lite uncomment the bit below for a minimal desktop and terminal
# package { [ 'awesome', 'lxterminal', ]:
#   ensure          => latest,
#   install_options => [
#     '--no-install-recommends',
#   ],
#   before          => Python::Requirements['/home/pi/PiWeatherRock/requirements.txt'],
# }

# allow all sessions to share the X server
# see https://www.computerhope.com/unix/xhost.htm
file {
  default:
    owner => 'pi',
    group => 'pi',
    mode  => '0755',
  ;
  '/home/pi/bin':
    ensure => directory,
  ;
  '/home/pi/bin/xhost.sh':
    ensure  => file,
    content => @(END),
      #!/bin/bash
      xhost +
      | END
  ;
}

# make lightdm use the xhost settings above
exec { 'enable display-setup-script':
  path    => '/bin:/usr/bin',
  command => "sed -i 's|#display-setup-script=|display-setup-script=/home/pi/bin/xhost.sh|' /etc/lightdm/lightdm.conf",
  unless  => "grep -e '^display-setup-script' /etc/lightdm/lightdm.conf",
}

service { 'vncserver-x11-serviced':
  ensure  => running,
  enable  => true,
  require => Package[$main_packages],
}

vcsrepo { '/home/pi/PiWeatherRock':
  ensure   => latest,
  provider => git,
  source   => 'https://github.com/genebean/PiWeatherRock.git',
}

python::requirements { '/home/pi/PiWeatherRock/requirements.txt':
  virtualenv   => '/home/pi/PiWeatherRock',
  pip_provider => 'pip3',
  owner        => 'pi',
  group        => 'pi',
  cwd          => '/home/pi/PiWeatherRock',
  require      => [
    Package[ $main_packages, $piweatherrock_packages, ],
    Vcsrepo['/home/pi/PiWeatherRock'],
  ],
}

systemd::unit_file { 'PiWeatherRock.service':
  source  => 'file:///home/pi/PiWeatherRock/PiWeatherRock.service',
  require => Python::Requirements['/home/pi/PiWeatherRock/requirements.txt'],
  notify  => Service['PiWeatherRock.service'],
}

service {'PiWeatherRock.service':
  ensure    => running,
  enable    => true,
  require   => Systemd::Unit_file['PiWeatherRock.service'],
  subscribe => [
    File['/home/pi/bin/xhost.sh'],
    Exec['enable display-setup-script'],
    Vcsrepo['/home/pi/PiWeatherRock'],
  ],
}
