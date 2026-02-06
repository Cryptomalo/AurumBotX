#!/usr/bin/env python3
# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

"""
AurumBotX Testnet vs Mainnet Analysis
Analisi completa delle differenze tra trading testnet e mainnet
"""

import os
import sys
import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TestnetAnalysis')

class TestnetMainnetAnalyzer:
    """Analizzatore differenze testnet vs mainnet"""
    
    def __init__(self):
        self.logger = logging.getLogger('TestnetMainnetAnalyzer')
        
    def get_real_market_data(self):
        """Ottieni dati reali dal mercato"""
        try:
            # Binance API per dati reali
            url = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'price': float(data['lastPrice']),
                    'volume_24h': float(data['volume']),
                    'price_change_24h': float(data['priceChangePercent']),
                    'high_24h': float(data['highPrice']),
                    'low_24h': float(data['lowPrice']),
                    'bid_price': float(data['bidPrice']),
                    'ask_price': float(data['askPrice'])
                }
            else:
                self.logger.error(f"Errore API Binance: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Errore recupero dati reali: {e}")
            return None
    
    def get_orderbook_data(self):
        """Ottieni dati orderbook reali"""
        try:
            url = "https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=100"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Analizza bid/ask
                bids = [[float(price), float(qty)] for price, qty in data['bids'][:10]]
                asks = [[float(price), float(qty)] for price, qty in data['asks'][:10]]
                
                # Calcola spread
                best_bid = bids[0][0]
                best_ask = asks[0][0]
                spread = best_ask - best_bid
                spread_percent = (spread / best_bid) * 100
                
                # Calcola liquidità
                bid_liquidity = sum([price * qty for price, qty in bids])
                ask_liquidity = sum([price * qty for price, qty in asks])
                
                return {
                    'spread_absolute': spread,
                    'spread_percent': spread_percent,
                    'bid_liquidity': bid_liquidity,
                    'ask_liquidity': ask_liquidity,
                    'best_bid': best_bid,
                    'best_ask': best_ask
                }
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Errore orderbook: {e}")
            return None
    
    def analyze_testnet_vs_mainnet(self):
        """Analizza differenze complete"""
        try:
            print("🔍 ANALISI TESTNET vs MAINNET")
            print("=" * 60)
            
            # Dati reali
            real_data = self.get_real_market_data()
            orderbook_data = self.get_orderbook_data()
            
            if not real_data:
                print("❌ Impossibile ottenere dati reali")
                return
            
            # Analisi dettagliata
            analysis = {
                'market_data': real_data,
                'orderbook': orderbook_data,
                'testnet_differences': self.calculate_testnet_differences(real_data, orderbook_data),
                'profit_impact': self.calculate_profit_impact(real_data, orderbook_data),
                'risk_factors': self.identify_risk_factors(),
                'recommendations': self.generate_recommendations()
            }
            
            # Report completo
            self.generate_detailed_report(analysis)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Errore analisi: {e}")
            return None
    
    def calculate_testnet_differences(self, real_data, orderbook_data):
        """Calcola differenze specifiche testnet"""
        differences = {
            'execution_differences': {
                'testnet': {
                    'slippage': '0% (simulato)',
                    'latency': '0ms (locale)',
                    'fill_rate': '100% (garantito)',
                    'market_impact': '0% (nessun impatto)',
                    'liquidity': 'Infinita (simulata)'
                },
                'mainnet': {
                    'slippage': f"{orderbook_data['spread_percent']:.3f}% + slippage dinamico",
                    'latency': '50-200ms (network + exchange)',
                    'fill_rate': '95-99% (dipende da liquidità)',
                    'market_impact': '0.01-0.1% per trade grandi',
                    'liquidity': f"${orderbook_data['bid_liquidity']:,.0f} bid / ${orderbook_data['ask_liquidity']:,.0f} ask"
                }
            },
            'price_differences': {
                'testnet': {
                    'price_source': 'Generato algoritmicamente',
                    'volatility': '15-25% (artificiale)',
                    'price_gaps': 'Controllati',
                    'market_hours': '24/7 simulato'
                },
                'mainnet': {
                    'price_source': 'Mercato reale',
                    'volatility': f"{abs(real_data['price_change_24h']):.2f}% (24h reale)",
                    'price_gaps': 'Naturali del mercato',
                    'market_hours': '24/7 reale con variazioni weekend'
                }
            },
            'fee_differences': {
                'testnet': {
                    'trading_fees': '0.1% simulato',
                    'withdrawal_fees': '0 (testnet)',
                    'funding_fees': 'Non applicabili',
                    'gas_fees': '0 (testnet)'
                },
                'mainnet': {
                    'trading_fees': '0.1% (Binance standard)',
                    'withdrawal_fees': '$25-50 (network fees)',
                    'funding_fees': '0.01-0.1% ogni 8h (futures)',
                    'gas_fees': 'Variabili (se DeFi)'
                }
            }
        }
        
        return differences
    
    def calculate_profit_impact(self, real_data, orderbook_data):
        """Calcola impatto sui profitti reali"""
        
        # Parametri attuali sistema mega-aggressivo
        current_avg_profit = 26.69  # USD per trade
        current_position_size = 350  # USD per trade
        current_win_rate = 100  # % (testnet)
        
        # Fattori di riduzione mainnet
        slippage_impact = orderbook_data['spread_percent'] / 100 if orderbook_data else 0.001
        latency_impact = 0.02  # 2% riduzione per latenza
        liquidity_impact = 0.01  # 1% riduzione per liquidità limitata
        market_impact = 0.005  # 0.5% per impatto mercato
        win_rate_reduction = 0.15  # 15% riduzione win rate
        
        # Calcoli realistici
        realistic_profit_per_trade = current_avg_profit * (1 - slippage_impact - latency_impact - liquidity_impact - market_impact)
        realistic_win_rate = current_win_rate * (1 - win_rate_reduction)
        
        # Profitto atteso reale
        expected_daily_trades = 20  # Stima realistica
        expected_daily_profit = realistic_profit_per_trade * expected_daily_trades * (realistic_win_rate / 100)
        
        impact_analysis = {
            'current_testnet': {
                'profit_per_trade': f"${current_avg_profit:.2f}",
                'win_rate': f"{current_win_rate}%",
                'daily_trades': "24+ (simulato)",
                'daily_profit': f"${current_avg_profit * 24:.2f}"
            },
            'expected_mainnet': {
                'profit_per_trade': f"${realistic_profit_per_trade:.2f}",
                'win_rate': f"{realistic_win_rate:.1f}%",
                'daily_trades': f"{expected_daily_trades}",
                'daily_profit': f"${expected_daily_profit:.2f}"
            },
            'reduction_factors': {
                'slippage_loss': f"{slippage_impact*100:.2f}%",
                'latency_loss': f"{latency_impact*100:.1f}%",
                'liquidity_loss': f"{liquidity_impact*100:.1f}%",
                'market_impact_loss': f"{market_impact*100:.2f}%",
                'win_rate_reduction': f"{win_rate_reduction*100:.0f}%",
                'total_profit_reduction': f"{(1 - realistic_profit_per_trade/current_avg_profit)*100:.1f}%"
            },
            'realistic_projections': {
                'daily_profit_range': f"${expected_daily_profit*0.7:.2f} - ${expected_daily_profit*1.3:.2f}",
                'monthly_profit_range': f"${expected_daily_profit*30*0.7:.0f} - ${expected_daily_profit*30*1.3:.0f}",
                'annual_roi_estimate': f"{(expected_daily_profit*365/1000)*100:.0f}% - {(expected_daily_profit*365*1.3/1000)*100:.0f}%"
            }
        }
        
        return impact_analysis
    
    def identify_risk_factors(self):
        """Identifica fattori di rischio mainnet"""
        risk_factors = {
            'technical_risks': [
                'Slippage su ordini grandi (>$500)',
                'Latenza network durante alta volatilità',
                'Partial fills su ordini market',
                'API rate limits durante picchi',
                'Disconnessioni temporanee exchange'
            ],
            'market_risks': [
                'Gap di prezzo durante weekend',
                'Bassa liquidità in orari asiatici',
                'Flash crashes improvvisi',
                'Manipolazione mercato su timeframe brevi',
                'Correlazione con mercati tradizionali'
            ],
            'operational_risks': [
                'Costi di transazione reali',
                'Tasse su capital gains',
                'Requisiti KYC/AML',
                'Limiti di withdrawal giornalieri',
                'Sicurezza fondi su exchange'
            ],
            'regulatory_risks': [
                'Cambiamenti regolamentari',
                'Restrizioni geografiche',
                'Reporting fiscale',
                'Compliance requirements',
                'Ban trading algoritmico'
            ]
        }
        
        return risk_factors
    
    def generate_recommendations(self):
        """Genera raccomandazioni per mainnet"""
        recommendations = {
            'immediate_actions': [
                'Ridurre position size iniziale al 15-20%',
                'Implementare stop-loss rigorosi',
                'Testare con capitale minimo ($100-500)',
                'Monitorare slippage reale per 1 settimana',
                'Configurare alerts per disconnessioni'
            ],
            'system_modifications': [
                'Aggiungere controllo spread bid-ask',
                'Implementare gestione partial fills',
                'Ridurre frequenza trading (ogni 2-5 minuti)',
                'Aggiungere filtri liquidità minima',
                'Implementare circuit breakers'
            ],
            'risk_management': [
                'Max 5% capitale per trade (vs 25% testnet)',
                'Stop-loss automatico a -2%',
                'Take-profit automatico a +3%',
                'Max 10 trade per giorno',
                'Pausa trading durante alta volatilità (>10%)'
            ],
            'monitoring_requirements': [
                'Dashboard real-time slippage',
                'Tracking fill rates',
                'Monitoring latenza API',
                'Alert su perdite consecutive',
                'Backup exchange configurato'
            ]
        }
        
        return recommendations
    
    def generate_detailed_report(self, analysis):
        """Genera report dettagliato"""
        print("\n📊 DATI MERCATO REALE ATTUALI")
        print("-" * 40)
        if analysis['market_data']:
            market = analysis['market_data']
            print(f"💰 Prezzo BTC: ${market['price']:,.2f}")
            print(f"📈 Variazione 24h: {market['price_change_24h']:+.2f}%")
            print(f"📊 Volume 24h: {market['volume_24h']:,.0f} BTC")
            print(f"🔺 High 24h: ${market['high_24h']:,.2f}")
            print(f"🔻 Low 24h: ${market['low_24h']:,.2f}")
        
        if analysis['orderbook']:
            orderbook = analysis['orderbook']
            print(f"\n📋 ORDERBOOK REALE")
            print(f"💵 Best Bid: ${orderbook['best_bid']:,.2f}")
            print(f"💵 Best Ask: ${orderbook['best_ask']:,.2f}")
            print(f"📏 Spread: ${orderbook['spread_absolute']:.2f} ({orderbook['spread_percent']:.3f}%)")
            print(f"💧 Liquidità Bid: ${orderbook['bid_liquidity']:,.0f}")
            print(f"💧 Liquidità Ask: ${orderbook['ask_liquidity']:,.0f}")
        
        print(f"\n🎯 IMPATTO PROFITTI REALI")
        print("-" * 40)
        profit = analysis['profit_impact']
        print("TESTNET (Attuale):")
        print(f"  💰 Profitto per trade: {profit['current_testnet']['profit_per_trade']}")
        print(f"  ✅ Win rate: {profit['current_testnet']['win_rate']}")
        print(f"  📊 Profitto giornaliero: {profit['current_testnet']['daily_profit']}")
        
        print("\nMAINNET (Stimato):")
        print(f"  💰 Profitto per trade: {profit['expected_mainnet']['profit_per_trade']}")
        print(f"  ✅ Win rate: {profit['expected_mainnet']['win_rate']}")
        print(f"  📊 Profitto giornaliero: {profit['expected_mainnet']['daily_profit']}")
        
        print(f"\n📉 FATTORI DI RIDUZIONE:")
        reduction = profit['reduction_factors']
        for factor, value in reduction.items():
            print(f"  • {factor.replace('_', ' ').title()}: {value}")
        
        print(f"\n🎯 PROIEZIONI REALISTICHE:")
        proj = profit['realistic_projections']
        for key, value in proj.items():
            print(f"  • {key.replace('_', ' ').title()}: {value}")
        
        print(f"\n⚠️ RACCOMANDAZIONI IMMEDIATE:")
        print("-" * 40)
        for i, action in enumerate(analysis['recommendations']['immediate_actions'], 1):
            print(f"{i}. {action}")
        
        # Salva report completo
        with open('testnet_vs_mainnet_analysis.json', 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        print(f"\n✅ Report completo salvato: testnet_vs_mainnet_analysis.json")

def main():
    """Funzione principale"""
    print("🔍 AurumBotX Testnet vs Mainnet Analysis")
    print("=" * 60)
    print("🎯 OBIETTIVO: Analizzare differenze trading reale")
    print("📊 FONTE: Dati live Binance API")
    print("💡 OUTPUT: Proiezioni realistiche e raccomandazioni")
    print("=" * 60)
    
    analyzer = TestnetMainnetAnalyzer()
    analysis = analyzer.analyze_testnet_vs_mainnet()
    
    if analysis:
        print("\n🎉 ANALISI COMPLETATA!")
        print("📄 Controlla il file testnet_vs_mainnet_analysis.json per dettagli completi")
    else:
        print("\n❌ ANALISI FALLITA!")
        print("💡 Controlla connessione internet e riprova")

if __name__ == "__main__":
    main()

