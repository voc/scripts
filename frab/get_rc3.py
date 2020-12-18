#!/usr/bin/env python3
# vim: tabstop=4 shiftwidth=4 expandtab

import requests
import json
import os
import sys
from dotenv import load_dotenv
from lxml import etree
import logging
loglevel = logging.INFO
logging.basicConfig(level=loglevel, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv(verbose=True)

import urllib3
urllib3.disable_warnings()

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
WEKAN_CUSTOM1 = os.getenv("WEKAN_CUSTOM1")
WEKAN_CUSTOM2 = os.getenv("WEKAN_CUSTOM2")
WEKAN_CUSTOM3 = os.getenv("WEKAN_CUSTOM3")
WEKAN_CUSTOM4 = os.getenv("WEKAN_CUSTOM4")
WEKAN_CUSTOM5 = os.getenv("WEKAN_CUSTOM5")

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
        try:
            logging.debug('Loading JSON')
            talks = json.loads(talks_json.text)
        except:
            logging.info('Something went wrong')
            sys.exit(0)
        #if talks['report']['count'] == 0:
        #    logging.info('JSON is empty.')
        #    sys.exit(0)
        try:
            logging.info('Writing local cache')
            with open('rc3.json', 'w') as fd:
               fd.write(talks_json.text)
               fd.close()
        except:
            logging.info('Something went wrong')
            sys.exit(0)
    else:
        logging.info('Using local cached data')
        with open('rc3.json', 'r') as fd:
            talks = json.loads(fd.read())
            fd.close()

    return talks

def check_card(eventid):
    found = []
    global event_check
    event_check = ""
    logging.debug('getting lists')
    get_lists = requests.get(WEKAN_URL + '/api/boards/' + WEKAN_BOARD + '/lists', headers=headers)
    for lists in get_lists.json():
        list_id = lists['_id']
        logging.debug('checking in list: ' + list_id)
        get_cards = requests.get(WEKAN_URL + '/api/boards/' + WEKAN_BOARD + '/lists/' + list_id + '/cards', headers=headers)
        for card in get_cards.json():
            card_id = card['_id']
            get_card = requests.get(WEKAN_URL + '/api/boards/' + WEKAN_BOARD + '/lists/' + list_id + '/cards/' + card_id, headers=headers)
            logging.debug('*** card ***')
            logging.debug(get_card.json())
            logging.debug('***')
            for field in get_card.json()['customFields']:
                if field['_id'] == WEKAN_CUSTOM1 and field['value'] == eventid:
                    event_check = eventid
                    logging.debug('adding title check')
                    found.append(card['title'])
                    found.append(card['_id'])
                    found.append(eventid)
                if field['_id'] == WEKAN_CUSTOM2 and event_check == eventid:
                    logging.debug('adding speaker check')
                    found.append(field['value'])
                if field['_id'] == WEKAN_CUSTOM4 and event_check == eventid:
                    logging.debug('adding studio check')
                    found.append(field['value'])
                if field['_id'] == WEKAN_CUSTOM5 and event_check == eventid:
                    logging.debug('adding rt check')
                    found.append(field['value'])
                else:
                    continue
    logging.debug('*** found ***')
    logging.debug(found)
    logging.debug('***')

    return found

def add_card(title, speakers, eventid, url):
    send = '{ "title": "' + title + '", "authorId": "' + WEKAN_USER + '", "swimlaneId": "' + WEKAN_SWIMLANE + '" }'
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

    send = '{ "receivedAt": "' + created + '", "customFields" : [ { "_id" : "' + WEKAN_CUSTOM1 + '", "value" : "' + eventid + '" }, { "_id" : "' + WEKAN_CUSTOM2 + '", "value" : "' + speakers + '" }, { "_id" : "' + WEKAN_CUSTOM3 + '", "value" : "' + url + '" }, { "_id" : "' + WEKAN_CUSTOM4 + '", "value" : "" }, { "_id" : "' + WEKAN_CUSTOM5 + '", "value" : "" } ] }'
    data = send.encode('utf-8')

    update = requests.put(WEKAN_URL + '/api/boards/' + WEKAN_BOARD + '/lists/' + WEKAN_LIST + '/cards/' + card_id, headers=headers, data=data)

    logging.debug(update.request.url)
    logging.debug(update.request.body)
    logging.debug(update)
    logging.debug(update.json())

    return True

def update_card(card, title, speakers, url, studio, rt):
    send = '{ "labelIds": "hbhJt3", "title": "' + title + '", "customFields" : [ { "_id" : "' + WEKAN_CUSTOM1 + '", "value" : "' + eventid + '" }, { "_id" : "' + WEKAN_CUSTOM2 + '", "value" : "' + speakers + '" }, { "_id" : "' + WEKAN_CUSTOM3 + '", "value" : "' + url + '" }, { "_id" : "' + WEKAN_CUSTOM4 + '", "value" : "' + studio + '" }, { "_id" : "' + WEKAN_CUSTOM5 + '", "value" : "' + rt + '" } ] }'
    data = send.encode('utf-8')
    logging.debug('*** send update ***')
    logging.debug(data)
    logging.debug('***')

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

    for key in talks:
        logging.debug('id: ' + str(key['id']))
        logging.debug('speakers: ' + str(key['speaker_names']))
        logging.debug('title: ' + key['title'])

        title = key['title']
        #desc = key['tech_rider']
        #desc = desc.replace('\r', '')
        #desc = desc.replace('\n', '<br />'a)
        speakers = key['speaker_names']
        eventid = str(key['event_id'])
        url = 'https://frab.cccv.de/en/' + FRAB_ACRONYM + '/events/' + eventid
        logging.debug('url: ' + str(url))

        check = check_card(eventid)
        logging.debug('check: ' + str(check))
        if check:
            logging.debug('check: title: ' + str(check[0]))
            logging.debug('json:  title: ' + str(title))
            
            logging.debug('check: card_id: ' + str(check[1]))
            
            logging.debug('check: event_id: ' + str(check[2]))
            logging.debug('json:  event_id: ' + str(eventid))
            
            logging.debug('check: speakers: ' + str(check[3]))
            logging.debug('json:  speakers: ' + str(speakers))

            logging.debug('check: studio: ' + str(check[4]))

            logging.debug('check: rt: ' + str(check[5]))

            
            if str(speakers) == str(check[3]) and str(title) == str(check[0]):
                logging.info('No changes in title/speakers')
                logging.info('Skip card for id ' + str(key['id']))
                continue
            else:
                logging.info('Speakers/title changed')
                logging.info('Updating card details for id ' + str(key['id']))
                update_card(str(check[1]), title, speakers, url, check[4], check[5])
        else:
            logging.info('Adding new card for id ' + str(key['id']))
            add_card(title, speakers, eventid, url)

        #sys.exit(0)
