from src.config.page_config import init_page_config
init_page_config()  # Должна быть первой строкой после импортов

import streamlit as st
from src.api.api import get_document_details
from src.auth.auth import authenticator
from src.ui.ui_components import display_search_form, display_results_table
from config.config import load_config
from src.utils.document_download import clear_document_cache
from src.utils.document_display import display_generated_documents_section, display_certificate_preview_templates
from src.utils.document_generator import generate_documents_for_selected
from src.api.client import FSAApiClient
from src.ui.ui_components import display_editable_merged_data
# Загружаем конфигурацию
config = load_config()

def clear_generated_documents():
    """Очистка сгенерированных документов и их кэша"""
    st.session_state.generated_documents = {}
    st.session_state.downloaded_documents = {}
    # Очищаем кэш документов
    clear_document_cache()

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

    if st.button("Поиск"):
        st.session_state.search_params = {k: v for k, v in search_params.items() if v}
        st.session_state.current_page = 0

        # Сбрасываем кэш клиента и, при необходимости, создаём новый экземпляр
        try:
            client = FSAApiClient.get_instance()
            client._last_search_response = None  # type: ignore[attr-defined]
            client._last_merged_data = None      # type: ignore[attr-defined]
            clear_generated_documents()
        except RuntimeError:
            # если инстанса ещё нет, ничего делать не нужно
            pass

    if st.session_state.search_params:
        client = FSAApiClient.get_instance()
        results = client.search(st.session_state.search_params, st.session_state.current_page)

        if results is not None:
            if isinstance(results, dict):
                st.session_state.total_pages = results.get('totalPages', 1)
                total_results = results.get('total', 0)
                items = results.get('items', [])
            elif isinstance(results, list):
                st.session_state.total_pages = 1
                total_results = len(results)
                items = results
            else:
                st.error(f"Неожиданный формат результатов: {type(results)}")
                return

            if not items:
                st.warning("По вашему запросу ничего не найдено.")
            else:
                st.subheader("Результаты поиска:")
                st.write(f"Нйдено результатов: {total_results}")

                edited_df = display_results_table(items)
                selected_items = edited_df[edited_df["Выбрать"]].index.tolist()

                if selected_items:
                    st.subheader("Подробная информация о выбранных документах:")
                    selected_details = {}
                    selected_search_data = {}  # Сохраняем данные из поиска

                    for index in selected_items:
                        item = items[index]
                        doc_type = "declaration" if item["Type"] == "D" else "certificate"
                        details = get_document_details(item["ID"], doc_type)

                        if details:
                            selected_details[item["ID"]] = details
                            selected_search_data[item["ID"]] = item  # Сохраняем данные поиска

                            # Показываем данные из обоих источников
                            st.write(f"Документ {item['ID']}:")

                            with st.expander("Данные из поиска"):
                                st.json(item)

                            with st.expander("Детальные данные"):
                                st.json(details)
                            
                            # Объединяем данные для текущего документа,
                            # но только если кэша ещё нет (чтобы не перезаписывать правки)
                            if client.get_last_merged_data() is None:
                                client.merge_search_and_details(item, details)
                            display_editable_merged_data()

                            display_certificate_preview_templates(selected_details, selected_search_data)

                    if st.button("Сгенерировать файлы для выбранных документов"):
                        clear_generated_documents()
                        generate_documents_for_selected(selected_details, selected_search_data)
                        st.rerun()

                    # Отображение сгенерированных документов и кнопки создания файлов
                    display_generated_documents_section(
                        st.session_state.get('generated_documents', {}),
                        selected_details,
                        selected_search_data
                    )

                    # Показываем предпросмотр сертификатов для сгенерированных документов
                    

        else:
            st.error("Произошла ошибка при выполнении поиска. Пожалуйста, попробуйте еще раз.")

if __name__ == "__main__":
    main()