import streamlit as st
from src.utils.certificate_generator import generate_documents, get_document_preview_json

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
    Получает JSON для предпросмотра для выбранных заявок.

    Args:
        selected_details (dict): Словарь с деталями выбранных документов.
        selected_search_data (dict): Словарь с данными поиска для выбранных документов.
        base_api_url (str): Базовый URL для API предпросмотра документов.
    """
    st.session_state.preview_jsons = {} # Очищаем предыдущие результаты предпросмотра
    for doc_id, details in selected_details.items():
        search_data = selected_search_data.get(doc_id, {})
        preview_json = get_document_preview_json(details, base_api_url=base_api_url, search_data=search_data)

        if preview_json:
            st.session_state.preview_jsons[doc_id] = preview_json
            st.success(f"JSON для предпросмотра заявки {doc_id} успешно получен!")
        else:
            st.error(f"Не удалось получить JSON для предпросмотра заявки {doc_id}") 