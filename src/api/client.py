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
from src.utils.json_path_registry import format_dates_inplace

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
        # здесь будем хранить результат последнего объединения данных поиска и деталей
        self._last_merged_data: Optional[Dict[str, Any]] = None
        self._last_data_to_api: Optional[Dict[str, Any]] = None
        # overrides для шаблонных значений (doc_id -> {key: value})
        self._template_overrides: Dict[str, Dict[str, str]] = {}

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

    def merge_search_and_details(self, search_json: Dict[str, Any], details_json: Dict[str, Any]) -> Dict[str, Any]:
        """Объединяет данные поиска и деталей, сохраняет результат в объекте и возвращает его.

        1. Клонируем ``details_json``.
        2. Для каждого поля из ``search_json``, отсутствующего в ``details_json``,
           добавляем вариант с префиксом ``search_`` (чтобы избежать конфликтов имён).
        3. Специально обрабатываем ключ ``TNVED`` — сохраняем также как ``tnved_codes``.
        """

        merged: Dict[str, Any] = details_json.copy()

        for key, value in search_json.items():
            if key not in merged:
                merged[f"search_{key}"] = value
                if key == "TNVED":
                    merged["tnved_codes"] = value

        # Приводим даты к формату DD.MM.YYYY (ин-плейс)
        format_dates_inplace(merged)

        # кэшируем результат, чтобы переиспользовать без повторного объединения
        self._last_merged_data = merged

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

    # Доступ к последнему результату объединения
    def get_last_merged_data(self) -> Optional[Dict[str, Any]]:
        """Возвращает кэшированный результат последнего объединения данных."""
        return self._last_merged_data

    # ---------------------------------------------------------------------
    # Работа с кэшированными merged_data
    # ---------------------------------------------------------------------

    def update_merged_data(self, path: str, value: Any) -> None:  # noqa: D401
        """Обновляет *cached* merged_data по указанному *path*.

        Пример ``path``: ``"RegistryData.applicant.fullName"`` или
        ``"RegistryData.product.identifications[0].idTnveds"``.

        Если кэш отсутствует – выводится предупреждение, изменение игнорируется.
        Метод не использует *try/except* – при ошибке структуры данных
        просто прекращает работу, оставляя кэш неизменным.
        """

        if self._last_merged_data is None:
            logger.warning("Кэш merged_data отсутствует – обновление пропущено")
            return

        parts = path.split(".")
        logger.debug("Попытка обновить merged_data по пути %s значением %s", path, value)
        current: Any = self._last_merged_data

        # Проходим все компоненты пути, кроме последнего ключа
        for idx, part in enumerate(parts):
            is_last = idx == len(parts) - 1

            # Обработка нотации key[index]
            if part.endswith("]") and "[" in part:
                key, index_str = part[:-1].split("[")
                index = int(index_str) if index_str.isdigit() else None

                # Проверка существования ключа
                match current:
                    case dict() as d if key in d:
                        # Удостоверяемся, что под ключом – список
                        if isinstance(d[key], list) and index is not None and index < len(d[key]):
                            if is_last:
                                logger.debug("Обновляем список: %s[%s]", key, index)
                                d[key][index] = value
                            else:
                                current = d[key][index]
                            continue
                    case _:
                        logger.warning("Путь '%s' недоступен в merged_data", path)
                        return
            else:
                # Обработка, когда ключ представляет собой число (идентификатор документа)
                match current:
                    case dict() as d if part.isdigit() and int(part) in d:
                        key_int = int(part)
                        if is_last:
                            logger.debug("Обновляем числовой ключ %s", key_int)
                            d[key_int] = value
                        else:
                            current = d[key_int]
                        continue
                # Обычный строковый ключ
                match current:
                    case dict() as d if part in d:
                        if is_last:
                            logger.debug("Обновляем ключ '%s'", part)
                            d[part] = value
                        else:
                            current = d[part]
                        continue
                    case _:
                        logger.warning("Путь '%s' недоступен в merged_data", path)
                        return

        logger.info("Поле '%s' успешно обновлено в merged_data", path)

    # ---------------------------------------------------------------------
    # Работа с пользовательскими overrides для шаблонных значений
    # ---------------------------------------------------------------------

    def get_template_overrides(self, doc_id: str) -> Dict[str, str]:
        """Возвращает dict overrides для конкретного *doc_id*."""
        return self._template_overrides.get(doc_id, {})

    def upsert_template_value(self, doc_id: str, key: str, value: str) -> None:  # noqa: D401
        """Создаёт/обновляет значение шаблона в overrides."""
        if doc_id not in self._template_overrides:
            self._template_overrides[doc_id] = {}
        self._template_overrides[doc_id][key] = value
        logger.info("Override шаблона обновлён: doc_id=%s, key=%s, value=%s", doc_id, key, value) 