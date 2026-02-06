# Copyright (c) 2025 AurumBotX
# SPDX-License-Identifier: MIT

import subprocess
import time
import os
import sys

def start_component(name, command, cwd=None):
    """Avvia un componente come sottoprocesso e ne gestisce l'output."""
    print(f"Avvio del componente: {name} con il comando: {' '.join(command)}")
    # Usiamo shell=True solo se il comando richiede funzionalità shell, altrimenti è meglio evitarlo
    # Qui usiamo shell=False per maggiore sicurezza e controllo
    try:
        process = subprocess.Popen(command, cwd=cwd, stdout=sys.stdout, stderr=sys.stderr, preexec_fn=os.setsid)
        print(f"{name} avviato con PID: {process.pid}")
        return process
    except FileNotFoundError:
        print(f"ERRORE: Comando non trovato per {name}. Assicurarsi che sia installato e nel PATH.")
        return None
    except Exception as e:
        print(f"ERRORE durante l'avvio di {name}: {e}")
        return None

def main():
    # Elenco dei processi da avviare
    processes = []

    # 1. Motore di Trading (Core Engine)
    # Si assume che il motore di trading sia un processo a lunga esecuzione
    # che gestisce anche il bot Telegram e il monitoraggio (o li avvia internamente)
    trading_engine_command = ["python", "src/core/trading_engine_usdt.py"]
    processes.append(start_component("Motore di Trading", trading_engine_command))

    # 2. Dashboard Streamlit Moderna (Porta 8502)
    # Streamlit deve essere avviato con l'opzione --server.port
    streamlit_command = [
        "streamlit", "run", "src/dashboards/unified_dashboard_modern.py",
        "--server.port", "8502",
        "--server.address", "0.0.0.0",
        "--server.headless", "true"
    ]
    processes.append(start_component("Dashboard Streamlit", streamlit_command))

    # 3. Server Web PWA (Porta 8080)
    # Per servire i file statici della PWA, usiamo un server HTTP semplice di Python
    # che deve essere avviato dalla directory che contiene i file (es. web_interface)
    # Assumiamo che i file siano in /usr/src/app/src/web
    # Se il progetto usa un server web più complesso, questo comando andrà modificato.
    # Per semplicità, useremo un server HTTP base di Python (richiede Python 3.7+)
    # che serve i file dalla directory 'src/web'
    # Nota: SimpleHTTPServer non è adatto per la produzione, ma per il container Docker
    # è un buon placeholder. In produzione si userebbe Nginx o un server Flask/FastAPI
    # dedicato. Qui usiamo un server Python che serve i file statici.
    # Se il file index.html è in 'src/web', dobbiamo servire da lì.
    # Verifico la struttura: /home/ubuntu/AurumBotX/src/web/index.html
    # Quindi il server deve essere avviato da /usr/src/app/src/web
    # Usiamo un piccolo script Flask/FastAPI se non vogliamo aggiungere dipendenze.
    # Dato che non abbiamo Flask/FastAPI nelle dipendenze, usiamo un server HTTP base
    # e avviamo il processo dalla directory corretta.
    
    # Metodo 1: Server HTTP semplice di Python (richiede che la directory sia 'src/web')
    # web_server_command = [
    #     "python", "-m", "http.server", "8080"
    # ]
    # processes.append(start_component("Server Web PWA (8080)", web_server_command, cwd="src/web"))

    # Metodo 2: Se la PWA è solo HTML/CSS/JS, il server HTTP semplice è sufficiente.
    # Se il file index.html è in /home/ubuntu/AurumBotX/src/web/index.html
    # Eseguiamo il server dalla directory radice del progetto e specifichiamo la directory
    # da servire se possibile. Altrimenti, usiamo il metodo 1 e cambiamo la directory.
    # Usiamo il Metodo 1 e ci assicuriamo che la directory 'src/web' esista e contenga i file.
    # Se la directory è web_interface, cambiamo di conseguenza.
    # Dai file chiave: /home/ubuntu/AurumBotX/src/web/index.html.
    web_server_command = [
        "python", "-m", "http.server", "8080"
    ]
    processes.append(start_component("Server Web PWA (8080)", web_server_command, cwd="src/web"))


    # Filtra i processi che non sono stati avviati correttamente (None)
    running_processes = [p for p in processes if p is not None]

    if not running_processes:
        print("Nessun componente è stato avviato. Uscita.")
        return

    print("\nTutti i componenti sono stati avviati. Il sistema è ora operativo.")
    print("Premi Ctrl+C per terminare tutti i processi.")

    try:
        # Loop infinito per mantenere lo script principale in esecuzione
        while True:
            time.sleep(1)
            # Controllo di base per vedere se qualche processo è terminato inaspettatamente
            for p in running_processes:
                if p.poll() is not None:
                    print(f"ATTENZIONE: Il processo con PID {p.pid} è terminato con codice {p.returncode}.")
                    # Qui si potrebbe implementare una logica di riavvio
                    running_processes.remove(p)
                    if not running_processes:
                        print("Tutti i processi sono terminati. Uscita.")
                        return

    except KeyboardInterrupt:
        print("\nRicevuto Ctrl+C. Terminazione di tutti i processi in corso...")
    finally:
        for p in running_processes:
            try:
                # Invia un segnale di terminazione (SIGTERM)
                os.killpg(os.getpgid(p.pid), 15)
            except Exception as e:
                print(f"Errore durante la terminazione del processo {p.pid}: {e}")
        
        # Attendiamo la terminazione dei processi per un breve periodo
        time.sleep(5)
        
        # Uccidi i processi che non sono terminati (SIGKILL)
        for p in running_processes:
            if p.poll() is None:
                try:
                    os.killpg(os.getpgid(p.pid), 9)
                    print(f"Processo {p.pid} terminato forzatamente.")
                except Exception as e:
                    print(f"Errore durante la terminazione forzata del processo {p.pid}: {e}")
        
        print("Uscita da start_aurumbotx.py.")

if __name__ == "__main__":
    main()
