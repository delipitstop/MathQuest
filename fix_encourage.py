#!/usr/bin/env python3
content = open('templates/learn_table.html', 'r', encoding='utf-8').read()

old = "einSpeak('Correct! ' + currentAnswer + ' is right! You are doing great!', null);"
new = "var encouragements = ['You are doing great!', 'Fantastic work!', 'Superb!', 'Brilliant!', 'Excellent!']; var encMsg = encouragements[(completedCount - 1) % encouragements.length]; einSpeak('Correct! ' + currentAnswer + ' is right! ' + encMsg, null);"
if old in content:
    content = content.replace(old, new, 1)
    print('Replaced successfully')
else:
    print('Pattern not found!')
    # Show what's actually there
    idx = content.find("is right!")
    print(repr(content[idx-20:idx+100]))
open('templates/learn_table.html', 'w', encoding='utf-8').write(content)
