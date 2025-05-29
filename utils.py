import json
import os
import re
import sqlite3
from constants import DB_FILE_NAME, DEFAULT_NOTE
import hashlib
import base64
from datetime import datetime

def save_configuration(name, config):
    """Salva una configurazione nel database"""
    conn = sqlite3.connect(DB_FILE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT OR REPLACE INTO company_configurations 
        (name, company_name, company_address, company_phone, company_email, company_vat_code, 
        company_logo, terms, vat_rate, notes, prepared_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name,
            config.get('company_name', ''),
            config.get('company_address', ''),
            config.get('company_phone', ''),
            config.get('company_email', ''),
            config.get('company_vat_code', ''),
            config.get('company_logo', ''),
            config.get('terms', ''),
            config.get('vat_rate', '22%'),
            config.get('notes', ''),
            config.get('prepared_by', '')
        ))

        conn.commit()
        return True
    except Exception as e:
        print(f"Errore nel salvataggio della configurazione: {str(e)}")
        return False
    finally:
        conn.close()


def load_configuration(name):
    """Carica una configurazione dal database"""
    conn = sqlite3.connect(DB_FILE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute('''
        SELECT company_name, company_address, company_phone, company_email, company_vat_code,
               company_logo, terms, vat_rate, notes, prepared_by
        FROM company_configurations
        WHERE LOWER(name) = LOWER(?)
        ''', (name,))

        row = cursor.fetchone()
        if row:
            config = {
                'company_name': row[0],
                'company_address': row[1],
                'company_phone': row[2],
                'company_email': row[3],
                'company_vat_code': row[4],
                'company_logo': row[5],
                'terms': row[6],
                'vat_rate': row[7],
                'notes': row[8],
                'prepared_by': row[9]
            }
            return config
        return None
    except Exception as e:
        print(f"Errore nel caricamento della configurazione: {str(e)}")
        return None
    finally:
        conn.close()


def get_configuration_names():
    """Restituisce la lista dei nomi delle configurazioni salvate"""
    conn = sqlite3.connect(DB_FILE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT name FROM company_configurations ORDER BY name')
        names = [row[0] for row in cursor.fetchall()]
        return names
    except Exception as e:
        print(f"Errore nel recupero delle configurazioni: {str(e)}")
        return []
    finally:
        conn.close()


def delete_configuration(name):
    """Elimina una configurazione dal database"""
    conn = sqlite3.connect(DB_FILE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM company_configurations WHERE LOWER(name) = LOWER(?)', (name,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore nell'eliminazione della configurazione: {str(e)}")
        return False
    finally:
        conn.close()


def save_customer_configuration(name, config):
    """Salva una configurazione cliente nel database"""
    conn = sqlite3.connect(DB_FILE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT OR REPLACE INTO customer_configurations 
        (name, customer_name, customer_address, customer_phone, customer_email, customer_vat_code)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            name,
            config.get('customer_name', ''),
            config.get('customer_address', ''),
            config.get('customer_phone', ''),
            config.get('customer_email', ''),
            config.get('customer_vat_code', '')
        ))

        conn.commit()
        return True
    except Exception as e:
        print(f"Errore nel salvataggio della configurazione cliente: {str(e)}")
        return False
    finally:
        conn.close()


def load_customer_configuration(name):
    """Carica una configurazione cliente dal database"""
    conn = sqlite3.connect(DB_FILE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute('''
        SELECT customer_name, customer_address, customer_phone, customer_email, customer_vat_code
        FROM customer_configurations
        WHERE LOWER(name) = LOWER(?)
        ''', (name,))

        row = cursor.fetchone()
        if row:
            config = {
                'customer_name': row[0],
                'customer_address': row[1],
                'customer_phone': row[2],
                'customer_email': row[3],
                'customer_vat_code': row[4]
            }
            return config
        return None
    except Exception as e:
        print(f"Errore nel caricamento della configurazione cliente: {str(e)}")
        return None
    finally:
        conn.close()


def get_customer_configuration_names():
    """Restituisce la lista dei nomi delle configurazioni cliente salvate"""
    conn = sqlite3.connect(DB_FILE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT name FROM customer_configurations ORDER BY name')
        names = [row[0] for row in cursor.fetchall()]
        return names
    except Exception as e:
        print(f"Errore nel recupero delle configurazioni cliente: {str(e)}")
        return []
    finally:
        conn.close()


def delete_customer_configuration(name):
    """Elimina una configurazione cliente dal database"""
    conn = sqlite3.connect(DB_FILE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM customer_configurations WHERE LOWER(name) = LOWER(?)', (name,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore nell'eliminazione della configurazione cliente: {str(e)}")
        return False
    finally:
        conn.close()


def delete_database():
    """Elimina il database"""
    try:
        if os.path.exists(DB_FILE_NAME):
            os.remove(DB_FILE_NAME)
            return True
        return False
    except Exception as e:
        print(f"Errore nell'eliminazione del database: {str(e)}")
        return False


def init_db():
    """Inizializza il database SQLite"""
    conn = sqlite3.connect(DB_FILE_NAME)
    cursor = conn.cursor()

    # Crea la tabella delle configurazioni se non esiste
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS company_configurations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        company_name TEXT NOT NULL,
        company_address TEXT NOT NULL,
        company_phone TEXT NOT NULL,
        company_email TEXT NOT NULL,
        company_vat_code TEXT NOT NULL,
        company_logo TEXT,
        terms TEXT,
        vat_rate TEXT,
        notes TEXT,
        prepared_by TEXT
    )
    ''')

    # Crea la tabella delle configurazioni cliente se non esiste
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customer_configurations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        customer_name TEXT NOT NULL,
        customer_address TEXT,
        customer_phone TEXT,
        customer_email TEXT NOT NULL,
        customer_vat_code TEXT
    )
    ''')

    # Abilito il supporto per le chiavi esterni in Sqlite3:
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Crea la tabella dei preventivi di una data compagnia e di un dato cliente se non esiste
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quotes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quote_code VARCHAR(20) UNIQUE NOT NULL,
        company_id INTEGER NOT NULL,
        customer_id INTEGER NOT NULL,
        quote_json TEXT,
        creation_date TEXT NOT NULL,
        FOREIGN KEY (company_id) REFERENCES company_configurations(id),
        FOREIGN KEY (customer_id) REFERENCES customer_configurations(id)
        
);

    ''')

    conn.commit()
    conn.close()

def save_quote_on_db(quote):
    """Salva un preventivo su un database SQLite"""
    conn = sqlite3.connect(DB_FILE_NAME)
    cursor = conn.cursor()
    company_id = _get_company_id_by_name(cursor, quote.get('company', {}).get('company_name'))
    customer_id = _get_customer_id_by_name(cursor, quote.get('customer', {}).get('customer_name'), quote.get('customer', {}).get('customer_email'))
    quote_code = quote.get('quote_code')
    creation_date = format_date_for_db(quote.get('date'))
    quote_json = json.dumps(quote, indent=4, default=str)
    cursor.execute('''
        INSERT INTO quotes (quote_code, company_id, customer_id, quote_json, creation_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (quote_code, company_id, customer_id, quote_json, creation_date))
    conn.commit()
    conn.close()


def _get_company_id_by_name(cursor, name):
    """Restituisce l'ID di una compagnia dal database"""
    cursor.execute('SELECT id FROM company_configurations WHERE LOWER(company_name) = LOWER(?)', (name,))
    company_id = cursor.fetchone() # [row[0] for row in cursor.fetchall()]
    return company_id[0]


def _get_customer_id_by_name(cursor, name, email):
    """Restituisce l'ID di un cliente dal database"""
    cursor.execute('SELECT id FROM customer_configurations WHERE LOWER(customer_name) = LOWER(?) and LOWER(customer_email) = LOWER(?)', (name, email))
    customer_id = cursor.fetchone() # [row[0] for row in cursor.fetchall()]
    return customer_id[0]


def is_valid_email(email):
    """Verifica se l'email è valida"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_vat(vat):
    """Verifica se la partita IVA è valida (semplice controllo di lunghezza)"""
    # Implementazione semplificata: controlla solo che sia un numero di 11 cifre (per l'Italia)
    # In una versione più completa, si dovrebbe implementare l'algoritmo di controllo specifico
    if not vat:  # Se vuoto, consideriamo valido (per il cliente è opzionale)
        return True
    return bool(re.match(r'^\d{11}$', vat))


def is_valid_phone(phone):
    """Verifica se il numero di telefono è valido, supportando prefissi internazionali"""
    # Accetta formati come: +39 123 456 7890, +39-123-456-7890, 123 456 7890, 1234567890
    # Rimuovi tutti gli spazi e i trattini per semplificare la validazione
    phone_clean = re.sub(r'[\s-]', '', phone)

    # Verifica che il numero sia composto solo da cifre, eventualmente precedute da un +
    if not re.match(r'^\+?\d+$', phone_clean):
        return False

    # Verifica che la lunghezza sia ragionevole (tra 8 e 15 cifre)
    digits_only = re.sub(r'\D', '', phone_clean)
    return 8 <= len(digits_only) <= 15


def is_valid_codice_fiscale(cf):
    """
    Verifica se una stringa è un codice fiscale italiano valido.
    """
    """
    Verifica se una stringa è un codice fiscale italiano valido.
    """
    try:
        # Converti in maiuscolo e rimuovi spazi
        cf = cf.upper().strip()

        # Verifica lunghezza e formato base
        if len(cf) != 16:
            return False

        # Controlla che il formato sia corretto usando un'espressione regolare
        regex = r'^[A-Z]{6}\d{2}[A-EHLMPRST]\d{2}[A-Z]\d{3}[A-Z]$'
        if not re.match(regex, cf):
            return False

        # Valori per le posizioni dispari (indice 0-based)
        val_dispari = {
            '0': 1, '1': 0, '2': 5, '3': 7, '4': 9, '5': 13, '6': 15, '7': 17, '8': 19,
            '9': 21, 'A': 1, 'B': 0, 'C': 5, 'D': 7, 'E': 9, 'F': 13, 'G': 15, 'H': 17,
            'I': 19, 'J': 21, 'K': 2, 'L': 4, 'M': 18, 'N': 20, 'O': 11, 'P': 3, 'Q': 6,
            'R': 8, 'S': 12, 'T': 14, 'U': 16, 'V': 10, 'W': 22, 'X': 25, 'Y': 24, 'Z': 23
        }

        # Valori per le posizioni pari (indice 0-based)
        val_pari = {
            '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
            '9': 9, 'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7,
            'I': 8, 'J': 9, 'K': 10, 'L': 11, 'M': 12, 'N': 13, 'O': 14, 'P': 15, 'Q': 16,
            'R': 17, 'S': 18, 'T': 19, 'U': 20, 'V': 21, 'W': 22, 'X': 23, 'Y': 24, 'Z': 25
        }

        # Calcolo del carattere di controllo
        s = 0
        for i in range(15):
            c = cf[i]
            if i % 2 == 0:  # Posizione dispari (indice pari in Python)
                if c not in val_dispari:
                    return False
                s += val_dispari[c]
            else:  # Posizione pari (indice dispari in Python)
                if c not in val_pari:
                    return False
                s += val_pari[c]

        # Verifica che il carattere di controllo sia corretto
        resto = s % 26
        carattere_controllo = chr(resto + ord('A'))
        return carattere_controllo == cf[15]

    except Exception as e:
        # Gestione di qualsiasi errore imprevisto
        print(e)
        return False


def _config_unchanged(config, old_config):
    """Indica se le due configurazioni sono uguali"""
    return json.dumps(config, indent=2, default=str) == json.dumps(old_config, indent=2, default=str)

def get_formatted_note(name, address, email):
    return DEFAULT_NOTE.format(
        company_name=name,
        company_address=address,
        company_email=email
    )

def add_default_note(config: dict , name: str, address: str, email: str):
    if isinstance(config, dict):
        if 'notes' not in config:
            config['notes'] = get_formatted_note(name, address, email)
        return config
    else:
        raise ValueError(f"La configurazione non è un dizionario, f{type(config)}")

def genera_codice_random(lunghezza=8):
    """
    Genera un codice alfanumerico casuale di lunghezza specificata.

    Args:
        lunghezza (int): Lunghezza del codice da generare. Default è 8.

    Returns:
        str: Codice alfanumerico casuale.
    """
    import random
    import string
    # Caratteri possibili (lettere maiuscole e numeri)
    caratteri = string.ascii_uppercase + string.digits

    # Generazione del codice

    return 'random_'.join(random.choice(caratteri) for _ in range(lunghezza))


def genera_codice(stringa, lunghezza=8, controlla_duplicati=False, codici_esistenti=None):
    """
    Genera un codice alfanumerico a lunghezza fissa utilizzando Base64.

    Args:
        stringa: La stringa di input
        lunghezza: La lunghezza desiderata del codice (default: 8)
        controlla_duplicati: Se verificare duplicati nei codici esistenti
        codici_esistenti: Set di codici già generati

    Returns:
        Un codice alfanumerico di lunghezza fissa in formato Base64
    """
    if controlla_duplicati and codici_esistenti is None:
        codici_esistenti = set()

    # Genera un hash SHA-256 per aumentare l'entropia e avere un input di lunghezza costante
    hash_input = hashlib.sha256(stringa.encode('utf-8')).digest()

    # Codifica l'hash in Base64
    codice_base64 = base64.b64encode(hash_input).decode('utf-8')

    # Rimuovi caratteri non alfanumerici (+ e /) sostituendoli con caratteri alfanumerici
    # In Base64 standard, + e / sono usati, mentre = è usato per il padding
    codice_base64 = codice_base64.replace('+', 'A').replace('/', 'B').replace('=', '')

    # Prendi i primi caratteri fino alla lunghezza desiderata
    codice = codice_base64[:lunghezza]

    # Se è attiva la verifica dei duplicati
    if controlla_duplicati:
        salt = 0
        while codice in codici_esistenti:
            # Aggiungi un salt e rigenera
            salt_stringa = stringa + str(salt)
            hash_salt = hashlib.sha256(salt_stringa.encode('utf-8')).digest()

            codice_base64 = base64.b64encode(hash_salt).decode('utf-8')
            codice_base64 = codice_base64.replace('+', 'A').replace('/', 'B').replace('=', '')
            codice = codice_base64[:lunghezza]
            salt += 1

        codici_esistenti.add(codice)

    return codice

def get_current_date():
    return datetime.now().strftime("%d/%m/%Y")

def get_all_quote_codes():
    conn = sqlite3.connect(DB_FILE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT quote_code FROM quotes")
    quote_codes = [row[0] for row in cursor.fetchall()]
    conn.close()
    return set(quote_codes)

def prepare_data_for_qr(data:dict):
    return {'customer_name': data.get('customer', {}).get('customer_name'), 'date': data.get('date', get_current_date()), 'quote_code': data.get('quote_code', genera_codice_random())}


def scrittura_pdf(output_path, data):
    """Scrive il PDF"""
    # Salva il PDF finale
    with open(output_path, "wb") as f:
        data.write(f)


def format_date_for_db(date_string):
    """Converte una data dal formato italiano DD/MM/YYYY al formato ISO YYYY-MM-DD per il database"""
    try:
        # Parsing della data nel formato italiano
        date_obj = datetime.strptime(date_string, '%d/%m/%Y')
        # Conversione nel formato ISO
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        # Gestione errore in caso di formato non valido
        return None

def format_date_for_display(date_string):
    """Converte una data dal formato ISO YYYY-MM-DD al formato italiano DD/MM/YYYY per visualizzazione"""
    try:
        # Parsing della data nel formato ISO
        date_obj = datetime.strptime(date_string, '%Y-%m-%d')
        # Conversione nel formato italiano
        return date_obj.strftime('%d/%m/%Y')
    except ValueError:
        # Gestione errore in caso di formato non valido
        return date_string

