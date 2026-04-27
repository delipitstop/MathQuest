with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\templates\parent_dashboard2.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Show lines 655-690
for i in range(654, 690):
    print(f'Line {i+1}: {repr(lines[i][:100])}')
