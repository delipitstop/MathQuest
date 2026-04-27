import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\templates\parent_dashboard2.html', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
depth = 0
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith('{% for') or stripped.startswith('{% if'):
        depth += 1
        print(f'Line {i+1} depth={depth} OPEN: {repr(stripped[:60])}')
    elif stripped.startswith('{% endfor') or stripped.startswith('{% endif'):
        print(f'Line {i+1} depth={depth} CLOSE: {repr(stripped[:60])}')
        depth -= 1
