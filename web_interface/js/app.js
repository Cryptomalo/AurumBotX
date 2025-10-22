/**
 * AurumBotX v2.1 - Enterprise Web Interface
 * Main Application JavaScript
 */

class AurumBotXApp {
    constructor() {
        this.apiBase = 'http://localhost:5678';
        this.refreshInterval = 30000; // 30 seconds
        this.refreshTimer = null;
        this.isConnected = false;
        this.currentPage = 'overview';
        this.data = {
            balance: 50.0,
            trades: [],
            performance: {},
            status: {}
        };
        
        this.init();
    }

    async init() {
        console.log('🚀 Initializing AurumBotX Enterprise Dashboard...');
        
        // Show loading screen
        this.showLoading();
        
        // Initialize components
        await this.initializeApp();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Start data refresh cycle
        this.startRefreshCycle();
        
        // Hide loading screen and show app
        setTimeout(() => {
            this.hideLoading();
        }, 2000);
        
        console.log('✅ AurumBotX Dashboard initialized successfully');
    }

    showLoading() {
        document.getElementById('loading-screen').style.display = 'flex';
        document.getElementById('app').style.display = 'none';
    }

    hideLoading() {
        document.getElementById('loading-screen').style.display = 'none';
        document.getElementById('app').style.display = 'block';
    }

    async initializeApp() {
        // Load initial data
        await this.refreshData();
        
        // Initialize charts
        if (window.ChartsManager) {
            window.ChartsManager.init();
        }
        
        // Load settings
        this.loadSettings();
        
        // Setup PWA
        this.setupPWA();
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                this.navigateToPage(page);
            });
        });

        // Trading controls
        const startBtn = document.getElementById('start-trading');
        const stopBtn = document.getElementById('stop-trading');
        
        if (startBtn) {
            startBtn.addEventListener('click', () => this.startTrading());
        }
        
        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopTrading());
        }

        // Emergency stop
        const emergencyBtn = document.getElementById('emergency-stop');
        if (emergencyBtn) {
            emergencyBtn.addEventListener('click', () => this.showEmergencyModal());
        }

        // Emergency modal
        const emergencyModal = document.getElementById('emergency-modal');
        const confirmEmergency = document.getElementById('confirm-emergency');
        const cancelEmergency = document.getElementById('cancel-emergency');
        const modalClose = emergencyModal?.querySelector('.modal-close');

        if (confirmEmergency) {
            confirmEmergency.addEventListener('click', () => this.emergencyStop());
        }

        if (cancelEmergency) {
            cancelEmergency.addEventListener('click', () => this.hideEmergencyModal());
        }

        if (modalClose) {
            modalClose.addEventListener('click', () => this.hideEmergencyModal());
        }

        // Settings
        const saveSettingsBtn = document.getElementById('save-settings');
        if (saveSettingsBtn) {
            saveSettingsBtn.addEventListener('click', () => this.saveSettings());
        }

        // Risk slider
        const riskSlider = document.getElementById('risk-slider');
        const riskValue = document.getElementById('risk-value');
        if (riskSlider && riskValue) {
            riskSlider.addEventListener('input', (e) => {
                riskValue.textContent = e.target.value;
            });
        }

        // Refresh button
        const refreshBtn = document.querySelector('[onclick="refreshData()"]');
        if (refreshBtn) {
            refreshBtn.onclick = () => this.refreshData();
        }

        // Fullscreen toggle
        const fullscreenBtn = document.getElementById('fullscreen-btn');
        if (fullscreenBtn) {
            fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
        }

        // Auto-refresh toggle
        const autoRefreshCheckbox = document.querySelector('input[type="checkbox"][id*="auto-refresh"]');
        if (autoRefreshCheckbox) {
            autoRefreshCheckbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.startRefreshCycle();
                } else {
                    this.stopRefreshCycle();
                }
            });
        }

        // Theme toggle
        const themeSelect = document.getElementById('theme-select');
        if (themeSelect) {
            themeSelect.addEventListener('change', (e) => {
                this.setTheme(e.target.value);
            });
        }

        // Window events
        window.addEventListener('beforeunload', () => {
            this.stopRefreshCycle();
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
    }

    navigateToPage(page) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        document.querySelector(`[data-page="${page}"]`)?.classList.add('active');

        // Update pages
        document.querySelectorAll('.page').forEach(pageEl => {
            pageEl.classList.remove('active');
        });
        
        const targetPage = document.getElementById(`${page}-page`);
        if (targetPage) {
            targetPage.classList.add('active');
            this.currentPage = page;
            
            // Update URL without reload
            history.pushState({ page }, '', `#${page}`);
            
            // Refresh page-specific data
            this.refreshPageData(page);
        }
    }

    async refreshData() {
        console.log('🔄 Refreshing data...');
        
        try {
            // Update connection status
            await this.checkConnection();
            
            // Fetch all data in parallel
            const [balance, status, trades, performance] = await Promise.all([
                this.fetchBalance(),
                this.fetchStatus(),
                this.fetchTrades(),
                this.fetchPerformance()
            ]);

            // Update data
            this.data.balance = balance;
            this.data.status = status;
            this.data.trades = trades;
            this.data.performance = performance;

            // Update UI
            this.updateUI();
            
            console.log('✅ Data refreshed successfully');
            
        } catch (error) {
            console.error('❌ Error refreshing data:', error);
            this.showNotification('Failed to refresh data', 'error');
        }
    }

    async checkConnection() {
        try {
            const response = await fetch(`${this.apiBase}/api/status`, {
                timeout: 5000
            });
            
            this.isConnected = response.ok;
            this.updateConnectionStatus();
            
        } catch (error) {
            this.isConnected = false;
            this.updateConnectionStatus();
        }
    }

    updateConnectionStatus() {
        const statusDot = document.getElementById('connection-status');
        const statusText = document.getElementById('connection-text');
        
        if (statusDot && statusText) {
            if (this.isConnected) {
                statusDot.className = 'status-dot online';
                statusText.textContent = 'Connected';
            } else {
                statusDot.className = 'status-dot offline';
                statusText.textContent = 'Disconnected';
            }
        }
    }

    async fetchBalance() {
        try {
            const response = await fetch(`${this.apiBase}/api/balance`);
            if (response.ok) {
                const data = await response.json();
                return data.USDT || 50.0;
            }
        } catch (error) {
            console.warn('Using cached balance data');
        }
        return this.data.balance || 50.0;
    }

    async fetchStatus() {
        try {
            const response = await fetch(`${this.apiBase}/api/status`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.warn('Using cached status data');
        }
        return {
            status: 'offline',
            trading_active: false,
            strategy: 'Challenge Growth'
        };
    }

    async fetchTrades() {
        try {
            const response = await fetch(`${this.apiBase}/api/trades`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.warn('Using cached trades data');
        }
        return this.data.trades || [];
    }

    async fetchPerformance() {
        try {
            const response = await fetch(`${this.apiBase}/api/performance`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.warn('Using cached performance data');
        }
        return {
            total_trades: 0,
            win_rate: 0,
            total_pnl: 0,
            sharpe_ratio: 0,
            best_trade: 0,
            avg_trade: 0
        };
    }

    updateUI() {
        this.updateHeader();
        this.updateOverview();
        this.updateMetrics();
        this.updateStatus();
        this.updateActivity();
        this.updateCharts();
    }

    updateHeader() {
        // Update balance in header
        const balanceEl = document.getElementById('current-balance');
        if (balanceEl) {
            balanceEl.textContent = `$${this.data.balance.toFixed(2)}`;
        }

        // Update daily P&L
        const pnlEl = document.getElementById('daily-pnl');
        if (pnlEl) {
            const dailyPnl = this.data.performance.daily_pnl || 0;
            pnlEl.textContent = `${dailyPnl >= 0 ? '+' : ''}$${dailyPnl.toFixed(2)}`;
            pnlEl.className = dailyPnl >= 0 ? 'positive' : 'negative';
        }
    }

    updateOverview() {
        // Challenge progress
        const currentEl = document.getElementById('challenge-current');
        const progressFill = document.getElementById('challenge-progress-fill');
        const progressPercent = document.getElementById('challenge-percentage');
        
        if (currentEl) {
            currentEl.textContent = `$${this.data.balance.toFixed(2)}`;
        }
        
        const progress = Math.min((this.data.balance / 100) * 100, 100);
        
        if (progressFill) {
            progressFill.style.width = `${progress}%`;
        }
        
        if (progressPercent) {
            progressPercent.textContent = `${progress.toFixed(1)}%`;
        }
    }

    updateMetrics() {
        const metrics = [
            { id: 'balance-metric', value: `$${this.data.balance.toFixed(2)}` },
            { id: 'trades-metric', value: this.data.performance.total_trades || 0 },
            { id: 'winrate-metric', value: `${(this.data.performance.win_rate || 0).toFixed(1)}%` },
            { id: 'sharpe-metric', value: (this.data.performance.sharpe_ratio || 0).toFixed(2) }
        ];

        metrics.forEach(metric => {
            const el = document.getElementById(metric.id);
            if (el) {
                el.textContent = metric.value;
            }
        });

        // Update metric changes
        const balanceChange = this.data.balance - 50.0;
        const balanceChangeEl = document.getElementById('balance-change');
        if (balanceChangeEl) {
            balanceChangeEl.textContent = `${balanceChange >= 0 ? '+' : ''}$${balanceChange.toFixed(2)}`;
            balanceChangeEl.className = `metric-change ${balanceChange >= 0 ? 'positive' : 'negative'}`;
        }

        const tradesChangeEl = document.getElementById('trades-change');
        if (tradesChangeEl) {
            const todayTrades = this.getTodayTrades();
            tradesChangeEl.textContent = `Today: ${todayTrades}`;
        }
    }

    updateStatus() {
        // API Status
        const apiIcon = document.getElementById('api-status-icon');
        const apiText = document.getElementById('api-status-text');
        
        if (apiIcon && apiText) {
            if (this.isConnected) {
                apiIcon.className = 'fas fa-circle status-online';
                apiText.textContent = 'ONLINE';
            } else {
                apiIcon.className = 'fas fa-circle status-offline';
                apiText.textContent = 'OFFLINE';
            }
        }

        // Trading Status
        const tradingIcon = document.getElementById('trading-status-icon');
        const tradingText = document.getElementById('trading-status-text');
        
        if (tradingIcon && tradingText) {
            const isActive = this.data.status.trading_active || false;
            if (isActive) {
                tradingIcon.className = 'fas fa-circle status-online';
                tradingText.textContent = 'ACTIVE';
            } else {
                tradingIcon.className = 'fas fa-circle status-offline';
                tradingText.textContent = 'STOPPED';
            }
        }

        // Performance summary
        const performanceItems = [
            { id: 'current-strategy', value: this.data.status.strategy || 'Challenge Growth' },
            { id: 'total-pnl', value: `$${(this.data.performance.total_pnl || 0).toFixed(2)}` },
            { id: 'best-trade', value: `$${(this.data.performance.best_trade || 0).toFixed(2)}` },
            { id: 'avg-trade', value: `$${(this.data.performance.avg_trade || 0).toFixed(2)}` },
            { id: 'last-update', value: new Date().toLocaleTimeString() }
        ];

        performanceItems.forEach(item => {
            const el = document.getElementById(item.id);
            if (el) {
                el.textContent = item.value;
                
                // Add color classes for P&L values
                if (item.id.includes('pnl') || item.id.includes('trade')) {
                    const value = parseFloat(item.value.replace('$', ''));
                    el.className = `pnl-value ${value >= 0 ? 'positive' : 'negative'}`;
                }
            }
        });
    }

    updateActivity() {
        const tableBody = document.querySelector('#activity-table tbody');
        if (!tableBody) return;

        // Clear existing rows
        tableBody.innerHTML = '';

        if (this.data.trades && this.data.trades.length > 0) {
            // Show recent trades (last 10)
            const recentTrades = this.data.trades.slice(-10).reverse();
            
            recentTrades.forEach(trade => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${new Date(trade.execution_time).toLocaleTimeString()}</td>
                    <td>${trade.symbol}</td>
                    <td><span class="badge ${trade.side.toLowerCase()}">${trade.side}</span></td>
                    <td>$${trade.amount_usdt.toFixed(2)}</td>
                    <td>$${trade.execution_price.toFixed(4)}</td>
                    <td class="pnl-value ${trade.net_amount_usdt >= 0 ? 'positive' : 'negative'}">
                        ${trade.net_amount_usdt >= 0 ? '+' : ''}$${trade.net_amount_usdt.toFixed(4)}
                    </td>
                `;
                tableBody.appendChild(row);
            });
        } else {
            // Show no data message
            const row = document.createElement('tr');
            row.className = 'no-data';
            row.innerHTML = '<td colspan="6">No recent trades found. Start trading to see activity.</td>';
            tableBody.appendChild(row);
        }
    }

    updateCharts() {
        if (window.ChartsManager) {
            window.ChartsManager.updateCharts(this.data);
        }
    }

    refreshPageData(page) {
        switch (page) {
            case 'trading':
                this.updateTradingPage();
                break;
            case 'portfolio':
                this.updatePortfolioPage();
                break;
            case 'analytics':
                this.updateAnalyticsPage();
                break;
            case 'history':
                this.updateHistoryPage();
                break;
        }
    }

    updateTradingPage() {
        // Update trading controls based on current status
        const strategySelect = document.getElementById('strategy-select');
        const modeSelect = document.getElementById('mode-select');
        
        if (strategySelect) {
            strategySelect.value = this.data.status.strategy?.toLowerCase() || 'challenge';
        }
        
        if (modeSelect) {
            modeSelect.value = this.data.status.mode?.toLowerCase() || 'testnet';
        }
    }

    updatePortfolioPage() {
        // Update portfolio metrics
        const portfolioMetrics = [
            { id: 'portfolio-total', value: `$${this.data.balance.toFixed(2)}` },
            { id: 'portfolio-pnl', value: `$${(this.data.performance.total_pnl || 0).toFixed(2)}` },
            { id: 'portfolio-roi', value: `${(((this.data.balance - 50) / 50) * 100).toFixed(1)}%` },
            { id: 'portfolio-progress', value: `${Math.min((this.data.balance / 100) * 100, 100).toFixed(1)}%` }
        ];

        portfolioMetrics.forEach(metric => {
            const el = document.getElementById(metric.id);
            if (el) {
                el.textContent = metric.value;
            }
        });
    }

    updateAnalyticsPage() {
        // Update analytics metrics
        const analyticsMetrics = [
            { id: 'analytics-sharpe', value: (this.data.performance.sharpe_ratio || 0).toFixed(2) },
            { id: 'analytics-winrate', value: `${(this.data.performance.win_rate || 0).toFixed(1)}%` },
            { id: 'analytics-avgtrade', value: `$${(this.data.performance.avg_trade || 0).toFixed(2)}` },
            { id: 'analytics-besttrade', value: `$${(this.data.performance.best_trade || 0).toFixed(2)}` }
        ];

        analyticsMetrics.forEach(metric => {
            const el = document.getElementById(metric.id);
            if (el) {
                el.textContent = metric.value;
            }
        });
    }

    updateHistoryPage() {
        const tableBody = document.querySelector('#history-table tbody');
        if (!tableBody) return;

        // Clear existing rows
        tableBody.innerHTML = '';

        if (this.data.trades && this.data.trades.length > 0) {
            this.data.trades.forEach(trade => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${new Date(trade.execution_time).toLocaleString()}</td>
                    <td>${trade.symbol}</td>
                    <td><span class="badge ${trade.side.toLowerCase()}">${trade.side}</span></td>
                    <td>$${trade.amount_usdt.toFixed(2)}</td>
                    <td>$${trade.execution_price.toFixed(4)}</td>
                    <td>$${(trade.fee_usdt || 0).toFixed(4)}</td>
                    <td class="pnl-value ${trade.net_amount_usdt >= 0 ? 'positive' : 'negative'}">
                        ${trade.net_amount_usdt >= 0 ? '+' : ''}$${trade.net_amount_usdt.toFixed(4)}
                    </td>
                    <td><span class="badge success">Completed</span></td>
                `;
                tableBody.appendChild(row);
            });
        } else {
            const row = document.createElement('tr');
            row.className = 'no-data';
            row.innerHTML = '<td colspan="8">No trading history found.</td>';
            tableBody.appendChild(row);
        }
    }

    async startTrading() {
        try {
            const response = await fetch(`${this.apiBase}/api/start-trading`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.showNotification('Trading started successfully!', 'success');
                await this.refreshData();
            } else {
                throw new Error('Failed to start trading');
            }
        } catch (error) {
            console.error('Error starting trading:', error);
            this.showNotification('Failed to start trading', 'error');
        }
    }

    async stopTrading() {
        try {
            const response = await fetch(`${this.apiBase}/api/stop-trading`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.showNotification('Trading stopped successfully!', 'warning');
                await this.refreshData();
            } else {
                throw new Error('Failed to stop trading');
            }
        } catch (error) {
            console.error('Error stopping trading:', error);
            this.showNotification('Failed to stop trading', 'error');
        }
    }

    showEmergencyModal() {
        const modal = document.getElementById('emergency-modal');
        if (modal) {
            modal.classList.add('show');
        }
    }

    hideEmergencyModal() {
        const modal = document.getElementById('emergency-modal');
        if (modal) {
            modal.classList.remove('show');
        }
    }

    async emergencyStop() {
        try {
            const response = await fetch(`${this.apiBase}/api/emergency-stop`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    reason: 'Manual emergency stop from web interface'
                })
            });
            
            if (response.ok) {
                this.showNotification('Emergency stop activated!', 'warning');
                this.hideEmergencyModal();
                await this.refreshData();
            } else {
                throw new Error('Failed to trigger emergency stop');
            }
        } catch (error) {
            console.error('Error triggering emergency stop:', error);
            this.showNotification('Failed to trigger emergency stop', 'error');
        }
    }

    saveSettings() {
        // Collect settings from form
        const settings = {
            api_key: document.getElementById('api-key')?.value,
            api_secret: document.getElementById('api-secret')?.value,
            telegram_token: document.getElementById('telegram-token')?.value,
            chat_id: document.getElementById('chat-id')?.value,
            max_trades: document.getElementById('max-trades')?.value,
            stop_loss: document.getElementById('stop-loss')?.value,
            take_profit: document.getElementById('take-profit')?.value,
            confidence: document.getElementById('confidence')?.value,
            position_size: document.getElementById('position-size')?.value,
            max_positions: document.getElementById('max-positions')?.value,
            theme: document.getElementById('theme-select')?.value,
            refresh_rate: document.getElementById('refresh-rate')?.value,
            notifications: document.getElementById('enable-notifications')?.checked,
            sound_alerts: document.getElementById('sound-alerts')?.checked
        };

        // Save to localStorage
        localStorage.setItem('aurumbotx_settings', JSON.stringify(settings));
        
        // Apply settings
        this.applySettings(settings);
        
        this.showNotification('Settings saved successfully!', 'success');
    }

    loadSettings() {
        const saved = localStorage.getItem('aurumbotx_settings');
        if (saved) {
            try {
                const settings = JSON.parse(saved);
                this.applySettings(settings);
                this.populateSettingsForm(settings);
            } catch (error) {
                console.error('Error loading settings:', error);
            }
        }
    }

    applySettings(settings) {
        // Apply theme
        if (settings.theme) {
            this.setTheme(settings.theme);
        }
        
        // Apply refresh rate
        if (settings.refresh_rate) {
            this.refreshInterval = parseInt(settings.refresh_rate) * 1000;
            this.startRefreshCycle();
        }
    }

    populateSettingsForm(settings) {
        Object.keys(settings).forEach(key => {
            const element = document.getElementById(key.replace('_', '-'));
            if (element) {
                if (element.type === 'checkbox') {
                    element.checked = settings[key];
                } else {
                    element.value = settings[key];
                }
            }
        });
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('aurumbotx_theme', theme);
    }

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    }

    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + R: Refresh data
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            this.refreshData();
        }
        
        // Escape: Close modals
        if (e.key === 'Escape') {
            this.hideEmergencyModal();
        }
        
        // Number keys: Navigate to pages
        const pageMap = {
            '1': 'overview',
            '2': 'trading',
            '3': 'portfolio',
            '4': 'analytics',
            '5': 'history',
            '6': 'settings'
        };
        
        if (pageMap[e.key] && !e.ctrlKey && !e.metaKey && !e.altKey) {
            this.navigateToPage(pageMap[e.key]);
        }
    }

    startRefreshCycle() {
        this.stopRefreshCycle();
        this.refreshTimer = setInterval(() => {
            this.refreshData();
        }, this.refreshInterval);
    }

    stopRefreshCycle() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }
    }

    setupPWA() {
        // Register service worker
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(registration => {
                    console.log('SW registered:', registration);
                })
                .catch(error => {
                    console.log('SW registration failed:', error);
                });
        }

        // Handle install prompt
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            
            // Show install button
            const installBtn = document.createElement('button');
            installBtn.textContent = 'Install App';
            installBtn.className = 'btn btn-primary';
            installBtn.onclick = () => {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then((choiceResult) => {
                    if (choiceResult.outcome === 'accepted') {
                        console.log('User accepted the install prompt');
                    }
                    deferredPrompt = null;
                    installBtn.remove();
                });
            };
            
            document.querySelector('.header-controls')?.appendChild(installBtn);
        });
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notifications');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <strong>${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
                <p>${message}</p>
            </div>
        `;

        container.appendChild(notification);

        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);

        // Remove on click
        notification.addEventListener('click', () => {
            notification.remove();
        });
    }

    getTodayTrades() {
        if (!this.data.trades) return 0;
        
        const today = new Date().toDateString();
        return this.data.trades.filter(trade => {
            const tradeDate = new Date(trade.execution_time).toDateString();
            return tradeDate === today;
        }).length;
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new AurumBotXApp();
});

// Global functions for backward compatibility
function refreshData() {
    if (window.app) {
        window.app.refreshData();
    }
}
