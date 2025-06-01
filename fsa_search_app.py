from src.config.page_config import init_page_config
init_page_config()  # Должна быть первой строкой после импортов

import streamlit as st
from src.api.api import search_fsa, get_document_details, search_one_fsa
from src.auth.auth import authenticator
from src.ui.ui_components import display_search_form, display_results_table
from config.config import load_config
from src.utils.document_download import clear_document_cache
from src.utils.document_display import display_generated_documents_section
from src.utils.document_generator import generate_documents_for_selected, preview_documents_for_selected

# Загружаем конфигурацию
config = load_config()

# --- НАЧАЛО: Логика выбора URL из конфигурации ---
USE_LOCAL_API_URL_FLAG = config.get('USE_LOCAL_CERTIFICATE_API_URL', False) # Ожидаем булево значение

if USE_LOCAL_API_URL_FLAG:
    CERTIFICATE_API_URL_TO_USE = config.get('LOCAL_CERTIFICATE_API_URL')
    if not CERTIFICATE_API_URL_TO_USE: # Фоллбэк, если LOCAL_CERTIFICATE_API_URL не указан в конфиге, но флаг USE_LOCAL_API_URL_FLAG = True
        st.sidebar.warning("Флаг USE_LOCAL_CERTIFICATE_API_URL установлен в True, но LOCAL_CERTIFICATE_API_URL не найден в конфигурации. Используется основной CERTIFICATE_API_URL.")
        CERTIFICATE_API_URL_TO_USE = config['CERTIFICATE_API_URL']
        st.sidebar.info(f"Генерация документов: СТАНДАРТНЫЙ URL (из-за отсутствия локального)")
    else:
        st.sidebar.info(f"Генерация документов: ЛОКАЛЬНЫЙ URL (из конфигурации)")
elif 'CERTIFICATE_API_URL' not in config:
    st.error("Ключ CERTIFICATE_API_URL не найден в конфигурационном файле! Приложение не может работать.")
    st.stop()
else:
    CERTIFICATE_API_URL_TO_USE = config['CERTIFICATE_API_URL']
    st.sidebar.info(f"Генерация документов: СТАНДАРТНЫЙ URL (из конфигурации)")

if not CERTIFICATE_API_URL_TO_USE: # Дополнительная проверка, что URL вообще есть
    st.error("URL для API генерации сертификатов не определен! Проверьте конфигурационный файл.")
    st.stop() # Останавливаем приложение, если URL не определен
# --- КОНЕЦ: Логика выбора URL из конфигурации ---

def clear_generated_documents():
    """Очистка сгенерированных документов и их кэша"""
    st.session_state.generated_documents = {}
    st.session_state.downloaded_documents = {}
    # Очищаем кэш документов
    clear_document_cache()

def clear_preview_jsons():
    """Очистка JSON для предпросмотра"""
    st.session_state.preview_jsons = {}

def main():
    st.title("Поиск в базе FSA")

    if not authenticator.is_authenticated():
        authenticator.login()
    else:
        show_search_interface()

def show_search_interface():
    col1, col2 = st.columns([3, 1])
    with col2:
        authenticator.logout()

    search_params = display_search_form()

    # Инициализация состояний
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0
    if 'total_pages' not in st.session_state:
        st.session_state.total_pages = 1
    if 'search_params' not in st.session_state:
        st.session_state.search_params = {}
    if 'generated_documents' not in st.session_state:
        st.session_state.generated_documents = {}
    if 'downloaded_documents' not in st.session_state:
        st.session_state.downloaded_documents = {}
    if 'search_items' not in st.session_state:
        st.session_state.search_items = []
    if 'selected_items' not in st.session_state:
        st.session_state.selected_items = []
    if 'selected_details' not in st.session_state:
        st.session_state.selected_details = {}
    if 'selected_search_data' not in st.session_state:
        st.session_state.selected_search_data = {}
    if 'preview_jsons' not in st.session_state:
        st.session_state.preview_jsons = {}

    if st.button("Поиск"):
        st.session_state.search_params = {k: v for k, v in search_params.items() if v}
        st.session_state.current_page = 0
        st.session_state.search_items = []
        st.session_state.selected_items = []
        st.session_state.selected_details = {}
        st.session_state.selected_search_data = {}
        clear_generated_documents()
        clear_preview_jsons()

    if st.session_state.search_params and not st.session_state.search_items:
        results = search_fsa(st.session_state.search_params, st.session_state.current_page)
        if results is not None:
            if isinstance(results, dict):
                st.session_state.total_pages = results.get('totalPages', 1)
                st.session_state.search_items = results.get('items', [])
            elif isinstance(results, list):
                st.session_state.total_pages = 1
                st.session_state.search_items = results
            else:
                st.error(f"Неожиданный формат результатов: {type(results)}")
                return

    items = st.session_state.search_items
    if not items:
        if st.session_state.search_params:
            st.warning("По вашему запросу ничего не найдено.")
        return

    st.subheader("Результаты поиска:")
    st.write(f"Нйдено результатов: {len(items)}")
    edited_df = display_results_table(items)
    selected_items = edited_df[edited_df["Выбрать"]].index.tolist()
    st.session_state.selected_items = selected_items

    if not selected_items:
        return

    st.subheader("Подробная информация о выбранных документах:")
    selected_details = {}
    selected_search_data = {}
    for index in selected_items:
        item = items[index]
        doc_type = "declaration" if item["Type"] == "D" else "certificate"
        details = get_document_details(item["ID"], doc_type)
        if details:
            selected_details[item["ID"]] = details
            selected_search_data[item["ID"]] = item
            st.write(f"Документ {item['ID']}:")
            with st.expander("Данные из поиска"):
                st.json(item)
            with st.expander("Детальные данные"):
                st.json(details)
    st.session_state.selected_details = selected_details
    st.session_state.selected_search_data = selected_search_data

    # --- Кнопки действий --- 
    col_actions1, col_actions2 = st.columns(2)
    with col_actions1:
        if st.button("Предпросмотр данных для выбранных", use_container_width=True):
            if not selected_items:
                st.warning("Пожалуйста, выберите документы для предпросмотра.")
            else:
                clear_preview_jsons()
                preview_documents_for_selected(
                    st.session_state.selected_details,
                    st.session_state.selected_search_data,
                    CERTIFICATE_API_URL_TO_USE
                )
                st.rerun()
    
    with col_actions2:
        if st.button("Сгенерировать файлы для выбранных", use_container_width=True):
            if not selected_items:
                st.warning("Пожалуйста, выберите документы для генерации.")
            else:
                clear_generated_documents()
                generate_documents_for_selected(
                    st.session_state.selected_details,
                    st.session_state.selected_search_data,
                    CERTIFICATE_API_URL_TO_USE
                )
                st.rerun()

    # --- Секция для отображения JSON предпросмотра --- 
    if st.session_state.get('preview_jsons'):
        st.subheader("Предпросмотр данных (JSON):")
        for doc_id, preview_data in st.session_state.preview_jsons.items():
            with st.expander(f"JSON для документа {doc_id}"):
                st.json(preview_data)

    # --- Секция для отображения сгенерированных документов ---
    display_generated_documents_section(
        st.session_state.get('generated_documents', {}),
        selected_details,
        selected_search_data
    )

if __name__ == "__main__":
    main()