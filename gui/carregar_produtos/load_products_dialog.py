import os
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QComboBox, QPushButton, QMessageBox
from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsProject, 
    QgsVectorLayer, 
    QgsGeometry, 
    QgsFeature, 
    QgsFields, 
    QgsField,
    QgsWkbTypes,
    QgsCoordinateReferenceSystem,
    Qgis,
    NULL
)

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'load_products_dialog.ui'))

def null_to_none(value):
    return None if value == NULL else value

class LoadProductsDialog(QDialog, FORM_CLASS):
    def __init__(self, iface, api_client, parent=None):
        super(LoadProductsDialog, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.api_client = api_client

        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Carregar Produtos")

        # Configurar o combobox para selecionar a camada
        self.layerComboBox.clear()
        layers = QgsProject.instance().mapLayers().values()
        polygon_layers = []
        for layer in layers:
            if isinstance(layer, QgsVectorLayer) and layer.geometryType() == QgsWkbTypes.PolygonGeometry:
                polygon_layers.append(layer)
                self.layerComboBox.addItem(layer.name(), layer)

        # Se não houver camadas de polígono, desabilitar o combobox e o botão de carregar
        if not polygon_layers:
            self.layerComboBox.setEnabled(False)
            self.loadButton.setEnabled(False)
            QMessageBox.warning(self, "Aviso", "Nenhuma camada de polígono encontrada no projeto.")
        
        # Configurar os comboboxes para correspondência de atributos
        self.setup_attribute_combos()

        # Conectar sinais
        self.layerComboBox.currentIndexChanged.connect(self.setup_attribute_combos)
        self.loadButton.clicked.connect(self.load_products)
        self.createModelLayerButton.clicked.connect(self.create_model_layer)

    def setup_attribute_combos(self):
        layer = self.layerComboBox.currentData()
        if not layer:
            return

        field_names = [field.name() for field in layer.fields()]

        # Dicionário de mapeamento entre os comboboxes e os nomes de campo padrão
        default_fields = {
            self.nomeComboBox: "nome",
            self.miComboBox: "mi",
            self.inomComboBox: "inom",
            self.tipoEscalaComboBox: "tipo_escala_id",
            self.denominadorEscalaComboBox: "denominador_escala_especial",
            self.tipoProdutoComboBox: "tipo_produto_id",
            self.descricaoComboBox: "descricao"
        }

        for combo, default_field in default_fields.items():
            combo.clear()
            combo.addItem("", None)  # Opção vazia
            combo.addItems(field_names)
            
            # Tenta encontrar o índice do campo padrão
            default_index = field_names.index(default_field) + 1 if default_field in field_names else 0
            combo.setCurrentIndex(default_index)

    def load_products(self):
        layer = self.layerComboBox.currentData()
        if not layer:
            QMessageBox.warning(self, "Aviso", "Selecione uma camada válida.")
            return

        produtos = []
        invalid_products = []
        for feature in layer.getFeatures():
            geom = feature.geometry()
            
            if geom.isMultipart():
                invalid_products.append((feature.id(), "Geometria multipart não é suportada"))
                continue

            if geom.type() != QgsWkbTypes.PolygonGeometry:
                invalid_products.append((feature.id(), "Geometria não é um polígono"))
                continue

            wkt = geom.asWkt()

            tipo_escala_id = null_to_none(feature.attribute(self.tipoEscalaComboBox.currentText())) if self.tipoEscalaComboBox.currentText() else None
            denominador_escala_especial = null_to_none(feature.attribute(self.denominadorEscalaComboBox.currentText())) if self.denominadorEscalaComboBox.currentText() else None

            # Validação da escala
            if (tipo_escala_id == 5 and denominador_escala_especial is None) or \
            (tipo_escala_id != 5 and denominador_escala_especial is not None):
                invalid_products.append((feature.id(), "Problema na validação da escala"))
                continue

            produto = {
                "nome": null_to_none(feature.attribute(self.nomeComboBox.currentText())) if self.nomeComboBox.currentText() else None,
                "mi": null_to_none(feature.attribute(self.miComboBox.currentText())) if self.miComboBox.currentText() else None,
                "inom": null_to_none(feature.attribute(self.inomComboBox.currentText())) if self.inomComboBox.currentText() else None,
                "tipo_escala_id": tipo_escala_id,
                "denominador_escala_especial": denominador_escala_especial,
                "tipo_produto_id": null_to_none(feature.attribute(self.tipoProdutoComboBox.currentText())) if self.tipoProdutoComboBox.currentText() else None,
                "descricao": null_to_none(feature.attribute(self.descricaoComboBox.currentText())) if self.descricaoComboBox.currentText() else None,
                "geom": f"SRID=4674;{wkt}"
            }
            produtos.append(produto)

        if invalid_products:
            error_msg = "Os seguintes produtos têm problemas:\n"
            for id, reason in invalid_products:
                error_msg += f"ID {id}: {reason}\n"
            QMessageBox.critical(self, "Erro de Validação", error_msg)
            return

        if not produtos:
            QMessageBox.warning(self, "Aviso", "Nenhum produto válido para carregar.")
            return

        try:
            self.api_client.post('acervo/produtos', {'produtos': produtos})
            QMessageBox.information(self, "Sucesso", "Produtos carregados com sucesso.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar produtos: {str(e)}")

    def create_model_layer(self):
        layer_name = "Modelo de Produtos"
        crs = QgsCoordinateReferenceSystem("EPSG:4674")

        fields = QgsFields()
        fields.append(QgsField("nome", QVariant.String))
        fields.append(QgsField("mi", QVariant.String))
        fields.append(QgsField("inom", QVariant.String))
        fields.append(QgsField("tipo_escala_id", QVariant.Int))
        fields.append(QgsField("denominador_escala_especial", QVariant.Int))
        fields.append(QgsField("tipo_produto_id", QVariant.Int))
        fields.append(QgsField("descricao", QVariant.String))

        layer = QgsVectorLayer("Polygon?crs=EPSG:4674", layer_name, "memory")
        layer.dataProvider().addAttributes(fields)
        layer.updateFields()

        QgsProject.instance().addMapLayer(layer)
        self.iface.messageBar().pushMessage("Sucesso", "Camada modelo criada com sucesso.", level=Qgis.Success)