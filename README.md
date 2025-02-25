# AurumBotX

## Avvio del Bot

Per avviare il bot, esegui il seguente comando nel terminale:

```sh
sh start_bot.sh
```

Questo comando avvierà l'interfaccia Streamlit, il Trading Bot e il System Monitor.

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

# 🚨 Errori Critici da Risolvere

## Errori di Alta Priorità

### 1. Errori Database
- [ ] Gestione delle connessioni fallite al database
- [ ] Implementare retry con backoff esponenziale per le query fallite
- [ ] Aggiungere pool di connessioni configurabile
- [ ] Monitoraggio dello stato delle connessioni

### 2. Errori AI Trading
- [ ] Errore: `module 'pandas' has no attribute 'isinf'`
  ```
  utils.ai_trading - ERROR - Errore nell'estrazione metriche: module 'pandas' has no attribute 'isinf'
  ```
- [ ] Gestione errori OpenAI API (quota exceeded)
- [ ] Validazione previsioni non valide
- [ ] Retry automatico per analisi di mercato fallite

### 3. Errori Integrazione API
- [ ] Gestione errori Reddit API (400 HTTP response)
- [ ] Riautenticazione automatica per API scadute
- [ ] Implementare fallback per sentiment analysis
- [ ] Validazione risposte API

### 4. Errori Predizione
```
utils.prediction_model - ERROR - Error preparing features: 'Close'
utils.prediction_model - ERROR - Training error: 'Close'
```
- [ ] Correzione preparazione features
- [ ] Validazione dati di training
- [ ] Gestione errori durante il training
- [ ] Implementare modello di fallback

## Soluzioni Implementate
✅ Retry intelligente per connessioni database
✅ Backoff esponenziale per riconnessioni
✅ Validazione ambiente di test
✅ Logging migliorato

## Note Importanti
- I log mostrano errori ricorrenti nell'analisi del sentiment
- Le previsioni falliscono frequentemente per dati mancanti
- La gestione delle connessioni necessita ottimizzazione
- È necessario implementare un sistema di monitoring più robusto

## Prossimi Passi
1. Implementare metriche di monitoraggio delle connessioni
2. Aggiungere supporto per connection pooling configurabile
3. Creare dashboard per monitoraggio dello stato delle connessioni
4. Implementare sistema di notifiche per problemi di connessione persistenti

## Log di Riferimento
```
2025-02-17 23:18:27,626 - utils.prediction_model - ERROR - Error preparing features: 'Close'
2025-02-17 23:18:27,626 - utils.prediction_model - ERROR - Training error: 'Close'
2025-02-17 23:18:27,626 - utils.prediction_model - ERROR - Error preparing training data: 'Close'