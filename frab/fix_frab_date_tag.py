import xml.etree.ElementTree as ET
import urllib.request
import sys

schedule_url = "ADD URL HERE"
print( "## getting meta data from " + schedule_url + " ##")
global frab_data
try:
    frab_data = urllib.request.urlopen(schedule_url)
except:
    print( "Could not load schedule xml. Please check url")
    sys.exit(1)

tree = ET.parse(frab_data)
root = tree.getroot()

for day in root.iter('day'):
    date = day.attrib['date']
    day.set('end', date + "T05:00:00+01:00")
    day.set('start', date + "T10:00:00+01:00")
    for event in day.iter('event'):
        # Append ISO 8601 date; example: 2016-02-29T23:42:00+01:00
        event.append(ET.Element('date'))
        event.find('date').text = date +  "T" + event.find('start').text + ":00+01:00"

tree.write("test.xml")
