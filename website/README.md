# AurumBotX Website

Sito web ufficiale della piattaforma di trading algoritmico AurumBotX.

## Descrizione

Questo è il sito web landing page per AurumBotX, una piattaforma enterprise di trading algoritmico progettata per operare in modo stabile e affidabile con intelligenza artificiale che adatta dinamicamente le strategie in base ai dati di mercato in tempo reale.

## Focus del Progetto

**AurumBotX** si concentra su:
- **Stabilità del Sistema**: 99.2% uptime garantito 24/7
- **Trading Automatico**: Esecuzione automatica con gestione del rischio avanzata
- **Strategie Algoritmiche**: Strategie create e testate per la stabilità
- **AI Adattiva**: 327 modelli AI che modificano le strategie in base ai dati di mercato
- **Controllo Totale**: Pieno controllo su parametri, strategie e decisioni

## Struttura dei File

```
website/
├── index.html          # Pagina principale
├── css/
│   └── styles.css      # Stili CSS
├── js/
│   └── main.js         # JavaScript per interattività
└── README.md           # Questo file
```

## Sezioni del Sito

1. **Navigation** - Barra di navigazione sticky con link alle sezioni
2. **Hero Section** - Introduzione al trading algoritmico adattivo
3. **Features** - 6 caratteristiche principali di AurumBotX
4. **Dashboards** - Le tre interfacce integrate (Web PWA, Streamlit, Telegram)
5. **Interfaces** - Tabella comparativa delle interfacce
6. **Performance** - Metriche di stabilità (Uptime, Max Drawdown, Sharpe Ratio, Strategia AI)
7. **Roadmap** - Timeline di sviluppo in 5 fasi
8. **Deployment** - Pipeline di deployment enterprise
9. **Advantages** - 6 vantaggi competitivi vs competitor
10. **CTA** - Call-to-action finale
11. **Footer** - Link utili e informazioni

## Design

- **Palette di Colori**:
  - Primario: #1A3A52 (blu scuro)
  - Secondario: #2E7D32 (verde)
  - Accento: #F57C00 (arancione)

- **Font**: Inter (Google Fonts)
- **Layout**: Responsive e mobile-friendly
- **Animazioni**: Fade-in, scroll effects, parallax

## Tecnologie Utilizzate

- HTML5
- CSS3 (Grid, Flexbox)
- JavaScript (Vanilla)
- Font Awesome (icone)
- Google Fonts (Inter)

## Come Visualizzare

### Localmente
```bash
# Aprire il file index.html in un browser
open index.html
# o
firefox index.html
# o
chrome index.html
```

### Con un Server Locale
```bash
# Usando Python 3
python -m http.server 8000

# Usando Node.js
npx http-server

# Usando Live Server (VS Code)
# Installa l'estensione Live Server e clicca "Go Live"
```

Poi accedi a `http://localhost:8000` nel tuo browser.

## Funzionalità JavaScript

- **Smooth Scrolling**: Navigazione fluida tra le sezioni
- **Scroll Effects**: Effetti visivi durante lo scroll
- **Intersection Observer**: Animazioni fade-in quando gli elementi entrano in vista
- **Counter Animation**: Animazione dei numeri nella hero section
- **Parallax Effect**: Effetto parallax nella hero section
- **Active Navigation**: Evidenziazione del link di navigazione attivo

## Responsive Design

Il sito è completamente responsive e si adatta a:
- Desktop (1200px+)
- Tablet (768px - 1199px)
- Mobile (< 768px)

## Performance

- Caricamento veloce con CSS e JS minimali
- Nessuna dipendenza da framework pesanti
- Immagini ottimizzate (usando icone SVG di Font Awesome)
- Lazy loading per le animazioni

## SEO

- Meta tags per descrizione e keywords
- Heading structure corretta (H1, H2, H3)
- Alt text per le icone
- Semantic HTML

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Deployment

Per deployare il sito:

1. **GitHub Pages**:
   ```bash
   # Copia i file nella cartella docs/ del repository
   cp -r website/* docs/
   # Abilita GitHub Pages dalle impostazioni del repository
   ```

2. **VPS/Server**:
   ```bash
   # Copia i file sul server
   scp -r website/ user@server:/var/www/aurumbotx/
   
   # Configura un web server (Nginx/Apache)
   # Punti la root a /var/www/aurumbotx/
   ```

3. **Docker**:
   ```dockerfile
   FROM nginx:alpine
   COPY website/ /usr/share/nginx/html/
   EXPOSE 80
   ```

## Manutenzione

Per aggiornare il sito:

1. Modifica i file HTML, CSS, JS
2. Testa localmente
3. Commit e push su GitHub
4. Deploy automatico (se configurato)

## Link Utili

- [GitHub Repository](https://github.com/Cryptomalo/AurumBotX)
- [Documentazione Completa](https://github.com/Cryptomalo/AurumBotX/blob/main/AURUMBOTX_ENTERPRISE_DOCUMENTATION.md)
- [Issues & Bug Reports](https://github.com/Cryptomalo/AurumBotX/issues)

## Licenza

Vedi il file LICENSE nel repository principale.

## Contatti

Per domande o suggerimenti, apri un issue su GitHub.

---

**Versione**: 2.0  
**Data**: Ottobre 2025  
**Progetto**: AurumBotX - Trading Algoritmico Stabile e Adattivo

