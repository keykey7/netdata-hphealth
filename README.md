<!--
title: "HP-Health monitoring with Netdata"
custom_edit_url: https://github.com/netdata/netdata/edit/master/collectors/python.d.plugin/hphealth/README.md
sidebar_label: "HP-Health"
-->

# HP-Health monitoring with Netdata

Monitors a local HPE ProLiant server using hp-health statistics a replacement for 'lm-sensors'.

## Requirements

- A local installation of the "ProLiant Management Command Line Interface Utility (`hpasmcli`)"
  This is usually not part of the standard repos, get it directly from HPE.
- password-less sudo access to the used "show" commands (if not running netdata as root)

To allow sudo without password for that specific read-only command execute `sudo visudo` and add the line:
```
netdata ALL=(ALL:ALL) NOPASSWD:/usr/sbin/hpasmcli -s show temp;show fans;show powersupply
```
The plugin will check this configuration at startup and recommend a propper setting. 

## Charts
This module will produce following charts (if data is available):

- Temperature charts for each detected temperature sensor separated by sensor location
- Fan charts for each detected fan speed sensor separated by sensor location
- A fan partner overview listing the amount of fans per partner group 
  (redundant fans in the same partner group can take over in the case of a fan failure)
- A power consumption chart per power supply
- A power supply chart counting the bays in ok condition 

## Alerts
This module will warn if:

- any temperature sensor comes close to 5°C of its predifened threshold value
- any fan partner group looses a fan
- a power supply changes to an unhealthy condition
