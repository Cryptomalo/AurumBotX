/**
 * AurumBotX - Multi-Wallet Dashboard Module
 * Gestisce visualizzazione e aggiornamento dati multi-wallet
 */

const API_BASE = 'http://localhost:8080/api';
let refreshInterval = null;

// Inizializza dashboard multi-wallet
function initMultiWalletDashboard() {
    console.log('Initializing Multi-Wallet Dashboard...');
    
    // Carica dati iniziali
    loadMultiWalletData();
    
    // Auto-refresh ogni 30 secondi
    refreshInterval = setInterval(loadMultiWalletData, 30000);
}

// Carica tutti i dati multi-wallet
async function loadMultiWalletData() {
    try {
        // Carica summary
        const summary = await fetch(`${API_BASE}/summary`).then(r => r.json());
        updateSummaryCards(summary);
        
        // Carica wallets
        const wallets = await fetch(`${API_BASE}/wallets`).then(r => r.json());
        updateWalletsTable(wallets);
        updateWalletsChart(wallets);
        
        // Carica trade recenti
        const trades = await fetch(`${API_BASE}/trades`).then(r => r.json());
        updateTradesTable(trades);
        
    } catch (error) {
        console.error('Error loading multi-wallet data:', error);
    }
}

// Aggiorna card riepilogo
function updateSummaryCards(summary) {
    document.getElementById('total-capital').textContent = `$${summary.total_capital.toFixed(2)}`;
    document.getElementById('total-pnl').textContent = `$${summary.total_pnl >= 0 ? '+' : ''}${summary.total_pnl.toFixed(2)}`;
    document.getElementById('total-roi').textContent = `${summary.total_roi >= 0 ? '+' : ''}${summary.total_roi.toFixed(2)}%`;
    document.getElementById('avg-win-rate').textContent = `${summary.avg_win_rate.toFixed(1)}%`;
    document.getElementById('total-trades').textContent = summary.total_trades;
    document.getElementById('active-wallets').textContent = summary.active_wallets;
    
    // Colori dinamici
    const pnlEl = document.getElementById('total-pnl');
    pnlEl.style.color = summary.total_pnl >= 0 ? '#10b981' : '#ef4444';
    
    const roiEl = document.getElementById('total-roi');
    roiEl.style.color = summary.total_roi >= 0 ? '#10b981' : '#ef4444';
}

// Aggiorna tabella wallets
function updateWalletsTable(wallets) {
    const tbody = document.getElementById('wallets-table-body');
    
    tbody.innerHTML = wallets.map(w => `
        <tr>
            <td>${w.name}</td>
            <td>$${w.capital.toFixed(2)}</td>
            <td style="color: ${w.total_pnl >= 0 ? '#10b981' : '#ef4444'}">
                $${w.total_pnl >= 0 ? '+' : ''}${w.total_pnl.toFixed(2)}
            </td>
            <td style="color: ${w.roi >= 0 ? '#10b981' : '#ef4444'}">
                ${w.roi >= 0 ? '+' : ''}${w.roi.toFixed(2)}%
            </td>
            <td>${w.total_trades}</td>
            <td>${w.win_rate.toFixed(1)}%</td>
            <td>
                <span class="status-badge ${w.status === 'active' ? 'active' : 'inactive'}">
                    ${w.status === 'active' ? '✅ Attivo' : '❌ Fermo'}
                </span>
            </td>
        </tr>
    `).join('');
}

// Aggiorna grafico wallets
let walletsChart = null;
function updateWalletsChart(wallets) {
    const ctx = document.getElementById('wallets-chart').getContext('2d');
    
    if (walletsChart) {
        walletsChart.destroy();
    }
    
    walletsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: wallets.map(w => w.name),
            datasets: [{
                label: 'P&L ($)',
                data: wallets.map(w => w.total_pnl),
                backgroundColor: wallets.map(w => w.total_pnl >= 0 ? 'rgba(16, 185, 129, 0.8)' : 'rgba(239, 68, 68, 0.8)'),
                borderColor: wallets.map(w => w.total_pnl >= 0 ? 'rgb(16, 185, 129)' : 'rgb(239, 68, 68)'),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'P&L per Wallet',
                    color: '#fff',
                    font: {
                        size: 16
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#fff',
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        }
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#fff'
                    }
                }
            }
        }
    });
}

// Aggiorna tabella trade
function updateTradesTable(trades) {
    const tbody = document.getElementById('trades-table-body');
    
    tbody.innerHTML = trades.slice(0, 20).map(t => `
        <tr>
            <td>${t.wallet_name || 'N/A'}</td>
            <td>${t.pair || 'N/A'}</td>
            <td>${t.action || 'N/A'}</td>
            <td>
                <span class="result-badge ${t.result === 'WIN' ? 'win' : 'loss'}">
                    ${t.result === 'WIN' ? '✅ WIN' : '❌ LOSS'}
                </span>
            </td>
            <td style="color: ${t.pnl >= 0 ? '#10b981' : '#ef4444'}">
                $${t.pnl >= 0 ? '+' : ''}${t.pnl.toFixed(4)}
            </td>
            <td>$${t.capital_after ? t.capital_after.toFixed(2) : 'N/A'}</td>
        </tr>
    `).join('');
}

// Cleanup
function cleanupMultiWalletDashboard() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    if (walletsChart) {
        walletsChart.destroy();
    }
}

// Export
window.MultiWalletDashboard = {
    init: initMultiWalletDashboard,
    cleanup: cleanupMultiWalletDashboard,
    refresh: loadMultiWalletData
};

