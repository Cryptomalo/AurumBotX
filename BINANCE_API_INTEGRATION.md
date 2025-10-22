
# 🔄 Integrazione API Binance e Calcolo Costi di Trading

**Data:** 30 Settembre 2025

**Autore:** Manus AI

## 🎯 OBIETTIVO

Questa fase si concentra sull'integrazione delle API reali di Binance per il trading live e sull'implementazione di un sistema accurato per il calcolo dei costi di transazione, includendo spread, commissioni e slippage. L'obiettivo è rendere il sistema pronto per operare in un ambiente di mercato reale, con una gestione dei costi trasparente e realistica.

## 🛠️ Integrazione API Binance

L'integrazione con Binance avverrà attraverso la libreria ufficiale `python-binance`. Le API key (API Key e Secret Key) verranno gestite in modo sicuro tramite un file `.env` per evitare di esporle nel codice sorgente.

### Passi per l'integrazione:

1.  **Installazione della libreria:**

    ```bash
    pip install python-binance
    ```

2.  **Gestione delle API Key:**

    Creazione di un file `.env.mainnet` nella root del progetto con il seguente formato:

    ```
    BINANCE_API_KEY=la_tua_api_key
    BINANCE_SECRET_KEY=la_tua_secret_key
    ```

3.  **Modifica del `BinanceAdapter`:**

    Il file `src/exchanges/binance_adapter.py` verrà aggiornato per utilizzare le API key e interagire con l'exchange reale. Verranno implementate le seguenti funzionalità:

    *   Ottenere il saldo dell'account.
    *   Recuperare i prezzi dei ticker in tempo reale.
    *   Inviare ordini di acquisto e vendita (MARKET, LIMIT).
    *   Verificare lo stato degli ordini.
    *   Ottenere lo storico dei trade.

## 💰 Calcolo dei Costi di Transazione

Per una simulazione realistica e un trading live profittevole, è fondamentale calcolare accuratamente tutti i costi associati a ogni operazione.

### 1. Commissioni (Fees)

Binance applica commissioni su ogni trade. Queste verranno recuperate dinamicamente tramite l'API e applicate a ogni operazione. Inizialmente, si considererà il livello di commissione base (0.1% per maker e taker), con la possibilità di adeguarlo in base al volume di trading e al possesso di BNB.

### 2. Spread

Lo spread è la differenza tra il prezzo di acquisto (ask) e il prezzo di vendita (bid) di un asset. Verrà calcolato in tempo reale utilizzando i dati del book degli ordini (order book) per determinare il costo effettivo di entrata e uscita da una posizione.

### 3. Slippage

Lo slippage si verifica quando un ordine viene eseguito a un prezzo diverso da quello previsto, a causa della volatilità del mercato. Per mitigare e calcolare lo slippage, verranno implementate le seguenti strategie:

*   **Utilizzo di ordini LIMIT:** Privilegiare l'uso di ordini LIMIT per avere un maggiore controllo sul prezzo di esecuzione.
*   **Monitoraggio della volatilità:** Evitare di operare in momenti di alta volatilità, se non specificamente richiesto dalla strategia.
*   **Calcolo post-trade:** Dopo ogni operazione, confrontare il prezzo di esecuzione effettivo con il prezzo richiesto per calcolare lo slippage e registrarlo per analisi future.

## 📝 Aggiornamento del Trading Engine

Il `TradingEngineUSDT` verrà modificato per integrare il calcolo dei costi. Ogni operazione di trading includerà:

*   Il costo delle commissioni.
*   Una stima dello spread al momento dell'ordine.
*   Il calcolo dello slippage a operazione conclusa.

Questi dati verranno salvati nel database insieme a ogni trade, permettendo un'analisi dettagliata delle performance e dei costi operativi.

## ✅ VANTAGGI

*   **Trading Live:** Il bot sarà in grado di operare con denaro reale su Binance.
*   **Performance Realistiche:** Le metriche di performance rifletteranno i costi reali del trading.
*   **Gestione del Rischio Migliorata:** Una stima accurata dei costi permette una gestione del rischio più precisa.
*   **Trasparenza:** Tutti i costi saranno tracciati e disponibili per l'analisi.

## ➡️ PROSSIMI PASSI

1.  **Implementazione del codice:** Scrivere il codice per l'integrazione dell'API di Binance e il calcolo dei costi.
2.  **Test in ambiente simulato:** Testare le nuove funzionalità in un ambiente di paper trading per verificare la correttezza dei calcoli.
3.  **Test con capitale ridotto:** Eseguire i primi trade live con un capitale minimo per validare il sistema in condizioni di mercato reali.

