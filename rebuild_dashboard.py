import sys
sys.stdout.reconfigure(encoding='utf-8')

# Build the complete parent_dashboard2.html from scratch

css = """
    .pdashboard { max-width: 1200px; margin: 0 auto; padding: 24px 16px; }
    .pd-header { text-align: center; margin-bottom: 24px; }
    .pd-header h1 { font-size: 32px; font-weight: 900; color: white; text-shadow: 0 4px 16px rgba(0,0,0,0.2); }
    .pd-header p { color: rgba(255,255,255,0.85); font-size: 16px; margin-top: 4px; }
    .child-selector { display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; margin-bottom: 20px; }
    .child-chip { background: white; border-radius: 50px; padding: 10px 22px; cursor: pointer; display: flex; align-items: center; gap: 8px; font-weight: 800; font-size: 15px; color: #1E1B4B; border: 3px solid transparent; transition: all 0.2s; box-shadow: 0 4px 16px rgba(0,0,0,0.15); }
    .child-chip:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.2); }
    .child-chip.selected { border-color: #FBBF24; background: #FFFbEB; }
    .child-chip .ava { font-size: 20px; }
    .dash-main { display: none; }
    .dash-main.active { display: block; }
    .dash-welcome { background: white; border-radius: 16px; padding: 16px 20px; margin-bottom: 14px; display: flex; align-items: center; gap: 14px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
    .dash-welcome .big-ava { font-size: 44px; }
    .dash-welcome h2 { font-size: 20px; font-weight: 900; color: #1E1B4B; }
    .dash-welcome p { color: #6B7280; font-size: 12px; margin-top: 2px; }
    .dash-badge { display: inline-block; background: linear-gradient(135deg,#667eea,#764ba2); color: white; font-size: 11px; font-weight: 800; padding: 2px 10px; border-radius: 50px; margin-top: 4px; }
    .stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 14px; }
    .stat-card { background: white; border-radius: 12px; padding: 10px 12px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.07); }
    .stat-card:hover { transform: translateY(-2px); }
    .stat-n { font-size: 22px; font-weight: 900; }
    .stat-n.purple { color: #7C3AED; }
    .stat-n.green { color: #34D399; }
    .stat-n.yellow { color: #FBBF24; }
    .stat-l { font-size: 10px; color: #6B7280; font-weight: 700; margin-top: 2px; text-transform: uppercase; }
    .ops-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 14px; }
    .op-card { background: white; border-radius: 12px; padding: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.07); }
    .op-header { display: flex; align-items: center; gap: 7px; margin-bottom: 8px; }
    .op-emoji { font-size: 20px; }
    .op-name { font-size: 12px; font-weight: 800; color: #1E1B4B; }
    .op-count { font-size: 10px; color: #6B7280; margin-top: 1px; }
    .op-bar-bg { background: #F3F4F6; border-radius: 7px; height: 7px; overflow: hidden; margin-bottom: 5px; }
    .op-bar-fill { height: 100%; border-radius: 7px; transition: width 0.6s ease; }
    .op-bar-fill.purple { background: linear-gradient(90deg,#7C3AED,#A78BFA); }
    .op-bar-fill.teal { background: linear-gradient(90deg,#059669,#34D399); }
    .op-bar-fill.blue { background: linear-gradient(90deg,#2563EB,#60A5FA); }
    .op-bar-fill.orange { background: linear-gradient(90deg,#EA580C,#FB923C); }
    .op-status { font-size: 10px; font-weight: 700; }
    .op-status.done { color: #34D399; }
    .op-status.progress { color: #FBBF24; }
    .op-status.start { color: #9CA3AF; }
    .struggle-section { background: white; border-radius: 12px; padding: 14px; margin-bottom: 14px; box-shadow: 0 2px 10px rgba(0,0,0,0.07); }
    .section-title { font-size: 14px; font-weight: 800; color: #1E1B4B; margin-bottom: 8px; display: flex; align-items: center; gap: 6px; }
    .struggle-grid { display: flex; flex-wrap: wrap; gap: 6px; }
    .struggle-tag { padding: 5px 10px; border-radius: 50px; font-size: 11px; font-weight: 700; }
    .struggle-tag.red { background: #FEF2F2; color: #DC2626; border: 2px solid #FECACA; }
    .struggle-tag.orange { background: #FFF7ED; color: #EA580C; border: 2px solid #FED7AA; }
    .no-struggles { color: #6B7280; font-size: 13px; padding: 4px 0; }
    .no-struggles span { color: #34D399; font-weight: 800; }
    .cert-panel { background: white; border-radius: 12px; padding: 18px; margin-bottom: 14px; box-shadow: 0 2px 10px rgba(0,0,0,0.07); text-align: center; }
    .cert-panel.locked { opacity: 0.75; }
    .cert-panel.unlocked { border: 2px solid #FBBF24; }
    .cert-lock-msg { font-size: 32px; margin-bottom: 6px; }
    .cert-lock-title { font-size: 16px; font-weight: 800; color: #1E1B4B; margin-bottom: 3px; }
    .cert-lock-sub { color: #6B7280; font-size: 12px; max-width: 400px; margin: 0 auto 12px; }
    .cert-req-list { text-align: left; max-width: 360px; margin: 0 auto 12px; display: inline-block; }
    .cert-req-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; font-size: 12px; font-weight: 700; color: #374151; }
    .cert-req-item.done { color: #34D399; }
    .cert-req-item.pending { color: #9CA3AF; }
    .cert-preview { background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 14px; padding: 18px; color: white; margin-bottom: 14px; }
    .cert-preview-emoji { font-size: 32px; }
    .cert-preview-title { font-size: 15px; font-weight: 800; margin: 6px 0 3px; }
    .cert-preview-sub { font-size: 12px; opacity: 0.85; }
    .cert-preview-score { font-size: 22px; font-weight: 900; margin-top: 8px; color: #FBBF24; }
    .btn-cert { padding: 11px 24px; border-radius: 50px; font-weight: 800; font-size: 14px; border: none; cursor: pointer; text-decoration: none; display: inline-block; transition: transform 0.2s; }
    .btn-cert:hover { transform: translateY(-2px); }
    .btn-cert-download { background: linear-gradient(135deg,#7C3AED,#764ba2); color: white; }
    .btn-cert-print { background: #FBBF24; color: #1E1B4B; }
    .top-bar { display: flex; justify-content: flex-end; margin-bottom: 16px; }
    .btn-logout { background: rgba(255,255,255,0.2); color: white; border: 2px solid rgba(255,255,255,0.4); padding: 7px 16px; border-radius: 50px; text-decoration: none; font-weight: 700; font-size: 13px; transition: all 0.2s; }
    .btn-logout:hover { background: rgba(255,255,255,0.35); }

    /* ========== FLOATING EINSTEIN BOT ========== */
    .ein-launcher { position: fixed; bottom: 24px; right: 24px; z-index: 1000; width: 64px; height: 64px; background: linear-gradient(135deg, #FFD54F, #FF8F00); border-radius: 50%; border: 3px solid white; box-shadow: 0 6px 24px rgba(0,0,0,0.25), 0 0 20px rgba(255,213,79,0.4); cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 26px; font-weight: 900; color: white; transition: transform 0.2s, box-shadow 0.2s; user-select: none; }
    .ein-launcher:hover { transform: scale(1.1); box-shadow: 0 8px 32px rgba(0,0,0,0.3), 0 0 30px rgba(255,213,79,0.6); }
    .ein-launcher .ein-badge { position: absolute; top: -4px; right: -4px; background: #EF4444; color: white; font-size: 10px; font-weight: 900; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid white; }
    .ein-launcher.hidden-badge .ein-badge { display: none; }
    .ein-float { position: fixed; bottom: 100px; right: 24px; width: 360px; max-width: calc(100vw - 40px); background: white; border-radius: 20px; box-shadow: 0 12px 60px rgba(0,0,0,0.25); z-index: 999; overflow: hidden; display: none; flex-direction: column; max-height: calc(100vh - 140px); }
    .ein-float.open { display: flex; }
    .ein-float-hdr { background: linear-gradient(135deg, #FFD54F, #FF8F00); padding: 12px 14px; display: flex; align-items: center; gap: 10px; cursor: grab; user-select: none; flex-shrink: 0; }
    .ein-float-hdr:active { cursor: grabbing; }
    .ein-hdr-ava { width: 36px; height: 36px; background: linear-gradient(135deg,#FF6F00,#E65100); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 900; color: white; box-shadow: 0 2px 8px rgba(0,0,0,0.2); flex-shrink: 0; }
    .ein-hdr-info { flex: 1; }
    .ein-hdr-name { font-size: 14px; font-weight: 900; color: #3E2723; }
    .ein-hdr-tag { font-size: 10px; color: #5D4037; font-weight: 600; }
    .ein-hdr-actions { display: flex; gap: 6px; margin-left: auto; }
    .hdr-btn { width: 28px; height: 28px; border-radius: 50%; border: none; background: rgba(255,255,255,0.3); color: #3E2723; font-size: 14px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background 0.2s; }
    .hdr-btn:hover { background: rgba(255,255,255,0.5); }
    .hdr-btn.speaking { animation: speakPulse 0.6s infinite; }
    .ein-float-msgs { flex: 1; overflow-y: auto; padding: 14px; background: #FFFDE7; min-height: 120px; max-height: 280px; }
    .ein-msg { font-size: 13px; line-height: 1.65; color: #3E2723; margin-bottom: 10px; font-weight: 600; padding: 10px 14px; border-radius: 14px; background: rgba(255,255,255,0.8); border-left: 3px solid #FFD54F; animation: msgIn 0.3s ease; }
    .ein-msg.user { background: rgba(124,58,237,0.1); border-left: none; border-right: 3px solid #7C3AED; text-align: right; }
    .msg-time { font-size: 10px; color: #9E9E9E; font-weight: 400; margin-top: 4px; display: block; }
    @keyframes msgIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes speakPulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.15)} }
    @keyframes dotBounce { 0%,80%,100%{transform:scale(0.6);opacity:0.4} 40%{transform:scale(1);opacity:1} }
    .ein-typing { display: flex; gap: 4px; padding: 10px 14px; margin-bottom: 10px; }
    .ein-typing .dot { width: 8px; height: 8px; background: #FF8F00; border-radius: 50%; animation: dotBounce 1.2s infinite; }
    .ein-typing .dot:nth-child(2) { animation-delay: 0.2s; }
    .ein-typing .dot:nth-child(3) { animation-delay: 0.4s; }
    .ein-float-body { padding: 12px 14px; border-top: 1px solid #F0F0F0; background: white; flex-shrink: 0; }
    .ein-child-select { width: 100%; padding: 8px 12px; border: 2px solid #E5E7EB; border-radius: 10px; font-size: 13px; font-weight: 700; color: #1E1B4B; background: white; margin-bottom: 10px; cursor: pointer; }
    .ein-actions { display: flex; gap: 8px; }
    .ein-get-btn { flex: 1; background: linear-gradient(135deg,#667eea,#764ba2); color: white; border: none; padding: 10px 14px; border-radius: 50px; font-size: 13px; font-weight: 800; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; display: flex; align-items: center; justify-content: center; gap: 6px; }
    .ein-get-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(102,126,234,0.4); }
    .ein-get-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
    .ein-speak-btn { width: 42px; height: 42px; border-radius: 50%; border: 2px solid #FFD54F; background: #FFF9C4; font-size: 18px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; flex-shrink: 0; }
    .ein-speak-btn:hover { background: #FFE082; transform: scale(1.1); }
    .ein-speak-btn.speaking { animation: speakPulse 0.6s infinite; background: #FFD54F; }
    @media (max-width: 768px) { .ops-grid { grid-template-columns: repeat(2, 1fr); } .stats-row { grid-template-columns: 1fr 1fr 1fr; } .dash-welcome { flex-direction: column; text-align: center; } .pd-header h1 { font-size: 24px; } .ein-float { width: calc(100vw - 32px); right: 16px; } }
    @media print { body { background: white !important; } .no-print, .ein-float, .ein-launcher { display: none !important; } }
"""

html_body = """
{% block body %}
<div class="pdashboard">
    <div class="top-bar no-print">
        <a href="/parent/logout" class="btn-logout">Logout</a>
    </div>
    <div class="pd-header">
        <h1>📊 Parent Dashboard</h1>
        <p>Track and support your child's maths journey</p>
    </div>

    {% if children|length > 1 %}
    <div class="child-selector no-print" id="childSelector">
        {% for child in children %}
        <div class="child-chip {% if loop.first %}selected{% endif %}" data-child-id="{{ child.id }}" onclick="selectChild({{ child.id }}, this)">
            <span class="ava">{{ child.avatar }}</span>
            {{ child.name }}
        </div>
        {% endfor %}
    </div>
    {% endif %}

    {% for child in children %}
    <div class="dash-main {% if loop.first %}active{% endif %}" id="dash-{{ child.id }}">
        <div class="dash-welcome">
            <div class="big-ava">{{ child.avatar }}</div>
            <div>
                <h2>{{ child.name }}</h2>
                <div class="dash-badge">✨ Growing Mathematician</div>
                {% set created_parts = child.created_at.split(' ')[0].split('-') if child.created_at else ['','',''] %}
                <p>{% if created_parts[1] %}{{ {"01":"January","02":"February","03":"March","04":"April","05":"May","06":"June","07":"July","08":"August","09":"September","10":"October","11":"November","12":"December"}[created_parts[1]] }} {{ created_parts[0] }}{% else %}Member recently{% endif %}</p>
            </div>
        </div>

        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-n purple">{{ child.total_quizzes }}</div>
                <div class="stat-l">Quizzes Taken</div>
            </div>
            <div class="stat-card">
                <div class="stat-n green">{{ child.achievements|length }}</div>
                <div class="stat-l">Badges Earned</div>
            </div>
            <div class="stat-card">
                <div class="stat-n yellow">{% if child.exam_result %}{{ child.exam_result.percentage }}%{% else %}--{% endif %}</div>
                <div class="stat-l">Best Exam Score</div>
            </div>
        </div>

        <div class="ops-grid">
            <div class="op-card">
                <div class="op-header"><span class="op-emoji">✨</span><div><div class="op-name">Times Tables</div><div class="op-count">{{ child.mult_passed }} / 15 Tables Passed</div></div></div>
                <div class="op-bar-bg"><div class="op-bar-fill purple" style="width:{{ (child.mult_passed / 15 * 100)|round|int }}%"></div></div>
                <div class="op-status {% if child.mult_passed == 15 %}done{% elif child.mult_passed > 0 %}progress{% else %}start{% endif %}">{% if child.mult_passed == 15 %}🎉 All mastered!{% elif child.mult_passed > 0 %}📖 In progress{% else %}🔓 Not started{% endif %}</div>
            </div>
            <div class="op-card">
                <div class="op-header"><span class="op-emoji">➗</span><div><div class="op-name">Division</div><div class="op-count">{{ child.div_passed }} / 15 Tables Passed</div></div></div>
                <div class="op-bar-bg"><div class="op-bar-fill teal" style="width:{{ (child.div_passed / 15 * 100)|round|int }}%"></div></div>
                <div class="op-status {% if child.div_passed == 15 %}done{% elif child.div_passed > 0 %}progress{% else %}start{% endif %}">{% if child.div_passed == 15 %}🎉 All mastered!{% elif child.div_passed > 0 %}📖 In progress{% else %}🔓 Not started{% endif %}</div>
            </div>
            <div class="op-card">
                <div class="op-header"><span class="op-emoji">➕</span><div><div class="op-name">Addition</div><div class="op-count">{{ child.add_passed }} / 15 Tables Passed</div></div></div>
                <div class="op-bar-bg"><div class="op-bar-fill blue" style="width:{{ (child.add_passed / 15 * 100)|round|int }}%"></div></div>
                <div class="op-status {% if child.add_passed == 15 %}done{% elif child.add_passed > 0 %}progress{% else %}start{% endif %}">{% if child.add_passed == 15 %}🎉 All mastered!{% elif child.add_passed > 0 %}📖 In progress{% else %}🔓 Not started{% endif %}</div>
            </div>
            <div class="op-card">
                <div class="op-header"><span class="op-emoji">➖</span><div><div class="op-name">Subtraction</div><div class="op-count">{{ child.sub_passed }} / 15 Tables Passed</div></div></div>
                <div class="op-bar-bg"><div class="op-bar-fill orange" style="width:{{ (child.sub_passed / 15 * 100)|round|int }}%"></div></div>
                <div class="op-status {% if child.sub_passed == 15 %}done{% elif child.sub_passed > 0 %}progress{% else %}start{% endif %}">{% if child.sub_passed == 15 %}🎉 All mastered!{% elif child.sub_passed > 0 %}📖 In progress{% else %}🔓 Not started{% endif %}</div>
            </div>
        </div>

        <div class="struggle-section no-print">
            <div class="section-title">🔍 Struggle Areas</div>
            {% if child.struggles %}
            <div class="struggle-grid">
                {% for s in child.struggles %}
                <span class="struggle-tag {% if s.score < 40 %}red{% else %}orange{% endif %}">{{ s.topic }} — {{ s.score }}%</span>
                {% endfor %}
            </div>
            <p style="margin-top:10px;font-size:11px;color:#6B7280;">💡 <strong>Tip:</strong> Focus on one table at a time with short daily practice sessions.</p>
            {% else %}
            <p class="no-struggles">🎉 <span>No struggles detected!</span> Keep up the great work or move on to harder tables.</p>
            {% endif %}
        </div>

        {% set cert_unlocked = child.mult_passed == 15 and child.div_passed == 15 and child.add_passed == 15 and child.sub_passed == 15 %}
        <div class="cert-panel {% if not cert_unlocked %}locked{% else %}unlocked{% endif %} no-print">
            {% if not cert_unlocked %}
            <div class="cert-lock-msg">🔒</div>
            <div class="cert-lock-title">Certificate Locked</div>
            <p class="cert-lock-sub">Pass all 60 tables across all 4 operations to unlock the certificate!</p>
            <div class="cert-req-list">
                <div class="cert-req-item {% if child.mult_passed == 15 %}done{% else %}pending{% endif %}">{% if child.mult_passed == 15 %}✅{% else %}⬜{% endif %} Times Tables — {{ child.mult_passed }}/15 passed</div>
                <div class="cert-req-item {% if child.div_passed == 15 %}done{% else %}pending{% endif %}">{% if child.div_passed == 15 %}✅{% else %}⬜{% endif %} Division — {{ child.div_passed }}/15 passed</div>
                <div class="cert-req-item {% if child.add_passed == 15 %}done{% else %}pending{% endif %}">{% if child.add_passed == 15 %}✅{% else %}⬜{% endif %} Addition — {{ child.add_passed }}/15 passed</div>
                <div class="cert-req-item {% if child.sub_passed == 15 %}done{% else %}pending{% endif %}">{% if child.sub_passed == 15 %}✅{% else %}⬜{% endif %} Subtraction — {{ child.sub_passed }}/15 passed</div>
            </div>
            {% else %}
            <div class="cert-preview">
                <div class="cert-preview-emoji">🏆</div>
                <div class="cert-preview-title">MathQuest Certificate of Achievement</div>
                <div class="cert-preview-sub">All 60 tables mastered! Ready to print!</div>
                <div class="cert-preview-score">{{ child.name }} — ✨ Mastered! 🏆</div>
            </div>
            <a href="/certificate/{{ child.id }}" class="btn-cert btn-cert-download" target="_blank">🏆 View &amp; Download Certificate</a>
            {% endif %}
        </div>
    </div>
    {% endfor %}

    {% if children|length > 1 %}
    {% for child in children %}
    {% if loop.first %}
    {% if child.mult_passed == 15 and child.div_passed == 15 and child.add_passed == 15 and child.sub_passed == 15 %}
    <div class="cert-panel unlocked no-print" id="multiCertPanel">
        <div class="section-title" style="justify-content:center">🏆 Family Certificates</div>
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:12px; margin-top:12px">
            {% for c in children %}
            <div style="background:linear-gradient(135deg,#667eea,#764ba2);border-radius:14px;padding:16px;color:white;text-align:center">
                <div style="font-size:36px;margin-bottom:6px">{{ c.avatar }}</div>
                <div style="font-weight:800;font-size:16px">{{ c.name }}</div>
                {% if c.mult_passed == 15 and c.div_passed == 15 and c.add_passed == 15 and c.sub_passed == 15 %}
                <div style="color:#FBBF24;font-weight:900;margin-top:4px">🏆 Mastered!</div>
                <a href="/certificate/{{ c.id }}" class="btn-cert btn-cert-print" style="margin-top:10px;font-size:12px;padding:7px 16px" target="_blank">🖨️ Certificate</a>
                {% else %}
                <div style="font-size:12px;opacity:0.7;margin-top:4px">🔒 In progress</div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}
    {% endif %}
    {% endfor %}
    {% endif %}
</div>

<!-- ========== FLOATING EINSTEIN BOT ========== -->
<div class="ein-launcher" id="einLauncher" onclick="toggleEinFloat()">
    A
    <div class="ein-badge" id="einBadge">!</div>
</div>

<div class="ein-float" id="einFloat">
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
    <div class="ein-float-msgs" id="einMsgs">
        <div class="ein-msg">
            &#128579; Hello! I am Albert Einstein, your Maths Advisor!
            <span class="msg-time">Just now</span>
        </div>
        <div class="ein-msg">
            Select a child below and click <strong>Get Advice</strong> to receive a personalised learning report.
            <span class="msg-time">Just now</span>
        </div>
    </div>
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
{% endblock %}
"""

js_code = """
<script>
var einMuted = false;
var einAudio = null;
var einSpeaking = false;
var einLastText = '';
var einFloatOpen = false;

// ---- Floating window drag ----
var dragState = { isDragging: false, offsetX: 0, offsetY: 0, startX: 0, startY: 0, floater: null, handle: null };

function initDrag() {
    dragState.floater = document.getElementById('einFloat');
    dragState.handle = document.getElementById('einDragHandle');
    if (!dragState.handle) return;
    dragState.handle.addEventListener('mousedown', function(e) {
        if (e.target.closest('.hdr-btn')) return;
        dragState.isDragging = true;
        dragState.startX = e.clientX;
        dragState.startY = e.clientY;
        var rect = dragState.floater.getBoundingClientRect();
        dragState.offsetX = e.clientX - rect.left;
        dragState.offsetY = e.clientY - rect.top;
        dragState.floater.style.transition = 'none';
    });
    document.addEventListener('mousemove', function(e) {
        if (!dragState.isDragging) return;
        var maxX = window.innerWidth - dragState.floater.offsetWidth - 8;
        var maxY = window.innerHeight - dragState.floater.offsetHeight - 8;
        var newX = Math.max(8, Math.min(maxX, e.clientX - dragState.offsetX));
        var newY = Math.max(8, Math.min(maxY, e.clientY - dragState.offsetY));
        dragState.floater.style.left = newX + 'px';
        dragState.floater.style.right = 'auto';
        dragState.floater.style.bottom = 'auto';
    });
    document.addEventListener('mouseup', function() {
        if (dragState.isDragging) { dragState.isDragging = false; dragState.floater.style.transition = ''; }
    });
    dragState.handle.addEventListener('touchstart', function(e) {
        if (e.target.closest('.hdr-btn')) return;
        var touch = e.touches[0];
        dragState.isDragging = true;
        var rect = dragState.floater.getBoundingClientRect();
        dragState.offsetX = touch.clientX - rect.left;
        dragState.offsetY = touch.clientY - rect.top;
        dragState.floater.style.transition = 'none';
    }, { passive: true });
    document.addEventListener('touchmove', function(e) {
        if (!dragState.isDragging) return;
        var touch = e.touches[0];
        var maxX = window.innerWidth - dragState.floater.offsetWidth - 8;
        var maxY = window.innerHeight - dragState.floater.offsetHeight - 8;
        var newX = Math.max(8, Math.min(maxX, touch.clientX - dragState.offsetX));
        var newY = Math.max(8, Math.min(maxY, touch.clientY - dragState.offsetY));
        dragState.floater.style.left = newX + 'px';
        dragState.floater.style.right = 'auto';
        dragState.floater.style.bottom = 'auto';
    }, { passive: true });
    document.addEventListener('touchend', function() {
        if (dragState.isDragging) { drag