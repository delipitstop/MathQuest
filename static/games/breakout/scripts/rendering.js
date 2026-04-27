const ctx = config.canvas.getContext('2d');

const BRICK_COLORS = ['#F472B6', '#FBBF24', '#F87171', '#34D399', '#60A5FA', '#A78BFA', '#FB923C', '#2dd4a8'];

function drawBall(x, y, ballRadius) {
    ctx.save();
    if (gameState.mathPowerBall) {
        ctx.shadowColor = '#34D399';
        ctx.shadowBlur = 18;
        ctx.fillStyle = '#34D399';
    } else {
        ctx.fillStyle = '#FFFF00';
    }
    ctx.beginPath();
    ctx.arc(x, y, ballRadius, 0, Math.PI * 2);
    ctx.fill();
    ctx.closePath();
    ctx.restore();
}

function drawPaddle(paddleX) {
    ctx.save();
    ctx.shadowColor = '#A78BFA';
    ctx.shadowBlur = 8;
    ctx.beginPath();
    ctx.rect(paddleX, config.canvas.height - config.paddleHeight, config.paddleWidth, config.paddleHeight);
    ctx.fillStyle = '#A78BFA';
    ctx.fill();
    ctx.closePath();
    ctx.restore();
}

function drawBricks(bricks) {
    for (let c = 0; c < bricks.length; c++) {
        for (let r = 0; r < bricks[c].length; r++) {
            if (bricks[c][r].status === 1) {
                let brickX = bricks[c][r].x;
                let brickY = bricks[c][r].y;
                const color = BRICK_COLORS[bricks[c][r].colorIndex % BRICK_COLORS.length];

                ctx.save();
                ctx.shadowColor = color;
                ctx.shadowBlur = 6;
                ctx.beginPath();
                ctx.rect(brickX, brickY, config.brickWidth, config.brickHeight);
                ctx.fillStyle = color;
                ctx.fill();
                ctx.closePath();
                ctx.restore();

                // Draw question on brick
                const qText = bricks[c][r].question || '';
                const fontSize = Math.min(config.brickWidth / (qText.length * 0.6), config.brickHeight * 0.55, 13);
                ctx.font = `bold ${fontSize}px Nunito, sans-serif`;
                ctx.fillStyle = 'rgba(255,255,255,0.95)';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(qText, brickX + config.brickWidth / 2, brickY + config.brickHeight / 2 - 2);

                // Draw "?" below
                ctx.font = `bold ${fontSize * 0.9}px Nunito, sans-serif`;
                ctx.fillStyle = 'rgba(255,255,255,0.5)';
                ctx.fillText('= ?', brickX + config.brickWidth / 2, brickY + config.brickHeight / 2 + fontSize * 0.9);
            }
        }
    }
}

function drawScore(score) {
    ctx.font = "bold 18px Nunito, sans-serif";
    ctx.fillStyle = document.body.classList.contains('light-mode') ? "#222" : "#fff";
    ctx.textAlign = 'left';
    ctx.fillText("Score: " + score, 8, 24);
}

function drawLives(lives) {
    ctx.save();
    ctx.font = "bold 18px Nunito, sans-serif";
    ctx.fillStyle = document.body.classList.contains('light-mode') ? "#222" : "#fff";
    ctx.textAlign = 'right';
    ctx.fillText("Lives: " + lives, config.canvas.width - 8, 24);
    ctx.restore();
}

function clearCanvas() {
    ctx.clearRect(0, 0, config.canvas.width, config.canvas.height);
    // Stars background
    ctx.fillStyle = 'rgba(255,255,255,0.05)';
    for (let i = 0; i < 40; i++) {
        ctx.fillRect((i * 73) % config.canvas.width, (i * 53) % config.canvas.height, 2, 2);
    }
}