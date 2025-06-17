import logging
import re

# Настройка логгера модуля
logger = logging.getLogger(__name__)

import streamlit as st
from src.utils.certificate_generator import generate_documents
from src.utils.preview_builder import build_preview_processed, render_preview_html
from src.templates.certificate_preview_template import PREVIEW_FIELDS
from src.utils.document_store import DocumentStore
from src.utils import preview_builder as _pb

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

def _parse_path(path: str):
    """Разбивает строку пути 'a.b.[0].c' на сегменты 'a','b',0,'c'"""
    parts = []
    for segment in path.split('.'):
        # contacts.[1].value => contacts , [1] , value handled by split but we still have '[1]'
        if re.fullmatch(r"\[[0-9]+]", segment):
            # чистый индекс вида [0]
            parts.append(int(segment[1:-1]))
        elif '[' in segment and segment.endswith(']'):
            name, idx = re.match(r"(.+)\[([0-9]+)]", segment).groups()
            parts.append(name)
            parts.append(int(idx))
        else:
            # обычный ключ или числовой индекс без []
            if segment.isdigit():
                parts.append(int(segment))
            else:
                parts.append(segment)
    return parts

def _set_by_path(root: dict, path: str, value):
    parts = _parse_path(path)
    cur = root
    for i, part in enumerate(parts):
        is_last = i == len(parts) - 1
        if is_last:
            if isinstance(part, int):
                # ensure list length
                if not isinstance(cur, list):
                    cur_part = []
                    cur.append(cur_part)  # unlikely
                while len(cur) <= part:
                    cur.append(None)
                cur[part] = value
            else:
                cur[part] = value
        else:
            nxt = parts[i + 1]
            if isinstance(part, int):
                if not isinstance(cur, list):
                    # convert to list if wrong type
                    cur_part = []
                    cur = cur_part
                while len(cur) <= part:
                    cur.append({} if not isinstance(nxt, int) else [])
                if cur[part] is None:
                    cur[part] = {} if not isinstance(nxt, int) else []
                cur = cur[part]
            else:
                if part not in cur or not isinstance(cur[part], (dict, list)):
                    cur[part] = [] if isinstance(nxt, int) else {}
                cur = cur[part]

def apply_processed_to_details(details: dict, processed_data: dict) -> dict:
    """Применяет processed_data к details и возвращает тот же объект.

    Предполагается, что `details` – это объект из DocumentStore, поэтому
    изменения станут видны во всех частях приложения.
    """
    patched = details  # работаем с тем же словарём in-place

    for flat_key, new_val in processed_data.items():
        # Сначала обрабатываем особые ключи, чтобы не пресечь их дальнейшей логикой
        if flat_key == 'filials':
            # Пока игнорируем, оставляем как есть
            continue

        if flat_key == 'tn_ved_codes':
            codes_list = [code.strip() for code in str(new_val).split(',') if code.strip()]
            patched['tnved_codes'] = codes_list
            # Ключу 'tn_ved_codes' не соответствует путь в KEY_TO_PATH, дальнейшая обработка не требуется
            continue

        path = KEY_TO_PATH.get(flat_key)
        if not path:
            continue

        # Особая обработка для некоторых ключей
        if flat_key == 'technical_regulation':
            # в доках нет этой залупаы ебаной
            new_val = [reg.strip() for reg in str(new_val).split(',') if reg.strip()]

        if flat_key in ('certification_body', 'applicant', 'manufacturer'):
            # Берём первую строку (до первой \n или целиком)
            new_val = str(new_val).split('\n')[0].replace('Название:', '').strip()

        _set_by_path(patched, flat_key, new_val)

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

    for doc_id, details in selected_details.items():
        search_data = DocumentStore().get_search(doc_id) or {}
        processed_local = build_preview_processed(details, search_data)

        # простенький шаблон: каждая переменная в фигурных скобках
        template_text_local = render_preview_html(processed_local)

        # --- Формируем словарь preview_values со значениями вместо плейсхолдеров ---
    
        preview_values: dict[str, str] = {}

        for key, template in _pb.PREVIEW_TEMPLATE.items():
            def _repl(match):
                path = match.group(1)
                return processed_local.get(path, '')

            rendered = _pb._PLACEHOLDER_RE.sub(_repl, template)

            if key == 'tn_ved_codes':
                parts = processed_local.get('search_Product.Tnveds', '').strip('[]').replace("'", '').split(',')
                rendered = ', '.join(p.strip() for p in parts if p.strip())

            preview_values[key] = rendered

        # Сохраняем внутри объекта деталей
        store = DocumentStore()
        doc_ref = store.get(doc_id)
        if isinstance(doc_ref, dict):
            doc_ref['preview_values'] = preview_values

        preview_json = {
            "processed_data": processed_local,
            "template_text": template_text_local,
        }

        st.session_state.preview_jsons[doc_id] = preview_json

        if isinstance(preview_json, dict):
            st.success(f"Данные для предпросмотра заявки {doc_id} успешно сформированы!")

            # Инициализация редактируемых полей в st.session_state для processed_data
            for _lbl, path in PREVIEW_FIELDS:
                st.session_state[f"preview_input_{doc_id}_{path}"] = str(processed_local.get(path, ""))
            # Пока filials не поддерживаем в локальном шаблоне
        else:
            st.error(f"Не удалось сформировать данные для предпросмотра документа {doc_id}")

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

        # Singleton-хранилище деталей
        
        store = DocumentStore()
        patched_details = store.get(doc_id) or {}
        search_data = store.get_search(doc_id) or {}

        # Применяем каждое поле
        for path, val in processed_data.items():
            if path.startswith('search_'):
                _set_by_path(search_data, path[len('search_'):], val)
            else:
                _set_by_path(patched_details, path, val)

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
                st.session_state.registry_details_cache[cache_key] = patched_details
                logger.info("Кэш ПОСЛЕ изменения для %s: %s", cache_key, patched_details)
        else:
            st.error(f"Не удалось сгенерировать документы из предпросмотра для заявки {doc_id}")

        for doc_id, preview_content in st.session_state.preview_jsons.items():
            current_data = {}
            for _lbl, path in PREVIEW_FIELDS:
                session_key = f"preview_input_{doc_id}_{path}"
                user_val = st.session_state.get(session_key, '')
                original_val = preview_content['processed_data'].get(path, '')
                current_data[path] = user_val if user_val != '' else original_val

            # filials не задействуем 