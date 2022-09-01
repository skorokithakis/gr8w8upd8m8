# Gr8W8Upd8M8

[![Code Shelter](https://www.codeshelter.co/static/badges/badge-flat.svg)](https://www.codeshelter.co/)

## A Wii balance board weight reporter

This script is based on [wiiboard-simple](https://code.google.com/p/wiiboard-simple/), with some dependencies (like
pygame) removed. I'm pretty sure it only works on Linux.

## Requirements

To run `gr8w8upd8m8`, you need:
* Recent version of Linux (e.g 5.15 kernel)
* Python 3
* Bluetooth (install `bluez` and `python3-bluez`). Bluez 5+ should be fine.

## Quickstart

 1. Get a Raspberry Pi
 1. Put the [Raspberry Pi OS Lite](https://www.raspberrypi.com/software/) on a SD card, and follow basic setup instructions
 1. Open a terminal on the Raspberry Pi (by SSHing or directly)
 1. Install necessary bluetooth software: `sudo apt-get install bluetooth bluez python3-bluez`
 1. Clone project
 1. Run script `./gr8w8upd8m8.py` (runs in userspace, no `sudo` required)
 1. Follow the instructions (note: sync button is in the battery compartment)
 1. When you're done, you should see output like the following, with your weight in kg at the bottom:
```
$ ./gr8w8upd8m8.py
Discovering board...
Press the red sync button on the board now
Found WiiBoard at address 00:22:4C:47:BC:9B
Trying to connect...
Connected to WiiBoard at address 00:22:4C:47:BC:9B
Requesting calibration
WiiBoard connected
ACK to data write received
Calibration input received
Calibration input received
Ready for input, please stand on WiiBoard
Starting measurement.
WiiBoard disconnected
77.62
```

## Environment tested on

```
$ cat /proc/cpuinfo | grep Model
Model           : Raspberry Pi 4 Model B Rev 1.1

$ uname -a
Linux raspberrypi 5.15.56-v8+ #1575 SMP PREEMPT Fri Jul 22 20:31:26 BST 2022 aarch64 GNU/Linux

$ dpkg -l | grep blue
ii  bluetooth                            5.55-3.1+rpt1                    all          Bluetooth support (metapackage)
ii  bluez                                5.55-3.1+rpt1                    arm64        Bluetooth tools and daemons
ii  bluez-firmware                       1.2-4+rpt8                       all          Firmware for Bluetooth devices
ii  libbluetooth3:arm64                  5.55-3.1+rpt1                    arm64        Library to use the BlueZ Linux Bluetooth stack
ii  pi-bluetooth                         0.1.19                           all          Raspberry Pi 3 bluetooth
ii  python3-bluez                        0.23-3                           arm64        Python 3 wrappers around BlueZ for rapid bluetooth development
```

## Constant running

While there will undoubtedly be a better Python way to do this, I run the script repeatedly in a `screen` session.

```sh
screen

while true; do ./gr8w8upd8m8.py; sleep 4; done
```

This will endlessly look for the board, so you can forget about having to run the script, and all you need to do is press the sync button.

## Pitfalls

Very very occasionally, the board can get into a state where it only reads zero as weight, and will continue to do so even after power cycling. When you run the script, the light on the board stays solid but it will never measure (as the script ignores any weight under 30Kg).

To fix this:
 1. The board needs to run through the correct initialisation sequence, so get your hands on a Wii + Wii Fit software and run the body test until you start getting readings from the board. It might take a few power cycles of the board and the Wii
 1. Ensure the batteries are charged.

## License

This software is made available under the [Lesser GPL license](http://www.gnu.org/licenses/lgpl.html).

## Credits

This project is a mix of various scripts and samples. Thanks go to:

* [wiiboard-simple](https://code.google.com/p/wiiboard-simple/), for providing the base script.
* [Ryan Myers](https://github.com/Ryan-Myers/), for his [Wiiboard-Net](https://github.com/Ryan-Myers/Wiiboard-Net)
project
