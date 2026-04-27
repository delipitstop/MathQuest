import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\templates\parent_dashboard2.html', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
print('Total lines:', len(lines))

# Find where the test div starts and ends
test_start = None
test_end = None
for i, line in enumerate(lines):
    if '<!-- EINSTEIN TEST -->' in line:
        test_start = i
        print('Test div starts at line', i+1)
    if test_start is not None and 'A - TEST BUTTON' in line:
        test_end = i
        print('Test div content ends at line', i+1)
        break

print('Lines around test div:')
for i in range(test_start-2 if test_start else 635, (test_end+3 if test_end else 645)):
    print('Line', i+1, ':', repr(lines[i][:80]) if i < len(lines) else 'N/A')
