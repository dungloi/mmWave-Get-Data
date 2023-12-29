#!/usr/bin/env python

# Copyright (c) 2019-2022, NVIDIA CORPORATION. All rights reserved.
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import Jetson.GPIO as GPIO
import time, threading

OUTPUT_PINS = {
    "JETSON_ORIN_NX": 32,
}


class HardwareTrigger:
    def __init__(self, gpio_high_duration_s, pulse_duration_s) -> None:
        self.output_pin = OUTPUT_PINS.get(GPIO.model, None)
        if self.output_pin is None:
            raise Exception("PWM not supported on this board")
        # Pin Setup:
        # Board pin-numbering scheme
        GPIO.setmode(GPIO.BOARD)
        # set pin as an output pin with optional initial state of LOW
        GPIO.setup(self.output_pin, GPIO.OUT, initial=GPIO.LOW)

        self.high_dur = gpio_high_duration_s
        self.pulse_dur = pulse_duration_s
        self.trigger_cnt = 0

    def trigger(self, event, callback=None) -> float:
        try:
            # Wait for the event to be set
            while event.wait(self.pulse_dur * 2):
                trigger_time = time.time()

                GPIO.output(self.output_pin, GPIO.HIGH)
                time.sleep(self.high_dur)
                GPIO.output(self.output_pin, GPIO.LOW)

                # call the time stamp writing callback
                if callback:
                    callback("TRIGGERED No.",self.trigger_cnt, trigger_time)

                self.trigger_cnt += 1
                # Reset the event
                event.clear()
        finally:
            print("Timeout. Trigger killed!")

    def __del__(self):
        GPIO.cleanup()


if __name__ == "__main__":
    cnt = 0
    pulse_dur = 0.1

    def callback(cnt, ts):
        print(f"trigger ts in sub thread: {ts}, num: {cnt}")

    trigger = HardwareTrigger(5e-6, pulse_dur)
    trigger_event = threading.Event()
    trigger_thread = threading.Thread(target=lambda: trigger.trigger(trigger_event, callback))

    start_ts = time.time()
    trigger_thread.start()
    while True:
        ts = time.time()
        if ts - start_ts > cnt * pulse_dur:
            trigger_event.set()
            print(f"trigger ts in main thread: {ts}, num: {cnt}")
            cnt += 1
