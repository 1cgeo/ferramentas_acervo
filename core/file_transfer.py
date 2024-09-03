import os
import platform
import subprocess
from qgis.PyQt.QtCore import QThread, pyqtSignal
from qgis import utils
from .authSMB import AuthSMB

class FileTransferThread(QThread):
    progress_update = pyqtSignal(int, int)
    file_transferred = pyqtSignal(bool, str, str)

    def __init__(self, source_path, destination_path, identifier):
        QThread.__init__(self)
        self.source_path = source_path
        self.destination_path = destination_path
        self.identifier = identifier

    def run(self):
        try:
            if platform.system() == 'Windows':
                success = self.transfer_file_windows()
            else:
                success = self.transfer_file_linux()
            
            self.file_transferred.emit(success, self.destination_path, self.identifier)
        except Exception as e:
            print(f"Erro ao transferir arquivo: {str(e)}")
            self.file_transferred.emit(False, self.destination_path, self.identifier)

    def transfer_file_windows(self):
        source_path = self.source_path.replace("/", "\\")
        dest_path = self.destination_path.replace("/", "\\")
        command = f'copy "{source_path}" "{dest_path}"'
        return self.run_system_command(command)

    def transfer_file_linux(self):
        auth_smb = AuthSMB(utils.iface.mainWindow())
        if not auth_smb.exec_():
            return False

        source_path = self.source_path.replace("\\", "/")
        script_path = os.path.join(os.path.dirname(__file__), 'getFileBySMB.py')
        command = [
            'python3',
            script_path,
            f"smb:{source_path}",
            self.destination_path,
            auth_smb.user,
            auth_smb.passwd,
            auth_smb.domain
        ]
        return self.run_system_command(command)

    def run_system_command(self, command):
        try:
            if isinstance(command, list):
                result = subprocess.run(command, check=True, capture_output=True, text=True)
            else:
                result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            print(f"Erro ao executar comando: {e}")
            return False