# AurumBot - Configurazione Telegram

## 🤖 Informazioni Bot
- Username Bot: `@aurum_crypto_bot`
- Canale Segnali: https://t.me/aurum_signals

## 📋 Istruzioni Configurazione API
1. Vai su https://my.telegram.org/auth e accedi
2. Clicca su 'API Development Tools'
3. Crea una nuova applicazione con questi dati:
   - App title: AurumBot
   - Short name: aurum_bot
   - Platform: Desktop
   - Description: Crypto trading bot for monitoring and analysis
4. Copia l'api_id (numero) e api_hash (stringa) che ricevi
5. Inserisci questi valori nelle variabili d'ambiente:
   - TELEGRAM_API_ID
   - TELEGRAM_API_HASH

## 🔌 Requisiti
- Python 3.11 o superiore
- Librerie necessarie:
  - telethon
  - streamlit
  - qrcode
  - pillow

## 🚀 Avvio
1. Assicurati che le credenziali API siano configurate nelle variabili d'ambiente
2. Avvia l'applicazione Streamlit:
   ```bash
   streamlit run app.py
   ```
3. Naviga alla pagina "Telegram Scanner" nel menu

## 📊 Funzionalità
- Monitoraggio canali Telegram per crypto trending
- Analisi sentiment dei messaggi
- Rilevamento nuove crypto e meme coins
- Tracking menzioni e engagement

## 🔍 Note Importanti
- Il bot deve essere autorizzato tramite credenziali API prima dell'uso
- Il monitoraggio inizia solo dopo la configurazione completa
- I dati vengono aggiornati in tempo reale durante la scansione
