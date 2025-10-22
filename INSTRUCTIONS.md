#  instrucciones para la ejecución local

**Data:** 03 Ottobre 2025

**Autore:** Manus AI

## 🎯 OBIETTIVO

Questa guida ti permetterà di avviare il bot AurumBotX sul tuo computer locale per iniziare la fase di testing live di 7 giorni. Segui attentamente ogni passo.

### 1. **Decomprimi il Progetto**

-   Decomprimi il file `AurumBotX.zip` in una cartella a tua scelta (es. sul Desktop).

### 2. **Apri il Terminale (Command Prompt o PowerShell)**

-   **Windows:** Premi il tasto `Windows`, digita `cmd` o `powershell` e premi Invio.
-   **macOS/Linux:** Apri l'applicazione `Terminale`.

### 3. **Naviga nella Cartella del Progetto**

-   Usa il comando `cd` per spostarti nella cartella dove hai decompresso il progetto. Ad esempio:
    ```bash
    cd Desktop/AurumBotX
    ```

### 4. **Crea un Ambiente Virtuale (Consigliato)**

-   Questo passo isola le dipendenze del progetto. Esegui questi comandi:
    ```bash
    python -m venv venv
    ```
-   Attiva l'ambiente virtuale:
    -   **Windows:** `venv\Scripts\activate`
    -   **macOS/Linux:** `source venv/bin/activate`

### 5. **Installa le Dipendenze**

-   Con l'ambiente virtuale attivo, esegui questo comando per installare tutte le librerie necessarie:
    ```bash
    pip install -r requirements.txt
    ```

### 6. **Imposta le API Key di Binance**

-   Sostituisci `LA_TUA_API_KEY` e `LA_TUA_SECRET_KEY` con le tue chiavi reali.
    -   **Windows (cmd):**
        ```bash
        set BINANCE_API_KEY=LA_TUA_API_KEY
        set BINANCE_SECRET_KEY=LA_TUA_SECRET_KEY
        ```
    -   **Windows (PowerShell):**
        ```bash
        $env:BINANCE_API_KEY="LA_TUA_API_KEY"
        $env:BINANCE_SECRET_KEY="LA_TUA_SECRET_KEY"
        ```
    -   **macOS/Linux:**
        ```bash
        export BINANCE_API_KEY='LA_TUA_API_KEY'
        export BINANCE_SECRET_KEY='LA_TUA_SECRET_KEY'
        ```

### 7. **Avvia il Bot!**

-   Ora sei pronto per avviare il bot. Esegui questo comando:
    ```bash
    python start_live_testing.py
    ```

-   Se tutto è corretto, vedrai un messaggio di conferma dell'avvio del bot. Lascia la finestra del terminale aperta, in quanto il bot opererà in background.

## 📊 Monitoraggio

-   Puoi monitorare l'attività del bot avviando la dashboard unificata. Apri un **nuovo terminale**, naviga nella cartella del progetto, attiva l'ambiente virtuale e lancia questo comando:
    ```bash
    streamlit run src/dashboards/aurumbotx_unified_dashboard.py
    ```
-   Apri il browser all'indirizzo che ti verrà mostrato nel terminale (di solito `http://localhost:8501`).

## 🛑 Fermare il Bot

-   Per fermare il bot, torna alla finestra del terminale in cui lo hai avviato e premi `Ctrl+C`.

--- 

Se riscontri qualsiasi problema, non esitare a chiedere. Buon trading.
