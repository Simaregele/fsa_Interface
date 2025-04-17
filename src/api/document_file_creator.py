import requests
import streamlit as st
from config.config import load_config
from src.auth.auth import authenticator
import json


config = load_config()


def create_document_file(document_data):
    url = f"{config['api_base_url']}{config['create_document_file_endpoint']}"

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    token = authenticator.get_token()
    if token:
        headers['Authorization'] = f'Bearer {token}'

    # Сериализуем данные в JSON с корректным кодированием
    json_data = json.dumps(document_data, ensure_ascii=False, indent=None)

    try:
        response = requests.post(url, data=json_data.encode('utf-8'), headers=headers)
        response.raise_for_status()  # Вызовет исключение для HTTP-ошибок
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка при создании файла документа: {str(e)}")
        return None
