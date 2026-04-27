import sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\templates\parent_dashboard2.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

depth = 0
results = []
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith('{% for') or stripped.startswith('{% if'):
        depth += 1
        results.append(f'Line {i+1} depth={depth} OPEN: {stripped[:60]}')
    elif stripped.startswith('{% endfor') or stripped.startswith('{% endif'):
        results.append(f'Line {i+1} depth={depth} CLOSE: {stripped[:60]}')
        depth -= 1
    elif i >= 615 and i <= 695:
        results.append(f'Line {i+1} depth={depth}: {repr(stripped[:80])}')

with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\nesting_output.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print('Written. Total lines checked:', len(lines))
