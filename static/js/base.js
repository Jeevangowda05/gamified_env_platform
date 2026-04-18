/**
 * Base JavaScript for Gamified Environmental Education Platform
 * Handles global functionality, navigation, and common interactions
 */

// Global app configuration
const APP_CONFIG = {
    API_BASE_URL: '/api/v1/',
    NOTIFICATION_POLL_INTERVAL: 30000, // 30 seconds
    SEARCH_DEBOUNCE_DELAY: 300,
    ANIMATION_DURATION: 300
};

// Utility functions
const Utils = {
    // Debounce function for search
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Format numbers with commas
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    },

    // Format date relative to now
    timeAgo(date) {
        const now = new Date();
        const diffInSeconds = Math.floor((now - new Date(date)) / 1000);

        const intervals = [
            { label: 'year', seconds: 31536000 },
            { label: 'month', seconds: 2592000 },
            { label: 'week', seconds: 604800 },
            { label: 'day', seconds: 86400 },
            { label: 'hour', seconds: 3600 },
            { label: 'minute', seconds: 60 }
        ];

        for (const interval of intervals) {
            const count = Math.floor(diffInSeconds / interval.seconds);
            if (count >= 1) {
                return `${count} ${interval.label}${count > 1 ? 's' : ''} ago`;
            }
        }

        return 'just now';
    },

    // Show loading spinner
    showLoading() {
        document.getElementById('loading-spinner').classList.add('show');
    },

    // Hide loading spinner
    hideLoading() {
        setTimeout(() => {
            document.getElementById('loading-spinner').classList.remove('show');
        }, 100);
    },

    // Show toast notification
    showToast(message, type = 'info') {
        const alertContainer = document.querySelector('.alert-container') || this.createAlertContainer();

        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            <i class="fas fa-${this.getAlertIcon(type)} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        alertContainer.appendChild(alert);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.classList.remove('show');
                setTimeout(() => alert.remove(), 150);
            }
        }, 5000);
    },

    createAlertContainer() {
        const container = document.createElement('div');
        container.className = 'alert-container';
        document.body.appendChild(container);
        return container;
    },

    getAlertIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-triangle',
            warning: 'exclamation-circle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
};

// API helper class
class APIClient {
    constructor() {
        this.baseURL = APP_CONFIG.API_BASE_URL;
    }

    async request(url, options = {}) {
        const config = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.csrfToken
            },
            ...options
        };

        try {
            const response = await fetch(this.baseURL + url, config);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    get(url) {
        return this.request(url);
    }

    post(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
}

// Global API client instance
const apiClient = new APIClient();

// Notification system
class NotificationManager {
    constructor() {
        this.pollInterval = null;
        this.notificationCount = 0;
        this.activeFilter = 'unread';
    }

    init() {
        this.startPolling();
        this.bindEvents();
    }

    startPolling() {
        // Initial load
        this.loadNotifications();

        // Set up polling interval
        this.pollInterval = setInterval(() => {
            this.loadNotifications();
        }, APP_CONFIG.NOTIFICATION_POLL_INTERVAL);
    }

    async loadNotifications() {
        try {
            const response = await fetch(`/api/notifications/?filter=${this.activeFilter}`);
            const data = await response.json();
            this.updateNotificationUI(data);
        } catch (error) {
            console.error('Failed to load notifications:', error);
        }
    }

    updateNotificationUI(data) {
        const countElement = document.getElementById('notificationCount');
        const listElement = document.getElementById('notificationsList');

        if (countElement) {
            this.notificationCount = data.unread_count;
            countElement.textContent = this.notificationCount;
            countElement.style.display = this.notificationCount > 0 ? 'flex' : 'none';
        }

        if (listElement) {
            listElement.innerHTML = this.renderNotifications(data.notifications);
        }
    }

    renderNotifications(notifications) {
        if (notifications.length === 0) {
            return `
                <div class="p-3 text-center text-muted">
                    <i class="fas fa-bell-slash fa-2x mb-2"></i>
                    <p class="mb-0">No notifications</p>
                </div>
            `;
        }

        return notifications.map(notification => `
            <div class="dropdown-item">
                <div class="d-flex">
                    <div class="me-3">
                        <i class="fas fa-${this.getNotificationIcon(notification.type)} text-${this.getNotificationColor(notification.type)}"></i>
                    </div>
                    <div class="flex-grow-1">
                        <h6 class="mb-1">${notification.title}</h6>
                        <p class="mb-1 small">${notification.message}</p>
                        <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
                            <small class="text-muted">${Utils.timeAgo(notification.timestamp)}</small>
                            <div class="d-flex gap-2">
                                ${!notification.is_read ? `<button class="btn btn-link btn-sm p-0 text-decoration-none notification-action" data-action="mark_read" data-id="${notification.id}">Mark as read</button>` : ''}
                                ${!notification.is_archived ? `<button class="btn btn-link btn-sm p-0 text-decoration-none text-muted notification-action" data-action="archive" data-id="${notification.id}">Archive</button>` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    }

    getNotificationIcon(type) {
        const icons = {
            new_course: 'book',
            badge_available: 'medal',
            challenge: 'fire',
            achievement: 'star',
            reminder: 'clock',
            course_enrollment: 'user-plus',
            quiz_completed: 'clipboard-check',
            course_completed: 'graduation-cap',
            course_created: 'book-open',
            quiz_created: 'circle-question',
            lesson_added: 'book-reader',
            challenge_submitted: 'flag-checkered'
        };
        return icons[type] || 'bell';
    }

    getNotificationColor(type) {
        const colors = {
            new_course: 'primary',
            badge_available: 'warning',
            challenge: 'danger',
            achievement: 'success',
            reminder: 'info',
            course_enrollment: 'primary',
            quiz_completed: 'info',
            course_completed: 'success',
            course_created: 'success',
            quiz_created: 'primary',
            lesson_added: 'info',
            challenge_submitted: 'warning'
        };
        return colors[type] || 'info';
    }

    bindEvents() {
        const filterButtons = document.querySelectorAll('[data-notification-filter]');
        filterButtons.forEach((button) => {
            button.addEventListener('click', () => {
                filterButtons.forEach((node) => node.classList.remove('active'));
                button.classList.add('active');
                this.activeFilter = button.dataset.notificationFilter;
                this.loadNotifications();
            });
        });

        const markAllButton = document.getElementById('markAllNotificationsRead');
        if (markAllButton) {
            markAllButton.addEventListener('click', async (event) => {
                event.preventDefault();
                await this.sendNotificationAction('mark_all_read');
                this.loadNotifications();
            });
        }

        const listElement = document.getElementById('notificationsList');
        if (listElement) {
            listElement.addEventListener('click', async (event) => {
                const target = event.target.closest('.notification-action');
                if (!target) {
                    return;
                }
                event.preventDefault();
                await this.sendNotificationAction(target.dataset.action, target.dataset.id);
                this.loadNotifications();
            });
        }
    }

    async sendNotificationAction(action, notificationId = null) {
        const payload = { action };
        if (notificationId) {
            payload.notification_id = Number(notificationId);
        }
        try {
            const response = await fetch('/api/notifications/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.csrfToken
                },
                body: JSON.stringify(payload)
            });
            if (!response.ok) {
                throw new Error(`Notification action failed with status ${response.status}`);
            }
            const data = await response.json();
            if (typeof data.unread_count === 'number') {
                const countElement = document.getElementById('notificationCount');
                this.notificationCount = data.unread_count;
                if (countElement) {
                    countElement.textContent = this.notificationCount;
                    countElement.style.display = this.notificationCount > 0 ? 'flex' : 'none';
                }
            }
        } catch (error) {
            console.error('Notification action failed:', error);
        }
    }
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
    });

    // Initialize notification manager for authenticated users
    if (document.body.dataset.authenticated === 'true') {
        const notificationManager = new NotificationManager();
        notificationManager.init();
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // Add fade-in animation to page content
    document.body.classList.add('fade-in');
});

// Export utilities for use in other scripts
window.Utils = Utils;
window.apiClient = apiClient;
