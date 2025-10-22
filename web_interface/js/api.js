/**
 * AurumBotX v2.1 - API Manager
 * Handles all API communications and data management
 */

class APIManager {
    constructor() {
        this.baseURL = 'http://localhost:5678';
        this.timeout = 10000; // 10 seconds
        this.retryAttempts = 3;
        this.retryDelay = 1000; // 1 second
        this.cache = new Map();
        this.cacheTimeout = 30000; // 30 seconds
        
        this.endpoints = {
            status: '/api/status',
            balance: '/api/balance',
            trades: '/api/trades',
            performance: '/api/performance',
            start: '/api/start-trading',
            stop: '/api/stop-trading',
            emergency: '/api/emergency-stop',
            settings: '/api/settings',
            history: '/api/history',
            portfolio: '/api/portfolio'
        };
        
        this.isOnline = navigator.onLine;
        this.setupNetworkListeners();
    }

    setupNetworkListeners() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            console.log('🌐 Network connection restored');
            this.notifyConnectionChange(true);
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            console.log('🔌 Network connection lost');
            this.notifyConnectionChange(false);
        });
    }

    notifyConnectionChange(isOnline) {
        // Dispatch custom event for connection changes
        const event = new CustomEvent('connectionChange', {
            detail: { isOnline }
        });
        window.dispatchEvent(event);
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const cacheKey = `${endpoint}_${JSON.stringify(options)}`;
        
        // Check cache first for GET requests
        if (!options.method || options.method === 'GET') {
            const cached = this.getFromCache(cacheKey);
            if (cached) {
                return cached;
            }
        }

        // Check network connectivity
        if (!this.isOnline) {
            throw new Error('No network connection');
        }

        const requestOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                ...options.headers
            },
            timeout: this.timeout,
            ...options
        };

        let lastError;
        
        for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
            try {
                console.log(`📡 API Request (attempt ${attempt}): ${endpoint}`);
                
                const response = await this.fetchWithTimeout(url, requestOptions);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                
                // Cache successful GET requests
                if (!options.method || options.method === 'GET') {
                    this.setCache(cacheKey, data);
                }
                
                console.log(`✅ API Success: ${endpoint}`);
                return data;
                
            } catch (error) {
                lastError = error;
                console.warn(`⚠️ API Error (attempt ${attempt}): ${endpoint} - ${error.message}`);
                
                // Don't retry for certain errors
                if (error.name === 'AbortError' || error.message.includes('404')) {
                    break;
                }
                
                // Wait before retry
                if (attempt < this.retryAttempts) {
                    await this.delay(this.retryDelay * attempt);
                }
            }
        }
        
        console.error(`❌ API Failed: ${endpoint} - ${lastError.message}`);
        throw lastError;
    }

    async fetchWithTimeout(url, options) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        
        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            throw error;
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    setCache(key, data) {
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
    }

    getFromCache(key) {
        const cached = this.cache.get(key);
        if (!cached) return null;
        
        const isExpired = Date.now() - cached.timestamp > this.cacheTimeout;
        if (isExpired) {
            this.cache.delete(key);
            return null;
        }
        
        console.log(`💾 Cache hit: ${key}`);
        return cached.data;
    }

    clearCache() {
        this.cache.clear();
        console.log('🗑️ Cache cleared');
    }

    // API Methods
    async getStatus() {
        try {
            return await this.request(this.endpoints.status);
        } catch (error) {
            return {
                status: 'offline',
                trading_active: false,
                strategy: 'Unknown',
                error: error.message
            };
        }
    }

    async getBalance() {
        try {
            return await this.request(this.endpoints.balance);
        } catch (error) {
            return {
                USDT: 50.0,
                BTC: 0,
                ETH: 0,
                SOL: 0,
                error: error.message
            };
        }
    }

    async getTrades(limit = 100) {
        try {
            return await this.request(`${this.endpoints.trades}?limit=${limit}`);
        } catch (error) {
            return {
                trades: [],
                total: 0,
                error: error.message
            };
        }
    }

    async getPerformance() {
        try {
            return await this.request(this.endpoints.performance);
        } catch (error) {
            return {
                total_trades: 0,
                win_rate: 0,
                total_pnl: 0,
                sharpe_ratio: 0,
                best_trade: 0,
                worst_trade: 0,
                avg_trade: 0,
                max_drawdown: 0,
                profit_factor: 0,
                error: error.message
            };
        }
    }

    async getHistory(filters = {}) {
        try {
            const queryParams = new URLSearchParams(filters).toString();
            const endpoint = queryParams ? `${this.endpoints.history}?${queryParams}` : this.endpoints.history;
            return await this.request(endpoint);
        } catch (error) {
            return {
                trades: [],
                total: 0,
                error: error.message
            };
        }
    }

    async getPortfolio() {
        try {
            return await this.request(this.endpoints.portfolio);
        } catch (error) {
            return {
                total_value: 50.0,
                allocations: {
                    USDT: 100,
                    BTC: 0,
                    ETH: 0,
                    SOL: 0
                },
                error: error.message
            };
        }
    }

    async startTrading(config = {}) {
        try {
            return await this.request(this.endpoints.start, {
                method: 'POST',
                body: JSON.stringify(config)
            });
        } catch (error) {
            throw new Error(`Failed to start trading: ${error.message}`);
        }
    }

    async stopTrading() {
        try {
            return await this.request(this.endpoints.stop, {
                method: 'POST'
            });
        } catch (error) {
            throw new Error(`Failed to stop trading: ${error.message}`);
        }
    }

    async emergencyStop(reason = 'Manual emergency stop') {
        try {
            return await this.request(this.endpoints.emergency, {
                method: 'POST',
                body: JSON.stringify({ reason })
            });
        } catch (error) {
            throw new Error(`Failed to trigger emergency stop: ${error.message}`);
        }
    }

    async saveSettings(settings) {
        try {
            return await this.request(this.endpoints.settings, {
                method: 'POST',
                body: JSON.stringify(settings)
            });
        } catch (error) {
            throw new Error(`Failed to save settings: ${error.message}`);
        }
    }

    async getSettings() {
        try {
            return await this.request(this.endpoints.settings);
        } catch (error) {
            return {
                api_key: '',
                api_secret: '',
                telegram_token: '',
                chat_id: '',
                max_trades: 20,
                stop_loss: 5.0,
                take_profit: 10.0,
                confidence: 0.6,
                position_size: 15.0,
                max_positions: 3,
                error: error.message
            };
        }
    }

    // Batch operations
    async getAllData() {
        console.log('📊 Fetching all data...');
        
        try {
            const [status, balance, trades, performance] = await Promise.allSettled([
                this.getStatus(),
                this.getBalance(),
                this.getTrades(),
                this.getPerformance()
            ]);

            return {
                status: status.status === 'fulfilled' ? status.value : status.reason,
                balance: balance.status === 'fulfilled' ? balance.value : balance.reason,
                trades: trades.status === 'fulfilled' ? trades.value : trades.reason,
                performance: performance.status === 'fulfilled' ? performance.value : performance.reason,
                timestamp: Date.now()
            };
        } catch (error) {
            console.error('❌ Failed to fetch all data:', error);
            throw error;
        }
    }

    // Health check
    async healthCheck() {
        try {
            const start = Date.now();
            await this.request('/api/health');
            const latency = Date.now() - start;
            
            return {
                status: 'healthy',
                latency,
                timestamp: Date.now()
            };
        } catch (error) {
            return {
                status: 'unhealthy',
                error: error.message,
                timestamp: Date.now()
            };
        }
    }

    // WebSocket connection (for real-time updates)
    connectWebSocket() {
        if (this.ws) {
            this.ws.close();
        }

        const wsUrl = this.baseURL.replace('http', 'ws') + '/ws';
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('🔌 WebSocket connected');
                this.dispatchEvent('wsConnected');
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.dispatchEvent('wsMessage', data);
                } catch (error) {
                    console.error('❌ WebSocket message parse error:', error);
                }
            };
            
            this.ws.onclose = () => {
                console.log('🔌 WebSocket disconnected');
                this.dispatchEvent('wsDisconnected');
                
                // Attempt to reconnect after 5 seconds
                setTimeout(() => {
                    if (this.isOnline) {
                        this.connectWebSocket();
                    }
                }, 5000);
            };
            
            this.ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
                this.dispatchEvent('wsError', error);
            };
            
        } catch (error) {
            console.error('❌ Failed to create WebSocket:', error);
        }
    }

    disconnectWebSocket() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    sendWebSocketMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.warn('⚠️ WebSocket not connected');
        }
    }

    dispatchEvent(eventName, data = null) {
        const event = new CustomEvent(eventName, {
            detail: data
        });
        window.dispatchEvent(event);
    }

    // Utility methods
    isHealthy() {
        return this.isOnline && this.cache.size >= 0;
    }

    getConnectionInfo() {
        return {
            isOnline: this.isOnline,
            baseURL: this.baseURL,
            cacheSize: this.cache.size,
            wsConnected: this.ws && this.ws.readyState === WebSocket.OPEN
        };
    }

    // Configuration
    setBaseURL(url) {
        this.baseURL = url;
        console.log(`🔧 API base URL updated: ${url}`);
    }

    setTimeout(timeout) {
        this.timeout = timeout;
        console.log(`🔧 API timeout updated: ${timeout}ms`);
    }

    setRetryAttempts(attempts) {
        this.retryAttempts = attempts;
        console.log(`🔧 API retry attempts updated: ${attempts}`);
    }

    setCacheTimeout(timeout) {
        this.cacheTimeout = timeout;
        console.log(`🔧 Cache timeout updated: ${timeout}ms`);
    }
}

// Create global instance
window.APIManager = new APIManager();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = APIManager;
}
