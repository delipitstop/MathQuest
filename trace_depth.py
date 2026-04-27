import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\templates\parent_dashboard2.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

depth = 0
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith('{% for') or stripped.startswith('{% if'):
        depth += 1
    elif stripped.startswith('{% endfor') or stripped.startswith('{% endif'):
        depth -= 1
    
    if i == 570 or i == 571 or i == 638 or i == 689 or i == 936:
        print(f'Line {i+1}: depth={depth} → {repr(stripped[:80])}')
