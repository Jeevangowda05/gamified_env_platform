/**
 * Dashboard JavaScript for Gamified Environmental Education Platform
 * Handles dashboard-specific functionality, charts, and interactions
 */

class DashboardManager {
    constructor() {
        this.charts = {};
        this.animationDelay = 100;
        this.refreshInterval = 60000; // 1 minute
    }

    init(config) {
        this.config = config || {};
        this.initializeAnimations();
        this.bindEvents();
    }

    initializeAnimations() {
        // Animate statistics cards
        this.animateStatCards();

        // Initialize intersection observer for scroll animations
        this.initializeScrollAnimations();
    }

    animateStatCards() {
        const statCards = document.querySelectorAll('.stat-card');
        statCards.forEach((card, index) => {
            setTimeout(() => {
                card.classList.add('fade-in-up');
            }, index * this.animationDelay);
        });

        // Animate numbers
        this.animateNumbers();
    }

    animateNumbers() {
        const numbers = document.querySelectorAll('.stat-number');
        numbers.forEach(numberElement => {
            const target = parseInt(numberElement.textContent.replace(/,/g, '')) || 0;
            this.animateCounter(numberElement, 0, target, 2000);
        });
    }

    animateCounter(element, start, end, duration) {
        const startTime = performance.now();

        const updateCounter = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Use easing function for smooth animation
            const easeOutCubic = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(start + (end - start) * easeOutCubic);

            element.textContent = Utils.formatNumber(current);

            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            }
        };

        requestAnimationFrame(updateCounter);
    }

    initializeScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in-up');
                }
            });
        }, observerOptions);

        // Observe elements that should animate on scroll
        const elementsToObserve = document.querySelectorAll(
            '.dashboard-card, .course-progress-card, .quick-action-card'
        );

        elementsToObserve.forEach(el => observer.observe(el));
    }

    bindEvents() {
        // Quick action buttons
        this.bindQuickActionEvents();

        // Course progress cards
        this.bindCourseProgressEvents();
    }

    bindQuickActionEvents() {
        const quickActionCards = document.querySelectorAll('.quick-action-card');
        quickActionCards.forEach(card => {
            card.addEventListener('mouseenter', (e) => {
                e.currentTarget.style.transform = 'translateY(-5px)';
                e.currentTarget.style.boxShadow = '0 10px 25px rgba(0,0,0,0.15)';
            });

            card.addEventListener('mouseleave', (e) => {
                e.currentTarget.style.transform = '';
                e.currentTarget.style.boxShadow = '';
            });

            card.addEventListener('click', (e) => {
                // Add click animation
                e.currentTarget.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    e.currentTarget.style.transform = '';
                }, 150);
            });
        });
    }

    bindCourseProgressEvents() {
        const courseCards = document.querySelectorAll('.course-progress-card');
        courseCards.forEach(card => {
            card.addEventListener('mouseenter', (e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 8px 25px rgba(0,0,0,0.1)';
            });

            card.addEventListener('mouseleave', (e) => {
                e.currentTarget.style.transform = '';
                e.currentTarget.style.boxShadow = '';
            });
        });
    }

    // Utility methods for dashboard interactions
    refreshDashboard() {
        Utils.showLoading();

        setTimeout(() => {
            window.location.reload();
        }, 500);
    }
}

// Progress tracking utilities
class ProgressTracker {
    static updateCourseProgress(courseId, progressPercentage) {
        const progressBars = document.querySelectorAll(`[data-course-id="${courseId}"] .progress-bar`);
        progressBars.forEach(bar => {
            bar.style.width = `${progressPercentage}%`;
            bar.setAttribute('aria-valuenow', progressPercentage);
        });

        // Update progress text
        const progressTexts = document.querySelectorAll(`[data-course-id="${courseId}"] .progress-text`);
        progressTexts.forEach(text => {
            text.textContent = `${progressPercentage.toFixed(1)}% complete`;
        });
    }

    static updatePoints(newPoints) {
        const pointsElements = document.querySelectorAll('.user-points, .total-points');
        pointsElements.forEach(element => {
            const currentPoints = parseInt(element.textContent.replace(/,/g, '')) || 0;
            if (currentPoints !== newPoints) {
                element.style.color = '#28a745';
                element.style.transform = 'scale(1.1)';

                setTimeout(() => {
                    element.style.color = '';
                    element.style.transform = '';
                }, 300);

                // Animate number change
                this.animateCounter(element, currentPoints, newPoints, 1000);
            }
        });
    }

    static animateCounter(element, start, end, duration) {
        const startTime = performance.now();

        const updateCounter = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeOutCubic = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(start + (end - start) * easeOutCubic);

            element.textContent = Utils.formatNumber(current);

            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            }
        };

        requestAnimationFrame(updateCounter);
    }
}

// Initialize dashboard when page loads
let dashboardManager;

function initializeDashboard(config) {
    dashboardManager = new DashboardManager();
    dashboardManager.init(config);

    // Handle window resize
    window.addEventListener('resize', Utils.debounce(() => {
        if (dashboardManager.handleResize) {
            dashboardManager.handleResize();
        }
    }, 250));
}

// Make functions available globally
window.initializeDashboard = initializeDashboard;
window.ProgressTracker = ProgressTracker;
