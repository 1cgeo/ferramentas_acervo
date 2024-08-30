import os
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QMessageBox, QCheckBox
from qgis.PyQt.QtCore import QDate, Qt

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'edit_project_dialog.ui'))

class EditProjectDialog(QDialog, FORM_CLASS):
    def __init__(self, api_client, project_data=None, parent=None):
        super(EditProjectDialog, self).__init__(parent)
        self.setupUi(self)
        self.api_client = api_client
        self.project_data = project_data
        self.status_types = {}

        self.setup_ui()
        if project_data:
            self.load_project()
        else:
            self.set_default_dates()

    def setup_ui(self):
        self.setWindowTitle("Editar Projeto" if self.project_data else "Adicionar Projeto")
        
        self.load_status_types()

        # Configurar os QDateEdit
        self.startDateEdit.setCalendarPopup(True)
        self.endDateEdit.setCalendarPopup(True)
        self.endDateEdit.setDate(QDate.currentDate())
        self.endDateEdit.setMinimumDate(self.startDateEdit.date())

        # Conectar sinais
        self.startDateEdit.dateChanged.connect(self.update_end_date_minimum)
        self.buttonBox.accepted.connect(self.save_project)
        self.buttonBox.rejected.connect(self.reject)

        self.endDateCheckBox.stateChanged.connect(self.toggle_end_date)

    def load_status_types(self):
        response = self.api_client.get('acervo/dominio/tipo_status_execucao')
        if response and 'dados' in response:
            self.status_types = {item['nome']: item['code'] for item in response['dados']}
            self.statusComboBox.clear()
            self.statusComboBox.addItems(self.status_types.keys())
        else:
            QMessageBox.warning(self, "Erro", "Não foi possível carregar os tipos de status.")

    def update_end_date_minimum(self, new_start_date):
        self.endDateEdit.setMinimumDate(new_start_date)

    def toggle_end_date(self, state):
        self.endDateEdit.setEnabled(not state)

    def load_project(self):
        self.nameLineEdit.setText(self.project_data['nome'])
        self.descriptionTextEdit.setPlainText(self.project_data['descricao'])
        self.startDateEdit.setDate(QDate.fromString(self.project_data['data_inicio'], Qt.ISODate))
        if self.project_data['data_fim']:
            self.endDateEdit.setDate(QDate.fromString(self.project_data['data_fim'], Qt.ISODate))
            self.endDateCheckBox.setChecked(False)
        else:
            self.endDateCheckBox.setChecked(True)
            self.endDateEdit.setEnabled(False)
        self.statusComboBox.setCurrentIndex(self.project_data['status_execucao_id'] - 1)

    def set_default_dates(self):
        today = QDate.currentDate()
        self.startDateEdit.setDate(today)
        self.endDateEdit.setDate(today)
        self.endDateCheckBox.setChecked(False)
        self.endDateEdit.setEnabled(True)

    def save_project(self):
        apiData = {
            'nome': self.nameLineEdit.text(),
            'descricao': self.descriptionTextEdit.toPlainText(),
            'data_inicio': self.startDateEdit.date().toString(Qt.ISODate),
            'data_fim': None if self.endDateCheckBox.isChecked() else self.endDateEdit.date().toString(Qt.ISODate),
            'status_execucao_id': self.statusComboBox.currentIndex() + 1
        }

        if self.project_data:
            apiData['id'] = int(self.project_data['id'])
            success = self.api_client.put('projetos/projeto', apiData)
        else:
            success = self.api_client.post('projetos/projeto', apiData)

        if success:
            QMessageBox.information(self, "Sucesso", "Projeto salvo com sucesso.")
            self.accept()
        else:
            QMessageBox.warning(self, "Erro", "Não foi possível salvar o projeto.")