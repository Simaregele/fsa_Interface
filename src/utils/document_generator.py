import logging
import copy

# Настройка логгера модуля
logger = logging.getLogger(__name__)

import streamlit as st
from src.utils.certificate_generator import generate_documents, get_document_preview_json

# Сопоставление «плоский ключ» → путь в original_details
KEY_TO_PATH = {
    'certificate_number': ['RegistryData', 'number'],
    'batch_number': ['RegistryData', 'blankNumber'],
    'product_description': ['RegistryData', 'product', 'fullName'],
    'technical_regulation': ['RegistryData', 'idTechnicalReglaments'],
    'standards_and_conditions': ['RegistryData', 'product', 'storageCondition'],
    'issue_date': ['RegistryData', 'certRegDate'],
    'expiry_date': ['RegistryData', 'certEndDate'],
    'certification_body': ['RegistryData', 'certificationAuthority', 'fullName'],
    'applicant': ['RegistryData', 'applicant', 'fullName'],
    'manufacturer': ['RegistryData', 'manufacturer', 'fullName'],
}

def _set_in_path(obj: dict, path: list, value):
    """Устанавливает value по вложенному path, создавая промежуточные dict при необходимости."""
    cur = obj
    for idx, key in enumerate(path):
        if idx == len(path) - 1:
            cur[key] = value
        else:
            if isinstance(key, int):
                while len(cur) <= key:
                    cur.append({})
                if not isinstance(cur[key], dict):
                    cur[key] = {}
                cur = cur[key]
            else:
                if key not in cur or not isinstance(cur[key], (dict, list)):
                    # если следующий ключ — int, создаём список, иначе dict
                    nxt = path[idx + 1]
                    cur[key] = [] if isinstance(nxt, int) else {}
                cur = cur[key]

def apply_processed_to_details(original_details: dict, processed_data: dict) -> dict:
    """Возвращает копию original_details c учётом правок processed_data."""
    patched = copy.deepcopy(original_details)

    for flat_key, new_val in processed_data.items():
        if flat_key == 'filials':
            # Пока игнорируем, оставляем как есть
            continue

        path = KEY_TO_PATH.get(flat_key)
        if not path:
            continue

        # Особая обработка для некоторых ключей
        if flat_key == 'tn_ved_codes':
            codes_list = [code.strip() for code in str(new_val).split(',') if code.strip()]
            patched['tnved_codes'] = codes_list
            continue  # не идём глубже, top-level достаточно

        if flat_key == 'technical_regulation':
            new_val = [reg.strip() for reg in str(new_val).split(',') if reg.strip()]

        if flat_key in ('certification_body', 'applicant', 'manufacturer'):
            # Берём первую строку (до первой \n или целиком)
            new_val = str(new_val).split('\n')[0].replace('Название:', '').strip()

        _set_in_path(patched, path, new_val)

    return patched

def generate_documents_for_selected(selected_details: dict, selected_search_data: dict, base_api_url: str) -> None:
    """
    Генерирует документы для выбранных заявок
    
    Args:
        selected_details (dict): Словарь с деталями выбранных документов
        selected_search_data (dict): Словарь с данными поиска для выбранных документов
        base_api_url (str): Базовый URL для API генерации документов
    """
    for doc_id, details in selected_details.items():
        search_data = selected_search_data.get(doc_id, {})
        logger.info("[GEN_SELECTED] payload_details_%s = %s", doc_id, details)
        logger.info("[GEN_SELECTED] payload_search_%s = %s", doc_id, search_data)

        documents = generate_documents(details, base_api_url=base_api_url, search_data=search_data)

        if documents:
            st.session_state.generated_documents[doc_id] = documents
            st.success(f"Документы для заявки {doc_id} успешно сгенерированы!")
            with st.expander(f"Данные, использованные для генерации {doc_id}"):
                st.json(documents.get('merged_data', {}))
        else:
            st.error(f"Не удалось сгенерировать документы для заявки {doc_id}")

def preview_documents_for_selected(selected_details: dict, selected_search_data: dict, base_api_url: str) -> None:
    """
    Получает JSON для предпросмотра для выбранных заявок и инициализирует состояние для редактируемых полей.

    Args:
        selected_details (dict): Словарь с деталями выбранных документов.
        selected_search_data (dict): Словарь с данными поиска для выбранных документов.
        base_api_url (str): Базовый URL для API предпросмотра документов.
    """
    # Очищаем предыдущие полные JSON предпросмотра (если есть)
    st.session_state.preview_jsons = {} 
    # Очищаем предыдущие редактируемые поля (позже в fsa_search_app.py будет более надежная очистка по паттерну)
    # Пока что здесь можно оставить так, но основная очистка будет в главном файле перед вызовом этой функции.

    if 'edited_details' not in st.session_state:
        st.session_state.edited_details = {}

    for doc_id, details in selected_details.items():
        search_data = selected_search_data.get(doc_id, {})
        preview_json = get_document_preview_json(details, base_api_url=base_api_url, search_data=search_data)

        if preview_json and isinstance(preview_json, dict): # Убедимся, что это словарь
            st.session_state.preview_jsons[doc_id] = preview_json

            # Сохраняем копию исходных деталей для дальнейшего патча
            if doc_id not in st.session_state.edited_details:
                st.session_state.edited_details[doc_id] = copy.deepcopy(details)

            st.success(f"Данные для предпросмотра заявки {doc_id} успешно получены!")

            # Инициализация редактируемых полей в st.session_state для processed_data
            if 'processed_data' in preview_json and isinstance(preview_json['processed_data'], dict):
                for key, value in preview_json['processed_data'].items():
                    if key != 'filials': # Пропускаем сами филиалы, они будут обработаны отдельно
                        st.session_state[f"preview_input_{doc_id}_{key}"] = str(value if value is not None else "")
                
                # Инициализация редактируемых полей для филиалов
                if 'filials' in preview_json['processed_data'] and isinstance(preview_json['processed_data']['filials'], list):
                    for index, filial_item in enumerate(preview_json['processed_data']['filials']):
                        if isinstance(filial_item, dict):
                            st.session_state[f"preview_input_{doc_id}_filial_{index}_name"] = str(filial_item.get('name', '') if filial_item.get('name') is not None else "")
                            st.session_state[f"preview_input_{doc_id}_filial_{index}_address"] = str(filial_item.get('address', '') if filial_item.get('address') is not None else "")
            else:
                st.warning(f"В ответе для предпросмотра документа {doc_id} отсутствует 'processed_data' или это не словарь.")
        
        elif preview_json: # Если preview_json не пустой, но и не словарь (маловероятно из get_document_preview_json, но для безопасности)
             st.error(f"Не удалось получить корректные данные для предпросмотра заявки {doc_id}. Получен неожиданный тип: {type(preview_json)}")
        else:
            st.error(f"Не удалось получить данные для предпросмотра заявки {doc_id}") 

def generate_documents_from_preview_data(all_preview_data: dict, base_api_url: str) -> None:
    """
    Генерирует документы на основе измененных данных из секции предпросмотра.

    Args:
        all_preview_data (dict): Словарь, где ключ - doc_id, а значение - 
                                 словарь с 'processed_data' и 'template_text'.
        base_api_url (str): Базовый URL для API генерации.
    """
    for doc_id, preview_data in all_preview_data.items():
        processed_data = preview_data.get('processed_data', {})
        logger.info("[PREVIEW_PATCH] processed_data_%s = %s", doc_id, processed_data)

        original_details = st.session_state.edited_details.get(doc_id, st.session_state.selected_details.get(doc_id, {}))
        search_data = st.session_state.selected_search_data.get(doc_id, {})

        patched_details = apply_processed_to_details(original_details, processed_data)

        # Обновляем search_data для TNVED, чтобы _prepare_request_data не перезаписал наше значение
        if 'tn_ved_codes' in processed_data:
            first_code = str(processed_data['tn_ved_codes']).split(',')[0].strip()
            if doc_id in st.session_state.selected_search_data:
                st.session_state.selected_search_data[doc_id]['TNVED'] = first_code
            search_data['TNVED'] = first_code

        logger.info("[PREVIEW_PATCH] patched_details_%s = %s", doc_id, patched_details)
        logger.info("[PREVIEW_PATCH] search_data_%s = %s", doc_id, search_data)

        generated_result = generate_documents(
            patched_details,
            base_api_url=base_api_url,
            search_data=search_data
        )

        if generated_result:
            st.session_state.generated_documents[doc_id] = generated_result
            st.success(f"Документы для заявки {doc_id} успешно сгенерированы из предпросмотра!")
            with st.expander(f"Изменённые данные, использованные для генерации {doc_id}"):
                st.json(generated_result.get('merged_data', {}))

            # Обновляем кэш RegistryData и логируем изменения
            cache_key = f"{patched_details.get('docType', '')}_{doc_id}"
            if 'registry_details_cache' in st.session_state:
                before = st.session_state.registry_details_cache.get(cache_key)
                logger.info("Кэш ДО изменения для %s: %s", cache_key, before)
                st.session_state.registry_details_cache[cache_key] = copy.deepcopy(patched_details)
                logger.info("Кэш ПОСЛЕ изменения для %s: %s", cache_key, patched_details)
        else:
            st.error(f"Не удалось сгенерировать документы из предпросмотра для заявки {doc_id}") 