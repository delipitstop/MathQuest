with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\templates\parent_dashboard2.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print('Total lines:', len(lines))

# Find ein-related divs
for i, line in enumerate(lines):
    if 'ein-launcher' in line or 'ein-float' in line or 'FLOATING' in line or 'ein-hdr' in line:
        print(f'Line {i+1}: {repr(line[:100])}')
