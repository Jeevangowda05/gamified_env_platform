(function () {
    function escapeHtml(value) {
        return String(value || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function debounce(fn, delay) {
        let timer = null;
        return function (...args) {
            clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), delay);
        };
    }

    function renderBarChart(canvasId) {
        const canvas = document.getElementById(canvasId);
        if (!canvas || typeof Chart === 'undefined') {
            return;
        }
        const payload = JSON.parse(canvas.dataset.chart || '{"labels":[],"students":[]}');
        if (!payload.labels || !payload.labels.length) {
            return;
        }
        new Chart(canvas, {
            type: 'bar',
            data: {
                labels: payload.labels,
                datasets: [{
                    label: 'Students',
                    data: payload.students,
                    backgroundColor: '#4f46e5',
                    borderRadius: 6,
                }],
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
            },
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        renderBarChart('teacherCourseChart');
        renderBarChart('teacherAnalyticsChart');

        const input = document.getElementById('teacherSearchInput');
        const topic = document.getElementById('teacherSearchTopic');
        const difficulty = document.getElementById('teacherSearchDifficulty');
        const status = document.getElementById('teacherSearchStatus');
        const resultBox = document.getElementById('teacherSearchResults');

        if (!input || !resultBox) {
            return;
        }

        const runSearch = debounce(async function () {
            const q = input.value.trim();
            const params = new URLSearchParams({
                q,
                topic: topic ? topic.value : '',
                difficulty: difficulty ? difficulty.value : '',
                status: status ? status.value : '',
            });
            if (!q && !params.get('topic') && !params.get('difficulty') && !params.get('status')) {
                resultBox.classList.add('d-none');
                resultBox.innerHTML = '';
                return;
            }
            try {
                const response = await fetch(`/teacher/search/?${params.toString()}`);
                const data = await response.json();
                resultBox.classList.remove('d-none');
                resultBox.innerHTML = `
                    <div class="small text-muted mb-2">
                        ${data.counts.courses} courses • ${data.counts.quizzes} quizzes • ${data.counts.students} students
                    </div>
                    <div class="row g-3">
                        <div class="col-md-4"><strong>Courses</strong>${(data.courses || []).map(c => `<div class="small">${escapeHtml(c.title)}</div>`).join('') || '<div class="small text-muted">No results</div>'}</div>
                        <div class="col-md-4"><strong>Quizzes</strong>${(data.quizzes || []).map(qz => `<div class="small">${escapeHtml(qz.title)}</div>`).join('') || '<div class="small text-muted">No results</div>'}</div>
                        <div class="col-md-4"><strong>Students</strong>${(data.students || []).map(st => `<div class="small">${escapeHtml(st.name)} • ${escapeHtml(st.course)}</div>`).join('') || '<div class="small text-muted">No results</div>'}</div>
                    </div>
                `;
            } catch (error) {
                resultBox.classList.remove('d-none');
                resultBox.innerHTML = '<div class="small text-danger">Search unavailable right now.</div>';
            }
        }, 250);

        input.addEventListener('input', runSearch);
        if (topic) topic.addEventListener('change', runSearch);
        if (difficulty) difficulty.addEventListener('change', runSearch);
        if (status) status.addEventListener('change', runSearch);
    });
})();
