import re

with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\templates\target_shoot.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the start screen div id
m = re.search(r'id="(start[^"]*)"', content)
print('Start screen id:', m.group(1) if m else 'not found')

m2 = re.search(r'id="(result[^"]*)"', content)
print('Result screen id:', m2.group(1) if m2 else 'not found')

# Check the JS references
print('JS uses: startScreen =', 'startScreen' in content)
print('JS uses: resultScreen =', 'resultScreen' in content)

# Check getElementById calls
ids = re.findall(r'getElementById\([\'"](\w+)[\'"]\)', content)
print('getElementById calls:', set(ids))

# Check classList operations
classes = re.findall(r'classList\.(add|remove)\([\'"](\w+)[\'"]\)', content)
print('classList operations:', classes)