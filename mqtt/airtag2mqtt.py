import os
import json
import time
import shutil
import subprocess
import random
import paho.mqtt.client as mqtt
from dacite import from_dict

from airtag import Item

import logging


VALID_PREFIXES = {
    'audio',
    'case',
    'regie',
    'server',
}


home = os.path.expanduser('~')
source_file = home + '/Library/Caches/com.apple.findmy.fmipcore/Items.data'
# source_file = './temp.json'
temp_file = '/tmp/air-tags'
last_mtime = 0

broker = 'mqtt.c3voc.de'
port = 1883
username = 'script'
password = os.environ['PASSWORD']
topic = 'owntracks/voc'
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
            logging.info("Connected to MQTT Broker!")
        else:
            logging.error("Failed to connect, return code %d\n", rc)
    # Set Connecting Client ID
    client = mqtt.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def publish_location(item: Item, raw):
    # https://owntracks.org/booklet/tech/json/#_typelocation
    slug = item.name.replace(' ', '').lower()
    allowlisted_slug = False
    for prefix in VALID_PREFIXES:
        if slug.startswith(prefix):
            allowlisted_slug = True
    if not allowlisted_slug:
        logging.info(f"Skipping {slug} because not in VALID_PREFIXES")
    logging.debug(item)
    result = mq.publish(f"{topic}/{slug}", json.dumps({
        '_type': 'location',
        'lat': item.location.latitude,
        'lon': item.location.longitude,
        'batt': (6 - item.batteryStatus) * 20,
        'tid': item.role.emoji,  # item.name.split(' ')[1],
        'tst': int(item.location.timeStamp/1000), # apple does ms, owntracks does seconds
        'raw': raw
    }))
    # result: [0, 1]
    status = result[0]
    if status == 0:
        logging.info(f"Sent location of `{item.role.emoji} {item.name}` to topic `{topic}/{slug}`")
    else:
        logging.error(f"Failed to send message to topic {topic}/{slug}")


def process_locations():
    global last_mtime

    print("Starting to read locations")

    try:
        current_mtime = os.path.getmtime(source_file)
        if not current_mtime > last_mtime:
            logging.debug("Skipping file hasn't changed")
            return last_mtime
        last_mtime = current_mtime
        shutil.copyfile(source_file, temp_file)
    except Exception as e:
        logging.error("Unable to copy file, check permissions")
        logging.exception(e)
        exit(2)

    with open(temp_file) as json_file:
        data = json.load(json_file)
        for item in data:
            try:
                publish_location(from_dict(data_class=Item, data=item), item)
            except Exception as e:
                logging.exception(e)
                logging.debug(item)

    logging.info("Done, sleeping")
    return last_mtime


def checkRunning():
    output = int(subprocess.getoutput('ps aux|grep "FindMy.app/Contents/MacOS/FindM[y]"|wc -l'))
    if output <= 0:
        logging.warning("FindMy not running so attempting to start")
        subprocess.getoutput("open /System/Applications/FindMy.app")


if __name__ == "__main__":
    main()
