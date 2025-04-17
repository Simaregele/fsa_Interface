import streamlit as st
from src.utils.document_download import display_document_download_button
from src.api.document_file_creator import create_document_file

def display_generated_documents_section(generated_documents, selected_details, selected_search_data):
    """
    Отображает секцию с сгенерированными документами и кнопкой создания файлов
    
    Args:
        generated_documents (dict): Словарь с сгенерированными документами
        selected_details (dict): Детали выбранных документов
        selected_search_data (dict): Данные поиска для выбранных документов
    """
    # Отображение сгенерированных документов
    if generated_documents:
        for doc_id, documents in generated_documents.items():
            st.write(f"Документы для заявки {doc_id}:")
            cols = st.columns(len(documents['documents']))
            for col, doc in zip(cols, documents['documents']):
                with col:
                    display_document_download_button(doc, doc_id)

