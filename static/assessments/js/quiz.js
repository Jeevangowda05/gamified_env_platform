let currentQuestionIndex = 0;
let totalQuestions = 0;
let selectedAnswers = {};
let correctAnswersCount = 0;
let totalPointsEarned = 0;
let timeRemaining = 0;
let timerInterval;

document.addEventListener('DOMContentLoaded', function() {
    totalQuestions = document.querySelectorAll('.question-card').length;
    const timeLimit = parseInt(document.getElementById('time-remaining').textContent);
    timeRemaining = timeLimit * 60;
    
    initializeQuiz();
    startTimer();
    attachOptionListeners();
    updateQuestionNavigation();
});

function initializeQuiz() {
    updateProgressBar();
    updateQuestionCounter();
}

function attachOptionListeners() {
    const options = document.querySelectorAll('.option');
    options.forEach(option => {
        option.addEventListener('click', function() {
            const questionCard = this.closest('.question-card');
            const questionNumber = parseInt(questionCard.dataset.question);
            const selectedAnswer = this.dataset.answer;
            
            questionCard.querySelectorAll('.option').forEach(opt => {
                opt.classList.remove('selected');
            });
            
            this.classList.add('selected');
            selectedAnswers[questionNumber] = selectedAnswer;
            
            updateQuestionNavigation();
            updateAnsweredCount();
            
            if (currentQuestionIndex < totalQuestions - 1) {
                document.getElementById('nextBtn').disabled = false;
            }
        });
    });
}

function nextQuestion() {
    if (currentQuestionIndex < totalQuestions - 1) {
        currentQuestionIndex++;
        showQuestion(currentQuestionIndex);
        updateButtons();
        updateProgressBar();
        updateQuestionCounter();
        updateQuestionNavigation();
    }
}

function previousQuestion() {
    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        showQuestion(currentQuestionIndex);
        updateButtons();
        updateProgressBar();
        updateQuestionCounter();
        updateQuestionNavigation();
    }
}

function jumpToQuestion(questionNumber) {
    currentQuestionIndex = questionNumber - 1;
    showQuestion(currentQuestionIndex);
    updateButtons();
    updateProgressBar();
    updateQuestionCounter();
    updateQuestionNavigation();
}

function showQuestion(index) {
    const questions = document.querySelectorAll('.question-card');
    questions.forEach((q, i) => {
        if (i === index) {
            q.classList.add('active');
        } else {
            q.classList.remove('active');
        }
    });
}

function updateButtons() {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    
    prevBtn.disabled = currentQuestionIndex === 0;
    
    if (currentQuestionIndex === totalQuestions - 1) {
        nextBtn.style.display = 'none';
        submitBtn.style.display = 'flex';
    } else {
        nextBtn.style.display = 'flex';
        submitBtn.style.display = 'none';
    }
}

function updateProgressBar() {
    const progress = ((currentQuestionIndex + 1) / totalQuestions) * 100;
    document.getElementById('progressBar').style.width = progress + '%';
}

function updateQuestionCounter() {
    document.getElementById('currentQuestion').textContent = currentQuestionIndex + 1;
    document.getElementById('totalQuestions').textContent = totalQuestions;
}

function updateQuestionNavigation() {
    const navButtons = document.querySelectorAll('.question-nav-btn');
    navButtons.forEach((btn, index) => {
        btn.classList.remove('active');
        btn.classList.remove('answered');
        
        if (index === currentQuestionIndex) {
            btn.classList.add('active');
        }
        
        if (selectedAnswers[index + 1]) {
            btn.classList.add('answered');
        }
    });
}

function updateAnsweredCount() {
    const answeredCount = Object.keys(selectedAnswers).length;
    document.getElementById('answeredCount').textContent = answeredCount;
}

function startTimer() {
    timerInterval = setInterval(() => {
        timeRemaining--;
        
        const minutes = Math.floor(timeRemaining / 60);
        const seconds = timeRemaining % 60;
        
        document.getElementById('time-remaining').textContent = 
            `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        if (timeRemaining <= 0) {
            clearInterval(timerInterval);
            submitQuiz();
        }
    }, 1000);
}

function submitQuiz() {
    const unanswered = [];
    for (let i = 1; i <= totalQuestions; ++i) {
        if (!selectedAnswers[i]) {
            unanswered.push(i);
        }
    }

    if (unanswered.length > 0) {
        showUnansweredWarning(unanswered);
        return;
    }

    clearInterval(timerInterval);
    
    // Build answers payload
    const questions = document.querySelectorAll('.question-card');
    let answersPayload = {};
    
    questions.forEach((card, index) => {
        let questionId = card.dataset.questionId || card.dataset.question;
        let answerLabel = selectedAnswers[index + 1];
        if (answerLabel) {
            answersPayload[questionId] = answerLabel;
        }
    });

    // ✅ FIXED: Correct URL pattern replacement
    const submitUrl = window.location.pathname.replace('/take/', '/submit/');
    
    fetch(submitUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie('csrftoken')
        },
        body: JSON.stringify({
            answers: answersPayload
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('finalScore').textContent = data.score_percentage.toFixed(1) + '%';
            document.getElementById('correctAnswers').textContent = data.correct_answers + '/' + data.total_questions;
            document.getElementById('totalPoints').textContent = data.points_earned;
            document.getElementById('resultsModal').classList.add('active');
        } else {
            alert('Error submitting quiz: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Quiz submission error:', error);
        alert('Failed to submit quiz. Please try again.');
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function reviewAnswers() {
    document.getElementById('resultsModal').classList.remove('active');
    
    const questions = document.querySelectorAll('.question-card');
    questions.forEach((card, index) => {
        const questionNumber = index + 1;
        const correctAnswer = card.querySelector('.correct-answer').value;
        const userAnswer = selectedAnswers[questionNumber];
        
        const options = card.querySelectorAll('.option');
        options.forEach(option => {
            const answer = option.dataset.answer;
            
            if (answer === correctAnswer) {
                option.classList.add('correct');
            } else if (answer === userAnswer && userAnswer !== correctAnswer) {
                option.classList.add('incorrect');
            }
            
            option.style.pointerEvents = 'none';
        });
    });
    
    document.getElementById('prevBtn').disabled = false;
    document.getElementById('nextBtn').style.display = 'flex';
    document.getElementById('submitBtn').style.display = 'none';
    
    currentQuestionIndex = 0;
    showQuestion(0);
}

function showUnansweredWarning(unanswered) {
    let warning = document.getElementById('unansweredWarning');
    if (!warning) {
        warning = document.createElement('div');
        warning.id = 'unansweredWarning';
        warning.className = 'sidebar-warning';
        const sidebar = document.querySelector('.quiz-sidebar');
        sidebar.insertBefore(warning, document.querySelector('.sidebar-submit'));
    }

    warning.style.display = 'block';
    if (unanswered.length === 1) {
        warning.innerHTML = `<i class="fas fa-exclamation-triangle"></i> You have not answered question ${unanswered[0]}. Please answer all questions before submitting.`;
    } else {
        warning.innerHTML = `<i class="fas fa-exclamation-triangle"></i> You have not answered questions ${unanswered.join(', ')}. Please answer all questions before submitting.`;
    }

    const navButtons = document.querySelectorAll('.question-nav-btn');
    navButtons.forEach((btn, index) => {
        if (unanswered.indexOf(index + 1) !== -1) {
            btn.classList.add('unanswered');
        } else {
            btn.classList.remove('unanswered');
        }
    });
}
