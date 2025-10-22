/**
 * AurumBotX v2.1 - Charts Manager
 * Handles all chart rendering and updates
 */

class ChartsManager {
    constructor() {
        this.charts = {};
        this.chartConfigs = {};
        this.colors = {
            primary: '#667eea',
            success: '#28a745',
            danger: '#dc3545',
            warning: '#ffc107',
            info: '#17a2b8',
            light: '#f8f9fa',
            dark: '#343a40'
        };
        
        this.gradients = {};
        this.isInitialized = false;
    }

    init() {
        if (this.isInitialized) return;
        
        console.log('📊 Initializing Charts Manager...');
        
        // Set Chart.js defaults
        this.setChartDefaults();
        
        // Initialize all charts
        this.initializeCharts();
        
        this.isInitialized = true;
        console.log('✅ Charts Manager initialized');
    }

    setChartDefaults() {
        Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
        Chart.defaults.font.size = 12;
        Chart.defaults.color = '#6c757d';
        Chart.defaults.borderColor = '#e9ecef';
        Chart.defaults.backgroundColor = 'rgba(102, 126, 234, 0.1)';
        
        // Responsive defaults
        Chart.defaults.responsive = true;
        Chart.defaults.maintainAspectRatio = false;
        
        // Animation defaults
        Chart.defaults.animation.duration = 750;
        Chart.defaults.animation.easing = 'easeInOutQuart';
    }

    initializeCharts() {
        // Performance Chart (Trading Page)
        this.initPerformanceChart();
        
        // Portfolio Allocation Chart
        this.initAllocationChart();
        
        // P&L Chart (Analytics Page)
        this.initPnLChart();
        
        // Win/Loss Chart (Analytics Page)
        this.initWinLossChart();
    }

    initPerformanceChart() {
        const canvas = document.getElementById('performance-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        
        // Create gradient
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(102, 126, 234, 0.3)');
        gradient.addColorStop(1, 'rgba(102, 126, 234, 0.05)');
        this.gradients.performance = gradient;

        this.chartConfigs.performance = {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Portfolio Value',
                    data: [],
                    borderColor: this.colors.primary,
                    backgroundColor: gradient,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: this.colors.primary,
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: this.colors.primary,
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return `Value: $${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        display: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    }
                }
            }
        };

        this.charts.performance = new Chart(ctx, this.chartConfigs.performance);
    }

    initAllocationChart() {
        const canvas = document.getElementById('allocation-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        this.chartConfigs.allocation = {
            type: 'doughnut',
            data: {
                labels: ['USDT', 'BTC', 'ETH', 'SOL', 'Other'],
                datasets: [{
                    data: [100, 0, 0, 0, 0],
                    backgroundColor: [
                        this.colors.success,
                        this.colors.warning,
                        this.colors.info,
                        this.colors.primary,
                        this.colors.light
                    ],
                    borderWidth: 0,
                    hoverBorderWidth: 3,
                    hoverBorderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: this.colors.primary,
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${percentage}%`;
                            }
                        }
                    }
                }
            }
        };

        this.charts.allocation = new Chart(ctx, this.chartConfigs.allocation);
    }

    initPnLChart() {
        const canvas = document.getElementById('pnl-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        
        // Create gradient for positive P&L
        const positiveGradient = ctx.createLinearGradient(0, 0, 0, 400);
        positiveGradient.addColorStop(0, 'rgba(40, 167, 69, 0.3)');
        positiveGradient.addColorStop(1, 'rgba(40, 167, 69, 0.05)');
        
        // Create gradient for negative P&L
        const negativeGradient = ctx.createLinearGradient(0, 0, 0, 400);
        negativeGradient.addColorStop(0, 'rgba(220, 53, 69, 0.3)');
        negativeGradient.addColorStop(1, 'rgba(220, 53, 69, 0.05)');

        this.chartConfigs.pnl = {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Cumulative P&L',
                    data: [],
                    borderColor: this.colors.success,
                    backgroundColor: positiveGradient,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: this.colors.success,
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: this.colors.success,
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed.y;
                                const sign = value >= 0 ? '+' : '';
                                return `P&L: ${sign}$${value.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        display: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            callback: function(value) {
                                const sign = value >= 0 ? '+' : '';
                                return sign + '$' + value.toFixed(2);
                            }
                        }
                    }
                }
            }
        };

        this.charts.pnl = new Chart(ctx, this.chartConfigs.pnl);
    }

    initWinLossChart() {
        const canvas = document.getElementById('winloss-chart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        this.chartConfigs.winloss = {
            type: 'bar',
            data: {
                labels: ['Wins', 'Losses'],
                datasets: [{
                    label: 'Trades',
                    data: [0, 0],
                    backgroundColor: [
                        this.colors.success,
                        this.colors.danger
                    ],
                    borderColor: [
                        this.colors.success,
                        this.colors.danger
                    ],
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: this.colors.primary,
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((context.parsed.y / total) * 100).toFixed(1) : 0;
                                return `${context.label}: ${context.parsed.y} (${percentage}%)`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        display: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            stepSize: 1,
                            callback: function(value) {
                                return Math.floor(value);
                            }
                        }
                    }
                }
            }
        };

        this.charts.winloss = new Chart(ctx, this.chartConfigs.winloss);
    }

    updateCharts(data) {
        if (!this.isInitialized) return;
        
        this.updatePerformanceChart(data);
        this.updateAllocationChart(data);
        this.updatePnLChart(data);
        this.updateWinLossChart(data);
    }

    updatePerformanceChart(data) {
        const chart = this.charts.performance;
        if (!chart || !data.trades) return;

        // Generate time series data from trades
        const timeSeriesData = this.generateTimeSeriesData(data.trades, data.balance);
        
        chart.data.labels = timeSeriesData.labels;
        chart.data.datasets[0].data = timeSeriesData.values;
        
        // Update colors based on performance
        const lastValue = timeSeriesData.values[timeSeriesData.values.length - 1];
        const firstValue = timeSeriesData.values[0] || 50;
        
        if (lastValue >= firstValue) {
            chart.data.datasets[0].borderColor = this.colors.success;
            chart.data.datasets[0].pointBackgroundColor = this.colors.success;
        } else {
            chart.data.datasets[0].borderColor = this.colors.danger;
            chart.data.datasets[0].pointBackgroundColor = this.colors.danger;
        }
        
        chart.update('none');
    }

    updateAllocationChart(data) {
        const chart = this.charts.allocation;
        if (!chart) return;

        // For now, show 100% USDT allocation
        // In the future, this could be calculated from actual holdings
        chart.data.datasets[0].data = [100, 0, 0, 0, 0];
        chart.update('none');
    }

    updatePnLChart(data) {
        const chart = this.charts.pnl;
        if (!chart || !data.trades) return;

        // Generate cumulative P&L data
        const pnlData = this.generatePnLData(data.trades);
        
        chart.data.labels = pnlData.labels;
        chart.data.datasets[0].data = pnlData.values;
        
        // Update colors based on final P&L
        const finalPnL = pnlData.values[pnlData.values.length - 1] || 0;
        
        if (finalPnL >= 0) {
            chart.data.datasets[0].borderColor = this.colors.success;
            chart.data.datasets[0].pointBackgroundColor = this.colors.success;
        } else {
            chart.data.datasets[0].borderColor = this.colors.danger;
            chart.data.datasets[0].pointBackgroundColor = this.colors.danger;
        }
        
        chart.update('none');
    }

    updateWinLossChart(data) {
        const chart = this.charts.winloss;
        if (!chart || !data.trades) return;

        // Calculate wins and losses
        const wins = data.trades.filter(trade => trade.net_amount_usdt > 0).length;
        const losses = data.trades.filter(trade => trade.net_amount_usdt < 0).length;
        
        chart.data.datasets[0].data = [wins, losses];
        chart.update('none');
    }

    generateTimeSeriesData(trades, currentBalance) {
        const labels = [];
        const values = [];
        
        if (!trades || trades.length === 0) {
            // Show initial balance
            labels.push(new Date().toLocaleTimeString());
            values.push(currentBalance);
            return { labels, values };
        }

        // Start with initial balance
        let runningBalance = 50.0;
        values.push(runningBalance);
        labels.push('Start');

        // Process trades chronologically
        const sortedTrades = [...trades].sort((a, b) => 
            new Date(a.execution_time) - new Date(b.execution_time)
        );

        sortedTrades.forEach((trade, index) => {
            runningBalance += trade.net_amount_usdt;
            values.push(runningBalance);
            
            const time = new Date(trade.execution_time);
            labels.push(time.toLocaleTimeString());
        });

        // Limit to last 20 points for readability
        if (labels.length > 20) {
            const start = labels.length - 20;
            return {
                labels: labels.slice(start),
                values: values.slice(start)
            };
        }

        return { labels, values };
    }

    generatePnLData(trades) {
        const labels = [];
        const values = [];
        
        if (!trades || trades.length === 0) {
            labels.push(new Date().toLocaleTimeString());
            values.push(0);
            return { labels, values };
        }

        let cumulativePnL = 0;
        values.push(cumulativePnL);
        labels.push('Start');

        // Process trades chronologically
        const sortedTrades = [...trades].sort((a, b) => 
            new Date(a.execution_time) - new Date(b.execution_time)
        );

        sortedTrades.forEach(trade => {
            cumulativePnL += trade.net_amount_usdt;
            values.push(cumulativePnL);
            
            const time = new Date(trade.execution_time);
            labels.push(time.toLocaleTimeString());
        });

        // Limit to last 20 points for readability
        if (labels.length > 20) {
            const start = labels.length - 20;
            return {
                labels: labels.slice(start),
                values: values.slice(start)
            };
        }

        return { labels, values };
    }

    resizeCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.resize();
            }
        });
    }

    destroyCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart) {
                chart.destroy();
            }
        });
        this.charts = {};
        this.isInitialized = false;
    }

    // Utility method to create gradients
    createGradient(ctx, color1, color2, direction = 'vertical') {
        let gradient;
        
        if (direction === 'vertical') {
            gradient = ctx.createLinearGradient(0, 0, 0, 400);
        } else {
            gradient = ctx.createLinearGradient(0, 0, 400, 0);
        }
        
        gradient.addColorStop(0, color1);
        gradient.addColorStop(1, color2);
        
        return gradient;
    }

    // Method to export chart as image
    exportChart(chartName, filename) {
        const chart = this.charts[chartName];
        if (!chart) return;

        const url = chart.toBase64Image();
        const link = document.createElement('a');
        link.download = filename || `${chartName}-chart.png`;
        link.href = url;
        link.click();
    }

    // Method to get chart data for external use
    getChartData(chartName) {
        const chart = this.charts[chartName];
        if (!chart) return null;

        return {
            labels: chart.data.labels,
            datasets: chart.data.datasets
        };
    }
}

// Create global instance
window.ChartsManager = new ChartsManager();

// Handle window resize
window.addEventListener('resize', () => {
    if (window.ChartsManager) {
        window.ChartsManager.resizeCharts();
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChartsManager;
}
