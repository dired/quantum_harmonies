# Quantum Harmonies
“Quantum harmonies” is an art project that intertwines
geiger counter measurements with a simulated
quantum computing circuit, translating emerging dynamics
into a captivating musical experience.
Following an approach, where the most meaningful relationships
between the concepts are tried to be established,
the project explores the notions of superposition, entanglement,
measurement, and effects of radiation.
Drawing inspiration from the many-worlds interpretation
of quantum mechanics, the life of a hypothetical musical
quantum organism whose sole sensory organ is a geiger
counter was modeled. Characteristic effects taking place
during it’s journey are portrayed visually and audibly, aiming
to offer an immersive way of understanding the dynamic
relationship between geiger counter measurements
and quantum concepts.

## Requirements for the hardware

- ESP32
- geiger counter that emits pulses
- Arduino IDE

For the software in `software/esp32` to work in your environment, the mqtt-broker-address, mqtt-topics, wifi-ssid and -password have to be set in `software/esp32/FreqCountESP.cpp`.

The ESP32 running the code will wait for arriving pulses from a geiger counter (worth to mention, it could be something else). In our code, PIN 14 is configured as the pulse-receiving PIN. By the arrival of a pulse, an interrupt is triggered to measure the exact timestamp. Every 1ms, the existence of data is checked, and if a pulse was added to a list, the whole list is sent to MQTT broker via the configured topic.

## Requirements for the software

- python3
- `pip install paho-mqtt`
- `pip install python-rtmidi`
- 4 webbrowser tabs running [Q1Synth][https://iccmr-q1synth.cephasteom.co.uk/]
- 4 virtual midi devices (if on windows: [loopMidi][https://www.tobias-erichsen.de/software/loopmidi.html])

For the software to run on another system than windows, no extra software like loopMidi may be necessary. I have not tried, please look for the way to create fake midi devices for your operating system if it is not windows for yourself.

For my environment, I have for now hard-coded the indices of the midi-devices. Please refer to [python-rtmidi][https://spotlightkid.github.io/python-rtmidi/readme.html] and make the changes necessary for your environment at the beginnning of `software/esp32/quantum_harmonies.py`.

Otherwise, four midi devices at the specified indices in code are assumed.

Likewise, the 4 running instances of Q1Synth have to be configured to the correct midi port (first click "advanced", then "config" on the right hand side).

The mqtt-broker's address has to be configured at the very bottom of `quantum_harmonies.py` through the line stating `client.connect("192.168.0.3", 1883, 60)`.

Then, the model watches for the expected mqtt-messages carrying the timestamps, and generates quantum harmonics.
