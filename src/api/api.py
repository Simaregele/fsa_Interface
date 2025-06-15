import requests
import streamlit as st
import logging
import json
from config.config import load_config
from src.auth.auth import authenticator
from src.api.document_updater import DocumentUpdateRequest
from typing import Dict, Any, Optional, Union
import copy

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
    # Инициализируем кэш, если ещё не создан
    if 'registry_details_cache' not in st.session_state:
        st.session_state.registry_details_cache = {}

    url = config.get_service_url('registry', 'document_by_id', doc_type=doc_type, doc_id=doc_id)

    headers = {}
    token = authenticator.get_token()
    if token:
        headers['Authorization'] = f'Bearer {token}'

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        try:
            response_data = response.json()
            # Проверяем, что response_data действительно словарь после парсинга JSON
            if not isinstance(response_data, dict):
                logger.error(f"API вернуло не словарь для doc_id {doc_id}, doc_type {doc_type}. Получено: {type(response_data)}, Данные: {response_data}")
                st.error(f"Ошибка при обработке ответа от сервера: неверный формат данных.")
                return None
            
            response_data['docType'] = doc_type

            # Сохраняем в кэш для текущей сессии
            cache_key = f"{doc_type}_{doc_id}"
            st.session_state.registry_details_cache[cache_key] = response_data
            logger.info("Добавлены данные в кэш registry_details_cache для %s", cache_key)

            return copy.deepcopy(response_data)
        except requests.exceptions.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON для doc_id {doc_id}, doc_type {doc_type}: {e}")
            logger.error(f"Содержимое ответа: {response.text}")
            st.error(f"Ошибка при обработке ответа от сервера: неверный формат JSON.")
            return None
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

def update_document(doc_type: str, doc_id: str, data: Union[dict, DocumentUpdateRequest]) -> Optional[Dict[str, Any]]:
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
    
    # Логируем полную структуру отправляемых данных
    logger.info(f"Отправка запроса обновления для документа {doc_id} типа {doc_type}")
    logger.info(f"Структура payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    # Преобразуем payload в JSON строку и обратно для удаления None значений
    clean_payload_str = json.dumps(payload, ensure_ascii=False, skipkeys=True)
    clean_payload = json.loads(clean_payload_str)
    logger.info(f"Очищенная структура payload: {json.dumps(clean_payload, ensure_ascii=False, indent=2)}")
    
    response = requests.put(url, json=clean_payload, headers=headers)
    
    if response.status_code == 200:
        logger.info(f"Документ {doc_id} успешно обновлен")
        
        # Проверяем наличие данных в ответе
        if not response.text or not response.text.strip():
            logger.info("Успешный ответ от сервера, но пустое тело ответа")
            return {"success": True, "message": "Документ успешно обновлен"} 
        
        # Проверяем базовую структуру JSON без исключений
        if not (response.text.strip().startswith('{') or response.text.strip().startswith('[')):
            logger.warning(f"Ответ не выглядит как JSON: {response.text}")
            return {"success": True, "message": "Ответ не является JSON"}
            
        # В этом месте response.json() может вызвать исключение JSONDecodeError,
        # но мы не будем обрабатывать его, как указано в требованиях
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