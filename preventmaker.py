import sys
import os
from functools import partial
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QTextEdit, QPushButton, QTableWidget,
                             QSpinBox, QDoubleSpinBox, QComboBox,
                             QFileDialog, QMessageBox, QWizard, QWizardPage, QFormLayout,
                             QGroupBox, QDialog, QListWidget, QInputDialog, QHeaderView, QSplashScreen)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QSettings, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
import tempfile

from custom_events import ConfigReadyEvent
from products_enums import ProductTableWidgetColumn, ProductTableWidget, ProductTableJsonFieldsNames
from utils import save_configuration, load_configuration, get_configuration_names, delete_configuration, \
    save_customer_configuration, load_customer_configuration, get_customer_configuration_names, \
    delete_customer_configuration, \
    delete_database, init_db, is_valid_email, is_valid_vat, is_valid_phone, _config_unchanged, add_default_note, \
    get_formatted_note

from constants import *


def dialog_with_icon(self, title, label, icon_path=None, default_text=""):
    """
    Versione personalizzata di QInputDialog.getText() che supporta l'impostazione di un'icona

    Args:
        title: Titolo della finestra
        label: Testo dell'etichetta
        icon_path: Percorso all'icona (opzionale)
        default_text: Testo predefinito (opzionale)

    Returns:
        tuple: (testo inserito, flag di accettazione)
    """
    dialog = QInputDialog(self)
    dialog.setWindowTitle(title)
    dialog.setLabelText(label)
    dialog.setTextValue(default_text)

    if icon_path:
        dialog.setWindowIcon(QIcon(icon_path))

    # ok = dialog.exec() == QInputDialog.accepted
    return dialog


class CompanyConfigWizard(QWizard):
    """Wizard per la configurazione della società emittente."""

    def __init__(self, parent=None, config_name=None):
        super().__init__(parent)
        self.setWindowTitle("Configurazione Società Emittente")
        self.setStyleSheet(COMPANY_STYLESHEET)
        self.setWindowIcon(QIcon(COMPANY_ICON_PATH))
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.config_name = config_name
        self._old_config = {}
        self._temp_config = {}
        self.is_rejected = False
        self.is_initialized = False
        self.cancel_button = self.button(QWizard.WizardButton.CancelButton)
        # disconnetto il comportamento predefinito e applico il mio override
        self.cancel_button.disconnect()
        self.cancel_button.clicked.connect(self.custom_cancel_callback)
        # Inizializza il database se necessario
        init_db()

        # Aggiungi le pagine del wizard
        self.company_page = CompanyPage()
        self.terms_page = TermsPage()

        self.addPage(self.company_page)
        self.addPage(self.terms_page)

        # Se è stata specificata una configurazione, caricala
        if config_name:
            self.load_config(config_name)

        self.setMinimumSize(600, 400)
        self.currentIdChanged.connect(self.on_page_changed)
        self.finished.connect(self.on_finish)
        self.is_initialized = True

    def on_page_changed(self, id):
        # Se siamo passati alla terms_page
        if self.is_initialized and self.page(id) == self.terms_page:
            # Imposta i valori dinamici nella nota
            self.set_name_address_email_for_note()

    def set_name_address_email_for_note(self):
        """Imposta i valori dinamici della company_page nella nota predefinita della terms_page"""
        # Ottieni i valori dalla company_page
        company_name = self.company_page.company_name.text()
        company_address = self.company_page.company_address.toPlainText().strip()
        company_email = self.company_page.company_email.text()

        # Formatta la nota predefinita con i valori
        nota_formattata = get_formatted_note(
            company_name,
            company_address,
            company_email
        )

        # Imposta la nota formattata come testo predefinito nella terms_page
        # Assumendo che terms_page.notes sia un QTextEdit o simile
        self.terms_page.notes.setPlainText(nota_formattata)

    def custom_cancel_callback(self):
        """Override del metodo invocato alla pressione del tasto cancel. Per fare il controllo se la configurazione
         non è stata modificata"""
        self._temp_config = self.get_config()
        self.is_rejected = True
        # invoco il metodo predefinito
        self.reject()

    def on_finish(self):
        """
        Salva la configurazione finale.
        :return:
        """
        if self.is_rejected:
            return
        config = self.get_config() if not self.is_rejected else self._temp_config
        if _config_unchanged(config, self._old_config):
            self.is_rejected = False
            self._temp_config = {}
            return
        if config and all(list(map(lambda page: page.isComplete(), [self.company_page, self.terms_page]))):
            # Aggiungi nota predefinita
            config = add_default_note(config, config.get('company_name', ''), config.get('company_address', ''),
                                      config.get('company_email', ''))
            # Salva la configurazione
            save_configuration(self.config_name, config)
            QMessageBox.information(self, "Salvataggio", "La configurazione è stata salvata.")
        else:
            QMessageBox.warning(self, "Errore", "Impossibile salvare la configurazione.")

    def load_config(self, name):
        """Carica una configurazione esistente nel wizard"""
        config = load_configuration(name)
        if config:
            # Imposta i campi della società
            self.company_page.company_name.setText(config.get('company_name', ''))
            self.company_page.company_address.setPlainText(config.get('company_address', ''))
            self.company_page.company_phone.setText(config.get('company_phone', ''))
            self.company_page.company_email.setText(config.get('company_email', ''))
            self.company_page.company_vat.setText(config.get('company_vat', ''))
            self.company_page.logo_path.setText(config.get('company_logo', ''))
            config = add_default_note(config, config.get('company_name', ''), config.get('company_address', ''),
                                      config.get('company_email', ''))
            # Imposta i campi dei termini
            self.terms_page.terms.setPlainText(config.get('terms', ''))
            vat_rate = config.get('vat_rate', '22%')
            index = self.terms_page.vat_rate.findText(vat_rate)
            if index >= 0:
                self.terms_page.vat_rate.setCurrentIndex(index)
            self.terms_page.notes.setPlainText(config.get('notes', ''))
            self.terms_page.prepared_by.setText(config.get('prepared_by', ''))
            self._old_config = config.copy()
        else:
            self._old_config = {}

    def get_config(self):
        """Restituisce la configurazione completa dal wizard"""
        config = {
            # Dati società
            'company_name': self.field('company_name'),
            'company_address': self.field('company_address'),
            'company_phone': self.field('company_phone'),
            'company_email': self.field('company_email'),
            'company_vat': self.field('company_vat'),
            'company_logo': self.field('company_logo'),
            # Termini e condizioni
            'terms': self.field('terms'),
            'vat_rate': self.field('vat_rate'),
            'notes': self.field('notes'),
            'prepared_by': self.field('prepared_by')
        }

        return config


class CompanyPage(QWizardPage):
    """Pagina per i dati della società emittente"""

    def __init__(self):
        super().__init__()
        self.setTitle("Dati Società Emittente")
        self.setSubTitle("Inserisci i dati della tua società")
        self.validate_attempted = False

        layout = QFormLayout()

        # Campi per i dati della società
        self.company_name = QLineEdit()
        self.company_address = QTextEdit()
        self.company_phone = QLineEdit()
        self.company_email = QLineEdit()
        self.company_vat = QLineEdit()

        # Logo
        logo_layout = QHBoxLayout()
        self.logo_path = QLineEdit()
        self.logo_path.setReadOnly(True)
        self.browse_button = QPushButton("Sfoglia...")
        self.browse_button.clicked.connect(self.browseLogo)
        logo_layout.addWidget(self.logo_path)
        logo_layout.addWidget(self.browse_button)

        # Registra i campi (con * per i campi obbligatori)
        self.registerField('company_name*', self.company_name)
        self.registerField('company_address*', self.company_address, 'plainText')
        self.registerField('company_phone*', self.company_phone)
        self.registerField('company_email*', self.company_email)
        self.registerField('company_vat*', self.company_vat)
        self.registerField('company_logo', self.logo_path)

        # Aggiungi i campi al layout
        layout.addRow("Nome Società (*):", self.company_name)
        layout.addRow("Indirizzo (*):", self.company_address)
        layout.addRow("Telefono (*):", self.company_phone)
        layout.addRow("Email (*):", self.company_email)
        layout.addRow("Partita IVA (*):", self.company_vat)
        layout.addRow("Logo:", logo_layout)

        self.setLayout(layout)

    def isComplete(self):
        """Verifica che tutti i campi obbligatori siano compilati"""
        # Verifica che i campi obbligatori siano compilati
        return self._isComplete(self.company_name.text(),
                                self.company_address.toPlainText(),
                                self.company_phone.text(),
                                self.company_email.text(),
                                self.company_vat.text())

    def _isComplete(self, name, address, phone, email, vat):
        """Verifica che tutti i campi obbligatori siano compilati"""
        if (name.strip() == "" or
                address.strip() == "" or
                phone.strip() == "" or
                email.strip() == "" or
                vat.strip() == ""):
            return False
        return True

    def validatePage(self):
        """Valida i campi quando si tenta di passare alla pagina successiva"""
        self.validate_attempted = True
        return self.validate(self.company_email.text(), self.company_phone.text(), self.company_vat.text())

    def validate(self, email: str, phone: str, vat: str):
        if not is_valid_email(email):
            QMessageBox.warning(
                self, "Email non valida",
                "L'indirizzo email del società non è valido. Inserisci un indirizzo email valido."
            )
            return False
        # Verifica che il numero di telefono sia valido (se compilato)
        if not is_valid_phone(phone.strip()):
            QMessageBox.warning(
                self, "Numero di telefono non valido",
                "Il numero di telefono del società non è valido. Inserisci un numero valido (es. +39 123 456 7890)."
            )
            return False
        # Verifica che la partita IVA sia valida (se compilata)
        if not is_valid_vat(vat.strip()):
            QMessageBox.warning(
                self, "Partita IVA non valida",
                "La partita IVA del società non è valida. Deve essere un numero di 11 cifre."
            )
            return False

        return True

    def browseLogo(self):
        """Apre un dialogo per selezionare il logo"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Seleziona Logo", "", "Immagini (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_name:
            self.logo_path.setText(file_name)


class CustomerPage(QWizardPage):
    """Pagina per i dati del cliente"""

    def __init__(self):
        super().__init__()
        self.setTitle("Dati Cliente")
        self.setSubTitle("Inserisci i dati del cliente destinatario")
        self.validate_attempted = False

        layout = QFormLayout()

        # Campi per i dati del cliente
        self.customer_name = QLineEdit()
        self.customer_address = QTextEdit()
        self.customer_phone = QLineEdit()
        self.customer_email = QLineEdit()
        self.customer_vat = QLineEdit()

        # Registra i campi (con * per i campi obbligatori)
        self.registerField('customer_name*', self.customer_name)
        self.registerField('customer_address', self.customer_address, 'plainText')
        self.registerField('customer_phone', self.customer_phone)
        self.registerField('customer_email*', self.customer_email)
        self.registerField('customer_vat', self.customer_vat)

        # Aggiungi i campi al layout
        layout.addRow("Nome Cliente (*):", self.customer_name)
        layout.addRow("Indirizzo:", self.customer_address)
        layout.addRow("Telefono:", self.customer_phone)
        layout.addRow("Email (*):", self.customer_email)
        layout.addRow("Partita IVA:", self.customer_vat)

        self.setLayout(layout)

    def isComplete(self):
        """Verifica che tutti i campi obbligatori siano compilati"""
        # Verifica che i campi obbligatori siano compilati
        return self._isComplete(self.customer_name.text(), self.customer_email.text())

    def _isComplete(self, name, email):
        """Verifica che tutti i campi obbligatori siano compilati"""
        if (name.strip() == "" or
                email.strip() == ""):
            return False
        return True

    def validatePage(self):
        """Valida i campi quando si tenta di passare alla pagina successiva"""
        self.validate_attempted = True
        return self.validate(self.customer_email.text(), self.customer_phone.text(), self.customer_vat.text())

    def validate(self, email: str, phone: str, vat: str):
        if not is_valid_email(email):
            QMessageBox.warning(
                self, "Email non valida",
                "L'indirizzo email del cliente non è valido. Inserisci un indirizzo email valido."
            )
            return False
        # Verifica che il numero di telefono sia valido (se compilato)
        if phone.strip() and not is_valid_phone(phone.strip()):
            QMessageBox.warning(
                self, "Numero di telefono non valido",
                "Il numero di telefono del cliente non è valido. Inserisci un numero valido (es. +39 123 456 7890)."
            )
            return False
        # Verifica che la partita IVA sia valida (se compilata)
        if vat.strip() and not is_valid_vat(vat.strip()):
            QMessageBox.warning(
                self, "Partita IVA non valida",
                "La partita IVA del cliente non è valida. Deve essere un numero di 11 cifre."
            )
            return False

        return True


class TermsPage(QWizardPage):
    """Pagina per termini e condizioni"""

    def __init__(self):
        super().__init__()
        self.company_name = ""
        self.company_address = ""
        self.company_email = ""
        self.setTitle("Termini e Condizioni")
        self.setSubTitle("Imposta termini, condizioni e altre informazioni")

        layout = QFormLayout()

        # Campi per termini e condizioni
        self.terms = QTextEdit()
        self.terms.setPlaceholderText("Inserisci qui i termini e le condizioni...")

        # Aliquota IVA
        self.vat_rate = QComboBox()
        self.vat_rate.addItems(["22%", "10%", "4%", "0%"])

        # Note aggiuntive
        self.notes = QTextEdit()
        self.notes.setPlainText(get_formatted_note(self.company_name, self.company_address, self.company_email))

        # Preparato da
        self.prepared_by = QLineEdit()

        # Registra i campi (con * per i campi obbligatori)
        self.registerField('terms', self.terms, 'plainText')
        self.registerField('vat_rate', self.vat_rate, 'currentText')
        self.registerField('notes', self.notes, 'plainText')
        self.registerField('prepared_by*', self.prepared_by)

        # Aggiungi i campi al layout
        layout.addRow("Termini e Condizioni:", self.terms)
        layout.addRow("Aliquota IVA:", self.vat_rate)
        layout.addRow("Note:", self.notes)
        layout.addRow("Preparato da (*):", self.prepared_by)

        self.setLayout(layout)

    def isComplete(self):
        """Verifica che tutti i campi obbligatori siano compilati"""
        return self.prepared_by.text().strip() != ""


class ProductTable(QTableWidget):
    """Tabella per i prodotti del preventivo"""

    totalChanged = pyqtSignal(float, float, float)  # Segnale per totale netto, iva, totale ivato

    def __init__(self, parent=None, labels=["Art.", "Descrizione", "Qnt", "P. U.",
                                            "S. %", "IVA", "Valore"]):
        super().__init__(0, 7, parent)
        self.setHorizontalHeaderLabels(labels)
        self.labels = labels
        # Imposta le proporzioni delle colonne
        self.column_proportions = [0.08, 0.4, 0.08, 0.12, 0.08, 0.08, 0.16]  # Proporzioni relative

        # Configura l'header orizzontale
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.sectionResized.connect(self.adjustColumnWidths)

        # Imposta il comportamento di selezione
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        # Connetti il segnale di modifica cella
        self.itemChanged.connect(self.updateTotals)

        # Connetti il segnale di ridimensionamento della tabella
        self.parent_resized = False

    def showEvent(self, event):
        """Gestisce l'evento di visualizzazione della tabella"""
        super().showEvent(event)
        # Imposta le larghezze iniziali delle colonne
        self.adjustColumnWidths()

    def resizeEvent(self, event):
        """Gestisce l'evento di ridimensionamento della tabella"""
        super().resizeEvent(event)
        # Aggiusta le larghezze delle colonne quando la tabella viene ridimensionata
        if self.parent_resized:
            self.adjustColumnWidths()
            self.parent_resized = False

    def adjustColumnWidths(self, column=None, old_size=None, new_size=None):
        """Aggiusta le larghezze delle colonne in base alle proporzioni"""
        # Se il ridimensionamento è stato avviato dall'utente, mantieni le proporzioni
        if column is not None and old_size != new_size:
            # Calcola la nuova proporzione per la colonna ridimensionata
            total_width = self.viewport().width()
            if total_width > 0:
                self.column_proportions[column] = new_size / total_width

                # Normalizza le proporzioni
                total_prop = sum(self.column_proportions)
                self.column_proportions = [p / total_prop for p in self.column_proportions]

                # Salva le proporzioni nelle impostazioni
                if hasattr(self.parent(), 'settings'):
                    self.parent().saveSettings()

        # Imposta le larghezze delle colonne in base alle proporzioni
        total_width = self.viewport().width()
        if total_width > 0:
            # Assicurati che la colonna della descrizione (indice 1) abbia sempre almeno il 30% dello spazio
            min_desc_proportion = 0.3
            if self.column_proportions[1] < min_desc_proportion:
                # Calcola quanto spazio dobbiamo prendere dalle altre colonne
                extra_needed = min_desc_proportion - self.column_proportions[1]
                # Distribuisci proporzionalmente la riduzione alle altre colonne
                other_columns_total = sum(self.column_proportions) - self.column_proportions[1]
                if other_columns_total > 0:
                    reduction_factor = extra_needed / other_columns_total
                    for i in range(len(self.column_proportions)):
                        if i != 1:  # Salta la colonna della descrizione
                            self.column_proportions[i] *= (1 - reduction_factor)
                    self.column_proportions[1] = min_desc_proportion

            # Imposta le larghezze effettive
            for i, proportion in enumerate(self.column_proportions):
                width = int(total_width * proportion)
                self.setColumnWidth(i, width)

    def addRow(self):
        """Aggiunge una nuova riga alla tabella"""
        row = self.rowCount()
        self.insertRow(row)

        # Crea gli elementi della riga
        # Codice articolo (default: numero riga + 1)
        code_item = ProductTableWidget.CODE_ITEM.value(str(row + 1))

        desc_item = ProductTableWidget.DESCRIPTION.value("")

        # Usa spinbox per quantità
        qty_spin = ProductTableWidget.QNT.value()  # QSpinBox()
        qty_spin.setRange(1, 9999)
        qty_spin.setValue(1)
        qty_spin.valueChanged.connect(self.updateTotals)

        # Usa doublespinbox per prezzo unitario
        price_spin = ProductTableWidget.PRICE.value()  # QDoubleSpinBox()
        price_spin.setRange(0, 999999.99)
        price_spin.setDecimals(4)
        price_spin.setSuffix(" €")
        price_spin.valueChanged.connect(self.updateTotals)

        # Usa doublespinbox per sconto
        discount_spin = ProductTableWidget.DISCOUNT.value()  # QDoubleSpinBox()
        discount_spin.setRange(0, 100)
        discount_spin.setDecimals(2)
        discount_spin.setSuffix(" %")
        discount_spin.valueChanged.connect(self.updateTotals)

        # Usa combobox per IVA
        vat_combo = ProductTableWidget.VAT.value()  # QComboBox()
        vat_combo.addItems(["22", "10", "4", "0"])
        vat_combo.currentTextChanged.connect(self.updateTotals)

        # Totale netto (calcolato)
        total_item = ProductTableWidget.NET.value("0.00 €")
        total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        # Imposta gli elementi nella riga
        self.setItem(row, ProductTableWidgetColumn.CODE_ITEM.value, code_item)
        self.setItem(row, ProductTableWidgetColumn.DESCRIPTION.value, desc_item)
        self.setCellWidget(row, ProductTableWidgetColumn.QNT.value, qty_spin)
        self.setCellWidget(row, ProductTableWidgetColumn.PRICE.value, price_spin)
        self.setCellWidget(row, ProductTableWidgetColumn.DISCOUNT.value, discount_spin)
        self.setCellWidget(row, ProductTableWidgetColumn.VAT.value, vat_combo)
        self.setItem(row, ProductTableWidgetColumn.NET.value, total_item)

        return row

    def removeSelectedRows(self):
        """Rimuove le righe selezionate"""
        rows = sorted(set(index.row() for index in self.selectedIndexes()), reverse=True)
        for row in rows:
            self.removeRow(row)
        self.updateTotals()

    def updateTotals(self):
        """Aggiorna i totali di ogni riga e il totale complessivo"""
        total_net = 0.0
        total_vat = 0.0
        qnt_col = ProductTableWidgetColumn.QNT.value
        price_col = ProductTableWidgetColumn.PRICE.value
        discount_col = ProductTableWidgetColumn.DISCOUNT.value
        vat_col = ProductTableWidgetColumn.VAT.value
        net_col = ProductTableWidgetColumn.NET.value
        for row in range(self.rowCount()):
            if isinstance(self.cellWidget(row, qnt_col), QSpinBox) and \
                    isinstance(self.cellWidget(row, price_col), QDoubleSpinBox) and \
                    isinstance(self.cellWidget(row, discount_col), QDoubleSpinBox) and \
                    isinstance(self.cellWidget(row, vat_col), QComboBox):
                qty = self.cellWidget(row, qnt_col).value()
                price = self.cellWidget(row, price_col).value()
                discount = self.cellWidget(row, discount_col).value() / 100.0
                vat_rate = float(self.cellWidget(row, vat_col).currentText()) / 100.0

                # Calcola il netto
                net = qty * price * (1 - discount)

                # Calcola l'IVA
                vat = net * vat_rate

                # Aggiorna il totale netto nella tabella
                if self.item(row, net_col):
                    self.item(row, net_col).setText(f"{net:.4f} €")

                # Aggiorna i totali complessivi
                total_net += net
                total_vat += vat

        # Emetti il segnale con i totali aggiornati
        total_with_vat = total_net + total_vat
        self.totalChanged.emit(total_net, total_vat, total_with_vat)

    def getProductsData(self):
        """Restituisce i dati dei prodotti come lista di dizionari"""
        products = []

        for row in range(self.rowCount()):
            if self.item(row, 0) and self.item(row, 1) and isinstance(self.cellWidget(row, 2), QSpinBox):
                product = {
                    'code': self.item(row, 0).text(),
                    'description': self.item(row, 1).text(),
                    'quantity': self.cellWidget(row, 2).value(),
                    'unit_price': self.cellWidget(row, 3).value(),
                    'discount': self.cellWidget(row, 4).value(),
                    'vat_rate': float(self.cellWidget(row, 5).currentText()),
                    'net_total': float(self.item(row, 6).text().replace(" €", ""))
                }
                products.append(product)

        return products


class CustomerConfigWizard(QWizard):
    """WIP questa classe deve sostituire il QDialog costruito al volo dentro CustomerConfigManagerDialog per uniformarla
        al QWizard di CompanyConfigWizard
    """

    def __init__(self, parent=None, config_name=None):
        super().__init__(parent)
        self.config_name = config_name
        self.setStyleSheet(CUSTOMER_STYLESHEET)
        self.setWindowIcon(QIcon(CUSTOMER_ICON_PATH))
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(600, 400)

        init_db()

        self.customer_page = CustomerPage()
        self.addPage(self.customer_page)
        if self.config_name:
            self.load_config(self.config_name)
        self.finished.connect(self.on_finish)

    def load_config(self, name):
        config = load_customer_configuration(name)
        if config:
            self.customer_page.customer_name.setText(config.get("customer_name", ""))
            self.customer_page.customer_address.setText(config.get("customer_address", ""))
            self.customer_page.customer_vat.setText(config.get("customer_vat", ""))
            self.customer_page.customer_email.setText(config.get("customer_email", ""))
            self.customer_page.customer_phone.setText(config.get("customer_phone", ""))

    def get_config(self):
        return {
            # # Dati cliente
            'customer_name': self.field('customer_name'),
            'customer_address': self.field('customer_address'),
            'customer_phone': self.field('customer_phone'),
            'customer_email': self.field('customer_email'),
            'customer_vat': self.field('customer_vat'),
        }

    def on_finish(self):
        """
        Salva la configurazione finale.
        :return:
        """
        config = self.get_config()
        if config and self.customer_page.isComplete():
            # Salva la configurazione
            save_customer_configuration(self.config_name, config)
            QMessageBox.information(self, "Salvataggio", "La configurazione Cliente è stata salvata.")
        else:
            QMessageBox.warning(self, "Errore", "Impossibile salvare la configurazione Cliente.")


class ConfigManagerDialog(QDialog):
    """Dialogo per la gestione delle configurazioni"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestione Configurazioni - PreventMaker")
        self.setMinimumSize(500, 400)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowIcon(QIcon(COMPANY_ICON_PATH))
        # Inizializza il database
        init_db()

        layout = QVBoxLayout()

        # Lista delle configurazioni
        self.config_list = QListWidget()
        self.config_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.config_list.itemDoubleClicked.connect(self.accept)
        self.load_configurations()

        # Pulsanti per la gestione delle configurazioni
        buttons_layout = QHBoxLayout()

        self.new_button = QPushButton("Nuova")
        self.new_button.clicked.connect(self.new_configuration)

        self.rename_button = QPushButton("Rinomina")
        self.rename_button.clicked.connect(self.rename_configuration)

        self.delete_button = QPushButton("Elimina")
        self.delete_button.clicked.connect(self.delete_configuration)

        self.load_button = QPushButton("Carica")
        self.load_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("Annulla")
        self.cancel_button.clicked.connect(self.reject)

        # Pulsante per eliminare il database
        self.delete_db_button = QPushButton("Elimina Database")
        self.delete_db_button.setStyleSheet("background-color: #ffcccc;")  # Colore rosso chiaro
        self.delete_db_button.clicked.connect(self.delete_db)

        buttons_layout.addWidget(self.new_button)
        buttons_layout.addWidget(self.rename_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.delete_db_button)
        buttons_layout.addWidget(self.load_button)
        buttons_layout.addWidget(self.cancel_button)

        # Assembla il layout
        layout.addWidget(QLabel("Configurazioni disponibili:"))
        layout.addWidget(self.config_list)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def load_configurations(self):
        """Carica la lista delle configurazioni dal database"""
        self.config_list.clear()
        names = get_configuration_names()
        for name in names:
            self.config_list.addItem(name)

    def new_configuration(self):
        """Crea una nuova configurazione"""
        dialog = dialog_with_icon(
            self, "Nuova Configurazione", "Nome della configurazione:", COMPANY_ICON_PATH
        )
        name = None
        if dialog.exec():
            name = dialog.textValue().strip()
        if name:
            # Verifica se il nome esiste già
            existing_names = get_configuration_names()
            if name in existing_names:
                QMessageBox.warning(
                    self, "Nome Duplicato",
                    "Esiste già una configurazione con questo nome. Scegli un nome diverso."
                )
                return

            # Apri il wizard di configurazione per compilare i dati
            wizard = CompanyConfigWizard(self, name)
            if wizard.exec():
                self.load_configurations()

                # Seleziona la nuova configurazione
                items = self.config_list.findItems(name, Qt.MatchFlag.MatchExactly)
                if items:
                    self.config_list.setCurrentItem(items[0])

    def rename_configuration(self):
        """Rinomina una configurazione esistente"""
        current_item = self.config_list.currentItem()
        if not current_item:
            QMessageBox.warning(
                self, "Nessuna Selezione",
                "Seleziona una configurazione da rinominare."
            )
            return

        old_name = current_item.text()
        dialog = dialog_with_icon(
            self, "Rinomina Configurazione",
            "Nuovo nome:", icon_path=COMPANY_ICON_PATH, default_text=old_name
        )
        new_name = None
        if dialog.exec():
            name = dialog.textValue().strip()
        if new_name and new_name != old_name:
            # Verifica se il nuovo nome esiste già
            existing_names = get_configuration_names()
            if new_name in existing_names:
                QMessageBox.warning(
                    self, "Nome Duplicato",
                    "Esiste già una configurazione con questo nome. Scegli un nome diverso."
                )
                return

            # Carica la configurazione esistente
            config = load_configuration(old_name)
            if config:
                # Salva con il nuovo nome
                if save_configuration(new_name, config):
                    # Elimina la vecchia configurazione
                    delete_configuration(old_name)
                    self.load_configurations()

                    # Seleziona la configurazione rinominata
                    items = self.config_list.findItems(new_name, Qt.MatchFlag.MatchExactly)
                    if items:
                        self.config_list.setCurrentItem(items[0])

    def delete_configuration(self):
        """Elimina una configurazione esistente"""
        current_item = self.config_list.currentItem()
        if not current_item:
            QMessageBox.warning(
                self, "Nessuna Selezione",
                "Seleziona una configurazione da eliminare."
            )
            return

        name = current_item.text()
        reply = QMessageBox.question(
            self, "Conferma Eliminazione",
            f"Sei sicuro di voler eliminare la configurazione '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if delete_configuration(name):
                self.load_configurations()

    def get_selected_configuration(self):
        """Restituisce il nome della configurazione selezionata"""
        current_item = self.config_list.currentItem()
        if current_item:
            return current_item.text()
        return None

    def delete_db(self):
        """Elimina il database"""
        reply = QMessageBox.question(
            self, "Conferma Eliminazione Database",
            "Sei sicuro di voler eliminare il database? Tutte le configurazioni saranno perse.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if delete_database():
                QMessageBox.information(
                    self, "Database Eliminato",
                    "Il database è stato eliminato con successo. L'applicazione verrà riavviata."
                )
                # Reinizializza il database
                init_db()
                # Ricarica le configurazioni
                self.load_configurations()
            else:
                QMessageBox.critical(
                    self, "Errore",
                    "Si è verificato un errore durante l'eliminazione del database."
                )


class CustomerConfigManagerDialog(QDialog):
    """Dialogo per la gestione delle configurazioni cliente"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cliente")
        self.setStyleSheet(CUSTOMER_STYLESHEET)
        self.setWindowIcon(QIcon(CUSTOMER_ICON_PATH))
        self.setMinimumSize(600, 400)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # Inizializza il database
        init_db()

        layout = QVBoxLayout()

        # Lista delle configurazioni
        self.config_list = QListWidget()
        self.config_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.config_list.itemDoubleClicked.connect(self.accept)
        self.load_configurations()

        # Pulsanti per la gestione delle configurazioni
        buttons_layout = QHBoxLayout()

        self.new_button = QPushButton("Nuova")
        self.new_button.clicked.connect(self.new_configuration)

        self.rename_button = QPushButton("Rinomina")
        self.rename_button.clicked.connect(self.rename_configuration)

        self.modify_button = QPushButton("Modifica")
        self.modify_button.setStyleSheet("background-color: #DAA520;")
        self.modify_button.clicked.connect(self.modify_configuration)

        self.delete_button = QPushButton("Elimina")
        self.delete_button.clicked.connect(self.delete_configuration)

        self.load_button = QPushButton("Carica")
        self.load_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton("Annulla")
        self.cancel_button.clicked.connect(self.reject)

        buttons_layout.addWidget(self.new_button)
        buttons_layout.addWidget(self.rename_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.modify_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.load_button)
        buttons_layout.addWidget(self.cancel_button)

        # Assembla il layout
        layout.addWidget(QLabel("Configurazioni cliente disponibili:"))
        layout.addWidget(self.config_list)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def load_configurations(self):
        """Carica la lista delle configurazioni dal database"""
        self.config_list.clear()
        names = get_customer_configuration_names()
        for name in names:
            self.config_list.addItem(name)

    def new_configuration(self):
        """Crea una nuova configurazione cliente"""
        dialog = dialog_with_icon(self, "Nuovo Cliente", "Nome configurazione:", CUSTOMER_ICON_PATH)
        name = None
        if dialog.exec():
            name = dialog.textValue().strip()
        if name:
            # Verifica se il nome esiste già
            existing_names = get_customer_configuration_names()
            if name in existing_names:
                QMessageBox.warning(
                    self, "Nome Duplicato",
                    "Esiste già una configurazione cliente con questo nome. Scegli un nome diverso."
                )
                return
            wizard = CustomerConfigWizard(self, name)

            if wizard.exec():
                self.load_configurations()

                # Seleziona la nuova configurazione
                items = self.config_list.findItems(name, Qt.MatchFlag.MatchExactly)
                if items:
                    self.config_list.setCurrentItem(items[0])

    def rename_configuration(self):
        """Rinomina una configurazione cliente esistente"""
        current_item = self.config_list.currentItem()
        if not current_item:
            QMessageBox.warning(
                self, "Nessuna Selezione",
                "Seleziona una configurazione cliente da rinominare."
            )
            return

        old_name = current_item.text()
        dialog = dialog_with_icon(self, "Rinomina Configurazione Cliente", "Nuovo nome:",
                                  icon_path=CUSTOMER_ICON_PATH, default_text=old_name)
        new_name = None
        if dialog.exec():
            new_name = dialog.textValue().strip()
        if new_name and new_name != old_name:
            # Verifica se il nuovo nome esiste già
            existing_names = get_customer_configuration_names()
            if new_name in existing_names:
                QMessageBox.warning(
                    self, "Nome Duplicato",
                    "Esiste già una configurazione cliente con questo nome. Scegli un nome diverso."
                )
                return

            # Carica la configurazione esistente
            config = load_customer_configuration(old_name)
            if config:
                # Salva con il nuovo nome
                if save_customer_configuration(new_name, config):
                    # Elimina la vecchia configurazione
                    delete_customer_configuration(old_name)
                    self.load_configurations()

                    # Seleziona la configurazione rinominata
                    items = self.config_list.findItems(new_name, Qt.MatchFlag.MatchExactly)
                    if items:
                        self.config_list.setCurrentItem(items[0])

    def delete_configuration(self):
        """Elimina una configurazione cliente esistente"""
        current_item = self.config_list.currentItem()
        if not current_item:
            QMessageBox.warning(
                self, "Nessuna Selezione",
                "Seleziona una configurazione cliente da eliminare."
            )
            return

        name = current_item.text()
        reply = QMessageBox.question(
            self, "Conferma Eliminazione",
            f"Sei sicuro di voler eliminare la configurazione cliente '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if delete_customer_configuration(name):
                self.load_configurations()

    def modify_configuration(self):
        """Modifica una configurazione cliente"""
        current_item = self.config_list.currentItem()
        if not current_item:
            QMessageBox.warning(
                self, "Nessuna Selezione",
                "Selecta una configurazione cliente da modificar."
            )
            return
        name = self.get_selected_configuration()
        wizard = CustomerConfigWizard(self, name)

        if wizard.exec():
            self.load_configurations()

            # Seleziona la nuova configurazione
            items = self.config_list.findItems(name, Qt.MatchFlag.MatchExactly)
            if items:
                self.config_list.setCurrentItem(items[0])

    def get_selected_configuration(self):
        """Restituisce il nome della configurazione cliente selezionata"""
        current_item = self.config_list.currentItem()
        if current_item:
            return current_item.text()
        return None


class PDFPreviewDialog(QDialog):
    """Dialogo per la visualizzazione dell'anteprima del PDF"""

    def __init__(self, pdf_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Anteprima PDF")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout()

        # Crea il visualizzatore web per il PDF
        self.web_view = QWebEngineView()
        self.web_view.settings().setAttribute(
            self.web_view.settings().WebAttribute.PluginsEnabled, True
        )
        self.web_view.settings().setAttribute(
            self.web_view.settings().WebAttribute.PdfViewerEnabled, True
        )

        # Carica il PDF
        self.web_view.load(QUrl.fromLocalFile(pdf_path))

        # Pulsanti
        button_layout = QHBoxLayout()
        self.close_button = QPushButton("Chiudi")
        self.close_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)

        # Aggiungi i widget al layout
        layout.addWidget(self.web_view)
        layout.addLayout(button_layout)

        self.setLayout(layout)


class AddNoteDialog(QDialog):
    def __init__(self, parent=None, current_note=""):
        super().__init__(parent)
        self.current_note = current_note
        # Imposta il titolo della finestra
        self.setWindowTitle("Aggiungi Nota")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        # Imposta le dimensioni della finestra
        self.resize(400, 300)

        # Crea il layout principale
        main_layout = QVBoxLayout()

        # Aggiungi etichetta per il text box
        label = QLabel("Inserisci il testo della nota:")
        main_layout.addWidget(label)

        # Crea il text box
        self.text_edit = QTextEdit()
        if current_note:
            self.text_edit.setText(current_note)
        main_layout.addWidget(self.text_edit)

        # Crea il layout per i pulsanti
        button_layout = QHBoxLayout()

        # Crea i pulsanti
        self.add_button = QPushButton("Aggiungi")
        self.cancel_button = QPushButton("Annulla")

        # Collega i pulsanti alle azioni
        self.add_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # Aggiungi i pulsanti al layout
        button_layout.addStretch()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.cancel_button)

        # Aggiungi il layout dei pulsanti al layout principale
        main_layout.addLayout(button_layout)

        # Imposta il layout principale
        self.setLayout(main_layout)

    def get_text(self):
        """Restituisce il testo inserito nel text box"""
        return self.text_edit.toPlainText().strip()


class PreventMaker(QMainWindow):
    """Finestra principale dell'applicazione"""

    def __init__(self):
        super().__init__()
        # Inizializza il database
        init_db()

        self.initUI()
        self.current_file = None
        self.modified = False
        self.config = {}
        self.customer_config = {}
        self.current_config_name = None
        # Crea un timer che si attiva dopo un breve ritardo (es. 100 ms)
        self.closing_timer = QTimer()  # altrimenti l'applicazione non si chiude correttamente
        self.closing_timer.setSingleShot(True)  # Esegue l'azione una sola volta
        self.closing_timer.timeout.connect(lambda: QApplication.instance().quit())
        # Carica le impostazioni
        self.settings = QSettings("PreventMaker", "PreventMaker")
        self.loadSettings()
        self.company_config_is_present = False
        self.customer_config_is_present = False
        # Connetti l'evento di ridimensionamento della finestra
        self.installEventFilter(self)

    @property
    def config_is_ready(self):
        return all([self.company_config_is_present, self.customer_config_is_present])

    def handle_config_provider(self):
        """
        Crea e mostra il wizard di configurazione per compilare i dati.
        """
        # Chiedi la configurazione all'avvio
        if not self.showConfigManager():
            # Se l'utente ha annullato, chiudi l'applicazione
            self.close()
            self.chiudi_app_con_timer()  # altrimenti l'applicazione non si chiude correttamente

            return False

        has_customer = False
        while not has_customer:
            # Chiedi la configurazione del cliente
            has_customer = self.showClientConfigManager()
        return True

    def chiudi_app_con_timer(self):
        # Avvio il timer per la chiusura che si attiva dopo un breve ritardo (es. 100 ms)
        self.closing_timer.start(100)

    def initUI(self):
        """Inizializza l'interfaccia utente"""
        self.setWindowTitle("PreventMaker")
        self.setMinimumSize(1000, 700)

        # Widget centrale
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # Intestazione
        header_layout = QHBoxLayout()
        self.company_label = QLabel("Società: ")
        self.client_label = QLabel("Cliente: ")
        self.config_name_label = QLabel("Configurazione: Nessuna")
        header_layout.addWidget(self.company_label)
        header_layout.addWidget(self.config_name_label)
        header_layout.addStretch()
        header_layout.addWidget(self.client_label)

        # Tabella prodotti
        products_group = QGroupBox("Prodotti")
        products_layout = QVBoxLayout()

        self.product_table = ProductTable()
        self.product_table.totalChanged.connect(self.updateTotals)

        table_buttons = QHBoxLayout()
        self.add_product_btn = QPushButton("Aggiungi Prodotto")
        self.add_product_btn.clicked.connect(self.addProduct)
        self.remove_product_btn = QPushButton("Rimuovi Selezionati")
        self.remove_product_btn.clicked.connect(self.removeProducts)

        table_buttons.addWidget(self.add_product_btn)
        table_buttons.addWidget(self.remove_product_btn)
        table_buttons.addStretch()

        products_layout.addLayout(table_buttons)
        products_layout.addWidget(self.product_table)
        products_group.setLayout(products_layout)

        # Totali
        totals_group = QGroupBox("Totali")
        totals_layout = QFormLayout()

        self.total_net_label = QLabel("0.00 €")
        self.total_vat_label = QLabel("0.00 €")
        self.total_with_vat_label = QLabel("0.00 €")

        # TODO AGGIUNGERE QUI LA DATA ??????????????????????????
        totals_layout.addRow("Totale Netto:", self.total_net_label)
        totals_layout.addRow("Totale IVA:", self.total_vat_label)
        totals_layout.addRow("Totale Ivato:", self.total_with_vat_label)

        totals_group.setLayout(totals_layout)

        # Pulsanti azioni
        actions_layout = QHBoxLayout()

        self.preview_btn = QPushButton("Anteprima PDF")
        self.preview_btn.clicked.connect(self.previewPDF)

        self.save_btn = QPushButton("Salva")
        self.save_btn.clicked.connect(self.saveQuote)

        self.load_btn = QPushButton("Carica")
        self.load_btn.clicked.connect(self.loadQuote)

        self.export_btn = QPushButton("Esporta PDF")
        self.export_btn.clicked.connect(self.exportPDF)

        self.add_note_btn = QPushButton("Aggiungi Nota")
        self.add_note_btn.clicked.connect(self.addNote)

        self.config_btn = QPushButton("Configurazione")
        self.config_btn.clicked.connect(self.showConfigWizard)

        self.manage_configs_btn = QPushButton("Gestisci Configurazioni")
        self.manage_configs_btn.clicked.connect(self.showConfigManager)

        self.manage_client_configs_btn = QPushButton("Gestisci Clienti")
        self.manage_client_configs_btn.clicked.connect(self.showClientConfigManager)

        actions_layout.addWidget(self.preview_btn)
        actions_layout.addWidget(self.save_btn)
        actions_layout.addWidget(self.load_btn)
        actions_layout.addWidget(self.export_btn)
        actions_layout.addWidget(self.add_note_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(self.config_btn)
        actions_layout.addWidget(self.manage_configs_btn)
        actions_layout.addWidget(self.manage_client_configs_btn)

        # Assembla il layout principale
        main_layout.addLayout(header_layout)
        main_layout.addWidget(products_group)
        main_layout.addWidget(totals_group)
        main_layout.addLayout(actions_layout)

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Aggiungi un prodotto di default
        self.addProduct()

    def showConfigManager(self):
        """Mostra il gestore delle configurazioni"""
        dialog = ConfigManagerDialog(self)
        if dialog.exec():
            config_name = dialog.get_selected_configuration()
            if config_name:
                return self.loadConfiguration(config_name)
            else:
                return self.showConfigWizard()
        return False

    def showClientConfigManager(self):
        """Mostra il gestore delle configurazioni cliente"""
        dialog = CustomerConfigManagerDialog(self)
        if dialog.exec():
            config_name = dialog.get_selected_configuration()
            if config_name:
                return self.loadClientConfiguration(config_name)
            # Se non è stata selezionata una configurazione, non fare nulla
            # ma considera comunque l'operazione come completata
            return True
        # Se l'utente ha annullato, considera l'operazione come opzionale
        return True

    def addNote(self):
        """Aggiunge una nota al preventivo"""

        # Chiedi conferma prima di aggiungere la nota
        reply = QMessageBox.question(
            self, "Aggiungi Nota",
            f"Vuoi aggiungere / modificare la nota del preventivo?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Aggiungi la nota al preventivo (implementazione da definire in base alle esigenze)
            old_nota = self.config.get('notes')
            note_dialog = AddNoteDialog(self, old_nota)
            if note_dialog.exec():
                new_note = note_dialog.get_text()
                if new_note != old_nota:
                    self.config['notes'] = new_note
                    self.modified = True
            QMessageBox.information(
                self, "Nota Aggiunta",
                "La nota è stata aggiunta al preventivo."
            )

    def loadConfiguration(self, name):
        """Carica una configurazione dal database"""
        config = load_configuration(name)
        # if self.config
        if config:
            # Aggiorna la configurazione corrente
            self.config = config
            self.current_config_name = name
            self.config_name_label.setText(f"Configurazione: {name}")
            self.updateHeaderLabels()
            self.company_config_is_present = True
            return True
        return False

    def loadClientConfiguration(self, name):
        """Carica una configurazione cliente dal database"""
        client_config = load_customer_configuration(name)
        if client_config:
            # Aggiorna la configurazione cliente corrente
            self.customer_config = client_config

            self.customer_config_is_present = True
            self.updateHeaderLabels()
            return True
        return False

    def saveConfiguration(self, name=None):
        """Salva la configurazione corrente nel database"""
        if not name and not self.current_config_name:
            dialog = dialog_with_icon(
                self, "Salva Configurazione", "Nome della configurazione:", COMPANY_ICON_PATH
            )
            name = None
            if dialog.exec():
                name = dialog.textValue().strip()
            else:
                return False
            if not name:
                return False

        config_name = name or self.current_config_name

        # Salva solo i dati della società emittente e i termini
        company_config = {
            'company_name': self.config.get('company_name', ''),
            'company_address': self.config.get('company_address', ''),
            'company_phone': self.config.get('company_phone', ''),
            'company_email': self.config.get('company_email', ''),
            'company_vat': self.config.get('company_vat', ''),
            'company_logo': self.config.get('company_logo', ''),
            'terms': self.config.get('terms', ''),
            'vat_rate': self.config.get('vat_rate', '22%'),
            'notes': self.config.get('notes', ''),
            'prepared_by': self.config.get('prepared_by', '')
        }

        if save_configuration(config_name, company_config):
            self.current_config_name = config_name
            self.config_name_label.setText(f"Configurazione: {config_name}")
            return True
        return False

    def showConfigWizard(self):
        """Mostra il wizard di configurazione"""
        # Se c'è una configurazione corrente, passa il nome al wizard
        wizard = CompanyConfigWizard(self, self.current_config_name)
        if wizard.exec():
            self.config = wizard.get_config()
            self.updateHeaderLabels()
            return True
        return False

    def updateHeaderLabels(self):
        """Aggiorna le etichette dell'intestazione con i dati di configurazione"""
        if self.config:
            self.company_label.setText(f"Società: {self.config.get('company_name', '')}")
            self.client_label.setText(f"Cliente: {self.customer_config.get('customer_name', '')}")

    def addProduct(self):
        """Aggiunge un nuovo prodotto alla tabella"""
        self.product_table.addRow()
        self.setModified(True)

    def removeProducts(self):
        """Rimuove i prodotti selezionati dalla tabella"""
        self.product_table.removeSelectedRows()
        self.setModified(True)

    def updateTotals(self, net, vat, total):
        """Aggiorna le etichette dei totali"""
        self.total_net_label.setText(f"{net:.2f} €")
        self.total_vat_label.setText(f"{vat:.2f} €")
        self.total_with_vat_label.setText(f"{total:.2f} €")
        self.setModified(True)

    def setModified(self, modified=True):
        """Imposta lo stato di modifica del preventivo"""
        self.modified = modified
        title = self.windowTitle()
        if modified and not title.endswith('*'):
            self.setWindowTitle(f"{title} *")
        elif not modified and title.endswith('*'):
            self.setWindowTitle(title[:-2])

    def generatePDF(self, output_path=None):
        """Genera il PDF del preventivo"""
        # Se non è specificato un percorso di output, usa un file temporaneo
        if not output_path:
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, "preventivo_temp.pdf")

        # Crea il documento PDF
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm
        )

        # Stili
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']
        normal_style = styles['Normal']

        # Elementi del documento
        elements = []

        # Intestazione
        if self.config:
            # Crea una tabella per l'intestazione con logo a sinistra e dati società a destra
            header_data = [[]]

            # Logo (se presente)
            logo_path = self.config.get('company_logo')
            if logo_path and os.path.exists(logo_path):
                img = Image(logo_path)
                img.drawHeight = 2 * cm
                img.drawWidth = 4 * cm
                header_data[0].append(img)
            else:
                # Se non c'è logo, inserisci uno spazio vuoto
                header_data[0].append(Paragraph("", normal_style))

            # Dati società
            company_info = []
            company_info.append(Paragraph(f"<b>{self.config.get('company_name', '')}</b>", subtitle_style))
            company_info.append(Paragraph(self.config.get('company_address', ''), normal_style))
            company_info.append(Paragraph(f"Tel: {self.config.get('company_phone', '')}", normal_style))
            company_info.append(Paragraph(f"Email: {self.config.get('company_email', '')}", normal_style))
            company_info.append(Paragraph(f"P.IVA: {self.config.get('company_vat', '')}", normal_style))

            # Aggiungi i dati società alla tabella
            header_data[0].append(company_info)

            # Crea la tabella dell'intestazione
            header_table = Table(header_data, colWidths=[doc.width / 3, 2 * doc.width / 3])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (0, 0), 'TOP'),  # Allinea il logo in alto
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),  # Allinea il logo a sinistra
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),  # Allinea i dati società a destra
                ('VALIGN', (1, 0), (1, 0), 'TOP'),  # Allinea i dati società in alto
            ]))

            elements.append(header_table)
            elements.append(Spacer(1, 10 * mm))

            # Dati cliente
            elements.append(Paragraph("<b>Cliente:</b>", subtitle_style))
            elements.append(Paragraph(self.customer_config.get('customer_name', ''), normal_style))
            elements.append(Paragraph(self.customer_config.get('customer_address', ''), normal_style))
            elements.append(Paragraph(f"Tel: {self.customer_config.get('customer_phone', '')}", normal_style))
            elements.append(Paragraph(f"Email: {self.customer_config.get('customer_email', '')}", normal_style))
            if self.customer_config.get('customer_vat'):
                elements.append(Paragraph(f"P.IVA: {self.customer_config.get('customer_vat', '')}", normal_style))
            elements.append(Spacer(1, 10 * mm))

        # Titolo preventivo
        elements.append(Paragraph("PREVENTIVO", title_style))
        elements.append(Spacer(1, 5 * mm))

        # Tabella prodotti
        products = self.product_table.getProductsData()
        if products:
            # Intestazioni tabella
            table_data = [self.product_table.labels]

            # Dati prodotti
            for product in products:
                # Creare un Paragraph per la descrizione per permettere il wrapping del testo
                description_paragraph = Paragraph(product['description'],
                                                  ParagraphStyle('DescriptionStyle',
                                                                 fontName='Helvetica',
                                                                 fontSize=10,
                                                                 leading=12))

                table_data.append([
                    product['code'],
                    description_paragraph,
                    str(product['quantity']),
                    f"{product['unit_price']:.2f} €",
                    f"{product['discount']:.2f}%",
                    f"{int(product['vat_rate'])}",
                    f"{product['net_total']:.2f} €"
                ])
            # Calcola le larghezze delle colonne dando priorità alla descrizione
            # La colonna descrizione prenderà il 40% dello spazio disponibile
            # Le altre colonne si divideranno lo spazio rimanente
            table_width = doc.width
            description_width = table_width * 0.4  # 40% per la colonna descrizione
            other_columns_width = (
                                              table_width - description_width) / 6  # Restante spazio diviso equamente tra le altre 6 colonne

            col_widths = [other_columns_width,  # Codice Art.
                          description_width,  # Descrizione (prioritaria)
                          other_columns_width,  # Quantità
                          other_columns_width,  # Prezzo Unit.
                          other_columns_width,  # Sconto
                          other_columns_width,  # IVA
                          other_columns_width]  # Totale Netto

            # Crea la tabella
            table = Table(table_data, repeatRows=1, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),  # Allinea a sinistra la colonna descrizione
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Allinea al centro verticalmente
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('WORDWRAP', (1, 0), (1, -1), True)  # Abilita il ritorno a capo per la colonna descrizione

            ]))

            elements.append(table)
            elements.append(Spacer(1, 10 * mm))

        # Totali
        total_net = float(self.total_net_label.text().replace(" €", ""))
        total_vat = float(self.total_vat_label.text().replace(" €", ""))
        total_with_vat = float(self.total_with_vat_label.text().replace(" €", ""))

        # TODO AGGIUNGERE QUI LA DATA ???????????????????????
        elements.append(Paragraph(f"<b>Totale Netto:</b> {total_net:.2f} €", normal_style))
        elements.append(Paragraph(f"<b>Totale IVA:</b> {total_vat:.2f} €", normal_style))
        elements.append(Paragraph(f"<b>Totale Ivato:</b> {total_with_vat:.2f} €", normal_style))
        elements.append(Spacer(1, 10 * mm))

        # Termini e condizioni
        if self.config.get('terms'):
            elements.append(Paragraph("<b>Termini e Condizioni:</b>", subtitle_style))
            elements.append(Paragraph(self.config.get('terms', ''), normal_style))
            elements.append(Spacer(1, 5 * mm))

        # Note
        if self.config.get('notes'):
            elements.append(Paragraph("<b>Note:</b>", subtitle_style))
            elements.append(Paragraph(self.config.get('notes', ''), normal_style))
            elements.append(Spacer(1, 5 * mm))

        # Preparato da
        if self.config.get('prepared_by'):
            elements.append(
                Paragraph(f"<i>Preventivo preparato da: {self.config.get('prepared_by', '')}</i>", normal_style))

        # Aggiungi spazio prima della firma
        elements.append(Spacer(1, 20 * mm))

        # Aggiungi la sezione per la firma del cliente
        signature_style = ParagraphStyle(
            'Signature',
            parent=normal_style,
            alignment=1,  # Centered
            fontSize=10
        )

        # Crea una tabella per la data e la firma
        signature_data = [
            ["Firma del cliente"],
            ["", "____________________"]
        ]

        signature_table = Table(signature_data, colWidths=[doc.width / 2.0] * 2)
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, 1), 15),  # Spazio per la firma
        ]))

        elements.append(signature_table)

        # Genera il PDF
        doc.build(elements)

        return output_path

    def checkConfigurationComplete(self):
        """Verifica che le configurazioni di società e cliente siano presenti"""
        if not self.config:
            QMessageBox.warning(
                self, "Configurazione Società Mancante",
                "Non è stata impostata alcuna configurazione per la società. Imposta una configurazione prima di procedere."
            )
            return False
        if not self.customer_config:
            QMessageBox.warning(
                self, "Configurazione Cliente Mancante",
                "Non è stata impostata alcuna configurazione per il cliente. Imposta una configurazione prima di procedere."
            )
            return False
        return all([self.check_company_config_is_complete(self.config),
                    self.check_customer_config_is_complete(self.customer_config)])

    def check_company_config_is_complete(self, config):
        # Verifica che ci siano i dati della società emittente
        if not (config.get('company_name') and config.get('company_address') and
                config.get('company_phone') and config.get('company_email') and
                config.get('company_vat')):
            QMessageBox.warning(
                self, "Dati Società Mancanti",
                "I dati della società emittente sono incompleti. Completa la configurazione prima di procedere."
            )
            return False
        return True

    def check_customer_config_is_complete(self, config):
        # Verifica che ci siano i dati del cliente
        if not (config.get('customer_name') and config.get('customer_email')):
            QMessageBox.warning(
                self, "Dati Cliente Mancanti",
                "I dati del cliente sono incompleti. Completa la configurazione prima di procedere."
            )
            return False

        return True

    def previewPDF(self):
        """Mostra l'anteprima del PDF"""
        if not self.checkConfigurationComplete():
            return

        try:
            pdf_path = self.generatePDF()
            preview_dialog = PDFPreviewDialog(pdf_path, self)
            preview_dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nella generazione dell'anteprima: {str(e)}")

    def exportPDF(self):
        """Esporta il preventivo come PDF"""
        if not self.checkConfigurationComplete():
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Esporta PDF", "", "File PDF (*.pdf)"
        )

        if file_path:
            try:
                self.generatePDF(file_path)
                QMessageBox.information(self, "Esportazione Completata",
                                        f"Il preventivo è stato esportato in:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore nell'esportazione: {str(e)}")

    def saveQuote(self):
        """Salva il preventivo nel database"""
        # Implementazione del salvataggio nel database # todo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Per semplicità, in questa versione salviamo solo in un file JSON
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salva Preventivo", "", "File Preventivo (*.prev)"
        )

        if file_path:
            try:
                import json
                config = self.config.copy()
                config['customer'] = self.customer_config
                # Raccogli i dati del preventivo
                data = {
                    'config': config,
                    'products': self.product_table.getProductsData(),
                    'totals': {
                        'net': float(self.total_net_label.text().replace(" €", "")),
                        'vat': float(self.total_vat_label.text().replace(" €", "")),
                        'total': float(self.total_with_vat_label.text().replace(" €", ""))
                    }
                }

                # Salva i dati
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=4)

                self.current_file = file_path
                self.setModified(False)
                QMessageBox.information(self, "Salvataggio Completato",
                                        f"Il preventivo è stato salvato in:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore nel salvataggio: {str(e)}")

    def loadQuote(self):
        """Carica un preventivo salvato"""
        if self.modified:
            reply = QMessageBox.question(
                self, "Preventivo Modificato",
                "Il preventivo corrente è stato modificato. Vuoi salvarlo prima di caricarne un altro?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Cancel:
                return
            elif reply == QMessageBox.StandardButton.Yes:
                self.saveQuote()

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Carica Preventivo", "", "File Preventivo (*.prev)"
        )

        if file_path:
            try:
                import json

                # Carica i dati
                with open(file_path, 'r') as f:
                    data = json.load(f)

                # Imposta la configurazione
                self.customer_config = data.get('config', {}).get('customer', {})
                self.check_customer_config_is_complete(self.customer_config)
                self.config = data.get('config', {})
                self.config.pop('customer')
                self.check_company_config_is_complete(self.config)
                self.updateHeaderLabels()

                # Pulisci la tabella prodotti
                while self.product_table.rowCount() > 0:
                    self.product_table.removeRow(0)

                # Aggiungi i prodotti
                products = data.get('products', [])
                for product in products:
                    row = self.product_table.addRow()

                    # Imposta i valori
                    self.product_table.item(row, ProductTableWidgetColumn.CODE_ITEM.value).setText(
                        product.get(ProductTableJsonFieldsNames.CODE_ITEM.value, ""))
                    self.product_table.item(row, ProductTableWidgetColumn.DESCRIPTION.value).setText(
                        product.get(ProductTableJsonFieldsNames.DESCRIPTION.value, ""))
                    self.product_table.cellWidget(row, ProductTableWidgetColumn.QNT.value).setValue(
                        int(product.get(ProductTableJsonFieldsNames.QNT.value, 1)))
                    self.product_table.cellWidget(row, ProductTableWidgetColumn.PRICE.value).setValue(
                        product.get(ProductTableJsonFieldsNames.PRICE.value, ""))
                    self.product_table.cellWidget(row, ProductTableWidgetColumn.DISCOUNT.value).setValue(
                        product.get(ProductTableJsonFieldsNames.DISCOUNT.value, ""))

                    # Trova l'indice dell'aliquota IVA
                    vat_rate = str(int(product.get(ProductTableJsonFieldsNames.VAT.value, 22)))
                    vat_combo = self.product_table.cellWidget(row, ProductTableWidgetColumn.VAT.value)
                    index = vat_combo.findText(vat_rate)
                    if index >= 0:
                        vat_combo.setCurrentIndex(index)

                # Aggiorna i totali
                self.product_table.updateTotals()

                self.current_file = file_path
                self.setModified(False)
                QMessageBox.information(self, "Caricamento Completato",
                                        f"Il preventivo è stato caricato da:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Errore nel caricamento: {str(e)}")

    def eventFilter(self, obj, event):
        """Filtra gli eventi per gestire il ridimensionamento della finestra"""
        if obj == self and event.type() == event.Type.Resize:
            # Notifica la tabella prodotti che la finestra è stata ridimensionata
            if hasattr(self, 'product_table'):
                self.product_table.parent_resized = True
        elif event.type() == ConfigReadyEvent.EVENT_TYPE and obj == self:
            if self.config_is_ready:
                self.setVisible(True)
                return True
        return super().eventFilter(obj, event)

    def loadSettings(self):
        """Carica le impostazioni dell'applicazione"""
        # Carica le larghezze delle colonne della tabella prodotti
        if hasattr(self, 'product_table'):
            size = self.settings.beginReadArray("ColumnProportions")
            if size > 0:
                proportions = []
                for i in range(size):
                    self.settings.setArrayIndex(i)
                    proportions.append(self.settings.value("proportion", type=float))
                self.product_table.column_proportions = proportions
            self.settings.endArray()

    def saveSettings(self):
        """Salva le impostazioni dell'applicazione"""
        # Salva le larghezze delle colonne della tabella prodotti
        if hasattr(self, 'product_table'):
            self.settings.beginWriteArray("ColumnProportions")
            for i, proportion in enumerate(self.product_table.column_proportions):
                self.settings.setArrayIndex(i)
                self.settings.setValue("proportion", proportion)
            self.settings.endArray()

    def closeEvent(self, event):
        """Gestisce l'evento di chiusura della finestra"""
        accepted = False
        if self.modified:
            reply = QMessageBox.question(
                self, "Preventivo Modificato",
                "Il preventivo è stato modificato. Vuoi salvarlo prima di uscire?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.saveQuote()
                accepted = True
            elif reply == QMessageBox.StandardButton.No:
                accepted = True
            else:
                accepted = False
        else:
            accepted = True
        if accepted:
            self.saveSettings()
            event.accept()
            QApplication.instance().quit()
        else:
            event.ignore()


def _hide_splash(splash):
    """Ridimensiona la splash screen"""
    splash.hide()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Stile moderno

    # Imposta il foglio di stile
    app.setStyleSheet("""
        QMainWindow, QDialog {
            background-color: #f5f5f5;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #cccccc;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 3px;
        }
        QPushButton {
            background-color: #4a86e8;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #3a76d8;
        }
        QPushButton:pressed {
            background-color: #2a66c8;
        }
        QTableWidget {
            gridline-color: #d0d0d0;
        }
        QHeaderView::section {
            background-color: #e0e0e0;
            padding: 4px;
            border: 1px solid #c0c0c0;
            font-weight: bold;
        }
    """)
    app_icon = QIcon("./icons/PreventMaker.ico")  # Formato .ico per Windows
    app.setWindowIcon(app_icon)

    # Crea e mostra lo splash screen
    splash_pixmap = QPixmap("./icons/PreventMaker_logo.png")  # Sostituisci con il percorso del tuo logo
    splash = QSplashScreen(splash_pixmap, Qt.WindowType.WindowStaysOnTopHint)
    hide_splash = partial(_hide_splash, splash)
    splash.show()
    QTimer.singleShot(2000, hide_splash)
    main_window = PreventMaker()
    main_window.show()
    main_window.setVisible(True)
    if main_window.handle_config_provider():
        QApplication.postEvent(main_window, ConfigReadyEvent())
    # window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
