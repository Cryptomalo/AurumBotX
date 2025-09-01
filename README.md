# AurumBotX

Questo repository contiene il codice per AurumBotX, un bot di trading e la sua dashboard Streamlit.

## Avvio Rapido

Segui questi passaggi per avviare il progetto localmente:

1.  **Clona il repository:**
    ```bash
    git clone https://github.com/Cryptomalo/AurumBotX
    cd AurumBotX
    ```

2.  **Installa le dipendenze:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Avvia la dashboard Streamlit:**
    ```bash
    streamlit run streamlit_app.py
    ```

    L'applicazione dovrebbe aprirsi automaticamente nel tuo browser. Se non lo fa, copia l'URL fornito nel terminale (solitamente `http://localhost:8501`).

## Database

Il bot e la dashboard utilizzano un database SQLite locale (`aurumbotx_trading.db`) che viene creato automaticamente se non esiste. I dati di trading verranno letti da questo file. Non è necessaria alcuna configurazione aggiuntiva del database per l'avvio rapido.

**Nota:** I processi di trading del bot e l'accesso alla dashboard sono separati. L'accesso alla dashboard non interromperà le operazioni di trading in corso.

## Contribuzione

Per contribuire al progetto, clona il repository, crea un nuovo branch per le tue modifiche e apri una Pull Request.

---

**Nota per gli sviluppatori:**

Le modifiche recenti hanno semplificato la configurazione del database per l'uso di SQLite. Se si desidera utilizzare PostgreSQL, è possibile impostare la variabile d'ambiente `DATABASE_URL` prima di avviare l'applicazione:

```bash
export DATABASE_URL="postgresql://user:password@host:port/database_name"
streamlit run streamlit_app.py
```

Assicurarsi che il server PostgreSQL sia in esecuzione e accessibile con le credenziali fornite.


