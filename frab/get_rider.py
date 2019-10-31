#!/usr/bin/env python3
# vim: tabstop=4 shiftwidth=4 expandtab

import requests
import json
import os
from dotenv import load_dotenv
from lxml import etree
import logging
loglevel = logging.INFO
logging.basicConfig(level=loglevel, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv(verbose=True)

FRAB_ACRONYM = os.getenv("FRAB_ACRONYM")
FRAB_LOGIN_URL = os.getenv("FRAB_LOGIN_URL")
FRAB_JSON_URL = os.getenv("FRAB_JSON_URL")
FRAB_USERNAME = os.getenv("FRAB_USERNAME")
FRAB_PASSWORD = os.getenv("FRAB_PASSWORD")
WEKAN_USERNAME = os.getenv("WEKAN_USERNAME")
WEKAN_PASSWORD = os.getenv("WEKAN_PASSWORD")
WEKAN_URL = os.getenv("WEKAN_URL")
WEKAN_BOARD = os.getenv("WEKAN_BOARD")
WEKAN_SWIMLANE = os.getenv("WEKAN_SWIMLANE")
WEKAN_LIST = os.getenv("WEKAN_LIST")
WEKAN_USER = os.getenv("WEKAN_USER")
LOCAL = False

def wekan_auth():
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*'
    }

    r = requests.post(WEKAN_URL + '/users/login', data={
        "username" : WEKAN_USERNAME,
        "password" : WEKAN_PASSWORD
    }, headers = headers)

    return r.json()['token']


def grab_frab_data():
    if not LOCAL:
        logging.info('Getting live data from frab')
        sess = requests.Session()
        new_session_page = sess.get(FRAB_LOGIN_URL)
        tree = etree.HTML(new_session_page.text)
        auth_token = tree.xpath("//meta[@name='csrf-token']")[0].get("content")
        login_data = dict()
        login_data['user[email]'] = FRAB_USERNAME
        login_data['user[password]'] = FRAB_PASSWORD
        login_data['user[remember_me]'] = 1
        login_data['authenticity_token'] = auth_token
        sess.post(FRAB_LOGIN_URL, login_data, verify=False)
        talks_json = sess.get(FRAB_JSON_URL, verify=False, stream=True)
        with open('tech_rider.json', 'w') as fd:
            fd.write(talks_json.text)
            fd.close()
        talks = json.loads(talks_json.text)

    else:
        logging.info('Using local cached data')
        with open('tech_rider.json', 'r') as fd:
            talks = json.loads(fd.read())
            fd.close()

    return talks

def check_card(title):
    get_cards = requests.get(WEKAN_URL + '/api/boards/' + WEKAN_BOARD + '/lists/' + WEKAN_LIST + '/cards', headers=headers)
    found = []
    for card in get_cards.json():
        if card['title'] == title:
            found.append(card['title'])
            found.append(card['description'])
            found.append(card['_id'])
            continue
        else:
            continue
    logging.debug('found: ' + str(found))

    return found

def add_card(title, description, eventid):
    send = '{ "title": "' + title + '", "description": "' + description + '", "authorId": "' + WEKAN_USER + '", "swimlaneId": "' + WEKAN_SWIMLANE + '" }'
    data = send.encode('utf-8')

    r = requests.post(WEKAN_URL + '/api/boards/' + WEKAN_BOARD + '/lists/' + WEKAN_LIST + '/cards', headers=headers, data=data)

    logging.debug(r.request.url)
    logging.debug(r.request.body)
    logging.debug(r)
    logging.debug(r.json())
    response = r.json()
    card_id = response['_id']
    logging.debug('card id: ' + card_id)

    get_card = requests.get(WEKAN_URL + '/api/boards/' + WEKAN_BOARD + '/lists/' + WEKAN_LIST + '/cards/' + card_id, headers=headers)

    logging.debug(get_card.request.url)
    logging.debug(get_card.request.body)
    logging.debug(get_card)
    logging.debug(get_card.json())
    created = str(get_card.json()['createdAt'])

    send = '{ "receivedAt": "' + created + '" }'
    #, "customFields": "' + guid + '" }'
    data = send.encode('utf-8')

    update = requests.put(WEKAN_URL + '/api/boards/' + WEKAN_BOARD + '/lists/' + WEKAN_LIST + '/cards/' + card_id, headers=headers, data=data)

    logging.debug(update.request.url)
    logging.debug(update.request.body)
    logging.debug(update)
    logging.debug(update.json())

    return True

def update_card(card, title, description, eventid):
    send = '{ "title": "' + title + '", "description": "' + description + '" }'
    data = send.encode('utf-8')

    update = requests.put(WEKAN_URL + '/api/boards/' + WEKAN_BOARD + '/lists/' + WEKAN_LIST + '/cards/' + card, headers=headers, data=data)

    logging.debug(update.request.url)
    logging.debug(update.request.body)
    logging.debug(update)
    logging.debug(update.json())

    return True

if __name__== "__main__":
    WEKAN_TOKEN = wekan_auth()
    headers = {
        'Authorization': 'Bearer ' + WEKAN_TOKEN,
        'Content-type': 'application/json',
    }
    talks = grab_frab_data()

    for key in talks['report']['events']:
        logging.debug('id: ' + str(key['id']))
        logging.debug('guid: ' + str(key['guid']))
        logging.debug('title: ' + key['title'])
        logging.debug('tech_rider: ' + key['tech_rider'])

        title = str(key['id']) + ': ' + key['title']
        desc = key['tech_rider']
        desc = desc.replace('\r', '')
        desc = desc.replace('\n', '<br />')
        eventid = str(key['id'])
        desc += '<br /><br />https://frab.cccv.de/en/' + FRAB_ACRONYM + '/events/' + eventid
        guid = str(key['guid'])

        check = check_card(title)
        logging.debug('check: ' + str(check))
        if check:
            logging.debug('title: ' + str(check[0]))
            logging.debug('description: ' + str(check[1]))
            logging.debug('_id: ' + str(check[2]))
            if desc == str(check[1]):
                logging.info('No changes in description')
                logging.info('Skip card for id ' + str(key['id']))
                continue
            else:
                logging.info('Description changed')
                logging.info('Updating card details for id ' + str(key['id']))
                update_card(str(check[2]), title, desc, eventid)
        else:
            logging.info('Adding new card for id ' + str(key['id']))
            add_card(title, desc, eventid)
