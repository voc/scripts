input = '''
9:20 Public Sector Information (en)
13:30 Password Strength Meters (en)
18:00 Netlink and Go (en)
23:05 Food Hacking Base 2019 (en)
28:30 Getaviz (en)
32:05 Sigrok (en)
38:05 Datenkrake gefunden, und nun? (de)
44:00 Borg Backup (en)
50:00 TUMexam: Wie wir mit 1000+ Klausuren fertig werden (de)
54:15 IRMA (en)
1:00:00 Warum wir zwei Jahre lang Wikibooks ausgedruckt haben (de)
1:04:50 Openage (en)
1:10:50 Dash (en)
1:16:10 BalCCon2K19 (en)
1:21:00 Sophron Win Wifi Bug (en)
1:26:10 Human Connection - Free Socialnetwork (en)
1:31:36 The Importance of iOs Privacy (en)
1:37:10 TAN Tree Area Network (en)
1:40:50 GNU/Linux improved (en)
1:45:15 Navigating in Linux Kernel Security Area (en)
1:50:20 Pass the cookie and pivot the cloud (en)
1:56:00 War on drugs (en)
'''

talks = input.strip().split('\n')

# from https://stackoverflow.com/a/6402859/521791
def get_sec(time_str):
    try:
        h, m, s = time_str.split(':')
    except ValueError:
        h = 0
        m, s = time_str.split(':')

    return int(h) * 3600 + int(m) * 60 + int(s)

print('<ul>')
for line in talks:
    time, text = line.split(' ', 1)
    #print(time, text)
    print('<li><a href="#t={}">{}</a> {}</li>'.format(get_sec(time), time, text))
print('</ul>')