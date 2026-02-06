# AurumBotX - Repo Health Check (2025-09-XX)

## ✅ Fixes applied in this pass
- Normalizzato `.env.example` per usare `BINANCE_SECRET_KEY` e includere variabili DB/AI coerenti con la documentazione di setup. 【F:.env.example†L1-L22】
- Aggiornata la sezione **Testing** della README con script effettivamente presenti nel repo. 【F:README.md†L226-L237】
- Rimosse variabili hardcoded e aggiunte verifiche di configurazione in `start_bot.sh`, con avvio dashboard/monitor condizionale ai file presenti. 【F:start_bot.sh†L1-L29】
- Rimossi settaggi hardcoded in `monitor_24_7.py` e reso il path di progetto dinamico. 【F:monitor_24_7.py†L11-L23】
- Resi obbligatori gli env var per `restart_bot_with_api.py`, con avvio opzionale se il file `test_trading_1000_euro.py` non è presente. 【F:restart_bot_with_api.py†L15-L120】
- Rimosse API keys hardcoded e reso il path di progetto dinamico in `force_real_data_simple.py`. 【F:force_real_data_simple.py†L1-L104】
- Ripulito `force_real_data_setup.py` rimuovendo chiavi hardcoded, path assoluti e correzione della logica di setup con env vars. 【F:force_real_data_setup.py†L1-L260】

## ⚠️ Incongruenze e rischi ancora presenti
- `start_bot.sh` in origine puntava a `streamlit_app.py` e `utils/system_checkup.py` che non esistono; ora l’avvio è condizionale, ma i file mancanti restano da ripristinare o deprecate. 【F:start_bot.sh†L17-L29】
- `restart_bot_with_api.py` faceva riferimento a `test_trading_1000_euro.py` inesistente; ora è protetto ma il file resta mancante. 【F:restart_bot_with_api.py†L93-L114】
- Il repo include numerosi artefatti di rilascio/report (`*.pdf`, `*.tar.gz`, `*_REPORT.md`) che possono essere obsoleti o duplicati e aumentare il rumore del repository. (vedi root listing)

## 🔧 Raccomandazioni prioritarie
1. **Pulizia sicurezza**: verificare che non restino chiavi hardcoded in altri script o report storici (es. demo/setup legacy).
2. **Ripristino script mancanti**: decidere se `streamlit_app.py`, `utils/system_checkup.py`, `test_trading_1000_euro.py` vanno ricreati o rimossi definitivamente dalla documentazione/utility. 【F:start_bot.sh†L17-L29】【F:restart_bot_with_api.py†L93-L114】
3. **Normalizzazione percorsi**: verificare che gli script legacy non usino path assoluti residuali (oltre ai file già ripuliti).
4. **Audit artefatti**: spostare PDF/archivi in `reports/` o `releases/` e documentare quali sono correnti per evitare confusione.

## ✅ Prossimi step suggeriti (se vuoi che proceda)
- Verifica consistenza dei comandi di avvio tra `README.md`, `start_bot.sh`, `start_aurumbotx.sh`.
- Script di linting/check per trovare file referenziati ma mancanti.
