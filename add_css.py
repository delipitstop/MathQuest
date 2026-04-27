with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\templates\parent_dashboard2.html', 'r', encoding='utf-8') as f:
    content = f.read()

einstein_css = '''
    /* ========== FLOATING EINSTEIN BOT ========== */
    /* Floating launcher button */
    .ein-launcher {
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 1000;
        width: 64px;
        height: 64px;
        background: linear-gradient(135deg, #FFD54F, #FF8F00);
        border-radius: 50%;
        border: 3px solid white;
        box-shadow: 0 6px 24px rgba(0,0,0,0.25), 0 0 20px rgba(255,213,79,0.4);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 26px;
        font-weight: 900;
        color: white;
        transition: transform 0.2s, box-shadow 0.2s;
        user-select: none;
    }
    .ein-launcher:hover {
        transform: scale(1.1);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3), 0 0 30px rgba(255,213,79,0.6);
    }
    .ein-launcher .ein-badge {
        position: absolute;
        top: -4px;
        right: -4px;
        background: #EF4444;
        color: white;
        font-size: 10px;
        font-weight: 900;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 2px solid white;
    }
    .ein-launcher.hidden-badge .ein-badge { display: none; }

    /* Floating window */
    .ein-float {
        position: fixed;
        bottom: 100px;
        right: 24px;
        width: 360px;
        max-width: calc(100vw - 40px);
        background: white;
        border-radius: 20px;
        box-shadow: 0 12px 60px rgba(0,0,0,0.25), 0 0 0 1px rgba(0,0,0,0.05);
        z-index: 999;
        overflow: hidden;
        display: none;
        flex-direction: column;
        max-height: calc(100vh - 140px);
    }
    .ein-float.open { display: flex; }

    /* Drag handle / header */
    .ein-float-hdr {
        background: linear-gradient(135deg, #FFD54F, #FF8F00);
        padding: 12px 14px;
        display: flex;
        align-items: center;
        gap: 10px;
        cursor: grab;
        user-select: none;
        flex-shrink: 0;
    }
    .ein-float-hdr:active { cursor: grabbing; }
    .ein-hdr-ava {
        width: 36px;
        height: 36px;
        background: linear-gradient(135deg,#FF6F00,#E65100);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        font-weight: 900;
        color: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        flex-shrink: 0;
    }
    .ein-hdr-name { font-size: 14px; font-weight: 900; color: #3E2723; }
    .ein-hdr-tag { font-size: 10px; color: #5D4037; font-weight: 600; }
    .ein-hdr-actions { display: flex; gap: 6px; margin-left: auto; }
    .hdr-btn {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        border: none;
        background: rgba(255,255,255,0.3);
        color: #3E2723;
        font-size: 14px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background 0.2s;
    }
    .hdr-btn:hover { background: rgba(255,255,255,0.5); }
    .hdr-btn.speaking { animation: speakPulse 0.6s infinite; }

    /* Message area */
    .ein-float-msgs {
        flex: 1;
        overflow-y: auto;
        padding: 14px;
        background: #FFFDE7;
        min-height: 120px;
        max-height: 280px;
    }
    .ein-msg {
        font-size: 13px;
        line-height: 1.65;
        color: #3E2723;
        margin-bottom: 10px;
        font-weight: 600;
        padding: 10px 14px;
        border-radius: 14px;
        background: rgba(255,255,255,0.8);
        border-left: 3px solid #FFD54F;
        animation: msgIn 0.3s ease;
    }
    .ein-msg.user {
        background: rgba(124,58,237,0.1);
        border-left: none;
        border-right: 3px solid #7C3AED;
        text-align: right;
    }
    .msg-time {
        font-size: 10px;
        color: #9E9E9E;
        font-weight: 400;
        margin-top: 4px;
        display: block;
    }
    @keyframes msgIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes speakPulse { 0%,100%{transform:scale(1)} 50%{transform:scale(1.15)} }

    /* Typing dots */
    .ein-typing {
        display: flex;
        gap: 4px;
        padding: 10px 14px;
        margin-bottom: 10px;
    }
    .ein-typing .dot {
        width: 8px;
        height: 8px;
        background: #FF8F00;
        border-radius: 50%;
        animation: dotBounce 1.2s infinite;
    }
    .ein-typing .dot:nth-child(2) { animation-delay: 0.2s; }
    .ein-typing .dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes dotBounce { 0%,80%,100%{transform:scale(0.6);opacity:0.4} 40%{transform:scale(1);opacity:1} }

    /* Float body / actions */
    .ein-float-body {
        padding: 12px 14px;
        border-top: 1px solid #F0F0F0;
        background: white;
        flex-shrink: 0;
    }
    .ein-child-select {
        width: 100%;
        padding: 8px 12px;
        border: 2px solid #E5E7EB;
        border-radius: 10px;
        font-size: 13px;
        font-weight: 700;
        color: #1E1B4B;
        background: white;
        margin-bottom: 10px;
        cursor: pointer;
    }
    .ein-actions { display: flex; gap: 8px; }
    .ein-get-btn {
        flex: 1;
        background: linear-gradient(135deg,#667eea,#764ba2);
        color: white;
        border: none;
        padding: 10px 14px;
        border-radius: 50px;
        font-size: 13px;
        font-weight: 800;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
    }
    .ein-get-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(102,126,234,0.4); }
    .ein-get-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
    .ein-speak-btn {
        width: 42px;
        height: 42px;
        border-radius: 50%;
        border: 2px solid #FFD54F;
        background: #FFF9C4;
        font-size: 18px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s;
        flex-shrink: 0;
    }
    .ein-speak-btn:hover { background: #FFE082; transform: scale(1.1); }
    .ein-speak-btn.speaking { animation: speakPulse 0.6s infinite; background: #FFD54F; }
'''

style_end = content.find('</style>')
print('</style> at:', style_end)
if style_end > 0:
    new_content = content[:style_end] + einstein_css + '\n    </style>\n' + content[style_end + len('</style>'):]
    with open(r'C:\Users\Luis\.openclaw\workspace\work\mathquest\mathquest\templates\parent_dashboard2.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Done! New length:', len(new_content))
else:
    print('ERROR: </style> not found')
