import os
import json
import time
import shutil
import subprocess
import random
import paho.mqtt.client as mqtt
import dacite
from dacite import from_dict

from airtag import Item


home = os.path.expanduser('~')
temp_file = '/tmp/air-tags'
last_mtime = 0
broker = 'mqtt.c3voc.de'
port = 1883
username = 'script'
password = os.environ['PASSWORD']
topic = '/owntracks/voc'
client_id = f'airtag2mqtt-{random.randint(0, 1000)}'
mq = None


def main():
    global mq
    mq = connect_mqtt()
    mq.loop_start()

    while True:
        checkRunning()
        process_locations()
        time.sleep(60)


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    # Set Connecting Client ID
    client = mqtt.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def publish_location(item: Item):
    # https://owntracks.org/booklet/tech/json/#_typelocation
    slug = item.name.replace(' ', '').tolower()
    print(item)
    result = mq.publish(f"{topic}/{slug}", {
        '_type': 'location',
        'lat': item.location.latitude,
        'lon': item.location.longitude,
        'batt': (6 - item.battery_status) * 20,
        'tid': item.name.split(' ')[1],
        'tst': item.location.time_stamp
    })
    # result: [0, 1]
    status = result[0]
    if status == 0:
        print(f"Send location of `{item.name}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")


def process_locations():
    global last_mtime

    print("Starting to read locations")

    try:
        current_mtime = os.path.getmtime(home + '/Library/Caches/com.apple.findmy.fmipcore/Items.data')
        if not current_mtime > last_mtime:
            print("Skipping file hasn't changed")
            return last_mtime
        last_mtime = current_mtime
        shutil.copyfile(home + '/Library/Caches/com.apple.findmy.fmipcore/Items.data', temp_file)
    except Exception as e:
        print("Unable to copy file, check permissions")
        print(e)
        exit(2)

    with open(temp_file) as json_file:
        data = json.load(json_file)
        for item in data:

            print('.', end='')
            publish_location(from_dict(data_class=Item, data=item), config=dacite.Config(check_types=False))

            '''
            name=t["name"]
            model_name=t["productType"]["productInformation"]["modelName"]
            serialnumber=t["serialNumber"]
            producttype=t["productType"]["type"]
            productindentifier=t["productType"]["productInformation"]["productIdentifier"]
            vendoridentifier=t["productType"]["productInformation"]["vendorIdentifier"]
            antennapower=t["productType"]["productInformation"]["antennaPower"]
            systemversion=t["systemVersion"]
            batterystatus=t["batteryStatus"]
            locationpositiontype=t["location"]["positionType"]
            locationlatitude=t["location"]["latitude"]
            locationlongitude=t["location"]["longitude"]
            locationtimestamp=t["location"]["timeStamp"]
            locationverticalaccuracy=t["location"]["verticalAccuracy"]
            locationhorizontalaccuracy=t["location"]["horizontalAccuracy"]
            locationfloorlevel=t["location"]["floorLevel"]
            locationaltitude=t["location"]["altitude"]
            locationisinaccurate=t["location"]["isInaccurate"]
            locationisold=t["location"]["isOld"]
            locationfinished=t["location"]["locationFinished"]
            addresslabel=t["address"]["label"]
            addressstreetaddress=t["address"]["streetAddress"]
            addresscountrycode=t["address"]["countryCode"]
            addressstatecode=t["address"]["stateCode"]
            addressadministrativearea=t["address"]["administrativeArea"]
            addressstreetname=t["address"]["streetName"]
            addresslocality=t["address"]["locality"]
            addresscountry=t["address"]["country"]
            try:
                addressareaofinterest0=t["address"]["areaOfInterest"][0]
            except Exception:
                addressareaofinterest0=""
            try:
                addressareaofinterest1=t["address"]["areaOfInterest"][1]
            except Exception:
                addressareaofinterest1=""
            batterystatus=t["batteryStatus"]
            '''

    print("\nDone, sleeping")
    return last_mtime


def checkRunning():
    output = int(subprocess.getoutput('ps aux|grep "FindMy.app/Contents/MacOS/FindM[y]"|wc -l'))
    if output <= 0:
        print("FindMy not running so attempting to start")
        subprocess.getoutput("open /System/Applications/FindMy.app")


if __name__ == "__main__":
    main()
