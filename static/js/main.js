/* MathQuest - Main JavaScript */

// ===== CONFETTI =====
function showConfetti() {
    const colors = ['#A78BFA', '#34D399', '#FBBF24', '#F97316', '#F472B6', '#60A5FA', '#F87171'];
    const container = document.createElement('div');
    container.className = 'confetti';
    document.body.appendChild(container);
    
    for (let i = 0; i < 60; i++) {
        const piece = document.createElement('div');
        piece.className = 'confetti-piece';
        piece.style.left = Math.random() * 100 + '%';
        piece.style.background = colors[Math.floor(Math.random() * colors.length)];
        piece.style.animationDelay = Math.random() * 2 + 's';
        piece.style.animationDuration = (Math.random() * 2 + 2) + 's';
        container.appendChild(piece);
    }
    
    setTimeout(() => container.remove(), 5000);
}

// ===== PRACTICE =====
let currentQuestion = 0;
let questions = [];
let correctCount = 0;

function loadPractice(topic) {
    fetch(`/practice/${topic}`)
        .then(r => r.text())
        .then(html => {
            document.open();
            document.write(html);
            document.close();
        });
}

function initPractice(qs) {
    questions = qs;
    currentQuestion = 0;
    correctCount = 0;
    showQuestion();
}

function showQuestion() {
    const q = questions[currentQuestion];
    const total = questions.length;
    const pct = (currentQuestion / total) * 100;
    
    // Update progress bar
    const progressFill = document.getElementById('progressFill');
    if (progressFill) progressFill.style.width = pct + '%';
    
    // Update question
    document.getElementById('qNum').textContent = `Question ${currentQuestion + 1} of ${total}`;
    document.getElementById('qText').textContent = q.question;
    document.getElementById('answerInput').value = '';
    document.getElementById('answerInput').focus();
    
    // Hide hint/explanation
    const hintBox = document.getElementById('hintBox');
    const explBox = document.getElementById('explBox');
    if (hintBox) hintBox.style.display = 'none';
    if (explBox) explBox.style.display = 'none';
    
    // Reset input style
    const input = document.getElementById('answerInput');
    input.className = 'answer-input';
    input.disabled = false;
}

function showHint() {
    const q = questions[currentQuestion];
    const hintBox = document.getElementById('hintBox');
    hintBox.textContent = '💡 ' + q.hint;
    hintBox.style.display = 'block';
}

function showExplanation() {
    const q = questions[currentQuestion];
    const explBox = document.getElementById('explBox');
    explBox.innerHTML = '📖 <strong>Explanation:</strong><br>' + q.explanation;
    explBox.style.display = 'block';
}

function checkAnswer() {
    const input = document.getElementById('answerInput');
    const userAns = parseInt(input.value);
    const q = questions[currentQuestion];
    
    if (isNaN(userAns)) {
        input.classList.add('wrong');
        setTimeout(() => input.classList.remove('wrong'), 400);
        return;
    }
    
    input.disabled = true;
    
    if (userAns === q.answer) {
        input.classList.add('correct');
        correctCount++;
        showConfetti();
        
        // Update progress
        fetch('/api/update_progress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic: 'times_tables' })
        });
        
        setTimeout(() => {
            currentQuestion++;
            if (currentQuestion >= questions.length) {
                showPracticeComplete();
            } else {
                showQuestion();
            }
        }, 1200);
    } else {
        input.classList.add('wrong');
        setTimeout(() => {
            input.classList.remove('wrong');
            input.value = '';
            input.disabled = false;
            input.focus();
            showHint();
        }, 800);
    }
}

function showPracticeComplete() {
    const pct = Math.round((correctCount / questions.length) * 100);
    const container = document.querySelector('.practice-container');
    container.innerHTML = `
        <div class="result-card" style="background:white;border-radius:24px;padding:48px;text-align:center;box-shadow:0 8px 32px rgba(0,0,0,0.15);animation:popIn 0.6s cubic-bezier(0.34,1.56,0.64,1)">
            <div style="font-size:96px">🎉</div>
            <h2 style="font-size:36px;font-weight:900;color:#7C3AED;margin-bottom:8px">Amazing!</h2>
            <p style="font-size:20px;color:#6B7280;margin-bottom:24px">You finished all ${questions.length} questions!</p>
            <div style="font-size:72px;font-weight:900;color:#34D399;margin-bottom:8px">${pct}%</div>
            <p style="font-size:18px;color:#6B7280;margin-bottom:32px">${correctCount} out of ${questions.length} correct</p>
            <div style="display:flex;gap:16px;justify-content:center;flex-wrap:wrap">
                <a href="/student/dashboard" class="btn btn-purple" style="padding:16px 32px;border-radius:50px;font-size:18px;font-weight:800;text-decoration:none;display:inline-block;background:#A78BFA;color:white">← Back to Dashboard</a>
                <a href="/quiz/times_tables" class="btn btn-green" style="padding:16px 32px;border-radius:50px;font-size:18px;font-weight:800;text-decoration:none;display:inline-block;background:#34D399;color:white">Take Quiz →</a>
            </div>
        </div>
    `;
}

// ===== QUIZ =====
function checkQuizAnswer(qNum, totalQs) {
    const inputs = document.querySelectorAll('.quiz-a-input');
    let allAnswered = true;
    inputs.forEach(inp => {
        if (!inp.value.trim()) allAnswered = false;
    });
    
    if (!allAnswered) {
        alert('Please answer all questions!');
        return;
    }
    
    const form = document.getElementById('quizForm');
    const formData = new FormData(form);
    
    fetch('/submit_quiz', {
        method: 'POST',
        body: formData
    })
    .then(r => r.text())
    .then(html => {
        document.open();
        document.write(html);
        document.close();
        const pct = parseInt(document.body.querySelector('.result-score')?.textContent || '0');
        if (pct >= 80) showConfetti();
    });
}

// ===== MATH INVADERS GAME =====
let gameCanvas, gameCtx;
let player, aliens = [], bullets = [], alienBullets = [];
let score = 0, lives = 3, level = 1;
let currentMathQ = {}, mathAnswer = '';
let gameInterval = null;
let alienDirection = 1;
let alienSpeed = 1;

function initGame() {
    gameCanvas = document.getElementById('gameCanvas');
    gameCtx = gameCanvas.getContext('2d');
    
    // Responsive canvas
    const container = document.querySelector('.game-container');
    gameCanvas.width = Math.min(700, container.clientWidth - 40);
    gameCanvas.height = gameCanvas.width * 0.6;
    
    player = {
        x: gameCanvas.width / 2 - 25,
        y: gameCanvas.height - 50,
        w: 50,
        h: 30,
        speed: 6
    };
    
    aliens = [];
    const rows = 3 + Math.min(level - 1, 2);
    const cols = 6;
    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            aliens.push({
                x: 50 + c * 70,
                y: 40 + r * 50,
                w: 40,
                h: 30,
                alive: true,
                type: r
            });
        }
    }
    
    bullets = [];
    alienBullets = [];
    score = 0;
    
    generateMathQuestion();
    updateGameUI();
    
    if (gameInterval) clearInterval(gameInterval);
    gameInterval = setInterval(gameLoop, 1000 / 60);
    
    document.addEventListener('keydown', handleGameKey);
    gameCanvas.addEventListener('click', handleCanvasClick);
}

function generateMathQ() {
    const a = Math.floor(Math.random() * 12) + 1;
    const b = Math.floor(Math.random() * 12) + 1;
    return { q: `${a} × ${b}`, a: a * b };
}

function generateMathQuestion() {
    currentMathQ = generateMathQ();
    const qBox = document.getElementById('mathQ');
    if (qBox) {
        qBox.textContent = currentMathQ.q + ' = ?';
    }
    const inp = document.getElementById('mathInput');
    if (inp) {
        inp.value = '';
        inp.className = 'math-q-input';
    }
    mathAnswer = '';
}

function handleGameKey(e) {
    if (e.key === 'ArrowLeft') player.x -= player.speed;
    if (e.key === 'ArrowRight') player.x += player.speed;
    if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault();
        submitMathAnswer();
    }
    player.x = Math.max(0, Math.min(gameCanvas.width - player.w, player.x));
}

function handleCanvasClick(e) {
    submitMathAnswer();
}

function submitMathAnswer() {
    const inp = document.getElementById('mathInput');
    if (!inp || mathAnswer !== '') return;
    
    const val = parseInt(inp.value);
    if (isNaN(val)) return;
    
    mathAnswer = val;
    
    if (val === currentMathQ.a) {
        inp.classList.add('correct');
        // Shoot bullet
        bullets.push({ x: player.x + player.w / 2 - 3, y: player.y, w: 6, h: 14, speed: 10 });
        setTimeout(() => {
            generateMathQuestion();
            updateGameUI();
        }, 500);
    } else {
        inp.classList.add('wrong');
        setTimeout(() => {
            inp.classList.remove('wrong');
            inp.value = '';
            inp.focus();
            mathAnswer = '';
        }, 800);
    }
}

function gameLoop() {
    gameCtx.clearRect(0, 0, gameCanvas.width, gameCanvas.height);
    
    // Background stars
    gameCtx.fillStyle = 'rgba(255,255,255,0.3)';
    for (let i = 0; i < 50; i++) {
        gameCtx.fillRect(
            (i * 137) % gameCanvas.width,
            (i * 97) % gameCanvas.height,
            2, 2
        );
    }
    
    // Player
    gameCtx.fillStyle = '#34D399';
    gameCtx.fillRect(player.x, player.y, player.w, player.h);
    // Cockpit
    gameCtx.fillStyle = '#60A5FA';
    gameCtx.fillRect(player.x + 18, player.y + 5, 14, 10);
    
    // Aliens
    aliens.forEach(alien => {
        if (!alien.alive) return;
        const colors = ['#F472B6', '#FBBF24', '#F87171'];
        const emojis = ['👾', '👽', '🤖'];
        gameCtx.font = '28px Arial';
        gameCtx.textAlign = 'center';
        gameCtx.fillText(emojis[alien.type % 3], alien.x + alien.w / 2, alien.y + alien.h - 2);
    });
    
    // Bullets
    gameCtx.fillStyle = '#34D399';
    bullets.forEach(b => {
        gameCtx.fillRect(b.x, b.y, b.w, b.h);
    });
    
    // Move bullets
    bullets = bullets.filter(b => {
        b.y -= b.speed;
        // Check collision with aliens
        for (let alien of aliens) {
            if (!alien.alive) continue;
            if (b.x > alien.x && b.x < alien.x + alien.w && b.y < alien.y + alien.h && b.y > alien.y) {
                alien.alive = false;
                score += 10 * (alien.type + 1);
                updateGameUI();
                return false;
            }
        }
        return b.y > 0;
    });
    
    // Move aliens
    let hitEdge = false;
    aliens.forEach(alien => {
        if (!alien.alive) return;
        alien.x += alienDirection * (0.5 + level * 0.2);
        if (alien.x <= 0 || alien.x + alien.w >= gameCanvas.width) hitEdge = true;
    });
    
    if (hitEdge) {
        alienDirection *= -1;
        aliens.forEach(alien => {
            if (!alien.alive) return;
            alien.y += 15;
        });
    }
    
    // Check win
    if (aliens.every(a => !a.alive)) {
        level++;
        initGame();
    }
    
    // Check lose (aliens reach bottom)
    if (aliens.some(a => !a.alive && a.y + a.h >= player.y)) {
        gameOver();
    }
}

function updateGameUI() {
    const scoreEl = document.getElementById('gameScore');
    const levelEl = document.getElementById('gameLevel');
    const livesEl = document.getElementById('gameLives');
    if (scoreEl) scoreEl.textContent = score;
    if (levelEl) levelEl.textContent = level;
    if (livesEl) livesEl.textContent = '❤️'.repeat(Math.max(0, lives));
}

function gameOver() {
    clearInterval(gameInterval);
    gameCtx.fillStyle = 'rgba(0,0,0,0.7)';
    gameCtx.fillRect(0, 0, gameCanvas.width, gameCanvas.height);
    gameCtx.fillStyle = 'white';
    gameCtx.font = 'bold 36px Nunito';
    gameCtx.textAlign = 'center';
    gameCtx.fillText('GAME OVER', gameCanvas.width / 2, gameCanvas.height / 2 - 20);
    gameCtx.font = '24px Nunito';
    gameCtx.fillText(`Score: ${score}`, gameCanvas.width / 2, gameCanvas.height / 2 + 20);
}

// ===== STARTUP =====
document.addEventListener('DOMContentLoaded', function() {
    // Auto-focus answer inputs
    const inputs = document.querySelectorAll('.answer-input, .quiz-q-input, .math-q-input');
    inputs.forEach(inp => {
        inp.addEventListener('keydown', e => {
            if (e.key === 'Enter') {
                if (inp.classList.contains('answer-input')) checkAnswer();
                else if (inp.classList.contains('math-q-input')) submitMathAnswer();
            }
        });
    });
});
