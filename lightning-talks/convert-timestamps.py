#!/usr/bin/env python3

print('Enter/Paste the input as "(hh:)mm:ss text foo bar". Ctrl-D or Ctrl-Z ( windows ) to save it.')
talks = []
while True:
    try:
        line = input().strip()
    except EOFError:
        break
    if line:
        talks.append(line)

#talks = input.strip().split('\n')

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