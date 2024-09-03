import os
import hashlib
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QMessageBox, QProgressBar, QVBoxLayout
from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal
from qgis.core import QgsProject, QgsVectorLayer, QgsWkbTypes, Qgis, NULL
from ...core.file_transfer import FileTransferThread

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'load_systematic_files_dialog.ui'))

def null_to_none(value):
    return None if value == NULL else value

class LoadSystematicFilesDialog(QDialog, FORM_CLASS):
    def __init__(self, iface, api_client, parent=None):
        super(LoadSystematicFilesDialog, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.api_client = api_client
        self.transfer_threads = []
        self.versoes = []
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Carregar Arquivos a Produtos Sistemáticos")

        # Configurar o combobox para selecionar a camada
        self.layerComboBox.clear()
        layers = QgsProject.instance().mapLayers().values()
        valid_layers = []
        for layer in layers:
            if isinstance(layer, QgsVectorLayer) and layer.geometryType() == QgsWkbTypes.NullGeometry:
                valid_layers.append(layer)
                self.layerComboBox.addItem(layer.name(), layer)

        # Se não houver camadas válidas, desabilitar o combobox e o botão de carregar
        if not valid_layers:
            self.layerComboBox.setEnabled(False)
            self.loadButton.setEnabled(False)
            QMessageBox.warning(self, "Aviso", "Nenhuma camada tabular encontrada no projeto.")

        self.progressBar = QProgressBar(self)
        self.progressBar.setVisible(False)
        self.verticalLayout.addWidget(self.progressBar)

        # Conectar sinais
        self.loadButton.clicked.connect(self.initiate_load_process)
        self.createModelLayerButton.clicked.connect(self.create_model_layer)

    def initiate_load_process(self):
        layer = self.layerComboBox.currentData()
        if not layer:
            QMessageBox.warning(self, "Aviso", "Selecione uma camada válida.")
            return

        is_valid, error_message = self.validate_layer_structure(layer)
        if not is_valid:
            QMessageBox.critical(self, "Erro de Estrutura", f"A camada não possui a estrutura correta. {error_message}")
            return

        self.versoes = self.prepare_versoes_data(layer)
        if not self.versoes:
            QMessageBox.warning(self, "Aviso", "Nenhuma versão válida para carregar.")
            return

        try:
            response = self.api_client.post('arquivo/verifica_sistematico_versoes_multiplos_arquivos', {'versoes': self.versoes})
            self.process_server_response(response)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao verificar o processo de carregamento: {str(e)}")

    def process_server_response(self, response):
        if 'transfer_info' not in response:
            QMessageBox.critical(self, "Erro", "Resposta do servidor inválida.")
            return

        self.progressBar.setVisible(True)
        total_files = sum(len(files) for files in response['transfer_info'].values())
        self.progressBar.setRange(0, total_files)
        self.progressBar.setValue(0)

        for versao_id, file_infos in response['transfer_info'].items():
            for file_info in file_infos:
                local_path = self.get_local_path(file_info['destination_path'], versao_id)
                
                thread = FileTransferThread(local_path, file_info['destination_path'], versao_id)
                thread.progress_update.connect(self.update_file_progress)
                thread.file_transferred.connect(self.file_transfer_finished)
                self.transfer_threads.append(thread)
                thread.start()

    def get_local_path(self, destination_path, versao_id):
        # Encontrar o arquivo correspondente na versão
        versao = next(v for v in self.versoes if v['versao']['uuid_versao'] == versao_id)
        arquivo = next(a for a in versao['arquivos'] if os.path.basename(destination_path) == f"{a['nome_arquivo']}{a['extensao']}")
        
        # Retornar o caminho local fornecido pelo usuário
        return arquivo['path']

    def calculate_checksum(self, file_path):
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def update_file_progress(self, bytes_sent, total_bytes):
        # Atualizar a barra de progresso geral
        current_value = self.progressBar.value()
        self.progressBar.setValue(current_value + 1)

    def file_transfer_finished(self, success, file_path, versao_id):
        if not success:
            QMessageBox.critical(self, "Erro", f"Falha ao transferir o arquivo: {file_path}")
            self.cancel_all_transfers()
            return

        if all(thread.isFinished() for thread in self.transfer_threads if thread.versao_id == versao_id):
            versao_data = next(v for v in self.versoes if v['uuid_versao'] == versao_id)
            try:
                self.api_client.post('arquivo/sistematico_versoes_multiplos_arquivos', {'versao': versao_data})
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao finalizar o carregamento da versão: {str(e)}")
                self.cancel_all_transfers()
                return

        if self.progressBar.value() == self.progressBar.maximum():
            QMessageBox.information(self, "Sucesso", "Todos os arquivos foram transferidos com sucesso.")
            self.accept()

    def cancel_all_transfers(self):
        for thread in self.transfer_threads:
            if thread.isRunning():
                thread.terminate()
        QMessageBox.warning(self, "Aviso", "O processo de carregamento foi cancelado devido a um erro.")
        self.reject()

    def validate_layer_structure(self, layer):
        required_fields = [
            'produto_inom', 'uuid_versao', 'versao', 'nome_versao', 'tipo_versao_id',
            'lote_id', 'metadado', 'descricao', 'data_criacao', 'data_edicao',
            'path', 'situacao_bdgex_id', 'orgao_produtor',
            'descricao_arquivo', 'metadado_arquivo', 'tipo_arquivo_id', 'nome'
        ]
        
        field_names = [field.name() for field in layer.fields()]
        
        missing_fields = [field for field in required_fields if field not in field_names]
        
        if missing_fields:
            return False, f"Campos ausentes: {', '.join(missing_fields)}"
        
        return True, ""

    def prepare_versoes_data(self, layer):
        versoes = {}
        invalid_features = []
        for feature in layer.getFeatures():
            # Validação de campos não nulos
            non_null_fields = ['produto_inom', 'uuid_versao', 'versao', 'nome_versao', 'tipo_versao_id',
                               'data_criacao', 'data_edicao', 'path', 'situacao_bdgex_id', 'orgao_produtor',
                               'tipo_arquivo_id', 'nome']
            
            null_fields = [field for field in non_null_fields if feature[field] == NULL]
            if null_fields:
                invalid_features.append((feature.id(), f"Campos não podem ser nulos: {', '.join(null_fields)}"))
                continue

            produto_inom = feature['produto_inom']
            versao_id = feature['uuid_versao']
            
            if versao_id not in versoes:
                versoes[versao_id] = {
                    "produto_inom": produto_inom,
                    "versao": {
                        "uuid_versao": versao_id,
                        "versao": feature['versao'],
                        "nome": feature['nome_versao'],
                        "tipo_versao_id": feature['tipo_versao_id'],
                        "lote_id": null_to_none(feature['lote_id']),
                        "metadado": null_to_none(feature['metadado']),
                        "descricao": null_to_none(feature['descricao']),
                        "data_criacao": feature['data_criacao'],
                        "data_edicao": feature['data_edicao'],
                    },
                    "arquivos": []
                }

            file_path = feature['path']
            if not os.path.exists(file_path):
                invalid_features.append((feature.id(), f"Arquivo não encontrado: {file_path}"))
                continue

            nome_arquivo = os.path.basename(file_path)
            extensao = os.path.splitext(nome_arquivo)[1][1:]
            checksum = self.calculate_checksum(file_path)

            arquivo = {
                "nome": feature['nome'],
                "nome_arquivo": nome_arquivo,
                "extensao": extensao,
                "situacao_bdgex_id": feature['situacao_bdgex_id'],
                "orgao_produtor": feature['orgao_produtor'],
                "descricao": null_to_none(feature['descricao_arquivo']),
                "metadado": null_to_none(feature['metadado_arquivo']),
                "tipo_arquivo_id": feature['tipo_arquivo_id'],
                "tamanho_mb": os.path.getsize(file_path) / (1024 * 1024),
                "path": file_path,
                "checksum": checksum
            }
            
            versoes[versao_id]["arquivos"].append(arquivo)

        if invalid_features:
            error_msg = "As seguintes features têm problemas:\n"
            for id, reason in invalid_features:
                error_msg += f"ID {id}: {reason}\n"
            QMessageBox.critical(self, "Erro de Validação", error_msg)
            return None

        return list(versoes.values())

    def create_model_layer(self):
        layer_name = "Modelo de Versões Sistemáticas"
        
        uri = "NoGeometry?crs=EPSG:4326&field=produto_inom:string&field=uuid_versao:string&field=versao:string&field=nome_versao:string&field=tipo_versao_id:integer&field=lote_id:integer&field=metadado:string&field=descricao:string&field=data_criacao:date&field=data_edicao:date&field=path:string&field=situacao_bdgex_id:integer&field=orgao_produtor:string&field=descricao_arquivo:string&field=metadado_arquivo:string&field=tipo_arquivo_id:integer&field=nome:string"
        
        layer = QgsVectorLayer(uri, layer_name, "memory")
        
        if not layer.isValid():
            QMessageBox.critical(self, "Erro", "Não foi possível criar a camada modelo.")
            return

        QgsProject.instance().addMapLayer(layer)
        self.iface.messageBar().pushMessage("Sucesso", "Camada modelo criada com sucesso.", level=Qgis.Success)