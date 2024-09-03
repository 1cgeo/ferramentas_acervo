import os
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QMessageBox, QVBoxLayout, QWidget, QScrollArea
from qgis.PyQt.QtCore import Qt
from qgis.gui import QgsCollapsibleGroupBox
from qgis.core import QgsProject, QgsMapLayerType, Qgis

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'product_info_dialog.ui'))

class ProductInfoDialog(QDialog, FORM_CLASS):
    def __init__(self, iface, api_client, parent=None):
        super(ProductInfoDialog, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.api_client = api_client
        self.product_id = None

        self.setup_ui()
        self.loadButton.clicked.connect(self.load_product_info)

    def setup_ui(self):
        self.setWindowTitle("Informações do Produto")

        # Configurar áreas de rolagem para as abas
        for tab in [self.tabGeneral, self.tabDetailed]:
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_content = QWidget()
            scroll_area.setWidget(scroll_content)
            layout = QVBoxLayout(scroll_content)
            tab.layout().addWidget(scroll_area)
            setattr(self, f"{tab.objectName()}_layout", layout)

    def load_product_info(self):
        # Obter a camada ativa
        active_layer = self.iface.activeLayer()
        if not active_layer or active_layer.type() != QgsMapLayerType.VectorLayer:
            self.iface.messageBar().pushMessage("Erro", "Selecione uma camada de produto válida", level=Qgis.Warning)
            return

        # Verificar se a camada é uma view materializada de produto
        if not active_layer.name().startswith('mv_produto_'):
            self.iface.messageBar().pushMessage("Erro", "A camada selecionada não é uma camada de produto válida", level=Qgis.Warning)
            return

        # Obter as feições selecionadas
        selected_features = active_layer.selectedFeatures()
        if len(selected_features) != 1:
            self.iface.messageBar().pushMessage("Erro", "Selecione exatamente uma feição", level=Qgis.Warning)
            return

        # Obter o ID do produto
        self.product_id = selected_features[0]['id']

        try:
            general_info = self.api_client.get(f'acervo/produto/id/{self.product_id}')
            detailed_info = self.api_client.get(f'acervo/produto/detalhado/id/{self.product_id}')

            if general_info and 'dados' in general_info:
                self.display_general_info(general_info['dados'])
            else:
                self.add_info_group(self.tabGeneral_layout, "Erro", "Não foi possível carregar as informações gerais do produto.")

            if detailed_info and 'dados' in detailed_info:
                self.display_detailed_info(detailed_info['dados'])
            else:
                self.add_info_group(self.tabDetailed_layout, "Erro", "Não foi possível carregar as informações detalhadas do produto.")

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar informações do produto: {str(e)}")

    def display_general_info(self, data):
        # Limpar o layout existente
        self.clear_layout(self.tabGeneral_layout)

        self.add_info_group(self.tabGeneral_layout, "Informações Gerais", f"""
        Nome do Produto: {data.get('nome_produto', 'N/A')}
        MI: {data.get('mi', 'N/A')}
        INOM: {data.get('inom', 'N/A')}
        Escala: {data.get('escala', 'N/A')}
        Tipo de Produto: {data.get('tipo_produto', 'N/A')}
        Descrição: {data.get('descricao_produto', 'N/A')}
        Data de Cadastramento: {data.get('data_cadastramento', 'N/A')}
        Usuário de Cadastramento: {data.get('usuario_cadastramento', 'N/A')}
        Data de Modificação: {data.get('data_modificacao', 'N/A')}
        Usuário de Modificação: {data.get('usuario_modificacao', 'N/A')}
        """)

        self.add_info_group(self.tabGeneral_layout, "Última Versão", f"""
        ID: {data.get('versao_id', 'N/A')}
        Versão: {data.get('versao', 'N/A')}
        Nome: {data.get('nome_versao', 'N/A')}
        Tipo: {data.get('tipo_versao', 'N/A')}
        Data de Criação: {data.get('data_criacao', 'N/A')}
        Data de Edição: {data.get('data_edicao', 'N/A')}
        """)

        self.add_info_group(self.tabGeneral_layout, "Informações Adicionais", f"""
        Lote: {data.get('lote_nome', 'N/A')}
        PIT: {data.get('lote_pit', 'N/A')}
        Projeto: {data.get('projeto_nome', 'N/A')}
        Total de Versões: {data.get('num_versoes', 'N/A')}
        Total de Arquivos: {data.get('total_num_files', 'N/A')}
        Tamanho Total (GB): {data.get('total_size_gb', 'N/A')}
        """)

    def display_detailed_info(self, data):
        # Limpar o layout existente
        self.clear_layout(self.tabDetailed_layout)

        self.add_info_group(self.tabDetailed_layout, "Informações do Produto", f"""
        ID do Produto: {data.get('id', 'N/A')}
        Nome: {data.get('nome', 'N/A')}
        MI: {data.get('mi', 'N/A')}
        INOM: {data.get('inom', 'N/A')}
        Escala: {data.get('escala', 'N/A')}
        Denominador de Escala Especial: {data.get('denominador_escala_especial', 'N/A')}
        Tipo de Produto ID: {data.get('tipo_produto_id', 'N/A')}
        Descrição: {data.get('descricao', 'N/A')}
        Data de Cadastramento: {data.get('data_cadastramento', 'N/A')}
        Usuário de Cadastramento: {data.get('usuario_cadastramento', 'N/A')}
        Data de Modificação: {data.get('data_modificacao', 'N/A')}
        Usuário de Modificação: {data.get('usuario_modificacao', 'N/A')}
        """)

        for versao in data.get('versoes', []):
            versao_info = f"""
            UUID: {versao.get('uuid_versao', 'N/A')}
            Versão: {versao.get('versao', 'N/A')}
            Nome: {versao.get('nome_versao', 'N/A')}
            Tipo de Versão ID: {versao.get('tipo_versao_id', 'N/A')}
            Lote ID: {versao.get('lote_id', 'N/A')}
            Descrição: {versao.get('versao_descricao', 'N/A')}
            Data de Criação: {versao.get('versao_data_criacao', 'N/A')}
            Data de Edição: {versao.get('versao_data_edicao', 'N/A')}
            Data de Cadastramento: {versao.get('versao_data_cadastramento', 'N/A')}
            Usuário de Cadastramento: {versao.get('versao_usuario_cadastramento_uuid', 'N/A')}
            Data de Modificação: {versao.get('versao_data_modificacao', 'N/A')}
            Usuário de Modificação: {versao.get('versao_usuario_modificacao_uuid', 'N/A')}
            """

            versao_group = self.add_info_group(self.tabDetailed_layout, f"Versão: {versao.get('versao', 'N/A')}", versao_info)

            for arquivo in versao.get('arquivos', []):
                self.add_info_group(versao_group.layout(), f"Arquivo: {arquivo.get('nome', 'N/A')}", f"""
                ID: {arquivo.get('id', 'N/A')}
                Nome: {arquivo.get('nome', 'N/A')}
                Nome do Arquivo: {arquivo.get('nome_arquivo', 'N/A')}
                Tipo de Arquivo: {arquivo.get('tipo_arquivo', 'N/A')}
                Tamanho (MB): {arquivo.get('tamanho_mb', 'N/A')}
                Checksum: {arquivo.get('checksum', 'N/A')}
                Situação BDGEx ID: {arquivo.get('situacao_bdgex_id', 'N/A')}
                Órgão Produtor: {arquivo.get('orgao_produtor', 'N/A')}
                Descrição: {arquivo.get('descricao', 'N/A')}
                """)

    def add_info_group(self, parent_layout, title, content):
        group = QgsCollapsibleGroupBox(title)
        group.setCollapsed(False)
        layout = QVBoxLayout()
        group.setLayout(layout)
        label = QLabel(content)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(label)
        parent_layout.addWidget(group)
        return group

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()