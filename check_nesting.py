with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\templates\parent_dashboard2.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Count nesting depth of {% for %} and {% if %} at key positions
depth = 0
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith('{% for') or stripped.startswith('{% if'):
        depth += 1
        print(f'Line {i+1} DEPTH+1={depth}: {repr(stripped[:60])}')
    elif stripped.startswith('{% endfor') or stripped.startswith('{% endif'):
        depth -= 1
        print(f'Line {i+1} DEPTH-1={depth}: {repr(stripped[:60])}')
    elif i >= 636 and i <= 690:
        print(f'Line {i+1} DEPTH={depth}: {repr(stripped[:80])}')
