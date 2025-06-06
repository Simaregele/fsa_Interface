from src.config.page_config import init_page_config
init_page_config()  # Должна быть первой строкой после импортов

import streamlit as st
import re # Для замены плейсхолдеров в шаблоне
import html # Для экранирования HTML в значениях
from src.api.api import search_fsa, get_document_details, search_one_fsa
from src.auth.auth import authenticator
from src.ui.ui_components import display_search_form, display_results_table
from config.config import load_config
from src.utils.document_download import clear_document_cache
from src.utils.document_display import display_generated_documents_section
from src.utils.document_generator import generate_documents_for_selected, preview_documents_for_selected

# Загружаем конфигурацию
config = load_config()

# --- НАЧАЛО: Логика выбора URL из конфигурации (переработанная) ---
# Строгое чтение флага из конфигурации без значений по умолчанию.
use_local_flag = config.get('USE_LOCAL_CERTIFICATE_API_URL')

# Проверяем, что флаг вообще существует в конфиге.
if use_local_flag is None:
    st.error("Критическая ошибка: Ключ 'USE_LOCAL_CERTIFICATE_API_URL' не найден в config.json. Невозможно определить, какой URL использовать.")
    st.stop()

if use_local_flag:
    # Флаг установлен в true, ожидаем локальный URL.
    CERTIFICATE_API_URL_TO_USE = config.get('LOCAL_CERTIFICATE_API_URL')
    if CERTIFICATE_API_URL_TO_USE:
        st.sidebar.info("Генерация документов: ЛОКАЛЬНЫЙ URL")
    else:
        # Ошибка: флаг true, но локальный URL не указан.
        st.error("Критическая ошибка: Флаг 'USE_LOCAL_CERTIFICATE_API_URL' установлен в true, но ключ 'LOCAL_CERTIFICATE_API_URL' не найден в config.json.")
        st.stop()
else:
    # Флаг установлен в false, ожидаем основной URL.
    CERTIFICATE_API_URL_TO_USE = config.get('CERTIFICATE_API_URL')
    if CERTIFICATE_API_URL_TO_USE:
        st.sidebar.info("Генерация документов: СТАНДАРТНЫЙ URL")
    else:
        # Ошибка: флаг false, но основной URL не указан.
        st.error("Критическая ошибка: Флаг 'USE_LOCAL_CERTIFICATE_API_URL' установлен в false, но ключ 'CERTIFICATE_API_URL' не найден в config.json.")
        st.stop()
# --- КОНЕЦ: Логика выбора URL из конфигурации ---

def clear_generated_documents():
    """Очистка сгенерированных документов и их кэша"""
    st.session_state.generated_documents = {}
    st.session_state.downloaded_documents = {}
    # Очищаем кэш документов
    clear_document_cache()

def clear_preview_data():
    """Очистка всех данных, связанных с предпросмотром."""
    st.session_state.preview_jsons = {} # Очищаем сохраненные полные JSON
    # Очищаем все динамически созданные ключи для полей ввода, включая поля филиалов
    keys_to_delete = [key for key in st.session_state.keys() if key.startswith("preview_input_")]
    for key in keys_to_delete:
        del st.session_state[key]

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
        clear_preview_data()

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
    st.write(f"Найдено результатов: {len(items)}")
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
                clear_preview_data()
                preview_documents_for_selected(
                    st.session_state.selected_details,
                    st.session_state.selected_search_data,
                    CERTIFICATE_API_URL_TO_USE
                )
                st.rerun()
    
    with col_actions2:
        if st.button("Сгенерировать файлы для выбранных документов", use_container_width=True):
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


    # --- Секция для отображения сгенерированных документов ---
    display_generated_documents_section(
        st.session_state.get('generated_documents', {}),
        selected_details,
        selected_search_data,
        CERTIFICATE_API_URL_TO_USE
    )

        # --- Секция для отображения ИНТЕРАКТИВНОГО предпросмотра --- 
    if st.session_state.get('preview_jsons'):
        st.subheader("Интерактивный предпросмотр документов:")
        for doc_id, preview_data in st.session_state.preview_jsons.items():
            if not isinstance(preview_data, dict) or 'processed_data' not in preview_data or 'template_text' not in preview_data:
                st.warning(f"Некорректный формат данных для предпросмотра документа {doc_id}. Пропускается.")
                continue

            with st.expander(f"Предпросмотр для документа {doc_id}", expanded=True):
                st.markdown("**Редактируемые поля:**")
                processed_data_for_doc = preview_data['processed_data']
                current_template_values = {} 

                # Отображение основных редактируемых полей (кроме филиалов)
                field_keys = [k for k in processed_data_for_doc.keys() if k != 'filials']
                for i in range(0, len(field_keys), 3):
                    cols = st.columns(min(3, len(field_keys) - i))
                    for j in range(len(cols)):
                        if (i + j) < len(field_keys):
                            field_key = field_keys[i+j]
                            session_state_key = f"preview_input_{doc_id}_{field_key}"
                            with cols[j]:
                                st.text_input(
                                    label=f"{field_key.replace('_', ' ').capitalize()}", 
                                    key=session_state_key,
                                )
                            current_template_values[field_key] = st.session_state[session_state_key]
                
                st.markdown("---_Филиалы (редактируемые):_---")
                filials_data_original = preview_data.get('processed_data', {}).get('filials', [])
                if isinstance(filials_data_original, list):
                    for index, filial_item_original in enumerate(filials_data_original):
                        st.markdown(f"**Филиал {index + 1}**")
                        cols_filial = st.columns(2)
                        name_key = f"preview_input_{doc_id}_filial_{index}_name"
                        address_key = f"preview_input_{doc_id}_filial_{index}_address"
                        with cols_filial[0]:
                            st.text_input("Описание", key=name_key)
                        with cols_filial[1]:
                            st.text_input("Адрес", key=address_key)

                # Сбор данных для шаблона и HTML таблицы (теперь из st.session_state)
                # (current_template_values уже частично заполнен, дополним его, если нужно, или пересоздадим)
                # Для простоты, current_template_values уже содержит основные поля.
                # Для таблицы филиалов будем брать значения из session_state ниже.

                st.markdown("---_Шаблон документа (обновляется автоматически):_---")
                template_as_string = preview_data['template_text']
                base_template_html = template_as_string.replace("\\n", "<br>").replace("\n", "<br>")
                rendered_template_html = base_template_html

                # Подстановка основных значений
                for p_key, p_value_original in current_template_values.items():
                    safe_value = html.escape(str(p_value_original) if p_value_original is not None else "")
                    value_with_br = safe_value.replace("\\n", "<br>").replace("\n", "<br>")
                    pattern = rf"{{{{\s*{re.escape(p_key)}\s*}}}}"
                    rendered_template_html = re.sub(pattern, value_with_br, rendered_template_html)
                
                # Генерация и подстановка HTML таблицы для филиалов (теперь из st.session_state)
                table_html = ""
                if isinstance(filials_data_original, list) and filials_data_original: # Используем filials_data_original для определения количества филиалов
                    table_html = "<table border=\"1\" style=\"border-collapse: collapse; width: 100%;\">"
                    table_html += "<thead><tr><th style=\"text-align: left; padding: 5px;\">Описание</th><th style=\"text-align: left; padding: 5px;\">Адрес</th></tr></thead>"
                    table_html += "<tbody>"
                    for index, _ in enumerate(filials_data_original): # Итерируемся по индексам
                        name_val = st.session_state.get(f"preview_input_{doc_id}_filial_{index}_name", "")
                        address_val = st.session_state.get(f"preview_input_{doc_id}_filial_{index}_address", "")
                        
                        name_escaped = html.escape(name_val)
                        address_escaped = html.escape(address_val)

                        name_html = name_escaped.replace("\n", "<br>").replace("\\n", "<br>")
                        address_html = address_escaped.replace("\n", "<br>").replace("\\n", "<br>")
                        table_html += f"<tr><td style=\"padding: 5px; vertical-align: top;\">{name_html}</td><td style=\"padding: 5px; vertical-align: top;\">{address_html}</td></tr>"
                    table_html += "</tbody></table>"
                
                table_placeholder_pattern = rf"{{{{\s*TABLE_PLACEHOLDER\s*}}}}"
                rendered_template_html = re.sub(table_placeholder_pattern, table_html, rendered_template_html)

                st.markdown(rendered_template_html, unsafe_allow_html=True)


if __name__ == "__main__":
    main()