import requests
from requests.exceptions import RequestException, ConnectionError, Timeout, HTTPError
from qgis.PyQt.QtWidgets import QMessageBox
from urllib.parse import urljoin

class APIClient:
    def __init__(self, settings):
        self.settings = settings
        self.base_url = self.settings.get("server_url", "")
        self.token = None
        self.user_uuid = None
        self.is_admin = False

    def show_error(self, title, message):
        """Exibe uma mensagem de erro para o usuário."""
        QMessageBox.critical(None, title, message)

    def _make_request(self, method, endpoint, data=None, params=None):
        """Método interno para fazer requisições HTTP."""
        url = urljoin(urljoin(self.base_url, '/api/'), endpoint)
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, json=data, params=params)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")

            response.raise_for_status()
            return response.json()

        except ConnectionError:
            self.show_error("Falha na Conexão", "Não foi possível conectar ao servidor. Verifique sua conexão de internet.")
        except Timeout:
            self.show_error("Tempo Esgotado", "O servidor demorou muito para responder. Tente novamente mais tarde.")
        except HTTPError as e:
            self._handle_http_error(e, method)
        except ValueError:
            self.show_error("Resposta Inválida", "O servidor retornou uma resposta inválida. Contate o suporte técnico.")
        except Exception as e:
            self.show_error("Erro Inesperado", f"Ocorreu um erro inesperado: {str(e)}")
        
        return None

    def _handle_http_error(self, e, method):
        """Método interno para lidar com erros HTTP."""
        if e.response.status_code == 401:
            self.show_error("Não Autorizado", "Sua sessão pode ter expirado. Faça login novamente.")
        elif e.response.status_code == 403:
            self.show_error("Acesso Negado", "Você não tem permissão para realizar esta ação.")
        elif e.response.status_code == 404:
            self.show_error("Não Encontrado", "O recurso solicitado não foi encontrado no servidor.")
        elif e.response.status_code == 400:
            self.show_error("Requisição Inválida", "Os dados enviados são inválidos. Verifique as informações e tente novamente.")
        elif e.response.status_code >= 500:
            self.show_error("Erro do Servidor", "O servidor encontrou um erro interno. Tente novamente mais tarde.")
        else:
            self.show_error("Erro de HTTP", f"Ocorreu um erro durante a requisição {method}: {e.response.status_code} - {e.response.reason}")

    def login(self, username, password):
        """Realiza o login do usuário."""
        try:
            response = self._make_request('POST', 'login', data={"usuario": username, "senha": password, "cliente": "sca_qgis"})
            if response and "dados" in response:
                self.token = response["dados"]["token"]
                self.user_uuid = response["dados"]["uuid"]
                self.is_admin = response["dados"]["administrador"]
                return True
        except Exception as e:
            self.show_error("Falha no Login", f"Não foi possível fazer login: {str(e)}")
        return False

    def get(self, endpoint, params=None):
        """Realiza uma requisição GET."""
        return self._make_request('GET', endpoint, params=params)

    def post(self, endpoint, data=None):
        """Realiza uma requisição POST."""
        return self._make_request('POST', endpoint, data=data)

    def put(self, endpoint, data=None):
        """Realiza uma requisição PUT."""
        return self._make_request('PUT', endpoint, data=data)

    def delete(self, endpoint, data=None, params=None):
        """Realiza uma requisição DELETE."""
        return self._make_request('DELETE', endpoint, data=data, params=params)