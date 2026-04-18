document.addEventListener('DOMContentLoaded', () => {
    const MAX_TIME_JUMP_SECONDS = 1.5;
    const video = document.getElementById('lessonVideo');
    const config = document.getElementById('lessonVideoConfig');
    const nextLessonButton = document.getElementById('nextLessonButton');
    const lockMessage = document.getElementById('videoLockMessage');

    if (!video || !config) {
        return;
    }

    const completeUrl = config.dataset.completeUrl;
    const nextUrl = config.dataset.nextUrl;
    let videoFullyWatched = config.dataset.initiallyCompleted === 'true';
    let lastValidTime = 0;

    video.playbackRate = 1;

    const blockSeek = () => {
        if (!videoFullyWatched) {
            video.currentTime = lastValidTime;
        }
    };

    video.addEventListener('timeupdate', () => {
        if (video.currentTime >= lastValidTime && (video.currentTime - lastValidTime) <= MAX_TIME_JUMP_SECONDS) {
            lastValidTime = video.currentTime;
        }
    });

    video.addEventListener('seeking', blockSeek);

    video.addEventListener('ratechange', () => {
        if (!videoFullyWatched && video.playbackRate !== 1) {
            video.playbackRate = 1;
        }
    });

    video.addEventListener('ended', () => {
        if (videoFullyWatched) {
            return;
        }
        markLessonComplete(Math.floor(video.duration || video.currentTime || 0));
    });

    function markLessonComplete(watchedDuration) {
        const csrfToken = getCookie('csrftoken');
        const body = new URLSearchParams();
        body.append('video_completed', 'true');
        body.append('watched_duration', String(watchedDuration || 0));

        fetch(completeUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            },
            body: body.toString(),
        })
            .then((response) => response.json())
            .then((data) => {
                if (!data.success) {
                    return;
                }
                videoFullyWatched = true;
                unlockNextLesson();
            })
            .catch(() => {
                // local fallback for immediate UX while preserving backend as source of truth
                videoFullyWatched = true;
                unlockNextLesson();
            });
    }

    function unlockNextLesson() {
        if (lockMessage) {
            lockMessage.classList.add('d-none');
        }
        if (!nextLessonButton) {
            return;
        }
        nextLessonButton.classList.remove('next-lesson-hidden');
        nextLessonButton.classList.add('next-lesson-visible');
        if (nextUrl) {
            nextLessonButton.href = nextUrl;
        }
    }

    if (videoFullyWatched) {
        unlockNextLesson();
    }
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i += 1) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === `${name}=`) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
