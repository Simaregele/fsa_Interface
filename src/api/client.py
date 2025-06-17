"""Клиент для взаимодействия с Registry-API.
Реализован как синглтон-объект, чтобы единообразно управлять
заголовками, URL-ами и возможными модификациями ответа.
"""

from __future__ import annotations

import logging
import requests
import streamlit as st
from typing import Dict, Any, Optional, Union

from config.config import load_config
from src.auth.auth import authenticator

logger = logging.getLogger(__name__)


class FSAApiClient:
    """Singleton-клиент для Registry-API."""

    _instance: Optional["FSAApiClient"] = None

    def __init__(self) -> None:  # noqa: D401
        if FSAApiClient._instance is not None:
            # Защита от прямого создания второго экземпляра
            raise RuntimeError("Используйте get_instance() для доступа к клиенту")
        self._config = load_config()
        # здесь будем хранить последний ответ поиска
        self._last_search_response: Optional[Union[Dict[str, Any], list]] = None

    # --------------------------- Singleton helpers ---------------------------
    @classmethod
    def get_instance(cls) -> "FSAApiClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------------
    # Public API-методы
    # ------------------------------------------------------------------------

    def search(self, params: Dict[str, Any], page: int = 0, page_size: int = 20) -> Optional[Union[Dict[str, Any], list]]:
        url = self._config.get_service_url("registry", "search")
        params = params.copy()  # чтобы не мутировать исходный dict
        # поддержка фильтра филиалов
        if params.get("branchCountry"):
            params["branchCountry"] = params["branchCountry"]

        response = requests.get(url, params=params, headers=self._auth_headers())
        data = self._handle_response(response, "Ошибка при запросе поиска")
        # сохраняем/обновляем кэш
        self._last_search_response = data
        return data

    def search_one(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        url = self._config.get_service_url("registry", "search_one")
        response = requests.get(url, params=params, headers=self._auth_headers())
        return self._handle_response(response, "Ошибка при запросе поиска одного документа")

    def get_document_details(self, doc_id: str, doc_type: str) -> Optional[Dict[str, Any]]:
        url = self._config.get_service_url("registry", "document_by_id", doc_type=doc_type, doc_id=doc_id)
        response = requests.get(url, headers=self._auth_headers())
        data = self._handle_response(response, "Ошибка при запросе детальной информации")
        if isinstance(data, dict):
            data["docType"] = doc_type
        return data

    # ------------------------------------------------------------------------
    # Объединение данных для генератора документов
    # ------------------------------------------------------------------------

    @staticmethod
    def merge_search_and_details(search_json: Dict[str, Any], details_json: Dict[str, Any]) -> Dict[str, Any]:
        """Возвращает объединённый словарь на основе search_json и details_json.

        Алгоритм идентичен использовавшемуся ранее в build_payload:
        1. Клонируем details_json.
        2. Для каждого поля из search_json, отсутствующего в details_json, добавляем вариант с префиксом
           ``search_`` (чтобы избежать конфликтов с именами из деталей).
        3. Специально обрабатываем ключ ``TNVED`` — сохраняем также как ``tnved_codes``.
        """

        merged: Dict[str, Any] = details_json.copy()

        for key, value in search_json.items():
            if key not in merged:
                merged[f"search_{key}"] = value
                if key == "TNVED":
                    merged["tnved_codes"] = value

        return merged

    # ------------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------------

    def _auth_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        token = authenticator.get_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    @staticmethod
    def _handle_response(response: requests.Response, error_prefix: str) -> Optional[Any]:  # type: ignore[arg-type]
        """Единая проверка ответов.
        Возвращает JSON (dict/list) при 200 OK,
        при 401 – инициирует повторную аутентификацию,
        иначе выводит ошибку Streamlit.
        """
        if response.status_code == 200:
            return response.json()
        if response.status_code == 401:
            st.error("Ошибка аутентификации. Пожалуйста, войдите в систему снова.")
            st.session_state["authentication_status"] = False
            st.rerun()
        else:
            st.error(f"{error_prefix}: {response.status_code}")
            logger.error("%s: %s", error_prefix, response.text)
        return None

    # Доступ к последнему сохранённому результату поиска
    def get_last_search_response(self) -> Optional[Union[Dict[str, Any], list]]:
        return self._last_search_response 