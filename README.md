# PreventMaker
Una semplice interfaccia grafica per poter creare preventivi velocemente e facilmente!

## Descrizione progetto
Il software eseguibile per Windows 11 è stato creato a partire da codice python il quale implementa l'interfaccia grafica
attraverso la libreria PyQt.

## Punti salienti

- Possibilità di configurare i campi in maniera veloce e semplice attraverso un wizard:
  - Società emittente (Logo o nome, o logo e nome), compresi tutti i dati di intestazione:
    - indirizzo completo
    - telefono
    - email
    - partita iva
  - Cliente destinatario:
    - indirizzo completo
    - telefono
    - email
    - partita iva (eventuale)
  - Termini e condizioni
  - Corrispettivo IVA
  - Nome utente che ha preparato il documento
- Aggiunta dinamica delle righe nella tabella dei prodotti tramite comodo pulsante "Aggiungi Prodotto"
- Calcolo automatico di iva per riga di prodotto, sulla base del prezzo unitario
- Calcolo automatico del valore netto per ogni riga di prodotto, sulla base del prezzo unitario per la quantità meno lo sconto
- Calcolo automatico di percentuali di "totale netto", "totale iva" e "totale ivato" (totale ivato = netto + iva)
- Pulsante per eventuale aggiunta di note sotto la tabella dei prodotti, sopra il box "Termini e Condizioni", prelevati dalla configurazione
- Possibilità di visualizzare anteprima del pdf prima di completare la compilazione
- Possibilità di Salvare e Caricare un preventivo
- Path dell'output selezionabile
- Possibilità di creazione di diverse configurazioni, successivamente selezionabile
- Sistema di avvisi per domandare se si vuole salvare il preventivo, qualora fosse stato modificato, prima di chiudere l'applicazione

### Descrizione Tabella Prodotti
Ogni prodotto aggiunto al preventivo deve corrispondere a una nuova riga della tabella contente le seguenti colonne:
1. "Codice art.", usare come default il numero della riga partendo da 1 ( stringa ) 
2. "Descrizione", ( stringa )
3. "Disponibile", default "Sì", in alternativa deve essere selezionabile "Ordinabile", tuttavia il tipo di valore sottostante è di tipo booleano ( bool )
4. "Qnt.", indica la quantità, default 1 ( intero )
5. "U.M.", indica l'unità di misura del singolo prodotto, default "PZ", possibili scelte sono (PZ, KG, MT, CM, MM, CF, RS, CT, ES)
6. "Prezzo Unt.", indica il prezzo unitario del prodotto, ( float )
7. "Sconto", indica lo sconto percentuale ( float )
8. "Valore", indica il valore netto sulla base del prezzo unitario per la quantità meno lo sconto, ( float )
I campi "Prezzo Unt." e "Valore" devono essere rappresentati con il simbolo della valuta dell'euro ( € ) 
## Salvataggio e Caricamento dei preventivi
I preventivi possono essere conservati in un database Sqlite3.

## Creazione del file eseguibile per Windows
Per creare il file eseguibile per Windows, è stato utilizzato PyInstaller, uno strumento che consente di impacchettare applicazioni Python in un singolo file eseguibile. Il processo di creazione dell'eseguibile è gestito dallo script `build.py` incluso nel progetto.

### Requisiti
- Python 3.12 o superiore
- Tutte le dipendenze elencate in pyproject.toml

### Procedura
1. Assicurarsi che tutte le dipendenze siano installate:
   ```
   pip install -e .
   ```

2. Eseguire lo script di build:
   ```
   python build.py
   ```

3. Al termine del processo, l'eseguibile sarà disponibile nella cartella `dist` con il nome `PreventMaker.exe`

L'eseguibile creato contiene tutte le dipendenze necessarie e può essere distribuito su qualsiasi sistema Windows 11 senza necessità di installare Python o altre librerie.

## Sistema di visualizzazione di anteprime
Il sistema di visualizzazione delle anteprime dei PDF è stato implementato utilizzando la libreria PyQt6-WebEngine, che fornisce un componente di visualizzazione web integrato nell'applicazione. Questo approccio offre diversi vantaggi:

### Funzionamento
1. Quando l'utente richiede un'anteprima del preventivo, l'applicazione genera un file PDF temporaneo utilizzando la libreria ReportLab
2. Il PDF viene quindi caricato in un componente QWebEngineView, che utilizza il motore di rendering di Chromium per visualizzare il documento
3. L'utente può visualizzare il PDF completo all'interno dell'applicazione, senza necessità di aprire programmi esterni

### Vantaggi
- Visualizzazione integrata nell'applicazione
- Supporto nativo per lo zoom, la navigazione e altre funzionalità di visualizzazione PDF
- Rendering di alta qualità grazie al motore Chromium
- Esperienza utente fluida e coerente

### Implementazione
La classe `PDFPreviewDialog` gestisce la visualizzazione dell'anteprima, creando una finestra di dialogo modale che contiene il visualizzatore PDF. Il componente QWebEngineView è configurato per abilitare il supporto ai plugin e il visualizzatore PDF integrato.

Questo sistema consente agli utenti di verificare l'aspetto finale del preventivo prima di salvarlo o esportarlo, garantendo che il documento rispetti le aspettative in termini di formattazione e contenuto.
