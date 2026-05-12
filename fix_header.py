content = open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\app.py', 'r', encoding='utf-8').read()
old = "    sig = request.headers.get('Stripe-Signature', '')"
new = "    sig = request.headers.get('stripe-signature', request.headers.get('Stripe-Signature', ''))"
if old in content:
    print('FOUND - replacing')
    content = content.replace(old, new)
    open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\app.py', 'w', encoding='utf-8').write(content)
    print('Done')
else:
    print('NOT FOUND')