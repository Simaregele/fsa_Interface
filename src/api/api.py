import requests
import streamlit as st
import logging
from config.config import load_config
from src.auth.auth import authenticator
from src.api.document_updater import DocumentUpdateRequest
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

config = load_config()

def search_fsa(params, page=0, page_size=20):
    url = config.get_service_url('registry', 'search')
    params['page'] = page
    params['pageSize'] = page_size

    # Добавляем поддержку поиска по филиалам
    if 'branchCountry' in params and params['branchCountry']:
        params['branchCountry'] = params['branchCountry']

    headers = {}
    token = authenticator.get_token()
    if token:
        headers['Authorization'] = f'Bearer {token}'

    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        result = response.json()
        return result
    elif response.status_code == 401:
        st.error("Ошибка аутентификации. Пожалуйста, войдите в систему снова.")
        st.session_state["authentication_status"] = False
        st.rerun()
    else:
        st.error(f"Ошибка при запросе: {response.status_code}")
        return None


def search_one_fsa(params):
    url = config.get_service_url('registry', 'search_one')

    headers = {}
    token = authenticator.get_token()
    if token:
        headers['Authorization'] = f'Bearer {token}'

    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        st.error("Ошибка аутентификации. Пожалуйста, войдите в систему снова.")
        st.session_state["authentication_status"] = False
        st.rerun()
    else:
        st.error(f"Ошибка при запросе: {response.status_code}")
        return None

def get_document_details(doc_id, doc_type):
    url = config.get_service_url('registry', 'document_by_id', doc_type=doc_type, doc_id=doc_id)

    headers = {}
    token = authenticator.get_token()
    if token:
        headers['Authorization'] = f'Bearer {token}'

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        # Получаем JSON из ответа
        response_data = response.json()
        # Добавляем поле docType
        response_data['docType'] = doc_type
        return response_data
    elif response.status_code == 401:
        st.error("Ошибка аутентификации. Пожалуйста, войдите в систему снова.")
        st.session_state["authentication_status"] = False
        st.rerun()
    else:
        st.error(f"Ошибка при запросе детальной информации: {response.status_code}")
        return None

def sync_document(doc_id, doc_type):
    url = config.get_service_url('document', 'sync_document', doc_type=doc_type, doc_id=doc_id)

    headers = {}
    token = authenticator.get_token()
    if token:
        headers['Authorization'] = f'Bearer {token}'

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        st.error("Ошибка аутентификации. Пожалуйста, войдите в систему снова.")
        st.session_state["authentication_status"] = False
        st.rerun()
    else:
        st.error(f"Ошибка при синхронизации документа: {response.status_code}")
        return None

# Новые административные функции

def full_reindex():
    url = f"{config['api_base_url']}{config['full_reindex_endpoint']}"
    headers = {'X-API-Key': config['admin_api_key']}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return True
    else:
        st.error(f"Ошибка при выполнении полного переиндексирования: {response.status_code}")
        return False

def restart_index_queue():
    url = f"{config['api_base_url']}{config['restart_index_queue_endpoint']}"
    headers = {'X-API-Key': config['admin_api_key']}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return True
    else:
        st.error(f"Ошибка при перезапуске очереди индексирования: {response.status_code}")
        return False

def clear_queues():
    url = f"{config['api_base_url']}{config['clear_queues_endpoint']}"
    headers = {'X-API-Key': config['admin_api_key']}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return True
    else:
        st.error(f"Ошибка при очистке очередей: {response.status_code}")
        return False

def load_documents(doc_type, date):
    url = f"{config['api_base_url']}{config['load_endpoint']}"
    params = {'t': doc_type, 'dt': date}
    headers = {'X-API-Key': config['admin_api_key']}
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        return True
    else:
        st.error(f"Ошибка при загрузке документов: {response.status_code}")
        return False

def load_documents_period(doc_type, start_date, end_date):
    url = f"{config['api_base_url']}{config['load_period_endpoint']}"
    params = {'t': doc_type, 'from': start_date, 'to': end_date}
    headers = {'X-API-Key': config['admin_api_key']}
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        return True
    else:
        st.error(f"Ошибка при загрузке документов за период: {response.status_code}")
        return False

def update_dictionaries():
    url = f"{config['api_base_url']}{config['update_dictionaries_endpoint']}"
    headers = {'X-API-Key': config['admin_api_key']}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return True
    else:
        st.error(f"Ошибка при обновлении словарей: {response.status_code}")
        return False

def update_expired_documents():
    url = f"{config['api_base_url']}{config['update_expired_endpoint']}"
    headers = {'X-API-Key': config['admin_api_key']}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return True
    else:
        st.error(f"Ошибка при обновлении истекших документов: {response.status_code}")
        return False

def update_document(doc_id: str, doc_type: str, data: Union[dict, DocumentUpdateRequest]) -> Optional[Dict[str, Any]]:
    """Обновление пользовательских данных документа через PUT-запрос"""
    url = config.get_service_url('document', 'update_document', doc_type=doc_type, doc_id=doc_id)
    headers = {}
    token = authenticator.get_token()
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    # Если передан объект Pydantic, преобразуем его в словарь
    if isinstance(data, DocumentUpdateRequest):
        payload = data.model_dump(exclude_none=True)
    else:
        # Для обратной совместимости
        payload = {"userData": data}
    
    logger.info(f"Отправка запроса обновления для документа {doc_id} типа {doc_type}")
    response = requests.put(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        logger.info(f"Документ {doc_id} успешно обновлен")
        return response.json()
    elif response.status_code == 401:
        logger.error(f"Ошибка аутентификации при обновлении документа {doc_id}")
        st.error("Ошибка аутентификации. Пожалуйста, войдите в систему снова.")
        st.session_state["authentication_status"] = False
        st.rerun()
    else:
        logger.error(f"Ошибка при обновлении документа {doc_id}: {response.status_code}, тело ответа: {response.text}")
        st.error(f"Ошибка при обновлении документа: {response.status_code}")
        return None