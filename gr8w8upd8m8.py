#!/usr/bin/env python3
import collections
import subprocess
import sys
import time

import bluetooth

CONTINUOUS_REPORTING = "04"  # Easier as string with leading zero

COMMAND_LIGHT = 11
COMMAND_REPORTING = 12
COMMAND_REQUEST_STATUS = 15
COMMAND_REGISTER = 16
COMMAND_READ_REGISTER = 17

# input is Wii device to host
INPUT_STATUS = 20
INPUT_READ_DATA = 21

EXTENSION_8BYTES = 32
# end "hex" values

BUTTON_DOWN_MASK = 8

TOP_RIGHT = 0
BOTTOM_RIGHT = 1
TOP_LEFT = 2
BOTTOM_LEFT = 3

BLUETOOTH_NAME = "Nintendo RVL-WBC-01"


class EventProcessor:
    def __init__(self):
        self._measured = False
        self.done = False
        self._events = []

    def mass(self, event):
        if event.totalWeight > 30:
            self._events.append(event.totalWeight)
            if not self._measured:
                print("Starting measurement.")
                self._measured = True
        elif self._measured:
            self.done = True

    @property
    def weight(self):
        if not self._events:
            return 0
        histogram = collections.Counter(round(num, 3) for num in self._events)
        return histogram.most_common(1)[0][0]


class BoardEvent:
    def __init__(
        self, topLeft, topRight, bottomLeft, bottomRight, buttonPressed, buttonReleased
    ):

        self.topLeft = topLeft
        self.topRight = topRight
        self.bottomLeft = bottomLeft
        self.bottomRight = bottomRight
        self.buttonPressed = buttonPressed
        self.buttonReleased = buttonReleased
        # convenience value
        self.totalWeight = topLeft + topRight + bottomLeft + bottomRight


class Wiiboard:
    def __init__(self, processor):
        # Sockets and status
        self.receivesocket = None
        self.controlsocket = None

        self.processor = processor
        self.calibration = []
        self.calibrationRequested = False
        self.LED = False
        self.address = None
        self.buttonDown = False
        for i in range(3):
            self.calibration.append([])
            for j in range(4):
                self.calibration[i].append(
                    10000
                )  # high dummy value so events with it don't register

        self.status = "Disconnected"
        self.lastEvent = BoardEvent(0, 0, 0, 0, False, False)

        try:
            self.receivesocket = bluetooth.BluetoothSocket(bluetooth.L2CAP)
            self.controlsocket = bluetooth.BluetoothSocket(bluetooth.L2CAP)
        except ValueError:
            raise Exception("Error: Bluetooth not found")

    def isConnected(self):
        return self.status == "Connected"

    # Connect to the WiiBoard at bluetooth address <address>
    def connect(self, address):
        if address is None:
            print("Non existant address")
            return
        self.receivesocket.connect((address, 0x13))
        self.controlsocket.connect((address, 0x11))
        if self.receivesocket and self.controlsocket:
            print("Connected to WiiBoard at address " + address)
            self.status = "Connected"
            self.address = address
            self.calibrate()
            useExt = "00" + str(COMMAND_REGISTER) + "04" + "A4" + "00" + "40" + "00"
            self.send(useExt)
            self.setReportingType()
            print("WiiBoard connected")
        else:
            print("Could not connect to WiiBoard at address " + address)

    def receive(self):
        # try:
        #   self.receivesocket.settimeout(0.1)       #not for windows?
        while self.status == "Connected" and not self.processor.done:
            data = self.receivesocket.recv(25)
            intype = int(data.hex()[2:4])
            if intype == INPUT_STATUS:
                # TODO: Status input received. It just tells us battery life really
                self.setReportingType()
            elif intype == INPUT_READ_DATA:
                if self.calibrationRequested:
                    print("Calibration input received")
                    packetLength = int(int(data[4:5].hex(), 16) / 16) + 1
                    endSlice = 7 + packetLength
                    calibrationResponse = data[7:endSlice]
                    self.parseCalibrationResponse(calibrationResponse)

                    if packetLength < 16:
                        print("Ready for input, please stand on WiiBoard")
                        self.calibrationRequested = False
            elif intype == EXTENSION_8BYTES:
                boardEvent = self.createBoardEvent(data[2:12])
                self.processor.mass(boardEvent)
            else:
                print("ACK to data write received")

        self.status = "Disconnected"
        self.disconnect()

    def disconnect(self):
        if self.status == "Connected":
            self.status = "Disconnecting"
            while self.status == "Disconnecting":
                self.wait(100)
        try:
            self.receivesocket.close()
        except:
            pass
        try:
            self.controlsocket.close()
        except:
            pass
        print("WiiBoard disconnected")

    # Try to discover a Wiiboard
    def discover(self):
        print("Press the red sync button on the board now")
        address = None
        bluetoothdevices = bluetooth.discover_devices(duration=10, lookup_names=True)
        for bluetoothdevice in bluetoothdevices:
            if bluetoothdevice[1] == BLUETOOTH_NAME:
                address = bluetoothdevice[0]
                print("Found WiiBoard at address " + address)
        if address is None:
            print("No WiiBoard discovered.")
        return address

    def createBoardEvent(self, bytes):
        buttonBytes = bytes[0:2]
        bytes = bytes[2:12]
        buttonPressed = False
        buttonReleased = False

        state = (int(buttonBytes[0:1].hex(), 16) << 8) | int(buttonBytes[1:2].hex(), 16)
        if state == BUTTON_DOWN_MASK:
            buttonPressed = True
            if not self.buttonDown:
                print("Button pressed")
                self.buttonDown = True

        if not buttonPressed:
            if self.lastEvent.buttonPressed:
                buttonReleased = True
                self.buttonDown = False
                print("Button released")

        rawTR = (int(bytes[0:1].hex(), 16) << 8) + int(bytes[1:2].hex(), 16)
        rawBR = (int(bytes[2:3].hex(), 16) << 8) + int(bytes[3:4].hex(), 16)
        rawTL = (int(bytes[4:5].hex(), 16) << 8) + int(bytes[5:6].hex(), 16)
        rawBL = (int(bytes[6:7].hex(), 16) << 8) + int(bytes[7:8].hex(), 16)

        topLeft = self.calcMass(rawTL, TOP_LEFT)
        topRight = self.calcMass(rawTR, TOP_RIGHT)
        bottomLeft = self.calcMass(rawBL, BOTTOM_LEFT)
        bottomRight = self.calcMass(rawBR, BOTTOM_RIGHT)
        boardEvent = BoardEvent(
            topLeft, topRight, bottomLeft, bottomRight, buttonPressed, buttonReleased
        )
        return boardEvent

    def calcMass(self, raw, pos):
        val = 0.0
        # calibration[0] is calibration values for 0kg
        # calibration[1] is calibration values for 17kg
        # calibration[2] is calibration values for 34kg
        if raw < self.calibration[0][pos]:
            return val
        elif raw < self.calibration[1][pos]:
            val = 17 * (
                (raw - self.calibration[0][pos])
                / float((self.calibration[1][pos] - self.calibration[0][pos]))
            )
        elif raw > self.calibration[1][pos]:
            val = 17 + 17 * (
                (raw - self.calibration[1][pos])
                / float((self.calibration[2][pos] - self.calibration[1][pos]))
            )

        return val

    def getEvent(self):
        return self.lastEvent

    def getLED(self):
        return self.LED

    def parseCalibrationResponse(self, bytes):
        index = 0
        if len(bytes) == 16:
            for i in range(2):
                for j in range(4):
                    self.calibration[i][j] = (
                        int((bytes[index : index + 1]).hex(), 16) << 8
                    ) + int((bytes[index + 1 : index + 2]).hex(), 16)
                    index += 2
        elif len(bytes) < 16:
            for i in range(4):
                self.calibration[2][i] = (
                    int(bytes[index : index + 1].hex(), 16) << 8
                ) + int(bytes[index + 1 : index + 2].hex(), 16)
                index += 2

    # Send <data> to the Wiiboard
    # <data> should be an array of strings, each string representing a single hex byte
    def send(self, dataHex):
        if self.status != "Connected":
            return

        updatedHex = "52" + dataHex[2:]

        self.controlsocket.send(bytes.fromhex(updatedHex))

    # Turns the power button LED on if light is True, off if False
    # The board must be connected in order to set the light
    def setLight(self, light):
        if light:
            val = "10"
        else:
            val = "00"

        message = "00" + str(COMMAND_LIGHT) + val
        self.send(message)
        self.LED = light

    def calibrate(self):
        message = (
            "00" + str(COMMAND_READ_REGISTER) + "04" + "A4" + "00" + "24" + "00" + "18"
        )
        print("Requesting calibration")
        self.send(message)
        self.calibrationRequested = True

    def setReportingType(self):
        # bytearr = ["00", COMMAND_REPORTING, CONTINUOUS_REPORTING, EXTENSION_8BYTES]
        bytearr = (
            "00"
            + str(COMMAND_REPORTING)
            + str(CONTINUOUS_REPORTING)
            + str(EXTENSION_8BYTES)
        )
        self.send(bytearr)

    def wait(self, millis):
        time.sleep(millis / 1000.0)


def main():
    processor = EventProcessor()

    board = Wiiboard(processor)
    if len(sys.argv) == 1:
        print("Discovering board...")
        address = board.discover()
    else:
        address = sys.argv[1]

    print("Trying to connect...")
    board.connect(address)  # The wii board must be in sync mode at this time
    board.wait(200)
    # Flash the LED so we know we can step on.
    board.setLight(False)
    board.wait(500)
    board.setLight(True)
    board.receive()

    print(processor.weight)


if __name__ == "__main__":
    main()
