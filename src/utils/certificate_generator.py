import requests
import json
from typing import Dict, Any, Union, Optional, Tuple
import logging
from config.config import load_config
from src.utils.utils import get_nested_value, stringify_values

config = load_config()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')




def filter_contacts(contacts: list, id_type: int) -> str:
    filtered = [c['value'] for c in contacts if c.get('idContactType') == id_type]
    return filtered[0] if filtered else ''


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
    # 1. Берём оригинальные details как базу (уже содержит docType и RegistryData)
    merged_data_for_result = details.copy()

    # 2. Добавляем блок search_Product только с Tnveds
    if search_data and isinstance(search_data, dict):
        tnveds: list | None = None

        # возможная вложенная структура
        if isinstance(search_data.get('Product'), dict):
            tnveds = search_data['Product'].get('Tnveds')
        # возможный плоский ключ из UI
        if tnveds is None:
            tnveds = search_data.get('Product_Tnveds')

        if tnveds is not None:
            if not isinstance(tnveds, list):
                tnveds = [str(tnveds)]
            merged_data_for_result['search_Product'] = {"Tnveds": tnveds}

    # 3. Формируем payload без дополнительного UTF-8 преобразования – requests сам кодирует JSON в utf-8
    payload_for_request = {"data": merged_data_for_result}

    return payload_for_request, merged_data_for_result


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
        
        logging.info(
            "JSON для предпросмотра успешно получен для данных: %s (URL: %s)",
            merged_data.get('ID', '') or merged_data.get('search_ID', 'Unknown ID'),
            preview_url,
        )

        # Красивый вывод структуры ответа сервера
        logging.info("Структура ответа сервера (preview):\n%s",
                     json.dumps(preview_json, ensure_ascii=False, indent=2))

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
        
        # <<< ЗДЕСЬ ОТПРАВЛЯЕТСЯ ЗАПРОС НА ГЕНЕРАЦИЮ ДОКУМЕНТОВ И ОЖИДАЕТСЯ ОТВЕТ >>>
        response = requests.post(
            f"{base_api_url}/generate_documents",
            json=payload,
            headers={'Content-Type': 'application/json; charset=utf-8'}
        )
        response.raise_for_status()

        response_data = response.json()
        result = {
            'documents': response_data,
            'merged_data': merged_data
        }
        return result
    except requests.RequestException as e:
        error_url_info = f"{base_api_url}/generate_documents"
        logging.error("Ошибка при генерации документов (URL: %s): %s", error_url_info, str(e))
        if hasattr(e, 'response') and e.response is not None:
            logging.error("Статус код: %s", e.response.status_code)
            logging.error("Содержимое ответа: %s", e.response.text)
        return {}


