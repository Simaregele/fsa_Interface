import json
import os
from typing import Dict, Any


class Config:
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        # Получаем абсолютный путь к директории, где находится текущий файл (config.py)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Перемещаемся на уровень выше, чтобы достичь корневой директории проекта
        project_root = os.path.dirname(current_dir)
        # Формируем путь к файлу config.json
        config_path = os.path.join(project_root, 'config.json')

        try:
            with open(config_path) as config_file:
                self._config = json.load(config_file)

            # Проверяем наличие необходимых полей
            required_fields = ['api_base_url', 'auth_url', 'search_endpoint', 'document_endpoints', 'sync_endpoints']
            for field in required_fields:
                if field not in self._config:
                    raise ValueError(f"{field} отсутствует в файле config.json")

            # Проверяем наличие подполей в document_endpoints и sync_endpoints
            for endpoint_type in ['document_endpoints', 'sync_endpoints']:
                if 'declaration' not in self._config[endpoint_type] or 'certificate' not in self._config[endpoint_type]:
                    raise ValueError(f"В {endpoint_type} отсутствуют поля 'declaration' или 'certificate'")

        except FileNotFoundError:
            raise FileNotFoundError(f"Файл конфигурации не найден по пути: {config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Ошибка при разборе JSON в файле: {config_path}")

    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение по ключу"""
        return self._config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """Поддержка доступа через квадратные скобки"""
        return self._config[key]

    @classmethod
    def get_instance(cls):
        """Получить экземпляр конфига"""
        if cls._instance is None:
            cls._instance = Config()
        return cls._instance

    def get_service_url(self, service: str, endpoint: str, **path_vars) -> str:
        """
        Возвращает полный URL для указанного сервиса и эндпоинта,
        используя base_url или remote_url в зависимости от config['mode'].
        """
        mode = self._config.get('mode')
        svc = self._config['services'][service]
        base = svc['remote_url'] if mode == 'remote' else svc['base_url']
        url = base + svc['endpoints'][endpoint]
        return url.format(**path_vars)


# Для обратной совместимости
def load_config() -> Config:
    """
    Функция для совместимости.
    Возвращает экземпляр Config для доступа к методам и данным.
    """
    return Config.get_instance()
