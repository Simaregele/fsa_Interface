import requests
import json
from typing import Dict, Any, Union, Optional, Tuple
import logging
from config.config import load_config


config = load_config()

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


def filter_contacts(contacts: list, id_type: int) -> str:
    filtered = [c['value'] for c in contacts if c.get('idContactType') == id_type]
    return filtered[0] if filtered else ''


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
    return {
        'certificate_number': get_nested_value(data, 'RegistryData.number'),
        'batch_number': get_nested_value(data, 'RegistryData.blankNumber'),
    }


def process_certification_body(data: Dict[str, Any]) -> Dict[str, str]:
    cert_auth = get_nested_value(data, 'RegistryData.certificationAuthority', {})
    if isinstance(cert_auth, dict):
        return {
            'certification_body': (
                f"Название: {cert_auth.get('fullName', '')}\n"
                f"Адрес: {get_nested_value(cert_auth, 'addresses[0].fullAddress')}\n"
                f"Телефон: {filter_contacts(cert_auth.get('contacts', []), '1')}\n"
                f"Email: {filter_contacts(cert_auth.get('contacts', []), '4')}\n"
                f"Аттестат аккредитации: {cert_auth.get('attestatRegNumber', '')}\n"
                f"Дата регистрации: {cert_auth.get('attestatRegDate', '')}"
            )
        }
    return {'certification_body': str(cert_auth)}


def process_applicant(data: Dict[str, Any]) -> Dict[str, str]:
    applicant = get_nested_value(data, 'RegistryData.applicant', {})
    if isinstance(applicant, dict):
        return {
            'applicant': (
                f"Название: {applicant.get('fullName', '')}\n"
                f"Адрес: {get_nested_value(applicant, 'addresses[0].fullAddress')}\n"
                f"ОГРН: {applicant.get('ogrn', '')}\n"
                f"Телефон: {filter_contacts(applicant.get('contacts', []), '1')}\n"
                f"Email: {filter_contacts(applicant.get('contacts', []), '4')}"
            )
        }
    return {'applicant': str(applicant)}


def process_manufacturer(data: Dict[str, Any]) -> Dict[str, str]:
    manufacturer = get_nested_value(data, 'RegistryData.manufacturer', {})
    if isinstance(manufacturer, dict):
        return {
            'manufacturer': (
                f"Название: {manufacturer.get('fullName', '')}\n"
                f"Адрес: {get_nested_value(manufacturer, 'addresses[0].fullAddress')}"
            )
        }
    return {'manufacturer': str(manufacturer)}


def process_product_info(data: Dict[str, Any]) -> Dict[str, str]:
    tn_ved_codes = get_nested_value(data, 'RegistryData.product.identifications[0].idTnveds')
    return {
        'product_description': get_nested_value(data, 'RegistryData.product.fullName'),
        'tn_ved_codes': ', '.join(tn_ved_codes) if isinstance(tn_ved_codes, list) else str(tn_ved_codes),
        'technical_regulation': ', '.join(get_nested_value(data, 'RegistryData.idTechnicalReglaments', [])),
        'standards_and_conditions': get_nested_value(data, 'RegistryData.product.storageCondition'),
    }


def process_test_reports(data: Dict[str, Any]) -> Dict[str, str]:
    test_reports = get_nested_value(data, 'RegistryData.documents.applicantOtherDocuments', [])
    if isinstance(test_reports, list):
        return {
            'test_reports': '\n'.join(
                [f"{report.get('number', '')}: {report.get('name', '')}" for report in test_reports])
        }
    return {'test_reports': str(test_reports)}


def process_dates_and_personnel(data: Dict[str, Any]) -> Dict[str, str]:
    result = {
        'issue_date': get_nested_value(data, 'RegistryData.certRegDate'),
        'expiry_date': get_nested_value(data, 'RegistryData.certEndDate'),
    }

    expert = get_nested_value(data, 'RegistryData.experts[0]', {})
    if isinstance(expert, dict):
        result[
            'expert_name'] = f"{expert.get('surname', '')} {expert.get('firstName', '')} {expert.get('patronimyc', '')}"
    else:
        result['expert_name'] = str(expert)

    head = get_nested_value(data, 'RegistryData', {})
    if isinstance(head, dict):
        result[
            'head_of_certification_body'] = f"{head.get('surname', '')} {head.get('firstName', '')} {head.get('patronymic', '')}"
    else:
        result['head_of_certification_body'] = str(head)

    return result


def _prepare_request_data(details: Dict[str, Any], search_data: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Подготавливает данные для запроса и объединенные данные для логгирования/результата.

    Args:
        details (Dict[str, Any]): Основные детали документа.
        search_data (Optional[Dict[str, Any]]): Дополнительные данные из поиска.

    Returns:
        Tuple[Dict[str, Any], Dict[str, Any]]: Кортеж (payload_for_request, merged_data_for_result).
        `payload_for_request` содержит данные, закодированные в UTF-8 и обернутые в {"data": ...}.
        `merged_data_for_result` содержит объединенные данные до UTF-8 кодирования payload.
    """
    merged_data_for_result = details.copy()
    if search_data:
        for key, value in search_data.items():
            # Если исходный ключ из search_data не существует в merged_data_for_result (которое изначально равно details)
            if key not in merged_data_for_result:
                merged_data_for_result[f'search_{key}'] = value
                # И если этот отсутствующий ключ был 'TNVED'
                if key == 'TNVED':
                    merged_data_for_result['tnved_codes'] = value
    
    # Данные для payload должны быть UTF-8 закодированы
    data_for_payload = utf8_encode_dict(merged_data_for_result)
    payload_for_request = {"data": data_for_payload}
    
    return payload_for_request, merged_data_for_result


def document_preview(details: Dict[str, Any], search_data: Optional[Dict[str, Any]] = None) -> Dict[str, Union[bytes, str]]:
    pass


def get_document_preview_json(details: Dict[str, Any], base_api_url: str, search_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Отправляет данные на эндпоинт предпросмотра и возвращает JSON ответ.

    Args:
        details (Dict[str, Any]): Основные детали документа.
        base_api_url (str): Базовый URL API.
        search_data (Optional[Dict[str, Any]]): Дополнительные данные из поиска.

    Returns:
        Dict[str, Any]: JSON ответ от сервера предпросмотра или пустой словарь в случае ошибки.
    """
    try:
        payload, merged_data = _prepare_request_data(details, search_data)

        preview_url = f"{base_api_url}/preview_documents"
        response = requests.post(
            preview_url,
            json=payload,
            headers={'Content-Type': 'application/json; charset=utf-8'}
        )
        response.raise_for_status()
        
        preview_json = response.json()
        
        logging.info("JSON для предпросмотра успешно получен для данных: %s (URL: %s)",
                     merged_data.get('ID', '') or merged_data.get('search_ID', 'Unknown ID'), preview_url)
        
        return preview_json

    except requests.RequestException as e:
        error_url_info = f"{base_api_url}/preview_documents"
        logging.error("Ошибка при получении JSON для предпросмотра (URL: %s): %s", error_url_info, str(e))
        if hasattr(e, 'response') and e.response is not None:
            logging.error("Статус код: %s", e.response.status_code)
            logging.error("Содержимое ответа: %s", e.response.text)
        return {}
    except json.JSONDecodeError as e:
        error_url_info = f"{base_api_url}/preview_documents"
        logging.error("Ошибка декодирования JSON ответа для предпросмотра (URL: %s): %s", error_url_info, str(e))
        if 'response' in locals() and response is not None:
            logging.error("Содержимое ответа, вызвавшее ошибку: %s", response.text)
        return {}


def generate_documents(details: Dict[str, Any], base_api_url: str, search_data: Optional[Dict[str, Any]] = None) -> Dict[str, Union[bytes, str]]:
    try:
        payload, merged_data = _prepare_request_data(details, search_data)
        # Отправка запроса
        generate_url = f"{base_api_url}/generate_documents"
        response = requests.post(
            generate_url,
            json=payload,
            headers={'Content-Type': 'application/json; charset=utf-8'}
        )
        response.raise_for_status()
        documents_list = response.json()
        result = {
            'documents': documents_list,
            'merged_data': merged_data
        }
        logging.info("Документы успешно сгенерированы для данных: %s (URL: %s)",
                    merged_data.get('ID', '') or merged_data.get('search_ID', 'Unknown ID'), generate_url)
        return result
    except requests.RequestException as e:
        error_url_info = f"{base_api_url}/generate_documents"
        logging.error("Ошибка при генерации документов (URL: %s): %s", error_url_info, str(e))
        if hasattr(e, 'response') and e.response is not None:
            logging.error("Статус код: %s", e.response.status_code)
            logging.error("Содержимое ответа: %s", e.response.text)
        return {}

