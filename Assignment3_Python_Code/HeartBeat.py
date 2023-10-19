import qwiic_max3010x
import RPi.GPIO as GPIO
#from twilio.rest import Client
import time
import sys

GPIO.setmode(GPIO.BCM)
led_pin = 14
GPIO.setup(led_pin, GPIO.OUT)

#account_sid = 'ACbd7145b887a644feac5a005f70ac28b7'
#auth_token = 'ac2a05ef8dc684e84b2d19b6e23ae9e3'
#client = Client(account_sid, auth_token)

#def CriticalMessage(userName: str, mobileNumber: int):
#    message = client.messages.create(
#        body = "<<{0}>>: CRITICAL LEVEL HEART RATE".format(userName),
#        from_ = '+15017122661',
#        to = "{0}".format(mobileNumber)
#    )

def LEDControl(control: bool):
    if(control):
        GPIO.output(led_pin, True)
    else:
        GPIO.output(led_pin, False)

def millis():
    return int(round(time.time() * 1000))

def runSensor():

    sensor = qwiic_max3010x.QwiicMax3010x()

    if sensor.begin() == False:
        print("The Qwiic MAX3010x device isn't connected to the system. Please check your connection", \
            file=sys.stderr)
        return
    else:
        print("The Qwiic MAX3010x is connected.")

    print("Place your index finger on the sensor with steady pressure.")

    if sensor.setup() == False:
        print("Device setup failure. Please check your connection", \
            file=sys.stderr)
        return
    else:
        print("Setup complete.")

    sensor.setPulseAmplitudeRed(0x0A) # Turn Red LED to low to indicate sensor is running
    sensor.setPulseAmplitudeGreen(0) # Turn off Green LED

    RATE_SIZE = 4 # Increase this for more averaging. 4 is good.
    rates = list(range(RATE_SIZE)) # list of heart rates
    rateSpot = 0
    lastBeat = 0 # Time at which the last beat occurred
    beatsPerMinute = 0.00
    beatAvg = 0
    samplesTaken = 0 # Counter for calculating the Hz or read rate
    startTime = millis() # Used to calculate measurement rate
    
    while True:
                
        irValue = sensor.getIR()
        samplesTaken += 1
        if sensor.checkForBeat(irValue) == True:
            print('BEAT')
            delta = ( millis() - lastBeat )
            lastBeat = millis()
            
            beatsPerMinute = 60 / (delta / 1000.0)
            beatsPerMinute = round(beatsPerMinute,1)
            
            if beatsPerMinute < 255 and beatsPerMinute > 20:
                rateSpot += 1
                rateSpot %= RATE_SIZE
                rates[rateSpot] = beatsPerMinute

                beatAvg = 0
                for x in range(0, RATE_SIZE):
                    beatAvg += rates[x]
                    beatAvg /= RATE_SIZE
                    beatAvg = round(beatAvg)
        
        Hz = round(float(samplesTaken) / ( ( millis() - startTime ) / 1000.0 ) , 2)
        if (samplesTaken % 200 ) == 0:           
            print(\
                'IR=', irValue , ' \t',\
                    'BPM=', beatsPerMinute , '\t',\
                        'Avg=', beatAvg , '\t',\
                            'Hz=', Hz, \
            )
        
        if (beatsPerMinute > 100):
            LEDControl(True)
        else:
            LEDControl(False)

if __name__ == '__main__':
    try:
        runSensor()
    except (KeyboardInterrupt, SystemExit) as exErr:
        print("\nEnding Sensor")
        sys.exit(0)