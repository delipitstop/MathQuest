with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\templates\parent_dashboard2.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all {% endfor %} and {% endif %} positions
lines = content.split('\n')
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith('{%') and ('endfor' in stripped or 'endblock' in stripped):
        print(f'Line {i+1}: {repr(line.strip())}')
