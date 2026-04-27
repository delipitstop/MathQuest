// MathQuest - Target Shoot Game

var canvas, ctx, score=0, streak=0, level=1, hits=0, gameActive=false;
var totalAnswered=0, correctCount=0;
var targets=[], gameTimer=null, timeLeft=60;
var canvasW=720, canvasH=480;

function startGame(){
    score=0; streak=0; level=1; hits=0; totalAnswered=0; correctCount=0; gameActive=true; timeLeft=60;
    document.getElementById('startScreen').style.display = 'none';
    document.getElementById('resultScreen').style.display = 'none';
    updateHUD();
    spawnTargets();
    if(gameTimer) clearInterval(gameTimer);
    gameTimer = setInterval(function(){
        timeLeft--;
        document.getElementById('timeEl').textContent = timeLeft + 's';
        if(timeLeft<=0){ endGame(); return; }
        if(streak>0 && streak%10===0 && level<5){ level++; spawnTargets(); }
    }, 1000);
    draw();
}

function generateQuestion(){
    var type = level<=2 ? 'add' : (level<=4 ? 'both' : 'sub');
    var a, b, correct;
    if(type==='add'){
        a = Math.floor(Math.random()*50)+10;
        b = Math.floor(Math.random()*50)+10;
        correct = a+b;
    } else if(type==='sub'){
        a = Math.floor(Math.random()*50)+20;
        b = Math.floor(Math.random()*20)+1;
        correct = a-b;
    } else {
        var rnd = Math.random();
        if(rnd < 0.5){
            a = Math.floor(Math.random()*50)+10;
            b = Math.floor(Math.random()*50)+10;
            correct = a+b;
        } else {
            a = Math.floor(Math.random()*50)+20;
            b = Math.floor(Math.random()*20)+1;
            correct = a-b;
        }
    }
    var choices = [correct];
    while(choices.length < 4){
        var c = correct + (Math.floor(Math.random()*20)-10);
        if(c > 0 && !choices.includes(c)) choices.push(c);
    }
    choices.sort(function(){ return 0.5 - Math.random(); });
    var sign = type==='sub' ? ' - ' : ' + ';
    return {text: a+sign+b+' = ?', choices: choices, correct: correct};
}

function spawnTargets(){
    var q = generateQuestion();
    targets = [];
    var minDist = 90;
    for(var i=0; i<4; i++){
        var x, y, attempts=0;
        do {
            x = Math.floor(Math.random()*(canvasW-120))+60;
            y = Math.floor(Math.random()*(canvasH-120))+60;
            attempts++;
        } while(attempts<50 && (
            targets.some(function(t){ return Math.hypot(t.x-x,t.y-y)<minDist; }) ||
            (Math.abs(x-canvasW/2)<80 && Math.abs(y-canvasH/2)<60)
        ));
        var colors = ['#EF4444','#F97316','#EAB308','#22C55E','#06B6D4','#3B82F6','#8B5CF6','#EC4899'];
        targets.push({x:x, y:y, size:50, color:colors[i], value:q.choices[i], pulse:0});
    }
    window.currentQ = q;
}

function draw(){
    if(!gameActive) return;
    ctx.clearRect(0,0,canvasW,canvasH);
    // Stars background
    ctx.fillStyle='#60A5FA'; ctx.font='16px serif'; ctx.globalAlpha=0.15;
    for(var i=0; i<20; i++) ctx.fillText('*', (i*73)%canvasW, (i*47)%canvasH);
    ctx.globalAlpha=1;
    // Draw targets
    targets.forEach(function(t,i){
        t.pulse += 0.1;
        var pulse = 1 + Math.sin(t.pulse)*0.05;
        var s = t.size * pulse;
        ctx.save();
        ctx.translate(t.x, t.y);
        ctx.shadowColor = t.color;
        ctx.shadowBlur = 20 + Math.sin(t.pulse)*8;
        ctx.beginPath();
        ctx.arc(0,0,s,0,Math.PI*2);
        ctx.fillStyle = t.color;
        ctx.fill();
        ctx.beginPath();
        ctx.arc(0,0,s*0.65,0,Math.PI*2);
        ctx.fillStyle = 'rgba(255,255,255,0.3)';
        ctx.fill();
        ctx.beginPath();
        ctx.arc(0,0,s*0.3,0,Math.PI*2);
        ctx.fillStyle = 'rgba(255,255,255,0.6)';
        ctx.fill();
        ctx.shadowBlur = 0;
        ctx.fillStyle = 'white';
        ctx.font = 'bold 18px Nunito';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(t.value, 0, 1);
        ctx.restore();
    });
    // Timer bar
    var barW = canvasW - 40;
    ctx.fillStyle = 'rgba(0,0,0,0.3)';
    ctx.beginPath(); ctx.roundRect(20,canvasH-20,barW,8,4); ctx.fill();
    ctx.fillStyle = timeLeft>15 ? '#60A5FA' : '#EF4444';
    ctx.beginPath(); ctx.roundRect(20,canvasH-20,barW*(timeLeft/60),8,4); ctx.fill();
    ctx.fillStyle = 'rgba(96,165,250,0.9)';
    ctx.font = 'bold 14px Nunito';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText('Time: '+timeLeft+'s', 20, 20);
    ctx.fillText('Level: '+level, 20, 40);
    if(gameActive) requestAnimationFrame(draw);
}

function updateHUD(){
    document.getElementById('scoreEl').textContent = score;
    document.getElementById('streakEl').textContent = streak;
    document.getElementById('levelEl').textContent = level;
    document.getElementById('hitsEl').textContent = hits+'/'+totalAnswered;
}

function endGame(){
    gameActive = false;
    clearInterval(gameTimer);
    var acc = totalAnswered > 0 ? Math.round(correctCount/totalAnswered*100) : 0;
    document.getElementById('finalScore').textContent = score + ' pts';
    document.getElementById('finalAccuracy').textContent = 'Accuracy: ' + acc + '%';
    var badge = '';
    if(score >= 500) badge = '🎯 Sharpshooter!';
    else if(score >= 300) badge = '⭐ Level Up Star!';
    else if(score >= 100) badge = '🌟 Good Aim!';
    else badge = 'Keep Practicing!';
    document.getElementById('badgeEarned').textContent = badge;
    document.getElementById('resultScreen').style.display = 'flex';
    // Submit score
    var childId = document.body.getAttribute('data-child-id') || 1;
    fetch('/api/quiz/submit', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({child_id: parseInt(childId), game: 'targetshoot', score: score, accuracy: acc})
    }).catch(function(){});
}

// Init when page loads
document.addEventListener('DOMContentLoaded', function(){
    canvas = document.getElementById('gameCanvas');
    ctx = canvas ? canvas.getContext('2d') : null;

    var startBtn = document.getElementById('startBtn');
    if(startBtn && !startBtn.hasAttribute('data-listener')){
        startBtn.setAttribute('data-listener', 'true');
        startBtn.addEventListener('click', function(e){
            e.preventDefault();
            startGame();
        });
    }

    if(canvas){
        canvas.addEventListener('click', function(e){
            if(!gameActive) return;
            var rect = canvas.getBoundingClientRect();
            var mx = e.clientX - rect.left;
            var my = e.clientY - rect.top;
            var hit = null;
            targets.forEach(function(t){
                if(Math.hypot(t.x-mx, t.y-my) < t.size) hit = t;
            });
            if(!hit){ streak = 0; updateHUD(); return; }
            totalAnswered++;
            if(hit.value === window.currentQ.correct){
                correctCount++;
                hits++;
                score += 10 * level;
                streak++;
                hit.color = '#34D399';
            } else {
                streak = 0;
                hit.color = '#EF4444';
            }
            updateHUD();
            setTimeout(function(){ if(gameActive) spawnTargets(); }, 400);
        });
    }
});