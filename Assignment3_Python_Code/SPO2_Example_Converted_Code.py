import time
import sys
import MAX30105
from spo2_algorithm import maxim_heart_rate_and_oxygen_saturation

# Constants
MAX_BRIGHTNESS = 255

# Create MAX30105 instance
particleSensor = MAX30105.MAX30105()

# Data arrays
irBuffer = [0] * 100
redBuffer = [0] * 100

bufferLength = 100  # Data length
spo2 = 0
validSPO2 = 0
heartRate = 0
validHeartRate = 0

# Pins
pulseLED = 11  # Must be on PWM pin
readLED = 13  # Blinks with each data read

def setup():
    global bufferLength, spo2, validSPO2, heartRate, validHeartRate

    # Initialize sensor
    if not particleSensor.begin():
        sys.exit("MAX30105 was not found. Please check wiring/power.")

    print("Attach sensor to finger with a rubber band. Press Enter to start conversion")
    input()

    ledBrightness = 60
    sampleAverage = 4
    ledMode = 2
    sampleRate = 100
    pulseWidth = 411
    adcRange = 4096

    particleSensor.setup(ledBrightness, sampleAverage, ledMode, sampleRate, pulseWidth, adcRange)

def loop():
    global bufferLength, spo2, validSPO2, heartRate, validHeartRate

    # Read the first 100 samples and determine the signal range
    for i in range(bufferLength):
        while not particleSensor.available():
            particleSensor.check()

        redBuffer[i] = particleSensor.getRed()
        irBuffer[i] = particleSensor.getIR()
        particleSensor.nextSample()

        print(f"red={redBuffer[i]}, ir={irBuffer[i]}")

    # Calculate heart rate and SpO2 after the first 100 samples
    maxim_heart_rate_and_oxygen_saturation(irBuffer, bufferLength, redBuffer)

    # Continuously take samples from MAX30105
    while True:
        for i in range(25, 100):
            redBuffer[i - 25] = redBuffer[i]
            irBuffer[i - 25] = irBuffer[i]

        for i in range(75, 100):
            while not particleSensor.available():
                particleSensor.check()

            # Blink onboard LED with every data read
            readLEDState = not particleSensor.digitalRead(readLED)
            particleSensor.digitalWrite(readLED, readLEDState)

            redBuffer[i] = particleSensor.getRed()
            irBuffer[i] = particleSensor.getIR()
            particleSensor.nextSample()

            print(f"red={redBuffer[i]}, ir={irBuffer[i]}, HR={heartRate}, HRvalid={validHeartRate}, SPO2={spo2}, SPO2Valid={validSPO2}")

        # After gathering 25 new samples, recalculate HR and SpO2
        maxim_heart_rate_and_oxygen_saturation(irBuffer, bufferLength, redBuffer)

if __name__ == "__main__":
    setup()
    loop()