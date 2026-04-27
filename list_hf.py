#!/usr/bin/env python3
import urllib.request
import json

# List contents of the piper-voices repo
url = "https://huggingface.co/api/tree/main?recursive=true"
req = urllib.request.Request(
    url,
    headers={'User-Agent': 'Mozilla/5.0'}
)
try:
    r = urllib.request.urlopen(req, timeout=15)
    data = json.loads(r.read())
    # Flatten and find .onnx files
    def walk(items, path=""):
        for item in items:
            if item.get('type') == 'file' and item['path'].endswith('.onnx'):
                print(item['path'])
            elif item.get('type') == 'directory':
                walk(item.get('children', []), path + item['path'] + '/')
    walk(data)
except Exception as e:
    print(f"Error: {e}")
    # Try alternate
    url2 = "https://huggingface.co/api/tree/main/en_US/lessac/medium?recursive=true"
    req2 = urllib.request.Request(url2, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        r2 = urllib.request.urlopen(req2, timeout=15)
        data2 = json.loads(r2.read())
        for item in data2:
            print(item.get('path', item))
    except Exception as e2:
        print(f"Error2: {e2}")
