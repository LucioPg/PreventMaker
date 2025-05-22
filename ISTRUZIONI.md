# Istruzioni per PreventMaker

## Introduzione
PreventMaker è un'applicazione per la creazione di preventivi con un'interfaccia grafica intuitiva. Questo documento fornisce istruzioni dettagliate per l'installazione, l'utilizzo e la distribuzione dell'applicazione.

## Requisiti di Sistema
- Windows 11
- Se si utilizza il codice sorgente: Python 3.12 o superiore

## Installazione

### Opzione 1: Utilizzo dell'eseguibile
1. Scaricare l'eseguibile `PreventMaker.exe` dalla cartella `dist`
2. Fare doppio clic sull'eseguibile per avviare l'applicazione

### Opzione 2: Esecuzione dal codice sorgente
1. Assicurarsi di avere Python 3.12 o superiore installato
2. Installare le dipendenze:
   ```
   pip install -e .
   ```
3. Eseguire l'applicazione:
   ```
   python preventmaker.py
   ```

## Utilizzo dell'Applicazione

### Configurazione Iniziale
All'avvio dell'applicazione, si aprirà un wizard di configurazione che richiederà:
1. **Dati della società emittente**:
   - Nome società
   - Indirizzo completo
   - Telefono
   - Email
   - Partita IVA
   - Logo (opzionale)

2. **Dati del cliente**:
   - Nome cliente
   - Indirizzo completo
   - Telefono
   - Email
   - Partita IVA (opzionale)

3. **Termini e condizioni**:
   - Testo dei termini e condizioni
   - Aliquota IVA predefinita
   - Note aggiuntive
   - Nome dell'utente che prepara il documento

### Gestione dei Prodotti
- Utilizzare il pulsante "Aggiungi Prodotto" per inserire nuove righe nella tabella
- Per ogni prodotto, specificare:
  - Descrizione
  - Quantità
  - Prezzo unitario
  - Sconto (percentuale)
  - Aliquota IVA
- Il totale netto viene calcolato automaticamente
- Per rimuovere prodotti, selezionarli e cliccare su "Rimuovi Selezionati"

### Anteprima e Esportazione
- Cliccare su "Anteprima PDF" per visualizzare il preventivo prima di finalizzarlo
- Utilizzare "Esporta PDF" per salvare il preventivo come file PDF

### Salvataggio e Caricamento
- Cliccare su "Salva" per salvare il preventivo corrente (formato .prev)
- Cliccare su "Carica" per aprire un preventivo salvato in precedenza

### Modifica della Configurazione
- Utilizzare il pulsante "Configurazione" per modificare i dati della società, del cliente o i termini e condizioni

## Creazione dell'Eseguibile
Per creare l'eseguibile dell'applicazione:
1. Assicurarsi che tutte le dipendenze siano installate
2. Eseguire lo script di build:
   ```
   python build.py
   ```
3. L'eseguibile sarà disponibile nella cartella `dist`

## Risoluzione dei Problemi
Se si riscontrano problemi con l'applicazione:
1. Verificare che tutte le dipendenze siano installate correttamente
2. Eseguire il test dell'applicazione:
   ```
   python test_app.py
   ```
3. Controllare eventuali messaggi di errore nella console

## Struttura del Progetto
- `preventmaker.py`: File principale dell'applicazione
- `build.py`: Script per la creazione dell'eseguibile
- `test_app.py`: Script per testare l'applicazione
- `pyproject.toml`: Configurazione del progetto e dipendenze
- `README.md`: Documentazione del progetto
- `ISTRUZIONI.md`: Questo file di istruzioni

## Supporto
Per ulteriori informazioni o supporto, consultare la documentazione del progetto nel file README.md.