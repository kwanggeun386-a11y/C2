const participantInput = document.getElementById('participant-count');
const inputsContainer = document.getElementById('inputs-container');
const setupSection = document.getElementById('setup-section');
const gameSection = document.getElementById('game-section');
const resultSection = document.getElementById('result-section');
const canvas = document.getElementById('ladder-canvas');
const ctx = canvas.getContext('2d');

let count = 4;
let menus = [];
let ladderData = [];
const colWidth = 100;
const rowHeight = 40;
const padding = 50;

function changeCount(val) {
    count = Math.max(2, Math.min(10, count + val));
    participantInput.value = count;
    renderInputs();
}

function renderInputs() {
    inputsContainer.innerHTML = '';
    for (let i = 0; i < count; i++) {
        const div = document.createElement('div');
        div.className = 'input-item';
        div.innerHTML = `
            <label>메뉴 ${i + 1}</label>
            <input type="text" placeholder="예: 김치찌개, 돈까스..." class="menu-input">
        `;
        inputsContainer.appendChild(div);
    }
}

document.getElementById('start-btn').addEventListener('click', () => {
    const inputs = document.querySelectorAll('.menu-input');
    menus = Array.from(inputs).map(input => input.value.trim() || '랜덤 메뉴');
    
    setupSection.classList.add('hidden');
    gameSection.classList.remove('hidden');
    
    initLadder();
});

function initLadder() {
    const width = (count - 1) * colWidth + padding * 2;
    const height = 15 * rowHeight + padding * 2;
    canvas.width = width;
    canvas.height = height;
    
    ladderData = [];
    // Generate horizontal bars
    for (let i = 0; i < 15; i++) {
        const row = [];
        for (let j = 0; j < count - 1; j++) {
            // Only add bar if no adjacent bar exists
            if (row[j-1]) {
                row.push(false);
            } else {
                row.push(Math.random() > 0.6);
            }
        }
        ladderData.push(row);
    }
    
    drawLadder();
}

function drawLadder() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 4;
    ctx.lineCap = 'round';
    
    // Vertical lines
    for (let i = 0; i < count; i++) {
        const x = padding + i * colWidth;
        ctx.beginPath();
        ctx.moveTo(x, padding);
        ctx.lineTo(x, canvas.height - padding);
        ctx.stroke();
        
        // Label at top (1, 2, 3...)
        ctx.fillStyle = '#4d94ff';
        ctx.font = 'bold 16px Outfit';
        ctx.textAlign = 'center';
        ctx.fillText(i + 1, x, padding - 15);
    }
    
    // Horizontal bars
    ctx.lineWidth = 4;
    for (let i = 0; i < ladderData.length; i++) {
        const y = padding + (i + 1) * rowHeight;
        for (let j = 0; j < ladderData[i].length; j++) {
            if (ladderData[i][j]) {
                const x1 = padding + j * colWidth;
                const x2 = padding + (j + 1) * colWidth;
                ctx.beginPath();
                ctx.moveTo(x1, y);
                ctx.lineTo(x2, y);
                ctx.stroke();
            }
        }
    }

    // Menus at bottom
    for (let i = 0; i < count; i++) {
        const x = padding + i * colWidth;
        ctx.fillStyle = '#ff4d4d';
        ctx.fillText(menus[i], x, canvas.height - padding + 25);
    }
}

document.getElementById('run-btn').addEventListener('click', async () => {
    const results = [];
    const runBtn = document.getElementById('run-btn');
    runBtn.disabled = true;
    runBtn.textContent = '진행 중...';

    for (let i = 0; i < count; i++) {
        const endIdx = await animatePath(i);
        results.push({ start: i + 1, menu: menus[endIdx] });
    }
    
    showResults(results);
});

async function animatePath(startIdx) {
    let currentX = startIdx;
    let currentY = 0;
    
    ctx.strokeStyle = `hsl(${startIdx * 40}, 70%, 60%)`;
    ctx.lineWidth = 6;
    
    const xPos = (idx) => padding + idx * colWidth;
    const yPos = (row) => padding + row * rowHeight;

    // Draw full path for this person
    for (let i = 0; i <= ladderData.length; i++) {
        // Vertical move
        const startY = yPos(i);
        const endY = yPos(i + 1);
        
        // Check for horizontal bars at current level
        if (i < ladderData.length) {
            // Check left
            if (currentX > 0 && ladderData[i][currentX - 1]) {
                // Move left
                ctx.beginPath();
                ctx.moveTo(xPos(currentX), startY + rowHeight);
                ctx.lineTo(xPos(currentX - 1), startY + rowHeight);
                ctx.stroke();
                currentX--;
            } 
            // Check right
            else if (currentX < count - 1 && ladderData[i][currentX]) {
                // Move right
                ctx.beginPath();
                ctx.moveTo(xPos(currentX), startY + rowHeight);
                ctx.lineTo(xPos(currentX + 1), startY + rowHeight);
                ctx.stroke();
                currentX++;
            }
        }
        
        // We actually need a better drawing logic for step by step
        // But for simplicity, let's just trace the path
    }

    // Real logic to find the end:
    let x = startIdx;
    for(let r=0; r<ladderData.length; r++) {
        if(x > 0 && ladderData[r][x-1]) x--;
        else if(x < count-1 && ladderData[r][x]) x++;
    }
    
    return x;
}

function showResults(results) {
    gameSection.classList.add('hidden');
    resultSection.classList.remove('hidden');
    
    const list = document.getElementById('result-list');
    list.innerHTML = results.map(res => `
        <div class="result-item">
            <span class="name">${res.start}번 참가자</span>
            <span class="menu">${res.menu}</span>
        </div>
    `).join('');
}

document.getElementById('reset-btn').addEventListener('click', () => {
    gameSection.classList.add('hidden');
    setupSection.classList.remove('hidden');
});

// Initial render
renderInputs();
