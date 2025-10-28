# AurumBotX - Guida al Packaging Multi-Piattaforma

Questa guida illustra come creare un eseguibile stand-alone per AurumBotX utilizzando **PyInstaller**. L'eseguibile generato includerà tutti i componenti Python, le dipendenze e i file di dati necessari per eseguire il bot su Windows, macOS o Linux, a seconda del sistema operativo su cui viene eseguito PyInstaller.

## Prerequisiti

1.  **Python 3.x** installato.
2.  **PyInstaller** installato. A causa della complessità delle dipendenze (Streamlit, Plotly, ecc.), si consiglia vivamente di installare PyInstaller in un ambiente virtuale pulito:

    ```bash
    # 1. Crea e attiva un ambiente virtuale
    python -m venv venv
    source venv/bin/activate  # Su Linux/macOS
    # venv\Scripts\activate   # Su Windows

    # 2. Installa le dipendenze del progetto
    pip install -r requirements.txt

    # 3. Installa PyInstaller
    pip install pyinstaller
    ```

## Creazione dell'Eseguibile

Utilizzeremo il file di specifica `aurumbotx.spec` per istruire PyInstaller su come includere tutti i file necessari (inclusi i file web PWA, le configurazioni, ecc.).

1.  **Naviga nella directory principale del progetto:**

    ```bash
    cd /path/to/AurumBotX
    ```

2.  **Esegui PyInstaller con il file di specifica:**

    ```bash
    pyinstaller aurumbotx.spec
    ```

### Risultato

Dopo l'esecuzione, PyInstaller creerà due nuove directory: `build` e `dist`.

-   La directory `dist` conterrà la cartella `AurumBotX` che include l'eseguibile stand-alone (`AurumBotX.exe` su Windows, o semplicemente `AurumBotX` su Linux/macOS) e tutti i file di supporto.

### Distribuzione

Per la distribuzione, comprimi la cartella `AurumBotX` all'interno della directory `dist` (ad esempio, in un file ZIP o TGZ) e distribuiscila agli utenti finali.

**Nota Importante:** L'eseguibile deve essere eseguito dalla sua posizione originale all'interno della cartella `AurumBotX` (nella directory `dist`) per garantire che tutti i percorsi relativi ai file di dati e alle risorse siano corretti.

## Avvio dell'Eseguibile

L'eseguibile avvierà il sistema completo, come definito nello script `start_aurumbotx.py`, che include:

-   Motore di Trading (in background)
-   Dashboard Streamlit (Porta 8502)
-   Server Web PWA (Porta 8080)

Per avviare il bot, esegui semplicemente l'eseguibile:

```bash
# Su Linux/macOS
./dist/AurumBotX/AurumBotX

# Su Windows
.\dist\AurumBotX\AurumBotX.exe
```

Gli utenti dovranno configurare le loro variabili d'ambiente (API Key di Binance, Token Telegram, ecc.) prima dell'avvio, idealmente tramite un file `.env` nella stessa directory dell'eseguibile.

