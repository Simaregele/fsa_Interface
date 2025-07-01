import requests
import json
from typing import Dict, Any, Union, Optional, Tuple
import logging
from config.config import load_config
from src.api.client import FSAApiClient  # локальный импорт, чтобы избежать циклов
from src.generate_preview.new_cert_api_values import render_data_to_api



config = load_config()

# Настройка логирования модуля
logger = logging.getLogger(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def utf8_encode_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Рекурсивно кодирует все строковые значения в словаре в UTF-8."""
    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = value.encode('utf-8').decode('utf-8')
        elif isinstance(value, dict):
            result[key] = utf8_encode_dict(value)
        elif isinstance(value, list):
            result[key] = [
                utf8_encode_dict(item) if isinstance(item, dict)
                else item.encode('utf-8').decode('utf-8') if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            result[key] = value
    return result



def stringify_values(obj):
    if isinstance(obj, dict):
        return {k: stringify_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [stringify_values(i) for i in obj]
    elif obj is None:
        return ''
    else:
        return str(obj)




def build_payload() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Строит JSON-payload для сервиса генерации документов и возвращает его вместе с объединёнными данными."""
    client = FSAApiClient.get_instance()
    cached = client.get_last_merged_data()
    if cached is None:
        raise ValueError("Нет данных merged_data в кэше. Сначала объедините данные, затем вызывайте генерацию.")

    # Используем уже существующий (и, возможно, отредактированный) кэш
    merged_data = cached  # type: ignore[arg-type]

    utf8_data = utf8_encode_dict(merged_data)
    # Новое: формируем словарь с заполенными значениями шаблона
    templated = render_data_to_api(merged_data)

    # Применяем пользовательские overrides (редактируемые в UI)
    doc_id = str(merged_data.get("ID") or merged_data.get("search_ID") or merged_data.get("RegistryID") or "")
    templated.update(client.get_template_overrides(doc_id))

    # Добавляем values внутрь данных, чтобы не отправлять их отдельным полем
    utf8_data_with_values = dict(utf8_data)
    utf8_data_with_values["values"] = templated

    payload = {
        "data": utf8_data_with_values,
    }
    return payload, merged_data


def generate_documents(details: Dict[str, Any], search_data: Optional[Dict[str, Any]] = None) -> Dict[str, Union[bytes, str]]:
    try:
        # Формируем payload в отдельной функции
        payload, merged_data = build_payload()

        generate_url = f"{config['CERTIFICATE_API_URL']}/generate_documents"

        logger.info("Отправка запроса на генерацию документов: %s", generate_url)
        logger.debug("Payload: %s", json.dumps(payload, ensure_ascii=False))

        response = requests.post(
            generate_url,
            json=payload,
            headers={'Content-Type': 'application/json; charset=utf-8'}
        )

        logger.info("Ответ API генерации: %s", response.status_code)
        response.raise_for_status()
        
        # Получаем список документов в новом формате
        documents_list = response.json()  # Теперь это список словарей с type, format, name, url
        
        result = {
            'documents': documents_list  # список документов
        }
        
        logging.info("Документы успешно сгенерированы для данных: %s",
                    merged_data.get('ID', '') or merged_data.get('search_ID', 'Unknown ID'))
        
        return result

    except requests.RequestException as e:
        logging.error("Ошибка при генерации документов: %s", str(e))
        if hasattr(e, 'response') and e.response is not None:
            logging.error("Статус код: %s", e.response.status_code)
            logging.error("Содержимое ответа: %s", e.response.text)
        return {}

