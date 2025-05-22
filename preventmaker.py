import sys
import os
# import mysql.connector utilizzare sqlite3 invece
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QTextEdit, QPushButton, QTableWidget, 
                            QTableWidgetItem, QSpinBox, QDoubleSpinBox, QComboBox, 
                            QFileDialog, QMessageBox, QWizard, QWizardPage, QFormLayout,
                            QTabWidget, QGroupBox, QCheckBox, QDialog)
from PyQt6.QtGui import QPixmap, QIcon, QFont, QDoubleValidator
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtPrintSupport import QPrinter
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
import PyPDF2
import tempfile

class ConfigWizard(QWizard):
    """Wizard per la configurazione iniziale del preventivo"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurazione Preventivo")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        
        # Aggiungi le pagine del wizard
        self.addPage(CompanyPage())
        self.addPage(ClientPage())
        self.addPage(TermsPage())
        
        self.setMinimumSize(600, 400)
    
    def getConfig(self):
        """Restituisce la configurazione completa dal wizard"""
        config = {
            # Dati società
            'company_name': self.field('company_name'),
            'company_address': self.field('company_address'),
            'company_phone': self.field('company_phone'),
            'company_email': self.field('company_email'),
            'company_vat': self.field('company_vat'),
            'company_logo': self.field('company_logo'),
            
            # Dati cliente
            'client_name': self.field('client_name'),
            'client_address': self.field('client_address'),
            'client_phone': self.field('client_phone'),
            'client_email': self.field('client_email'),
            'client_vat': self.field('client_vat'),
            
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
        
        # Registra i campi
        self.registerField('company_name*', self.company_name)
        self.registerField('company_address', self.company_address, 'plainText')
        self.registerField('company_phone', self.company_phone)
        self.registerField('company_email', self.company_email)
        self.registerField('company_vat*', self.company_vat)
        self.registerField('company_logo', self.logo_path)
        
        # Aggiungi i campi al layout
        layout.addRow("Nome Società:", self.company_name)
        layout.addRow("Indirizzo:", self.company_address)
        layout.addRow("Telefono:", self.company_phone)
        layout.addRow("Email:", self.company_email)
        layout.addRow("Partita IVA:", self.company_vat)
        layout.addRow("Logo:", logo_layout)
        
        self.setLayout(layout)
    
    def browseLogo(self):
        """Apre un dialogo per selezionare il logo"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Seleziona Logo", "", "Immagini (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_name:
            self.logo_path.setText(file_name)

class ClientPage(QWizardPage):
    """Pagina per i dati del cliente"""
    
    def __init__(self):
        super().__init__()
        self.setTitle("Dati Cliente")
        self.setSubTitle("Inserisci i dati del cliente destinatario")
        
        layout = QFormLayout()
        
        # Campi per i dati del cliente
        self.client_name = QLineEdit()
        self.client_address = QTextEdit()
        self.client_phone = QLineEdit()
        self.client_email = QLineEdit()
        self.client_vat = QLineEdit()
        
        # Registra i campi
        self.registerField('client_name*', self.client_name)
        self.registerField('client_address', self.client_address, 'plainText')
        self.registerField('client_phone', self.client_phone)
        self.registerField('client_email', self.client_email)
        self.registerField('client_vat', self.client_vat)
        
        # Aggiungi i campi al layout
        layout.addRow("Nome Cliente:", self.client_name)
        layout.addRow("Indirizzo:", self.client_address)
        layout.addRow("Telefono:", self.client_phone)
        layout.addRow("Email:", self.client_email)
        layout.addRow("Partita IVA:", self.client_vat)
        
        self.setLayout(layout)

class TermsPage(QWizardPage):
    """Pagina per termini e condizioni"""
    
    def __init__(self):
        super().__init__()
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
        self.notes.setPlaceholderText("Inserisci qui eventuali note...")
        
        # Preparato da
        self.prepared_by = QLineEdit()
        
        # Registra i campi
        self.registerField('terms', self.terms, 'plainText')
        self.registerField('vat_rate', self.vat_rate, 'currentText')
        self.registerField('notes', self.notes, 'plainText')
        self.registerField('prepared_by', self.prepared_by)
        
        # Aggiungi i campi al layout
        layout.addRow("Termini e Condizioni:", self.terms)
        layout.addRow("Aliquota IVA:", self.vat_rate)
        layout.addRow("Note:", self.notes)
        layout.addRow("Preparato da:", self.prepared_by)
        
        self.setLayout(layout)

class ProductTable(QTableWidget):
    """Tabella per i prodotti del preventivo"""
    
    totalChanged = pyqtSignal(float, float, float)  # Segnale per totale netto, iva, totale ivato
    
    def __init__(self, parent=None):
        super().__init__(0, 6, parent)
        self.setHorizontalHeaderLabels([
            "Descrizione", "Quantità", "Prezzo Unitario (€)", 
            "Sconto (%)", "IVA (%)", "Totale Netto (€)"
        ])
        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Connetti il segnale di modifica cella
        self.itemChanged.connect(self.updateTotals)
    
    def addRow(self):
        """Aggiunge una nuova riga alla tabella"""
        row = self.rowCount()
        self.insertRow(row)
        
        # Crea gli elementi della riga
        desc_item = QTableWidgetItem("")
        
        # Usa spinbox per quantità
        qty_spin = QSpinBox()
        qty_spin.setRange(1, 9999)
        qty_spin.setValue(1)
        qty_spin.valueChanged.connect(self.updateTotals)
        
        # Usa doublespinbox per prezzo unitario
        price_spin = QDoubleSpinBox()
        price_spin.setRange(0, 999999.99)
        price_spin.setDecimals(2)
        price_spin.setSuffix(" €")
        price_spin.valueChanged.connect(self.updateTotals)
        
        # Usa doublespinbox per sconto
        discount_spin = QDoubleSpinBox()
        discount_spin.setRange(0, 100)
        discount_spin.setDecimals(2)
        discount_spin.setSuffix(" %")
        discount_spin.valueChanged.connect(self.updateTotals)
        
        # Usa combobox per IVA
        vat_combo = QComboBox()
        vat_combo.addItems(["22", "10", "4", "0"])
        vat_combo.currentTextChanged.connect(self.updateTotals)
        
        # Totale netto (calcolato)
        total_item = QTableWidgetItem("0.00 €")
        total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        # Imposta gli elementi nella riga
        self.setItem(row, 0, desc_item)
        self.setCellWidget(row, 1, qty_spin)
        self.setCellWidget(row, 2, price_spin)
        self.setCellWidget(row, 3, discount_spin)
        self.setCellWidget(row, 4, vat_combo)
        self.setItem(row, 5, total_item)
        
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
        
        for row in range(self.rowCount()):
            if isinstance(self.cellWidget(row, 1), QSpinBox) and \
               isinstance(self.cellWidget(row, 2), QDoubleSpinBox) and \
               isinstance(self.cellWidget(row, 3), QDoubleSpinBox) and \
               isinstance(self.cellWidget(row, 4), QComboBox):
                
                qty = self.cellWidget(row, 1).value()
                price = self.cellWidget(row, 2).value()
                discount = self.cellWidget(row, 3).value() / 100.0
                vat_rate = float(self.cellWidget(row, 4).currentText()) / 100.0
                
                # Calcola il netto
                net = qty * price * (1 - discount)
                
                # Calcola l'IVA
                vat = net * vat_rate
                
                # Aggiorna il totale netto nella tabella
                if self.item(row, 5):
                    self.item(row, 5).setText(f"{net:.2f} €")
                
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
            if self.item(row, 0) and isinstance(self.cellWidget(row, 1), QSpinBox):
                product = {
                    'description': self.item(row, 0).text(),
                    'quantity': self.cellWidget(row, 1).value(),
                    'unit_price': self.cellWidget(row, 2).value(),
                    'discount': self.cellWidget(row, 3).value(),
                    'vat_rate': float(self.cellWidget(row, 4).currentText()),
                    'net_total': float(self.item(row, 5).text().replace(" €", ""))
                }
                products.append(product)
        
        return products

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

class PreventMaker(QMainWindow):
    """Finestra principale dell'applicazione"""
    
    def __init__(self):
        super().__init__()
        self.initUI()
        self.current_file = None
        self.modified = False
        self.config = {}
        
        # Chiedi la configurazione all'avvio
        self.showConfigWizard()
    
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
        header_layout.addWidget(self.company_label)
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
        
        self.config_btn = QPushButton("Configurazione")
        self.config_btn.clicked.connect(self.showConfigWizard)
        
        actions_layout.addWidget(self.preview_btn)
        actions_layout.addWidget(self.save_btn)
        actions_layout.addWidget(self.load_btn)
        actions_layout.addWidget(self.export_btn)
        actions_layout.addStretch()
        actions_layout.addWidget(self.config_btn)
        
        # Assembla il layout principale
        main_layout.addLayout(header_layout)
        main_layout.addWidget(products_group)
        main_layout.addWidget(totals_group)
        main_layout.addLayout(actions_layout)
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Aggiungi un prodotto di default
        self.addProduct()
    
    def showConfigWizard(self):
        """Mostra il wizard di configurazione"""
        wizard = ConfigWizard(self)
        if wizard.exec():
            self.config = wizard.getConfig()
            self.updateHeaderLabels()
    
    def updateHeaderLabels(self):
        """Aggiorna le etichette dell'intestazione con i dati di configurazione"""
        if self.config:
            self.company_label.setText(f"Società: {self.config.get('company_name', '')}")
            self.client_label.setText(f"Cliente: {self.config.get('client_name', '')}")
    
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
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
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
            # Logo (se presente)
            logo_path = self.config.get('company_logo')
            if logo_path and os.path.exists(logo_path):
                img = Image(logo_path)
                img.drawHeight = 2*cm
                img.drawWidth = 4*cm
                elements.append(img)
                elements.append(Spacer(1, 5*mm))
            
            # Dati società
            elements.append(Paragraph(f"<b>{self.config.get('company_name', '')}</b>", subtitle_style))
            elements.append(Paragraph(self.config.get('company_address', ''), normal_style))
            elements.append(Paragraph(f"Tel: {self.config.get('company_phone', '')}", normal_style))
            elements.append(Paragraph(f"Email: {self.config.get('company_email', '')}", normal_style))
            elements.append(Paragraph(f"P.IVA: {self.config.get('company_vat', '')}", normal_style))
            elements.append(Spacer(1, 10*mm))
            
            # Dati cliente
            elements.append(Paragraph("<b>Cliente:</b>", subtitle_style))
            elements.append(Paragraph(self.config.get('client_name', ''), normal_style))
            elements.append(Paragraph(self.config.get('client_address', ''), normal_style))
            elements.append(Paragraph(f"Tel: {self.config.get('client_phone', '')}", normal_style))
            elements.append(Paragraph(f"Email: {self.config.get('client_email', '')}", normal_style))
            if self.config.get('client_vat'):
                elements.append(Paragraph(f"P.IVA: {self.config.get('client_vat', '')}", normal_style))
            elements.append(Spacer(1, 10*mm))
        
        # Titolo preventivo
        elements.append(Paragraph("PREVENTIVO", title_style))
        elements.append(Spacer(1, 5*mm))
        
        # Tabella prodotti
        products = self.product_table.getProductsData()
        if products:
            # Intestazioni tabella
            table_data = [["Descrizione", "Quantità", "Prezzo Unit.", "Sconto", "IVA", "Totale Netto"]]
            
            # Dati prodotti
            for product in products:
                table_data.append([
                    product['description'],
                    str(product['quantity']),
                    f"{product['unit_price']:.2f} €",
                    f"{product['discount']:.2f}%",
                    f"{product['vat_rate']:.2f}%",
                    f"{product['net_total']:.2f} €"
                ])
            
            # Crea la tabella
            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 10*mm))
        
        # Totali
        total_net = float(self.total_net_label.text().replace(" €", ""))
        total_vat = float(self.total_vat_label.text().replace(" €", ""))
        total_with_vat = float(self.total_with_vat_label.text().replace(" €", ""))
        
        elements.append(Paragraph(f"<b>Totale Netto:</b> {total_net:.2f} €", normal_style))
        elements.append(Paragraph(f"<b>Totale IVA:</b> {total_vat:.2f} €", normal_style))
        elements.append(Paragraph(f"<b>Totale Ivato:</b> {total_with_vat:.2f} €", normal_style))
        elements.append(Spacer(1, 10*mm))
        
        # Termini e condizioni
        if self.config.get('terms'):
            elements.append(Paragraph("<b>Termini e Condizioni:</b>", subtitle_style))
            elements.append(Paragraph(self.config.get('terms', ''), normal_style))
            elements.append(Spacer(1, 5*mm))
        
        # Note
        if self.config.get('notes'):
            elements.append(Paragraph("<b>Note:</b>", subtitle_style))
            elements.append(Paragraph(self.config.get('notes', ''), normal_style))
            elements.append(Spacer(1, 5*mm))
        
        # Preparato da
        if self.config.get('prepared_by'):
            elements.append(Paragraph(f"<i>Preventivo preparato da: {self.config.get('prepared_by', '')}</i>", normal_style))
        
        # Genera il PDF
        doc.build(elements)
        
        return output_path
    
    def previewPDF(self):
        """Mostra l'anteprima del PDF"""
        try:
            pdf_path = self.generatePDF()
            preview_dialog = PDFPreviewDialog(pdf_path, self)
            preview_dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore nella generazione dell'anteprima: {str(e)}")
    
    def exportPDF(self):
        """Esporta il preventivo come PDF"""
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
        # Implementazione del salvataggio nel database
        # Per semplicità, in questa versione salviamo solo in un file JSON
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salva Preventivo", "", "File Preventivo (*.prev)"
        )
        
        if file_path:
            try:
                import json
                
                # Raccogli i dati del preventivo
                data = {
                    'config': self.config,
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
                self.config = data.get('config', {})
                self.updateHeaderLabels()
                
                # Pulisci la tabella prodotti
                while self.product_table.rowCount() > 0:
                    self.product_table.removeRow(0)
                
                # Aggiungi i prodotti
                products = data.get('products', [])
                for product in products:
                    row = self.product_table.addRow()
                    
                    # Imposta i valori
                    self.product_table.item(row, 0).setText(product.get('description', ''))
                    self.product_table.cellWidget(row, 1).setValue(product.get('quantity', 1))
                    self.product_table.cellWidget(row, 2).setValue(product.get('unit_price', 0.0))
                    self.product_table.cellWidget(row, 3).setValue(product.get('discount', 0.0))
                    
                    # Trova l'indice dell'aliquota IVA
                    vat_rate = str(int(product.get('vat_rate', 22)))
                    vat_combo = self.product_table.cellWidget(row, 4)
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
    
    def closeEvent(self, event):
        """Gestisce l'evento di chiusura della finestra"""
        if self.modified:
            reply = QMessageBox.question(
                self, "Preventivo Modificato",
                "Il preventivo è stato modificato. Vuoi salvarlo prima di uscire?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.saveQuote()
                event.accept()
            elif reply == QMessageBox.StandardButton.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

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
    
    window = PreventMaker()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
