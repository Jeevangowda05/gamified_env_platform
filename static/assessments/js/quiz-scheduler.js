document.addEventListener('DOMContentLoaded', () => {
    const countdownEl = document.getElementById('quizCountdown');
    if (!countdownEl) {
        return;
    }

    const startTime = countdownEl.dataset.startTime;
    const endTime = countdownEl.dataset.endTime;
    const statusUrl = countdownEl.dataset.statusUrl;

    const updateCountdown = () => {
        const now = new Date().getTime();
        const start = startTime ? new Date(startTime).getTime() : null;
        const end = endTime ? new Date(endTime).getTime() : null;

        if (start && now < start) {
            countdownEl.innerText = `Available in ${formatTime(start - now)}`;
            return;
        }
        if (end && now > end) {
            countdownEl.innerText = 'Quiz closed';
            return;
        }
        if (end && now <= end) {
            countdownEl.innerText = `Quiz closes in ${formatTime(end - now)}`;
            return;
        }
        countdownEl.innerText = '';
    };

    const pollStatus = () => {
        if (!statusUrl) {
            return;
        }
        fetch(statusUrl)
            .then((response) => response.json())
            .then((data) => {
                if (data.is_live || data.status === 'closed') {
                    window.location.reload();
                }
            })
            .catch(() => {});
    };

    updateCountdown();
    setInterval(updateCountdown, 1000);
    setInterval(pollStatus, 30000);
});

function formatTime(timeLeftMs) {
    const days = Math.floor(timeLeftMs / (1000 * 60 * 60 * 24));
    const hours = Math.floor((timeLeftMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((timeLeftMs % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((timeLeftMs % (1000 * 60)) / 1000);

    if (days > 0) {
        return `${days}d ${hours}h ${minutes}m ${seconds}s`;
    }
    return `${hours}h ${minutes}m ${seconds}s`;
}
