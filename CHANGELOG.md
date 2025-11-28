# AurumBotX Changelog

## [4.1.0] - 2025-11-27 - Hyperliquid Production

### Added
- **Hyperliquid Testnet Integration**: Bot completamente riscritto per usare Hyperliquid Testnet API.
- **Oracle Cloud Deployment**: Script e guide per deployment su Oracle Cloud Always Free.
- **Systemd Integration**: Service e timer per esecuzione 24/7 affidabile.
- **Virtual Environment**: Setup con `venv` per gestione dipendenze.
- **Documentazione Completa**: Guide dettagliate per deployment, quick start, e summary.

### Changed
- **Architettura**: Da `while True` loop a `oneshot` systemd service.
- **Exchange**: Da MEXC a Hyperliquid Testnet.
- **Parametri**: Cicli ogni 1 ora, confidence 60%, max 12 trade/giorno.
- **README.md**: Completamente riscritto per Hyperliquid.

### Removed
- **Codice Obsoleto**: Rimossi tutti i wallet runner e configurazioni per MEXC.
- **Statistiche Obsolete**: Rimossi vecchi log e file di stato.
- **Documentazione Obsoleta**: Rimossa documentazione relativa a MEXC e sandbox.

---

## [3.6.0] - 2025-11-17

- Added: Live paper trading con dati reali da MEXC.
- Added: AI-powered analysis con OpenAI GPT-4.
- Added: Bear market filter.
- Fixed: Bug timing cicli con keep-alive anti-ibernazione.

## [3.5.0] - 2025-11-14

- Changed: Cicli ogni 4.5 ore, confidence 75%, take profit 8%.
- Changed: Holding dinamico fino a 24 ore.
- Added: Limite trade giornaliero (6).

## [3.0.0] - 2025-11-12

- Added: Strategia Chameleon con 3 livelli (TURTLE, RABBIT, EAGLE).
- Added: Paper trading demo mode.
- Initial release.
