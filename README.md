# Gr8W8Upd8M8

## A Wii balance board weight reporter

This script is based on [wiiboard-simple](https://code.google.com/p/wiiboard-simple/), with some dependencies (like
pygame) removed. I'm pretty sure it only works on Linux.

## Requirements

To run `gr8w8upd8m8`, you need:
* Linux.
* The `bluez-utils` package (you might need to install also `python-bluez`).
* Bluetooth.

## Usage

You can run it with:

    ./gr8w8upd8m8.py

It will prompt you to put the board in sync mode and it will search for and connect to it.

If you already know the address, you can just specify it:

    ./gr8w8upd8m8.py <board address>

That will skip the discovery process, and connect directly.

`gr8w8upd8m8` uses the `bluez-test-device` utility of `bluez-utils` to disconnect the board at the end, which causes
the board to shut off. Pairing it with the OS will allow you to use the front button to reconnect to it and run the
script.

Calculating the final weight is done by calculating the mode of all the event data, rounded to one decimal digit.

Feel free to use processor.weight to do whatever you want with the calculated weight (I send it to a server for
further pointless processing).

## License

This software is made available under the [Lesser GPL license](http://www.gnu.org/licenses/lgpl.html).
