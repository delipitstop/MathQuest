// MathQuest Snake — maths-powered version
// Eat the number that solves the equation!

const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
canvas.width = canvas.height = Math.min(window.innerWidth * 0.9, 560);

const COLS = 28;
const box = canvas.width / COLS;
let score = 0;
let lives = 3;
let speed = 150;
let level = 1;
let snake = [{ x: box * 5, y: box * 5 }];
let direction = 'RIGHT';
let nextDirection = 'RIGHT';
let foods = [];
let gameLoop;
let question = null;
let questionActive = false;
let questionTimer = null;
let answeredCorrectly = false;
let awaitingAnswer = false;

function generateQuestion() {
    const ops = ['+', '-', '\u00D7', '\u00F7'];
    const op = ops[Math.floor(Math.random() * ops.length)];
    let a, b, answer;
    if (op === '+') {
        a = Math.floor(Math.random() * 50) + 5;
        b = Math.floor(Math.random() * 50) + 5;
        answer = a + b;
    } else if (op === '-') {
        a = Math.floor(Math.random() * 50) + 10;
        b = Math.floor(Math.random() * Math.min(a, 50)) + 1;
        answer = a - b;
    } else if (op === '\u00D7') {
        a = Math.floor(Math.random() * 12) + 2;
        b = Math.floor(Math.random() * 12) + 2;
        answer = a * b;
    } else {
        b = Math.floor(Math.random() * 11) + 2;
        answer = Math.floor(Math.random() * 12) + 2;
        a = answer * b;
    }
    const wrongAnswers = [answer + Math.floor(Math.random() * 10) + 1,
                          answer - Math.floor(Math.random() * 10) - 1,
                          answer + Math.floor(Math.random() * 20) + 5];
    const choices = [...new Set([answer, ...wrongAnswers])].slice(0, 3);
    while (choices.length < 3) {
        const w = answer + Math.floor(Math.random() * 15) - 7;
        if (w > 0 && w !== answer && !choices.includes(w)) choices.push(w);
    }
    choices.sort(() => Math.random() - 0.5);
    return { text: a + ' ' + op + ' ' + b + ' = ?', answer, choices };
}

function createFoods() {
    foods = [];
    const q = generateQuestion();
    question = q;
    const positions = [];
    for (let r = 0; r < COLS; r++) {
        for (let c = 0; c < COLS; c++) {
            const gx = c * box, gy = r * box;
            const onSnake = snake.some(s => s.x === gx && s.y === gy);
            if (!onSnake && gx > box * 3 && gx < canvas.width - box * 3) {
                positions.push({ x: gx, y: gy });
            }
        }
    }
    positions.sort(() => Math.random() - 0.5);
    q.choices.forEach((choice, i) => {
        if (positions[i]) {
            foods.push({ x: positions[i].x, y: positions[i].y, value: choice, isCorrect: choice === q.answer });
        }
    });
}

document.addEventListener('keydown', changeDirection);
document.addEventListener('keydown', handleAnswer);

function changeDirection(e) {
    if (awaitingAnswer) return;
    const map = { ArrowUp: 'UP', ArrowDown: 'DOWN', ArrowLeft: 'LEFT', ArrowRight: 'RIGHT' };
    if (!map[e.key]) return;
    const nd = map[e.key];
    const opposite = { UP: 'DOWN', DOWN: 'UP', LEFT: 'RIGHT', RIGHT: 'LEFT' };
    if (nd !== opposite[direction]) nextDirection = nd;
    e.preventDefault();
}

function handleAnswer(e) {
    if (!awaitingAnswer) return;
    if (e.key >= '0' && e.key <= '9' || e.key === '-' || e.key === 'Enter') {
        const input = document.getElementById('mathInput');
        if (e.key === 'Enter') {
            submitAnswer();
        } else if (e.key === 'Backspace') {
            input.value = input.value.slice(0, -1);
        } else {
            input.value += e.key;
        }
    }
}

function submitAnswer() {
    if (!awaitingAnswer) return;
    const val = parseInt(document.getElementById('mathInput').value);
    if (val === question.answer) {
        score += 50;
        document.getElementById('feedback').textContent = '\u2705 Correct! +50';
        document.getElementById('feedback').style.color = '#34D399';
    } else {
        lives--;
        document.getElementById('feedback').textContent = '\u274C ' + val + ' \u2014 Answer: ' + question.answer;
        document.getElementById('feedback').style.color = '#F87171';
    }
    document.getElementById('score').innerText = 'Score: ' + score;
    document.getElementById('lives').innerText = 'Lives: ' + '\u2764\uFE0F'.repeat(Math.max(lives, 0));
    hideQuestion();
    if (lives <= 0) {
        showGameOver();
    } else {
        createFoods();
    }
}

function showQuestion() {
    const el = document.getElementById('questionBox');
    if (!el) return;
    el.style.display = 'block';
    document.getElementById('mathQ').textContent = question.text;
    document.getElementById('mathInput').value = '';
    document.getElementById('feedback').textContent = '';
    document.getElementById('mathInput').focus();
}

function hideQuestion() {
    const el = document.getElementById('questionBox');
    if (el) el.style.display = 'none';
    awaitingAnswer = false;
}

function drawSnake() {
    snake.forEach((seg, i) => {
        ctx.fillStyle = i === 0 ? '#00ff88' : '#00cc66';
        ctx.fillRect(seg.x + 1, seg.y + 1, box - 2, box - 2);
        ctx.strokeStyle = '#0a4a2a';
        ctx.lineWidth = 1;
        ctx.strokeRect(seg.x + 1, seg.y + 1, box - 2, box - 2);
        if (i === 0) {
            // Eyes
            ctx.fillStyle = 'white';
            const ex = direction === 'RIGHT' ? seg.x + box * 0.7 : direction === 'LEFT' ? seg.x + box * 0.2 : seg.x + box * 0.2;
            const ey = direction === 'DOWN' ? seg.y + box * 0.7 : direction === 'UP' ? seg.y + box * 0.2 : seg.y + box * 0.2;
            ctx.beginPath();
            ctx.arc(ex + 2, ey + 2, 2, 0, Math.PI * 2);
            ctx.arc(ex + box * 0.4, ey + 2, 2, 0, Math.PI * 2);
            ctx.fill();
        }
    });
}

function drawFoods() {
    foods.forEach(f => {
        const isCorrect = f.value === question.answer;
        ctx.save();
        ctx.shadowColor = isCorrect ? '#34D399' : '#FBBF24';
        ctx.shadowBlur = 10;
        ctx.fillStyle = isCorrect ? '#34D399' : '#FBBF24';
        ctx.beginPath();
        ctx.roundRect(f.x + 2, f.y + 2, box - 4, box - 4, 6);
        ctx.fill();
        ctx.fillStyle = 'white';
        ctx.font = 'bold ' + (box * 0.45) + 'px Nunito, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(f.value, f.x + box / 2, f.y + box / 2 + 1);
        ctx.restore();
    });
}

function drawStars() {
    ctx.fillStyle = 'rgba(255,255,255,0.15)';
    for (let i = 0; i < 30; i++) {
        ctx.fillRect((i * 73) % canvas.width, (i * 53) % canvas.height, 2, 2);
    }
}

function moveSnake() {
    direction = nextDirection;
    const head = { ...snake[0] };
    if (direction === 'UP') head.y -= box;
    else if (direction === 'DOWN') head.y += box;
    else if (direction === 'LEFT') head.x -= box;
    else if (direction === 'RIGHT') head.x += box;
    head.x = ((head.x % canvas.width) + canvas.width) % canvas.width;
    head.y = ((head.y % canvas.height) + canvas.height) % canvas.height;

    if (snake.slice(1).some(s => s.x === head.x && s.y === head.y)) {
        showGameOver(); return;
    }
    snake.unshift(head);

    if (head.y < 0 || head.y >= canvas.height || head.x < 0 || head.x >= canvas.width) {
        showGameOver(); return;
    }

    const eaten = foods.find(f => f.x === head.x && f.y === head.y);
    if (eaten) {
        if (eaten.isCorrect) {
            score += 20;
            awaitingAnswer = true;
            showQuestion();
            document.getElementById('score').innerText = 'Score: ' + score;
            foods = [];
        } else {
            lives--;
            document.getElementById('lives').innerText = 'Lives: ' + '\u2764\uFE0F'.repeat(Math.max(lives, 0));
            document.getElementById('feedback').textContent = '\u26A0\uFE0F Wrong number! Find the answer!';
            document.getElementById('feedback').style.color = '#FBBF24';
            snake.pop();
            foods = foods.filter(f => f.x !== head.x || f.y !== head.y);
            if (lives <= 0) { showGameOver(); return; }
        }
    } else {
        snake.pop();
    }
}

function checkCollision() {
    const head = snake[0];
    if (head.x < 0 || head.x >= canvas.width || head.y < 0 || head.y >= canvas.height) {
        showGameOver();
    }
}

function showGameOver() {
    clearInterval(gameLoop);
    ctx.fillStyle = 'rgba(0,0,0,0.82)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#FBBF24';
    ctx.font = 'bold 42px Nunito, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('GAME OVER', canvas.width / 2, canvas.height / 2 - 30);
    ctx.fillStyle = 'white';
    ctx.font = '26px Nunito, sans-serif';
    ctx.fillText('Score: ' + score + '  |  Level: ' + level, canvas.width / 2, canvas.height / 2 + 15);
    ctx.fillStyle = '#A78BFA';
    ctx.font = '18px Nunito, sans-serif';
    ctx.fillText('Click or press Enter to play again', canvas.width / 2, canvas.height / 2 + 60);
    canvas.style.cursor = 'pointer';
    canvas.onclick = function() {
        canvas.onclick = null;
        canvas.style.cursor = '';
        restartGame();
    };
}

function restartGame() {
    snake = [{ x: box * 5, y: box * 5 }];
    direction = 'RIGHT';
    nextDirection = 'RIGHT';
    score = 0;
    lives = 3;
    speed = 150;
    level = 1;
    document.getElementById('score').innerText = 'Score: 0';
    document.getElementById('lives').innerText = 'Lives: \u2764\uFE0F\u2764\uFE0F\u2764\uFE0F';
    document.getElementById('level').innerText = 'Level: 1';
    document.getElementById('feedback').textContent = '';
    hideQuestion();
    createFoods();
    gameLoop = setInterval(update, speed);
}

function update() {
    if (awaitingAnswer) {
        draw();
        return;
    }
    moveSnake();
    draw();
    checkCollision();
}

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawStars();
    drawFoods();
    drawSnake();
}

createFoods();
gameLoop = setInterval(update, speed);

window.addEventListener('resize', () => {
    canvas.width = canvas.height = Math.min(window.innerWidth * 0.9, 560);
});

// Polyfill roundRect
if (!CanvasRenderingContext2D.prototype.roundRect) {
    CanvasRenderingContext2D.prototype.roundRect = function(x, y, w, h, r) {
        this.beginPath();
        this.moveTo(x + r, y);
        this.lineTo(x + w - r, y);
        this.arcTo(x + w, y, x + w, y + r, r);
        this.lineTo(x + w, y + h - r);
        this.arcTo(x + w, y + h, x + w - r, y + h, r);
        this.lineTo(x + r, y + h);
        this.arcTo(x, y + h, x, y + h - r, r);
        this.lineTo(x, y + r);
        this.arcTo(x, y, x + r, y, r);
        this.closePath();
        return this;
    };
}
