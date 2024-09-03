from .projetos.manage_projects_dialog import ManageProjectsDialog
from .lotes.manage_lotes_dialog import ManageLotesDialog
from .usuarios.manage_users_dialog import ManageUsersDialog
from .volumes.manage_volumes_dialog import ManageVolumesDialog
from .volume_tipo_produto.manage_volume_tipo_produto_dialog import ManageVolumeTipoProdutoDialog
from .verificar_inconsistencias.verificar_inconsistencias_dialog import VerificarInconsistenciasDialog
from .carregar_produtos.load_products_dialog import LoadProductsDialog
from .carregar_arquivos_sistematico.load_systematic_files_dialog import LoadSystematicFilesDialog

PANEL_MAPPING = {
    "Carregar Produtos": {
        "class": LoadProductsDialog,
        "category": "Funções de Administrador",
        "admin_only": True
    },
    "Carregar Arquivos Sistemáticos": {
        "class": LoadSystematicFilesDialog,
        "category": "Funções de Administrador",
        "admin_only": True
    },
    "Gerenciar Volumes": {
        "class": ManageVolumesDialog,
        "category": "Funções de Administrador",
        "admin_only": True
    },
    "Gerenciar Relacionamento Volume e Tipo de Produto": {
        "class": ManageVolumeTipoProdutoDialog,
        "category": "Funções de Administrador",
        "admin_only": True
    },
    "Gerenciar Projetos": {
        "class": ManageProjectsDialog,
        "category": "Funções de Administrador",
        "admin_only": True
    },
    "Gerenciar Lotes": {
        "class": ManageLotesDialog,
        "category": "Funções de Administrador",
        "admin_only": True
    },
    "Gerenciar Usuários": {
        "class": ManageUsersDialog,
        "category": "Funções de Administrador",
        "admin_only": True
    },
    "Verificar Inconsistências": {
        "class": VerificarInconsistenciasDialog,
        "category": "Funções de Administrador",
        "admin_only": True
    }
}