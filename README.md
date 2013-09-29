# Gr8W8Upd8M8

## A Wii balance board weight reporter

This script is based on [wiiboard-simple](https://code.google.com/p/wiiboard-simple/), with some dependencies (like
pygame) removed. I'm pretty sure it only works on Linux.

## Requirements

To run `gr8webupd8m8`, you need:
* Linux.
* The `bluez-tools` package.
* Bluetooth.

## Usage

You can run it with:

    ./gr8w8upd8m8.py

It will prompt you to put the board in sync mode and it will search for and connect to it.

If you already know the address, you can just specify it:

    ./gr8w8upd8m8.py <board address>

That will skip the discovery process, and connect directly.

`gr8w8upd8m8` uses the `bt-device` utility of `bluez-tools` to disconnect the board at the end, which causes the board
to shut off. Pairing it with the OS will allow you to use the front button to reconnect to it and run the script.

Weight calculation is done by histogramming all values rounded to one decimal digit and picking the most frequent.

Feel free to use processor.weight to do whatever you want with the calculated weight (I send it to a server for
further pointless processing).
