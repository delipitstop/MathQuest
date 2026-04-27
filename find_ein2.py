with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\templates\parent_dashboard2.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print('Total lines:', len(lines))

# Show lines 628-640
for i in range(627, 640):
    print(f'Line {i+1}: {repr(lines[i][:120])}')
