import os
import re
import sqlite3
from constants import DB_FILE_NAME

def save_configuration(name, config):
    """Salva una configurazione nel database"""
    conn = sqlite3.connect(DB_FILE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT OR REPLACE INTO configurations 
        (name, company_name, company_address, company_phone, company_email, company_vat, 
        company_logo, terms, vat_rate, notes, prepared_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name,
            config.get('company_name', ''),
            config.get('company_address', ''),
            config.get('company_phone', ''),
            config.get('company_email', ''),
            config.get('company_vat', ''),
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
        SELECT company_name, company_address, company_phone, company_email, company_vat,
               company_logo, terms, vat_rate, notes, prepared_by
        FROM configurations
        WHERE name = ?
        ''', (name,))

        row = cursor.fetchone()
        if row:
            config = {
                'company_name': row[0],
                'company_address': row[1],
                'company_phone': row[2],
                'company_email': row[3],
                'company_vat': row[4],
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
        cursor.execute('SELECT name FROM configurations ORDER BY name')
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
        cursor.execute('DELETE FROM configurations WHERE name = ?', (name,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore nell'eliminazione della configurazione: {str(e)}")
        return False
    finally:
        conn.close()


def save_client_configuration(name, config):
    """Salva una configurazione cliente nel database"""
    conn = sqlite3.connect(DB_FILE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT OR REPLACE INTO client_configurations 
        (name, client_name, client_address, client_phone, client_email, client_vat)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            name,
            config.get('client_name', ''),
            config.get('client_address', ''),
            config.get('client_phone', ''),
            config.get('client_email', ''),
            config.get('client_vat', '')
        ))

        conn.commit()
        return True
    except Exception as e:
        print(f"Errore nel salvataggio della configurazione cliente: {str(e)}")
        return False
    finally:
        conn.close()


def load_client_configuration(name):
    """Carica una configurazione cliente dal database"""
    conn = sqlite3.connect(DB_FILE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute('''
        SELECT client_name, client_address, client_phone, client_email, client_vat
        FROM client_configurations
        WHERE name = ?
        ''', (name,))

        row = cursor.fetchone()
        if row:
            config = {
                'client_name': row[0],
                'client_address': row[1],
                'client_phone': row[2],
                'client_email': row[3],
                'client_vat': row[4]
            }
            return config
        return None
    except Exception as e:
        print(f"Errore nel caricamento della configurazione cliente: {str(e)}")
        return None
    finally:
        conn.close()


def get_client_configuration_names():
    """Restituisce la lista dei nomi delle configurazioni cliente salvate"""
    conn = sqlite3.connect(DB_FILE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT name FROM client_configurations ORDER BY name')
        names = [row[0] for row in cursor.fetchall()]
        return names
    except Exception as e:
        print(f"Errore nel recupero delle configurazioni cliente: {str(e)}")
        return []
    finally:
        conn.close()


def delete_client_configuration(name):
    """Elimina una configurazione cliente dal database"""
    conn = sqlite3.connect(DB_FILE_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM client_configurations WHERE name = ?', (name,))
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
    CREATE TABLE IF NOT EXISTS configurations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        company_name TEXT NOT NULL,
        company_address TEXT NOT NULL,
        company_phone TEXT NOT NULL,
        company_email TEXT NOT NULL,
        company_vat TEXT NOT NULL,
        company_logo TEXT,
        terms TEXT,
        vat_rate TEXT,
        notes TEXT,
        prepared_by TEXT
    )
    ''')

    # Crea la tabella delle configurazioni cliente se non esiste
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS client_configurations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        client_name TEXT NOT NULL,
        client_address TEXT,
        client_phone TEXT,
        client_email TEXT NOT NULL,
        client_vat TEXT
    )
    ''')

    conn.commit()
    conn.close()


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
