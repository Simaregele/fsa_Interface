import streamlit as st
from src.utils.certificate_generator import generate_documents

def generate_documents_for_selected(selected_details: dict, selected_search_data: dict) -> None:
    """
    Генерирует документы для выбранных заявок
    
    Args:
        selected_details (dict): Словарь с деталями выбранных документов
        selected_search_data (dict): Словарь с данными поиска для выбранных документов
    """
    for doc_id, details in selected_details.items():
        search_data = selected_search_data.get(doc_id, {})
        documents = generate_documents(details, search_data=search_data)

        if documents:
            st.session_state.generated_documents[doc_id] = documents
            st.success(f"Документы для заявки {doc_id} успешно сгенерированы!")
            with st.expander(f"Данные, использованные для генерации {doc_id}"):
                st.json(documents.get('merged_data', {}))
        else:
            st.error(f"Не удалось сгенерировать документы для заявки {doc_id}") 