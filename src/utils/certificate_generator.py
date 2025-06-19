import requests
import json
from typing import Dict, Any, Union, Optional, Tuple
import logging
from config.config import load_config
from src.api.client import FSAApiClient  # локальный импорт, чтобы избежать циклов
from src.utils.json_path_registry import get_value as gv


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


def get_nested_value(data: Dict[str, Any], path: str, default: Any = '') -> Any:
    keys = path.split('.')
    print('keys', keys)
    value = data
    for key in keys:
        if key.endswith(']'):
            key, index = key[:-1].split('[')
            try:
                value = value.get(key, [])[int(index)]
            except (IndexError, TypeError):
                return default
        else:
            value = value.get(key, {})
        if value == {}:
            return default
    return value if value != {} else default


def stringify_values(obj):
    if isinstance(obj, dict):
        return {k: stringify_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [stringify_values(i) for i in obj]
    elif obj is None:
        return ''
    else:
        return str(obj)


def process_complex_json(data: Dict[str, Any]) -> Dict[str, str]:
    logging.info("Входные данные: %s", json.dumps(data, ensure_ascii=False, indent=2))
    data = stringify_values(data)
    result = {}
    result.update(process_registry_data(data))
    result.update(process_certification_body(data))
    result.update(process_applicant(data))
    result.update(process_manufacturer(data))
    result.update(process_product_info(data))
    result.update(process_test_reports(data))
    result.update(process_dates_and_personnel(data))
    return result


def process_registry_data(data: Dict[str, Any]) -> Dict[str, str]:
    """Основные идентификаторы сертификата."""
    return {
        'certificate_number': gv(data, 'certificate_number'),
        'batch_number': gv(data, 'batch_number'),
    }


def process_certification_body(data: Dict[str, Any]) -> Dict[str, str]:
    """Составляем строку об органе по сертификации через PATHS."""
    return {
        'certification_body': (
            f"Название: {gv(data, 'certification_body_fullName')}\n"
            f"Адрес: {gv(data, 'certification_body_address')}\n"
            f"Телефон: {gv(data, 'certification_body_phone')}\n"
            f"Email: {gv(data, 'certification_body_email')}\n"
            f"Аттестат аккредитации: {gv(data, 'certification_body_attestatRegNumber')}\n"
            f"Дата регистрации: {gv(data, 'certification_body_attestatRegDate')}"
        )
    }


def process_applicant(data: Dict[str, Any]) -> Dict[str, str]:
    return {
        'applicant': (
            f"Название: {gv(data, 'applicant_fullname')}\n"
            f"Адрес: {gv(data, 'applicant_address')}\n"
            f"ОГРН: {gv(data, 'applicant_ogrn')}\n"
            f"Телефон: {gv(data, 'applicant_phone')}\n"
            f"Email: {gv(data, 'applicant_email')}"
        )
    }


def process_manufacturer(data: Dict[str, Any]) -> Dict[str, str]:
    return {
        'manufacturer': (
            f"Название: {gv(data, 'manufacturer_fullname')}\n"
            f"Адрес: {gv(data, 'manufacturer_address')}"
        )
    }


def process_product_info(data: Dict[str, Any]) -> Dict[str, str]:
    return {
        'product_description': gv(data, 'product_description_name'),
        'tn_ved_codes': gv(data, 'tn_ved_codes'),
        'technical_regulation': gv(data, 'technical_regulation'),
        'standards_and_conditions': gv(data, 'standards_and_conditions_storageCondition'),
    }


def process_test_reports(data: Dict[str, Any]) -> Dict[str, str]:
    """Готовим строку тест-протоколов (номер: дата: лаборатория)."""
    numbers = gv(data, 'test_reports_number')
    dates = gv(data, 'test_reports_date')
    names = gv(data, 'test_reports_fullname')

    # все три могут быть списками через ", " – разделяем на массивы
    nums_list = [x.strip() for x in str(numbers).split(',') if x]
    dates_list = [x.strip() for x in str(dates).split(',') if x]
    names_list = [x.strip() for x in str(names).split(',') if x]

    max_len = max(len(nums_list), len(dates_list), len(names_list))
    result_rows: list[str] = []
    for i in range(max_len):
        row = f"{nums_list[i] if i < len(nums_list) else ''}: " \
              f"{dates_list[i] if i < len(dates_list) else ''}: " \
              f"{names_list[i] if i < len(names_list) else ''}"
        result_rows.append(row.strip(': '))

    return {'test_reports': '\n'.join(result_rows)}


def process_dates_and_personnel(data: Dict[str, Any]) -> Dict[str, str]:
    return {
        'issue_date': gv(data, 'issue_date'),
        'expiry_date': gv(data, 'expiry_date'),
        'expert_name': ' '.join([
            gv(data, 'expert_name_surname'),
            gv(data, 'expert_name_name'),
            gv(data, 'expert_name_patronymic')
        ]).strip(),
        'head_of_certification_body': ' '.join([
            gv(data, 'head_of_certification_body_surname'),
            gv(data, 'head_of_certification_body_first_name'),
            gv(data, 'head_of_certification_body_patronymic')
        ]).strip(),
    }


def build_payload() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Строит JSON-payload для сервиса генерации документов и возвращает его вместе с объединёнными данными."""
    client = FSAApiClient.get_instance()
    cached = client.get_last_merged_data()
    if cached is None:
        raise ValueError("Нет данных merged_data в кэше. Сначала объедините данные, затем вызывайте генерацию.")

    # Используем уже существующий (и, возможно, отредактированный) кэш
    merged_data = cached  # type: ignore[arg-type]

    utf8_data = utf8_encode_dict(merged_data)
    payload = {"data": utf8_data}
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

