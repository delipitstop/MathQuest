with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\templates\parent_dashboard2.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find {% block %} positions
blocks = []
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith('{%') and ('block' in stripped or 'endblock' in stripped or 'extends' in stripped):
        blocks.append(f'Line {i+1}: {repr(stripped)}')

for b in blocks:
    print(b)
