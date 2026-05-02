let score = 0;
let timeLeft = 30;
let timerId = null;
let currentMode = 'random';
let currentAnswer = 0;

const startScreen = document.getElementById('start-screen');
const gameScreen = document.getElementById('game-screen');
const resultScreen = document.getElementById('result-screen');
const scoreDisplay = document.getElementById('score');
const timerDisplay = document.getElementById('timer');
const num1Display = document.getElementById('num1');
const num2Display = document.getElementById('num2');
const answerInput = document.getElementById('answer-input');
const submitBtn = document.getElementById('submit-btn');
const feedbackMsg = document.getElementById('feedback');
const finalScoreDisplay = document.getElementById('final-score');

function startGame(mode) {
    currentMode = mode;
    score = 0;
    timeLeft = 30;
    scoreDisplay.textContent = score;
    timerDisplay.textContent = timeLeft;
    
    startScreen.classList.remove('active');
    resultScreen.classList.remove('active');
    gameScreen.classList.add('active');
    
    answerInput.focus();
    generateQuestion();
    startTimer();
}

function generateQuestion() {
    let n1, n2;
    if (currentMode === 'random') {
        n1 = Math.floor(Math.random() * 8) + 2; // 2-9
    } else {
        n1 = currentMode;
    }
    n2 = Math.floor(Math.random() * 9) + 1; // 1-9
    
    currentAnswer = n1 * n2;
    num1Display.textContent = n1;
    num2Display.textContent = n2;
    answerInput.value = '';
    feedbackMsg.textContent = '';
    feedbackMsg.className = 'feedback-msg';
}

function checkAnswer() {
    const userAnswer = parseInt(answerInput.value);
    if (userAnswer === currentAnswer) {
        score += 10;
        scoreDisplay.textContent = score;
        showFeedback('정답입니다! 🚀', 'correct');
        setTimeout(generateQuestion, 500);
    } else if (!isNaN(userAnswer)) {
        showFeedback('아쉬워요! 다시 해보세요. 🛸', 'incorrect');
        answerInput.value = '';
        answerInput.focus();
    }
}

function showFeedback(text, className) {
    feedbackMsg.textContent = text;
    feedbackMsg.className = `feedback-msg ${className}`;
}

function startTimer() {
    if (timerId) clearInterval(timerId);
    timerId = setInterval(() => {
        timeLeft--;
        timerDisplay.textContent = timeLeft;
        if (timeLeft <= 0) {
            endGame();
        }
    }, 1000);
}

function endGame() {
    clearInterval(timerId);
    gameScreen.classList.remove('active');
    resultScreen.classList.add('active');
    finalScoreDisplay.textContent = score;
    
    let message = "잘했어요! 우주 탐험가님.";
    if (score >= 100) message = "와우! 당신은 구구단 마스터입니다! 👑";
    else if (score >= 50) message = "훌륭해요! 다음엔 100점에 도전해보세요! ⭐";
    
    document.getElementById('result-msg').textContent = message;
}

function resetGame() {
    resultScreen.classList.remove('active');
    startScreen.classList.add('active');
}

// Event Listeners
submitBtn.addEventListener('click', checkAnswer);
answerInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') checkAnswer();
});

// Focus input on any click within the game screen for better UX
gameScreen.addEventListener('click', () => answerInput.focus());
