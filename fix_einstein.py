with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\templates\parent_dashboard2.html', 'r', encoding='utf-8') as f:
    content = f.read()

einstein_html = '''

<!-- ========== FLOATING EINSTEIN BOT ========== -->
<div class="ein-launcher" id="einLauncher" onclick="toggleEinFloat()">
    A
    <div class="ein-badge" id="einBadge">!</div>
</div>

<div class="ein-float" id="einFloat">
    <!-- Drag handle header -->
    <div class="ein-float-hdr" id="einDragHandle">
        <div class="ein-hdr-ava">A</div>
        <div class="ein-hdr-info">
            <div class="ein-hdr-name">Albert Einstein</div>
            <div class="ein-hdr-tag">Maths Advisor - Click and drag to move</div>
        </div>
        <div class="ein-hdr-actions">
            <button class="hdr-btn" id="einFloatMute" onclick="toggleEinMute()" title="Mute">&#128266;</button>
            <button class="hdr-btn" onclick="toggleEinFloat()" title="Close">&#10005;</button>
        </div>
    </div>

    <!-- Messages -->
    <div class="ein-float-msgs" id="einMsgs">
        <div class="ein-msg" id="einWelcome">
            &#128579; Hello! I am Albert Einstein, your Maths Advisor!
            <span class="msg-time">Just now</span>
        </div>
        <div class="ein-msg" id="einPrompt">
            Select a child below and click <strong>Get Advice</strong> to receive a personalised learning report.
            <span class="msg-time">Just now</span>
        </div>
    </div>

    <!-- Body -->
    <div class="ein-float-body">
        <select class="ein-child-select" id="einChildSelect">
            {% for child in children %}
            <option value="{{ child.id }}">{{ child.avatar }} {{ child.name }}</option>
            {% endfor %}
        </select>
        <div class="ein-actions">
            <button class="ein-get-btn" id="einGetBtn" onclick="einGetAdvice()">
                &#127919; Get Personalised Advice
            </button>
            <button class="ein-speak-btn" id="einSpeakBtn" onclick="einSpeakLast()" title="Read advice aloud">
                &#128266;
            </button>
        </div>
    </div>
</div>

'''

js_marker = '// ---- Floating window drag ----'
js_idx = content.find(js_marker)
print('JS marker at:', js_idx, '/ total:', len(content))

if js_idx > 0:
    new_content = content[:js_idx] + einstein_html + '\n' + content[js_idx:]
    with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\templates\parent_dashboard2.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Done! New length:', len(new_content))
else:
    print('ERROR: JS marker not found!')
