from .projetos.manage_projects_dialog import ManageProjectsDialog
from .lotes.manage_lotes_dialog import ManageLotesDialog
from .usuarios.manage_users_dialog import ManageUsersDialog
from .volumes.manage_volumes_dialog import ManageVolumesDialog
from .volume_tipo_produto.manage_volume_tipo_produto_dialog import ManageVolumeTipoProdutoDialog

PANEL_MAPPING = {
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
    }
}