import configparser
import obd
import time
import signal
import sys
import paho.mqtt.client as mqtt
from datetime import datetime

payload = ""
config = configparser.ConfigParser()
config.read('config.ini')
fileconf = config['FILE']
mqttconf = config['MQTT']
obdconf = config['OBD']
gpsconf = config['GPS']

def handler(signum, frame):
    print ("Exiting \n")
    client.loop_stop()
    connection.stop()
    file.close()
    sys.exit(0)

#####################################################################################
                        #MQTT Connection#
#####################################################################################
if mqttconf.getboolean('enabled') == True:
    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(client, userdata, flags, rc):
        print("Connected to MQTT with result code "+str(rc))

    def on_publish(client,userdata,result):             #create function for callback
        print("Data published \n")

    #Create MQTT Client
    client = mqtt.Client(client_id=mqttconf['client_id']) 
    client.on_connect = on_connect
    client.on_publish = on_publish

    #Check if we make a tls connection to MQTT server
    if mqttconf.getboolean('tls_enabled') == True:
        client.tls_set(mqttconf['ca_cert'])

    #Create the MQTT Connection
    client.username_pw_set(mqttconf['username'], mqttconf['password'])
    client.connect(mqttconf['server'],port=int(mqttconf['port']))
    client.loop_start()

#####################################################################################
                       #OBD Connection#
#####################################################################################
#Connect to OBD adapter
connection = obd.Async()

#Create OBD Command watchers
connection.watch(obd.commands.RPM)
connection.watch(obd.commands.SPEED)
for x, y in obdconf.items():
    if y == "yes":
        connection.watch(obd.commands.x.upper())

#Start OBD Connection
connection.start()

#####################################################################################
    #Main loop for getting new data and publishing it to MQTT and to file#
#####################################################################################

while True:
    #Start by getting RPM
    r = connection.query(obd.commands.RPM).value.mangitude
    #If configured, get DTC and clear DTC
    if obdconf.getboolean('get_dtc') == True:
        d = connection.query(obd.commands.GET_DTC)
        payload = "DTC:" + d + ","
    if obdconf.getboolean('clear_dtc') == True:
        connection.query(obd.commands.CLEAR_DTC)

    #If RPM = 0 engine is not running and we don't want to send data
    while r > 0:
        #Check if we should write to a file
        if fileconf.getboolean('enabled') == True:
            #Check if we have initialized a file
            if file == "":
                #Open a file with current time as name
                filename = fileconf['location'] + datetime.now() + ".log"
                print("Opening file", filename, "for writing \n")
                file = open(filename,'w')

        #Get rpm and speed
        r = connection.query(obd.commands.RPM).value.mangitude
        s = connection.query(obd.commands.SPEED).value.mangitude
        payload = "RPM:" + r + "," + "SPEED:" + s
        #Listen to a kill signal
        signal.signal(signal.SIGINT, handler)
        
        
        for x, y in obdconf.items():
            if y == "yes":
                #Get all other configured OBD items and add them to the payload
                payload = "," + x + ":" + connection.query(obd.commands.x.upper()).value.magnitude

        if mqttconf.getboolean('enabled') == True:
            #Publish to MQTT if enabled
            print("Publishing data \n")
            publish= client.publish(mqttconf['topic'],payload=payload,qos=int(mqttconf['qos']))
        
        if fileconf.getboolean('enabled') == True:
            #Write data to file if enabled
            print("Writing data to file \n")
            file.write(payload)

        #Clear the payload for next run
        payload = ""
        #Sleep for the MQTT interval
        time.sleep(int(mqttconf['publish_interval']))

    #Engine shut down. Get DTC
    if obdconf.getboolean('get_current_dtc') == True:
        dtc = connection.query(obd.commands.GET_CURRENT_DTC)
        payload = "DTC:" + dtc
        publish= client.publish(mqttconf['topic'],payload)
        file.write(dtc)

    if fileconf.getboolean('enabled') == True:
        print("Closing file \n")
        file.close()
        file = ""

    print("Waiting for car to be switched on \n")
    time.sleep(5)
    signal.signal(signal.SIGINT, handler)