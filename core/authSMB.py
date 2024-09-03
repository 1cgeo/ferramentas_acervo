# -*- coding: utf-8 -*-
from qgis.PyQt import QtWidgets, uic
import os

class AuthSMB(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(AuthSMB, self).__init__(parent)
        self.setupUi()
        self.user = ""
        self.passwd = ""
        self.domain = "1CGEO"  # Valor padrão conforme o arquivo UI

    def setupUi(self):
        # Carrega o arquivo UI
        uic.loadUi(self.getUIPath(), self)
        
        # Conecta os sinais aos slots
        self.ok_bt.clicked.connect(self.validate)
        self.cancel_bt.clicked.connect(self.reject)

    def getUIPath(self):
        return os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'ui', 
            'authSMB.ui'
        )

    def validate(self):
        self.user = self.name_le.text()
        self.passwd = self.passwd_le.text()
        self.domain = self.domain_le.text()
        
        if self.user and self.passwd and self.domain:
            self.accept()
        else:
            QtWidgets.QMessageBox.warning(
                self,
                'Aviso',
                'Todos os campos devem ser preenchidos!'
            )

    @staticmethod
    def getCredentials(parent=None):
        dialog = AuthSMB(parent)
        result = dialog.exec_()
        if result == QtWidgets.QDialog.Accepted:
            return dialog.user, dialog.passwd, dialog.domain
        return None, None, None