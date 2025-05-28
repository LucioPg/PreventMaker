import json
import base64
import qrcode
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
# import cv2
# from pyzbar.pyzbar import decode

# def leggi_qr_preventivo(percorso_immagine, password):
#     # Leggere l'immagine
#     immagine = cv2.imread(percorso_immagine)
#
#     # Decodificare il QR code
#     risultati = decode(immagine)
#
#     if not risultati:
#         print("Nessun QR code trovato nell'immagine")
#         return None
#
#     # Estrarre i dati crittografati
#     dati_crittografati = risultati[0].data
#
#     try:
#         # Decrittografare
#         json_data = decrittografa_dati(dati_crittografati, password)
#
#         # Convertire da JSON a dizionario
#         preventivo = json.loads(json_data)
#
#         return preventivo
#     except Exception as e:
#         print(f"Errore durante la decrittografia: {e}")
#         return None





# 3. Generare una chiave di crittografia da una password
def genera_chiave(password, salt=None):
    if salt is None:
        salt = b'salt_predefinito'  # In produzione usa un salt casuale

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )

    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


# 4. Crittografare i dati JSON
def crittografa_dati(dati, password, salt=None):
    chiave = genera_chiave(password,salt)
    f = Fernet(chiave)
    dati_bytes = dati.encode()
    dati_crittografati = f.encrypt(dati_bytes)
    return dati_crittografati


# 5. Decrittografare i dati (utile per verificare)
def decrittografa_dati(dati_crittografati, password, salt=None):
    chiave = genera_chiave(password, salt)
    f = Fernet(chiave)
    dati_decrittografati = f.decrypt(dati_crittografati)
    return dati_decrittografati.decode()


# 6. Generare QR code dai dati crittografati
def genera_qr_code(dati, nome_file='preventivo_qr_old.png'):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(dati)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(nome_file)
    return img


# 7. Funzione completa
def crea_qr_preventivo(dati_preventivo, password, salt = None, nome_file='preventivo_qr_old.png'):
    # Convertire in JSON
    json_data = json.dumps(dati_preventivo)

    # Crittografare
    dati_crittografati = crittografa_dati(json_data, password)

    # Generare QR code
    qr_img = genera_qr_code(dati_crittografati, nome_file)

    print(f"QR code creato e salvato come '{nome_file}'")
    return qr_img

if __name__ == "__main__":
    # 1. Dati di esempio per il preventivo
    with open('test_qr.json', "r") as j:
        dati_preventivo = json.load(j)

    # 2. Convertire i dati in JSON
    json_string = json.dumps(dati_preventivo)
    print("Dati JSON originali:", json_string)
    # Esempio di utilizzo
    password = "password_segreta"
    qr_img = crea_qr_preventivo(dati_preventivo, password)

    # NOTA: i dati crittografati non sono più restituiti dalla funzione crea_qr_preventivo
    # qr_img, dati_crittografati = crea_qr_preventivo(dati_preventivo, password)
    # qr_decodificato = leggi_qr_preventivo('preventivo_qr_old.png', password)
    # # Verifica (decrittografia)
    # dati_decrittografati = decrittografa_dati(dati_crittografati, password)
    # print("\nVerifica decrittografia:")
    # print(dati_decrittografati)
    # print("Decrittografia riuscita:", dati_decrittografati == json_string == json.dumps(qr_decodificato))
