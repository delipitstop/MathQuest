import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\templates\parent_dashboard2.html', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
print('Total lines:', len(lines))

# Show lines 630-642
for i in range(629, 642):
    print('Line', i+1, ':', repr(lines[i][:80]))

# Find Einstein section and insert {% endfor %} before it
einstein_marker = '<!-- ========== FLOATING EINSTEIN BOT ========== -->'
new_lines = []
inserted = False
for i, line in enumerate(lines):
    if not inserted and i >= 637 and einstein_marker in lines[i]:
        new_lines.append('    {% endfor %}')
        print('Inserted {% endfor %} before Einstein section')
        inserted = True
    new_lines.append(line)

new_content = '\n'.join(new_lines)
with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\templates\parent_dashboard2.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Done! New total lines:', len(new_lines))
