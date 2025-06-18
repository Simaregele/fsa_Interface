import streamlit as st
from src.utils.certificate_generator import generate_documents
from src.api.client import FSAApiClient

def generate_documents_for_selected(selected_details: dict, selected_search_data: dict) -> None:
    """
    Генерирует документы для выбранных заявок
    
    Args:
        selected_details (dict): Словарь с деталями выбранных документов
        selected_search_data (dict): Словарь с данными поиска для выбранных документов
    """
    for doc_id, details in selected_details.items():
        search_data = selected_search_data.get(doc_id, {})
        client = FSAApiClient.get_instance()

        cached = client.get_last_merged_data()

        # Определяем, нужен ли новый merge (если кэш пуст или относится к другому документу)
        need_merge = True
        if cached is not None:
            # Пытаемся определить идентификатор документа в кэше
            cached_id = None
            if "RegistryID" in cached:
                cached_id = cached["RegistryID"]
            elif len(cached) == 1 and isinstance(next(iter(cached.keys())), int):
                cached_id = next(iter(cached.keys()))

            if cached_id == doc_id:
                need_merge = False

        if need_merge:
            client.merge_search_and_details(search_data, details)

        documents = generate_documents(details, search_data=search_data)

        if documents:
            st.session_state.generated_documents[doc_id] = documents
            st.success(f"Документы для заявки {doc_id} успешно сгенерированы!")

            # Показываем данные, использованные для генерации, из кэша клиента
            merged_data = client.get_last_merged_data() or {}
            with st.expander(f"Данные, использованные для генерации {doc_id}"):
                st.json(merged_data)
        else:
            st.error(f"Не удалось сгенерировать документы для заявки {doc_id}") 