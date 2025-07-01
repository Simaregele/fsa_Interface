import logging
import streamlit as st
from src.utils.document_download import display_document_download_button
from src.generate_preview.preview_templates import (
    CERTIFICATE_PREVIEW_TEMPLATE,
    DECLARATION_PREVIEW_TEMPLATE,
)
from src.utils.certificate_generator import build_payload  # NEW IMPORT
from src.api.client import FSAApiClient
from collections import defaultdict
from src.generate_preview.new_cert_api_values import render_data_to_api

# Логгер модуля
logger = logging.getLogger(__name__)

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
            logger.info("Документы для заявки %s: %s", doc_id, documents)
            cols = st.columns(len(documents['documents']))
            for col, doc in zip(cols, documents['documents']):
                with col:
                    logger.debug("Документ: %s", doc)
                    display_document_download_button(doc, doc_id)

# ---------------------------------------------------------------------------
# Предпросмотр сертификата на основании merged_data
# ---------------------------------------------------------------------------

def display_certificate_preview_templates(selected_details: dict, selected_search_data: dict) -> None:
    """Отображает HTML-предпросмотр для каждого выбранного документа до генерации.

    Args:
        selected_details: детали документов из `get_document_details`,
            формат {doc_id: details_json}
        selected_search_data: данные из поиска, формат {doc_id: search_json}
    """

    for doc_id, details in selected_details.items():
        client = FSAApiClient.get_instance()
        merged_data = client.get_last_merged_data() or {}

        # Формируем templated + применяем overrides
        templated = render_data_to_api(merged_data)
        doc_id_for_tpl = str(
            merged_data.get("ID")
            or merged_data.get("search_ID")
            or merged_data.get("RegistryID")
            or ""
        )
        templated.update(client.get_template_overrides(doc_id_for_tpl))

        # Выбираем шаблон по типу
        doc_type_raw = str(merged_data.get("docType", "")).lower()
        use_declaration = doc_type_raw.startswith("declaration")
        template = DECLARATION_PREVIEW_TEMPLATE if use_declaration else CERTIFICATE_PREVIEW_TEMPLATE

        # Подставляем значения, безопасно обрабатывая отсутствующие ключи
        preview_text = template.format_map(defaultdict(str, templated))
        st.subheader(f"Предпросмотр документа {doc_id}")
        st.markdown(preview_text.replace("\n", "<br>"), unsafe_allow_html=True)

