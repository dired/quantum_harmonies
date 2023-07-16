// This sketch for "Quantum Harmonies" builds upon a heavily modified version of https://github.com/kapraran/FreqCountESP

#include "FreqCountESP.h"
#include <ArduinoMqttClient.h>
#include <WiFi.h>

int inputPin = 14;
int timerMs = 1;

void setup()
{
  Serial.begin(115200);
  while(!Serial){delay(100);}


  FreqCountESP.begin(inputPin, timerMs);
}

void loop()
{
  if (FreqCountESP.available())
  {
    uint32_t frequency = FreqCountESP.read();
    uint64_t timestamp = FreqCountESP.read2();
  }
}
