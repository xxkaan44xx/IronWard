/**
 * Discord Bot Dashboard JavaScript
 * Advanced dashboard functionality and interactions
 */

// Global variables
let refreshInterval = null;
let notificationPermission = false;

// Initialize dashboard when DOM is loaded
$(document).ready(function() {
    initializeDashboard();
});

/**
 * Initialize dashboard components
 */
function initializeDashboard() {
    // Check for notification permissions
    checkNotificationPermission();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize auto-refresh
    initializeAutoRefresh();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize theme handling
    initializeTheme();
    
    // Initialize keyboard shortcuts
    initializeKeyboardShortcuts();
    
    // Initialize real-time updates
    initializeRealTimeUpdates();
    
    // Initialize performance monitoring
    initializePerformanceMonitoring();
    
    console.log('Dashboard initialized successfully');
}

/**
 * Check and request notification permissions
 */
function checkNotificationPermission() {
    if ('Notification' in window) {
        if (Notification.permission === 'default') {
            Notification.requestPermission().then(permission => {
                notificationPermission = permission === 'granted';
            });
        } else {
            notificationPermission = Notification.permission === 'granted';
        }
    }
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize auto-refresh functionality
 */
function initializeAutoRefresh() {
    const refreshRate = localStorage.getItem('autoRefreshRate') || 30000; // 30 seconds default
    
    if (refreshRate > 0) {
        refreshInterval = setInterval(() => {
            refreshDashboardData();
        }, refreshRate);
    }
}

/**
 * Initialize search functionality
 */
function initializeSearch() {
    const searchInputs = document.querySelectorAll('[data-search]');
    
    searchInputs.forEach(input => {
        input.addEventListener('input', debounce(function() {
            performSearch(this.value, this.dataset.search);
        }, 300));
    });
}

/**
 * Initialize theme handling
 */
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(savedTheme);
    
    // Theme toggle listeners
    document.querySelectorAll('[data-theme]').forEach(btn => {
        btn.addEventListener('click', function() {
            const theme = this.dataset.theme;
            applyTheme(theme);
            localStorage.setItem('theme', theme);
        });
    });
}

/**
 * Apply theme to dashboard
 */
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    
    // Update theme-specific elements
    const themeElements = document.querySelectorAll('[data-theme-target]');
    themeElements.forEach(element => {
        const themeClasses = element.dataset.themeTarget.split(',');
        element.className = element.className.replace(/bg-\w+|text-\w+/g, '');
        
        if (theme === 'dark') {
            element.classList.add(...themeClasses[0].split(' '));
        } else {
            element.classList.add(...(themeClasses[1] || themeClasses[0]).split(' '));
        }
    });
}

/**
 * Initialize keyboard shortcuts
 */
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('#globalSearch');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Ctrl/Cmd + R for refresh
        if ((e.ctrlKey || e.metaKey) && e.key === 'r' && !e.shiftKey) {
            e.preventDefault();
            refreshDashboardData();
        }
        
        // Esc to close modals
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(modal => {
                bootstrap.Modal.getInstance(modal)?.hide();
            });
        }
    });
}

/**
 * Initialize real-time updates
 */
function initializeRealTimeUpdates() {
    // Simulated WebSocket connection for real-time updates
    // In a real implementation, this would connect to a WebSocket server
    
    setInterval(() => {
        // Simulate receiving real-time data
        updateRealTimeStats();
    }, 5000);
}

/**
 * Initialize performance monitoring
 */
function initializePerformanceMonitoring() {
    // Monitor page load performance
    window.addEventListener('load', function() {
        const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
        console.log(`Dashboard loaded in ${loadTime}ms`);
        
        // Send performance data to analytics (if implemented)
        if (window.gtag) {
            gtag('event', 'page_load_time', {
                value: loadTime,
                event_category: 'Performance'
            });
        }
    });
    
    // Monitor API response times
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        const start = performance.now();
        return originalFetch.apply(this, args).then(response => {
            const end = performance.now();
            console.log(`API call to ${args[0]} took ${end - start}ms`);
            return response;
        });
    };
}

/**
 * Refresh dashboard data
 */
function refreshDashboardData() {
    showLoadingIndicator();
    
    // Refresh stats
    refreshStats();
    
    // Refresh recent activity
    refreshRecentActivity();
    
    // Refresh charts if on analytics page
    if (window.location.pathname.includes('analytics')) {
        refreshAnalyticsCharts();
    }
    
    hideLoadingIndicator();
    showNotification('Dashboard data refreshed', 'success');
}

/**
 * Refresh dashboard statistics
 */
function refreshStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            updateStatsDisplay(data);
        })
        .catch(error => {
            console.error('Error refreshing stats:', error);
            showNotification('Failed to refresh stats', 'error');
        });
}

/**
 * Refresh recent activity
 */
function refreshRecentActivity() {
    fetch('/api/recent-activity?limit=10')
        .then(response => response.json())
        .then(data => {
            updateRecentActivityDisplay(data);
        })
        .catch(error => {
            console.error('Error refreshing activity:', error);
        });
}

/**
 * Update statistics display
 */
function updateStatsDisplay(data) {
    const statElements = {
        'total-guilds': data.total_guilds,
        'total-warnings': data.total_warnings,
        'active-bans': data.active_bans,
        'active-mutes': data.active_mutes
    };
    
    Object.entries(statElements).forEach(([elementId, value]) => {
        const element = document.getElementById(elementId);
        if (element) {
            animateNumber(element, parseInt(element.textContent) || 0, value);
        }
    });
}

/**
 * Update recent activity display
 */
function updateRecentActivityDisplay(data) {
    const container = document.getElementById('recent-activity-list');
    if (!container) return;
    
    // Ensure data is an array
    if (!Array.isArray(data)) {
        console.error('Expected array but got:', typeof data);
        container.innerHTML = '<div class="text-center text-danger py-4">Veri formatı hatası.</div>';
        return;
    }
    
    let html = '';
    
    if (data.length === 0) {
        html = '<div class="text-center text-muted py-4">Henüz aktivite bulunmuyor.</div>';
    } else {
        data.forEach(activity => {
            const date = new Date(activity.timestamp).toLocaleString('tr-TR');
            const badgeClass = getBadgeClassForAction(activity.action);
            
            html += `
                <div class="border-bottom border-dark pb-2 mb-2 fade-in">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <span class="badge ${badgeClass}">${activity.action}</span>
                            <small class="text-muted d-block">
                                User: ${activity.target_id} | Moderator: ${activity.moderator_id}
                            </small>
                        </div>
                        <small class="text-muted">${date}</small>
                    </div>
                </div>
            `;
        });
    }
    
    container.innerHTML = html;
}

/**
 * Get badge class for action type
 */
function getBadgeClassForAction(action) {
    const badgeClasses = {
        'ban': 'bg-danger',
        'kick': 'bg-warning',
        'mute': 'bg-secondary',
        'warn': 'bg-info',
        'unban': 'bg-success',
        'unmute': 'bg-success'
    };
    
    return badgeClasses[action] || 'bg-primary';
}

/**
 * Animate number changes
 */
function animateNumber(element, start, end) {
    const duration = 1000;
    const startTime = performance.now();
    
    function updateNumber(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const current = Math.floor(start + (end - start) * easeOutQuart(progress));
        element.textContent = current.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(updateNumber);
        }
    }
    
    requestAnimationFrame(updateNumber);
}

/**
 * Easing function for animations
 */
function easeOutQuart(t) {
    return 1 - (--t) * t * t * t;
}

/**
 * Show loading indicator
 */
function showLoadingIndicator() {
    const indicator = document.getElementById('loading-indicator');
    if (indicator) {
        indicator.style.display = 'block';
    } else {
        // Create temporary loading indicator
        const loader = document.createElement('div');
        loader.id = 'temp-loading';
        loader.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center';
        loader.style.backgroundColor = 'rgba(0,0,0,0.5)';
        loader.style.zIndex = '9999';
        loader.innerHTML = '<div class="spinner-border text-primary" role="status"></div>';
        document.body.appendChild(loader);
    }
}

/**
 * Hide loading indicator
 */
function hideLoadingIndicator() {
    const indicator = document.getElementById('loading-indicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
    
    const tempLoader = document.getElementById('temp-loading');
    if (tempLoader) {
        tempLoader.remove();
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info', duration = 3000) {
    // Browser notification
    if (notificationPermission && type === 'error') {
        new Notification('Dashboard Alert', {
            body: message,
            icon: '/static/img/icon.png'
        });
    }
    
    // In-app notification
    const alertTypes = {
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    };
    
    const alert = document.createElement('div');
    alert.className = `alert ${alertTypes[type]} alert-dismissible fade show position-fixed`;
    alert.style.top = '20px';
    alert.style.right = '20px';
    alert.style.zIndex = '9999';
    alert.style.minWidth = '300px';
    
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alert);
    
    // Auto-dismiss
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, duration);
}

/**
 * Perform search
 */
function performSearch(query, target) {
    if (query.length < 2) return;
    
    const searchTargets = {
        'guilds': searchGuilds,
        'logs': searchLogs,
        'users': searchUsers
    };
    
    if (searchTargets[target]) {
        searchTargets[target](query);
    }
}

/**
 * Search guilds
 */
function searchGuilds(query) {
    const guildCards = document.querySelectorAll('.guild-card');
    guildCards.forEach(card => {
        const guildId = card.dataset.guildId;
        const isVisible = guildId.toLowerCase().includes(query.toLowerCase());
        card.style.display = isVisible ? 'block' : 'none';
    });
}

/**
 * Search logs
 */
function searchLogs(query) {
    const logRows = document.querySelectorAll('.log-row');
    logRows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const isVisible = text.includes(query.toLowerCase());
        row.style.display = isVisible ? '' : 'none';
    });
}

/**
 * Search users
 */
function searchUsers(query) {
    // Implementation for user search
    console.log('Searching users for:', query);
}

/**
 * Update real-time stats
 */
function updateRealTimeStats() {
    // Simulate real-time stat updates
    const stats = ['total-warnings', 'active-bans', 'active-mutes'];
    
    stats.forEach(statId => {
        const element = document.getElementById(statId);
        if (element && Math.random() > 0.7) { // 30% chance to update
            const currentValue = parseInt(element.textContent) || 0;
            const change = Math.floor(Math.random() * 3) - 1; // -1, 0, or 1
            const newValue = Math.max(0, currentValue + change);
            
            if (newValue !== currentValue) {
                animateNumber(element, currentValue, newValue);
                
                // Add visual indicator for changes
                const indicator = document.createElement('span');
                indicator.className = change > 0 ? 'text-success' : 'text-danger';
                indicator.textContent = change > 0 ? '+' + change : change;
                indicator.style.fontSize = '0.75rem';
                element.parentNode.appendChild(indicator);
                
                setTimeout(() => indicator.remove(), 2000);
            }
        }
    });
}

/**
 * Refresh analytics charts
 */
function refreshAnalyticsCharts() {
    if (typeof Chart !== 'undefined') {
        Chart.helpers.each(Chart.instances, function(instance) {
            instance.update();
        });
    }
}

/**
 * Debounce function for search
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Export data functionality
 */
function exportData(type, format = 'csv') {
    showLoadingIndicator();
    
    fetch(`/api/export/${type}?format=${format}`)
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${type}_export_${new Date().toISOString().split('T')[0]}.${format}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            hideLoadingIndicator();
            showNotification(`${type} data exported successfully`, 'success');
        })
        .catch(error => {
            hideLoadingIndicator();
            console.error('Export error:', error);
            showNotification('Export failed', 'error');
        });
}

/**
 * Copy to clipboard functionality
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard', 'success', 1000);
    }).catch(err => {
        console.error('Copy failed:', err);
        showNotification('Copy failed', 'error');
    });
}

/**
 * Format time ago
 */
function timeAgo(date) {
    const now = new Date();
    const diff = now - new Date(date);
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days} gün önce`;
    if (hours > 0) return `${hours} saat önce`;
    if (minutes > 0) return `${minutes} dakika önce`;
    return 'Az önce';
}

/**
 * Clean up on page unload
 */
window.addEventListener('beforeunload', function() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    // Clean up any pending animations
    const animations = document.querySelectorAll('.loading, .fade-in');
    animations.forEach(el => el.remove());
});

// Global error handling
window.addEventListener('error', function(e) {
    console.error('Dashboard error:', e.error);
    showNotification('An error occurred', 'error');
});

// Export functions for global use
window.dashboardUtils = {
    refreshDashboardData,
    showNotification,
    copyToClipboard,
    exportData,
    timeAgo
};