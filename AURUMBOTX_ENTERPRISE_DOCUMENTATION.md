# AurumBotX - Documentazione Enterprise

**Autore:** Manus AI
**Versione:** 2.2 (Post-Analytics & Reporting)
**Data:** Ottobre 2025

## 1. Panoramica del Progetto

AurumBotX è un progetto di trading algoritmico di livello enterprise progettato per la crescita aggressiva del capitale, con l'obiettivo di trasformare **50 USDT in 600 USDT** attraverso il trading automatizzato sulla piattaforma Binance. Il sistema è costruito su un'architettura modulare e robusta, che privilegia la sicurezza, l'analisi avanzata e le interfacce utente professionali.

### 1.1 Caratteristiche Chiave

| Funzionalità | Descrizione | Riferimento Tecnico |
| :--- | :--- | :--- |
| **Motore di Trading** | Basato su SQLAlchemy per la gestione persistente dei dati e calcolo del costo reale (fee, slippage, spread). | `src/core/trading_engine_usdt.py` |
| **Interfacce Utente** | Dashboard Streamlit moderna (port 8502), Web PWA stand-alone (port 8080) e Telegram Bot per il controllo remoto. | `src/dashboards/`, `src/web/`, `src/automation/telegram/` |
| **Sicurezza** | Protocolli di sicurezza avanzati, inclusi **Emergency Stop** con doppia conferma e **Circuit Breaker** per la gestione automatica del rischio. | `SAFETY_PROTOCOLS.md` |
| **Analisi Avanzata** | Calcolo di metriche finanziarie chiave (Sharpe Ratio, Profit Factor, Max Drawdown) e generazione di report PDF professionali. | `src/analytics/`, `src/reporting/` |
| **Deployment** | Soluzione pronta per la produzione con containerizzazione Docker e script di deployment VPS. | `Dockerfile`, `docker-compose.yml`, `deploy_vps.sh` |

## 2. Guida al Deployment Enterprise (Docker/VPS)

Il metodo di deployment raccomandato per l'ambiente di produzione è tramite container Docker, che garantisce isolamento, riproducibilità e scalabilità.

### 2.1 Prerequisiti

È necessario un server virtuale privato (VPS) con **Docker** e **Docker Compose** installati.

### 2.2 Deployment Automatico (VPS)

Utilizzare lo script `deploy_vps.sh` per automatizzare l'installazione e l'avvio del bot.

1.  **Carica lo script:** Copia `deploy_vps.sh` sul tuo VPS.
2.  **Esegui lo script:**
    ```bash
    chmod +x deploy_vps.sh
    ./deploy_vps.sh
    ```
    Lo script si occuperà di:
    *   Aggiornare il sistema.
    *   Installare Docker e Docker Compose (se mancanti).
    *   Clonare il repository AurumBotX.
    *   Creare un file `.env` per la configurazione iniziale.
    *   Avviare il container tramite `docker-compose up --build -d`.

### 2.3 Configurazione Variabili d'Ambiente

Prima di avviare il container, **è fondamentale** modificare il file `.env` generato nella directory principale del progetto (`AurumBotX/.env`) con le credenziali reali:

| Variabile | Descrizione | Esempio |
| :--- | :--- | :--- |
| `BINANCE_API_KEY` | Chiave API HMAC di Binance per il trading. | `AKJSDH78923HJSAD8923` |
| `BINANCE_SECRET_KEY` | Chiave segreta API di Binance. | `a8sd9a8sd9a8sd9a8sd9a8sd9a8sd9a8sd9a8sd9` |
| `TELEGRAM_BOT_TOKEN` | Token del bot Telegram per il controllo remoto. | `123456:ABC-DEF1234ghIkl-jkl` |
| `TELEGRAM_CHAT_ID` | ID della chat Telegram per ricevere notifiche e comandi. | `-123456789` |
| `DATABASE_URL` | URL di connessione al database (SQLite di default). | `sqlite:///data/trading_engine.db` |
| `AURUM_ENV` | Ambiente di esecuzione (impostato su `production` nel container). | `production` |

### 2.4 Gestione del Container

*   **Avvio:** `docker-compose up -d`
*   **Arresto:** `docker-compose down`
*   **Log:** `docker-compose logs -f`
*   **Stato:** `docker-compose ps`

## 3. Manuale Utente e Interfacce

AurumBotX offre tre interfacce per il monitoraggio e il controllo:

### 3.1 Dashboard Streamlit Moderna (Porta 8502)

Accessibile tramite `http://<IP_VPS>:8502`. Questa dashboard unificata offre:
*   Visualizzazioni interattive Plotly.
*   Metriche di performance in tempo reale (Sharpe, Max Drawdown).
*   Sezione di configurazione e stato del sistema.

### 3.2 Web PWA Stand-Alone (Porta 8080)

Accessibile tramite `http://<IP_VPS>:8080`. Questa interfaccia è progettata come una Progressive Web App (PWA) per l'accesso mobile e la visualizzazione dello stato essenziale del bot.

### 3.3 Bot Telegram Avanzato

Il bot Telegram consente il controllo remoto e la ricezione di notifiche in tempo reale. I comandi principali includono:

| Comando | Descrizione |
| :--- | :--- |
| `/status` | Stato attuale del bot e del conto. |
| `/stop_trading` | **Emergency Stop** - Arresta immediatamente il trading (richiede doppia conferma). |
| `/start_trading` | Riavvia il motore di trading. |
| `/performance` | Report rapido sulle metriche di performance. |
| `/report_pdf` | Genera e invia il report PDF completo. |
| `/update_check` | Controlla la disponibilità di aggiornamenti. |
| `/config` | Visualizza la configurazione di trading attiva. |

## 4. Analisi e Reporting

Il modulo di analisi avanzata calcola automaticamente le performance del bot.

### 4.1 Metriche Chiave

*   **Sharpe Ratio:** Misura il rendimento corretto per il rischio.
*   **Profit Factor:** Rapporto tra profitto lordo e perdita lorda.
*   **Max Drawdown:** La massima perdita osservata dal picco al minimo.

### 4.2 Generazione Report PDF

Il comando `/report_pdf` del bot Telegram, o la funzione equivalente nella dashboard Streamlit, attiva la generazione di un report PDF professionale (`src/reporting/performance_report_generator.py`) che riassume l'attività di trading e le metriche di performance.

## 5. Pipeline CI/CD (GitHub Actions)

Il progetto include una pipeline di Integrazione Continua e Distribuzione Continua (CI/CD) per garantire la qualità del codice e automatizzare il deployment.

*   **File:** `.github/workflows/main.yml`
*   **Funzionamento:** Ad ogni push sui branch `main` o `develop`, la pipeline esegue:
    1.  **Build & Test:** Linting (`flake8`) e test unitari/integrazione (`pytest`).
    2.  **Docker Build & Push:** Se il test ha successo e il push è sul branch `main`, l'immagine Docker viene costruita e caricata su Docker Hub.
    3.  **Notifica:** Viene inviata una notifica Telegram al canale di deployment.

## 6. Packaging Stand-Alone

Per gli utenti che preferiscono eseguire il bot come un'applicazione desktop nativa (Windows, macOS, Linux), è possibile creare un eseguibile stand-alone utilizzando **PyInstaller**.

*   **Riferimento:** Consultare il file `PACKAGING.md` per le istruzioni dettagliate sulla creazione dell'eseguibile.
*   **File di Specifica:** `aurumbotx.spec` è preconfigurato per includere tutte le dipendenze complesse (Streamlit, Plotly, ecc.) e i file di risorse.

---
**NOTA:** Questo sistema è pronto per il periodo di testing live di 7 giorni con 50 USDT. Assicurarsi che tutte le chiavi API siano valide e che il conto Binance sia configurato correttamente prima dell'avvio.

