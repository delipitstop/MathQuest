import codecs
import json

with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\templates\parent_dashboard2.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

result = []
result.append('Total lines: ' + str(len(lines)))

# Find advisor section lines
for i, line in enumerate(lines):
    if 'advisor-section' in line or '<!-- AI Advisor -->' in line or '<script>' in line:
        result.append('Line ' + str(i+1) + ': ' + repr(line[:100]))

# Show lines 568-590
result.append('--- Lines 568-590 ---')
for i in range(567, 590):
    result.append('Line ' + str(i+1) + ': ' + repr(lines[i][:100]))

with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\lines_output.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(result))

print('Written to lines_output.txt')
