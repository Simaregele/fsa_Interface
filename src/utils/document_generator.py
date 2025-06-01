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
        search_data = selected_search_data.get(doc_id, {})
        preview_json = get_document_preview_json(details, base_api_url=base_api_url, search_data=search_data)

        if preview_json and isinstance(preview_json, dict): # Убедимся, что это словарь
            st.session_state.preview_jsons[doc_id] = preview_json
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