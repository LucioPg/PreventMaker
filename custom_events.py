# Definizione del custom event
from PyQt6.QtCore import QEvent


class ConfigReadyEvent(QEvent):
    EVENT_TYPE = QEvent.Type(QEvent.Type.User + 1)

    def __init__(self):
        super().__init__(self.EVENT_TYPE)
