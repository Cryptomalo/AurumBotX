# Dockerfile di Produzione per AurumBotX
# Utilizza un'immagine base Python ufficiale
FROM python:3.11-slim

# Imposta la directory di lavoro nel container
WORKDIR /usr/src/app

# Copia il file requirements.txt e installa le dipendenze
# Utilizziamo un'installazione a più stadi per ottimizzare la dimensione dell'immagine finale
COPY requirements.txt .
# Installiamo i pacchetti necessari per fpdf2/reportlab e Pillow che potrebbero richiedere librerie di sistema
RUN apt-get update && apt-get install -y \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

# Copia il resto del codice sorgente
COPY . .

# Espone le porte necessarie per le interfacce web
# Streamlit moderno (8502) e Web PWA (8080)
EXPOSE 8502
EXPOSE 8080

# Variabili d'ambiente per la configurazione di produzione
ENV PYTHONUNBUFFERED 1
ENV AURUM_ENV production

# Comando di avvio del container
# Si assume che ci sia uno script di avvio principale per il sistema completo
CMD ["python", "start_aurumbotx.py"]
