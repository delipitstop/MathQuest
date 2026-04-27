#!/usr/bin/env python3
app = open('app.py', 'r', encoding='utf-8').read()
idx = app.find('def inject_analytics')
print('Found at:', idx)
print(repr(app[idx-50:idx+200]))
