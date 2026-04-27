with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\templates\parent_dashboard2.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print('Total lines:', len(lines))

# Find all {% for %} positions
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith('{%') and 'for' in stripped:
        print(f'Line {i+1}: {repr(line.strip())}')
