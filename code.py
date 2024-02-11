#
#
# Major = C E G

import analogio
import digitalio

from time import sleep

from board import A0, A1, A2, GP21, GP22, LED
from math import copysign

import usb_midi

import adafruit_midi
from adafruit_midi.control_change import ControlChange
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn
from adafruit_midi.pitch_bend import PitchBend

midi = adafruit_midi.MIDI( midi_out=usb_midi.ports[1], out_channel=0 )
print("Midi test")
print("Default output channel:", midi.out_channel + 1)

p21 = digitalio.DigitalInOut(GP21)
p21.direction = digitalio.Direction.INPUT
p21.pull = digitalio.Pull.UP

p22 = digitalio.DigitalInOut(GP22)
p22.direction = digitalio.Direction.INPUT
p22.pull = digitalio.Pull.UP

infoled = digitalio.DigitalInOut(LED)
infoled.direction = digitalio.Direction.OUTPUT
infoled.value = False

# Debug level allows me to check state during the debugging
#   2 - print all that happens
#   1 -
#   0 - no debugging
#
debuglevel = 0

# Levels when "delta" will mean the changing of finger state
#   you can monitor it with debuglevel =2 and choose the correct one
#
#   activationvalue - when the finger goes active (down)
#   deactivationvalue - when the finger return to relax state (up)
#
activationvalue = 3000
deactivationvalue = 2500

# This is the class to support flex sensors
#
#   pinid = pin number as in analogio
#   scale = 1 for 10k and 2 for 20k flex sensors
#
class AnalogFinger(object) :

    def __init__(self, name, pinid, scale, tone) :
        self.name = name
        self.pin = analogio.AnalogIn(pinid)
        self.tone = tone
        self.relaxed = self.pin.value
        self.current = self.pin.value
        self.activated = False
        self.volume = 0
        self.i = scale
        self.step = ""
        self.delta = 0
        self.normvalue = 0

    def relax(self) :
        self.relaxed = self.pin.value
        self.current = self.pin.value
        self.activated = False
        if debuglevel == 2 :
            print("Relaxed")

    def onloop(self) :
        self.delta = copysign(self.pin.value - self.relaxed, 1.0)

        if self.delta>activationvalue and self.activated is not True :
            self.activated = True
            self.normvalue = self.delta / self.i
            self.volume = 120 #int([4500, self.normvalue][self.normvalue <4500] / 36)
            midi.send(NoteOn(self.tone, self.volume))
            self.step = "Activ"
        elif self.delta<deactivationvalue and self.activated is True :
            self.activated = False
            self.volume = 0
            midi.send(NoteOff(self.tone, self.volume))
            self.step = "De-ac"
        else :
            self.step = "     "

        if debuglevel == 2 :
            print(self.step, self.name, self.pin.value, self.activated, int(self.delta), self.volume, sep="\t")
            pass

    def value(self) :
        return self.pin.value

    # End of Analog Finger

pinA = AnalogFinger("A", A0, 2, "C#1")
pinB = AnalogFinger("B", A1, 2, "E#1")
pinC = AnalogFinger("C", A2, 1, "G#1")

while True:
    if p22.value :
        pinA.onloop()
        pinB.onloop()
        pinC.onloop()
    else :
        pinA.relax()
        pinB.relax()
        pinC.relax()
        while not p22.value :
            infoled.value = True
            sleep(0.01)
        infoled.value = False

    if debuglevel == 2 :
        sleep(0.5)
    else :
        sleep(0.07)
