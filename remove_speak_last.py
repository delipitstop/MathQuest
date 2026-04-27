#!/usr/bin/env python3
content = open('templates/learn_table.html', 'r', encoding='utf-8').read()

old = '''function einSpeakLast() {
    if (lastSpokenText) einSpeak(lastSpokenText);
}

// ---- Einstein says something (shown + spoken) ----'''

new = '''// ---- Einstein says something (shown + spoken) ----'''

if old in content:
    content = content.replace(old, new, 1)
    open('templates/learn_table.html', 'w', encoding='utf-8').write(content)
    print('Removed einSpeakLast function')
else:
    print('Pattern not found')
