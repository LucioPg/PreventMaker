from enum import Enum

from PyQt6.QtWidgets import QTableWidgetItem, QSpinBox, QDoubleSpinBox, QComboBox


class ProductTableWidgetColumn(Enum):
    CODE_ITEM = 0
    DESCRIPTION = 1
    QNT = 2
    PRICE = 3
    DISCOUNT = 4
    VAT = 5
    NET = 6

class ProductTableJsonFieldsNames(Enum):
    CODE_ITEM = "code"
    DESCRIPTION = "description"
    QNT = "quantity"
    PRICE = "unit_price"
    DISCOUNT = "discount"
    VAT = "vat_rate"
    NET = "net_total"

class ProductTableWidget(Enum):
    CODE_ITEM = QTableWidgetItem
    DESCRIPTION = QTableWidgetItem
    QNT = QSpinBox
    PRICE = QDoubleSpinBox
    DISCOUNT = QDoubleSpinBox
    VAT = QComboBox
    NET = QTableWidgetItem
