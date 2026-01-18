import paho.mqtt.client as mqtt
host = "192.168.1.87"
client = mqtt.Client("main-raspberrypi")
client.connect(host)


def publish(sensor_name, json_data):
    client.publish("sensor/"+sensor_name, json_data)
