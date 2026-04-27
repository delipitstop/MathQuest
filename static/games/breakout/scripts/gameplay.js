const gameState = {
    x: config.canvas.width/2,
    y: config.canvas.height - 30,
    dx: config.initialSpeed,
    dy: -config.initialSpeed,
    speed: config.initialSpeed,
    ballRadius: config.ballRadius,
    paddleX: (config.canvas.width-config.paddleWidth)/2,
    score: 0,
    lives: config.initialLives,
    bricks: [],
    gameOver: false,
    mathPowerActive: false,
    mathPowerBall: false
};

let currentMathBrick = null;
let mathOverlayActive = false;
let mathInputVal = '';
let mathTimerId = null;
let mathTimeLeft = 0;

function makeMathQuestion() {
    const ops = ['+', '-', '\u00D7', '\u00F7'];
    const op = ops[Math.floor(Math.random() * ops.length)];
    let a, b, answer;
    if (op === '+') {
        a = Math.floor(Math.random() * 40) + 5;
        b = Math.floor(Math.random() * 40) + 5;
        answer = a + b;
    } else if (op === '-') {
        a = Math.floor(Math.random() * 40) + 15;
        b = Math.floor(Math.random() * Math.min(a - 1, 40)) + 1;
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
    return { text: a + ' ' + op + ' ' + b, answer };
}

function updatePaddleX(newPaddleX) {
    gameState.paddleX = newPaddleX;
}

function initBricks() {
    changeBrickColumnCountAndOffsetLeft();
    gameState.bricks = [];

    for (let c = 0; c < config.brickColumnCount; c++) {
        gameState.bricks[c] = [];
        for (let r = 0; r < config.brickRowCount; r++) {
            const q = makeMathQuestion();
            gameState.bricks[c][r] = {
                x: 0,
                y: 0,
                status: 1,
                lives: 1,
                question: q.text,
                answer: q.answer,
                colorIndex: r
            };
        }
    }

    for (let c = 0; c < config.brickColumnCount; c++) {
        for (let r = 0; r < config.brickRowCount; r++) {
            if (gameState.bricks[c][r].status === 1) {
                let brickX = (c * (config.brickWidth + config.brickPadding)) + config.brickOffsetLeft;
                let brickY = (r * (config.brickHeight + config.brickPadding)) + config.brickOffsetTop;
                gameState.bricks[c][r].x = brickX;
                gameState.bricks[c][r].y = brickY;
            }
        }
    }
}

function changeBrickColumnCountAndOffsetLeft() {
    let lengthBricks = (config.brickColumnCount * (config.brickWidth + config.brickPadding)) + config.brickOffsetLeft;
    while (lengthBricks >= config.canvas.width) {
        config.brickColumnCount = config.brickColumnCount - 1;
        lengthBricks = (config.brickColumnCount * (config.brickWidth + config.brickPadding)) + config.brickOffsetLeft;
    }
    config.brickOffsetLeft = ((config.canvas.width - lengthBricks) + config.brickOffsetLeft) / 2;
}

function showMathOverlay(brickRef) {
    currentMathBrick = brickRef;
    mathOverlayActive = true;
    mathInputVal = '';
    mathTimeLeft = 15;
    const el = document.getElementById('mathOverlay');
    if (el) {
        el.style.display = 'flex';
        document.getElementById('mathQ').textContent = brickRef.question + ' = ?';
        document.getElementById('mathInput2').value = '';
        document.getElementById('mathFeedback').textContent = '';
        document.getElementById('mathTimer').textContent = '15s';
        document.getElementById('mathInput2').focus();
    }
    if (mathTimerId) clearInterval(mathTimerId);
    mathTimerId = setInterval(() => {
        mathTimeLeft--;
        const timerEl = document.getElementById('mathTimer');
        if (timerEl) timerEl.textContent = mathTimeLeft + 's';
        if (mathTimeLeft <= 0) {
            clearInterval(mathTimerId);
            rejectMathAnswer();
        }
    }, 1000);
}

function submitMathAnswer() {
    if (!mathOverlayActive || !currentMathBrick) return;
    const val = parseInt(document.getElementById('mathInput2').value);
    const fb = document.getElementById('mathFeedback');
    if (val === currentMathBrick.answer) {
        if (fb) { fb.textContent = '\u2705 Correct! +10 pts'; fb.style.color = '#34D399'; }
        gameState.score += 10;
        clearInterval(mathTimerId);
        setTimeout(closeMathOverlay, 800);
        // Destroy brick
        currentMathBrick.status = 0;
        // Activate math power ball for 8 seconds
        gameState.mathPowerBall = true;
        gameState.mathPowerActive = true;
        setTimeout(() => { gameState.mathPowerActive = false; gameState.mathPowerBall = false; }, 8000);
        currentMathBrick = null;
    } else {
        if (fb) { fb.textContent = '\u274C Try again!'; fb.style.color = '#F87171'; }
        document.getElementById('mathInput2').value = '';
        document.getElementById('mathInput2').focus();
    }
}

function rejectMathAnswer() {
    if (!mathOverlayActive) return;
    clearInterval(mathTimerId);
    const fb = document.getElementById('mathFeedback');
    if (fb) { fb.textContent = '\u23F3 Time\'s up!'; fb.style.color = '#FBBF24'; }
    gameState.lives--;
    setTimeout(closeMathOverlay, 1000);
    currentMathBrick = null;
}

function closeMathOverlay() {
    mathOverlayActive = false;
    currentMathBrick = null;
    const el = document.getElementById('mathOverlay');
    if (el) el.style.display = 'none';
}

function collisionDetection() {
    for (let c = 0; c < config.brickColumnCount; c++) {
        for (let r = 0; r < config.brickRowCount; r++) {
            let b = gameState.bricks[c][r];
            if (!b || b.status !== 1) continue;

            if (gameState.x + gameState.ballRadius > b.x &&
                gameState.x - gameState.ballRadius < b.x + config.brickWidth &&
                gameState.y + gameState.ballRadius > b.y &&
                gameState.y - gameState.ballRadius < b.y + config.brickHeight) {

                // Check if this is a maths brick
                if (b.question && !mathOverlayActive) {
                    showMathOverlay(b);
                    // Still bounce the ball
                    const fromTop = gameState.y - gameState.ballRadius <= b.y;
                    const fromBottom = gameState.y + gameState.ballRadius >= b.y + config.brickHeight;
                    if (fromTop || fromBottom) {
                        gameState.dy = -gameState.dy;
                    } else {
                        gameState.dx = -gameState.dx;
                    }
                    return;
                }

                // Normal brick hit (no math)
                const fromTop = gameState.y - gameState.ballRadius <= b.y;
                const fromBottom = gameState.y + gameState.ballRadius >= b.y + config.brickHeight;
                if (fromTop || fromBottom) {
                    gameState.dy = -gameState.dy;
                } else {
                    gameState.dx = -gameState.dx;
                }

                // Math power ball smashes all bricks at once!
                if (gameState.mathPowerBall) {
                    b.status = 0;
                    gameState.score++;
                } else {
                    b.lives -= 1;
                    if (b.lives <= 0) {
                        b.status = 0;
                        gameState.score++;
                    }
                }

                if (gameState.score >= config.brickRowCount * config.brickColumnCount) {
                    resetValues(elements.success);
                }
                return;
            }
        }
    }
}

function resetValues(element) {
    element.style.top = "40%";
    gameState.gameOver = true;
}

function setupSliders() {
    elements.speedSlider.addEventListener("input", () => {
        gameState.speed = parseFloat(elements.speedSlider.value);
        if (!controls.isPaused) {
            gameState.dx = gameState.dx > 0 ? gameState.speed : -gameState.speed;
            gameState.dy = gameState.dy > 0 ? gameState.speed : -gameState.speed;
        }
    });
    elements.sizeSlider.addEventListener("input", () => {
        gameState.ballRadius = parseInt(elements.sizeSlider.value);
    });
}

function draw() {
    clearCanvas();
    drawBricks(gameState.bricks);
    drawBall(gameState.x, gameState.y, gameState.ballRadius);
    drawPaddle(gameState.paddleX);
    drawScore(gameState.score);
    drawLives(gameState.lives);

    // Math power indicator
    if (gameState.mathPowerBall) {
        ctx.save();
        ctx.fillStyle = '#34D399';
        ctx.font = 'bold 14px Nunito, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('\u26A1 MATH POWER: All bricks smash!', config.canvas.width / 2, 22);
        ctx.restore();
    }

    if (gameState.gameOver || controls.isPaused || mathOverlayActive) {
        requestAnimationFrame(draw);
        return;
    }

    collisionDetection();

    if (gameState.y + gameState.dy < gameState.ballRadius) {
        gameState.dy = -gameState.dy;
    } else if (gameState.y + gameState.dy > config.canvas.height - gameState.ballRadius) {
        if (gameState.x > gameState.paddleX && gameState.x < gameState.paddleX + config.paddleWidth) {
            gameState.dy = -gameState.dy;
        } else {
            gameState.lives--;
            if (gameState.lives <= 0) {
                gameState.lives = 0;
                resetValues(elements.failure);
                requestAnimationFrame(draw);
                return;
            } else {
                gameState.x = config.canvas.width / 2;
                gameState.y = config.canvas.height - 30;
                gameState.dx = gameState.speed;
                gameState.dy = -gameState.speed;
                gameState.paddleX = (config.canvas.width - config.paddleWidth) / 2;
            }
        }
    }

    if (gameState.x + gameState.dx > config.canvas.width - gameState.ballRadius ||
        gameState.x + gameState.dx < gameState.ballRadius) {
        gameState.dx = -gameState.dx;
        gameState.dy += getRandomArbitrary(-0.4, 0.4);
    }

    if (controls.rightPressed && gameState.paddleX < config.canvas.width - config.paddleWidth) {
        gameState.paddleX += 7;
    } else if (controls.leftPressed && gameState.paddleX > 0) {
        gameState.paddleX -= 7;
    }

    gameState.x += gameState.dx;
    gameState.y += gameState.dy;

    requestAnimationFrame(draw);
}

function init() {
    gameState.gameOver = false;
    gameState.lives = config.initialLives;
    gameState.score = 0;
    gameState.x = config.canvas.width / 2;
    gameState.y = config.canvas.height - 30;
    gameState.dx = config.initialSpeed;
    gameState.dy = -config.initialSpeed;
    gameState.ballRadius = config.ballRadius;
    gameState.paddleX = (config.canvas.width - config.paddleWidth) / 2;
    gameState.mathPowerBall = false;
    gameState.mathPowerActive = false;
    mathOverlayActive = false;
    if (mathTimerId) clearInterval(mathTimerId);

    if (elements.success) elements.success.style.top = "-40%";
    if (elements.failure) elements.failure.style.top = "-40%";
    controls.isPaused = false;

    setupEventListeners();
    setupSliders();
    initBricks();
    draw();
}