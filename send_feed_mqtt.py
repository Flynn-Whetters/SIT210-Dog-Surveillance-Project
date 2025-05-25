import paho.mqtt.client as mqtt
import sys

command = sys.argv[1] if len(sys.argv) > 1 else "feed"

client = mqtt.Client()
client.connect("broker.hivemq.com", 1883, 60)
client.publish("dogfeeder/command", command)
client.disconnect()
