"""Регистратор строковых путей внутри JSON-ответов FSA.

1. MAP содержит сопоставление «человекочитаемый ключ → JSON-путь».
   Вы наполняете его нужными элементами (пример оставлен закомментированным).
2. Функции get_value / set_value позволяют читать и писать значения
   по *ключу*, не заботясь о синтаксисе пути.
3. Поддерживается нотация списка: key[0].foo или key[n].foo (см. get_value).

Следующий шаг после наполнения MAP — использовать эти функции вместо прямого
парсинга путей в:
• preview_templates
• display_editable_merged_data
• certificate_generator
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Основной словарь путей
# ---------------------------------------------------------------------------

PATHS: dict[str, str] = {
    # Примеры, удалите после заполнения
    # "applicant_fullname": "RegistryData.applicant.fullName",
    # "applicant_address": "RegistryData.applicant.addresses[0].fullAddress",
}

# ---------------------------------------------------------------------------
# Внутренние помощники
# ---------------------------------------------------------------------------

_LIST_INDEX_RE = re.compile(r"^(\w+)\[(\d+|n)\]$")


def _split_tokens(path: str) -> List[str]:
    """Разбивает путь на токены, учитывая нотацию списков."""
    tokens: List[str] = []
    for raw in path.split('.'):
        raw = raw.replace('.[', '[')  # защита от `foo.[0]`
        tokens.append(raw)
    return tokens


# ---------------------------------------------------------------------------
# Публичный API
# ---------------------------------------------------------------------------

def _traverse(current: Any, tokens: List[str]) -> List[Any]:
    """Рекурсивно идём по *tokens* и собираем найденные значения."""
    if not tokens:
        return [current]

    token = tokens[0]
    list_match = _LIST_INDEX_RE.fullmatch(token)

    if list_match:
        dict_key, index_raw = list_match.group(1), list_match.group(2)
        match current:
            case dict() as d if dict_key in d:
                seq = d[dict_key]
                if not isinstance(seq, list):
                    return []
                # Случай key[n] – агрегируем по всем элементам
                if index_raw == "n":
                    collected: List[Any] = []
                    for item in seq:
                        collected.extend(_traverse(item, tokens[1:]))
                    return collected
                # Случай key[0], key[1] ...
                idx = int(index_raw)
                if idx < len(seq):
                    return _traverse(seq[idx], tokens[1:])
        return []
    else:
        match current:
            case dict() as d if token in d:
                return _traverse(d[token], tokens[1:])
        return []


def get_value(data: Dict[str, Any], key: str, default: Any = "") -> Any:
    """Возвращает значение по *ключу*, поддерживая индексы и [n]."""
    if key not in PATHS:
        logger.warning("Ключ '%s' не найден в PATHS", key)
        return default

    path = PATHS[key]
    tokens = _split_tokens(path)

    values = _traverse(data, tokens)
    filtered = [v for v in values if v not in (None, {}, [])]

    if not filtered:
        return default

    # Если единственное значение – возвращаем как есть, иначе объединяем строкой
    if len(filtered) == 1:
        return filtered[0]
    return ", ".join(str(v) for v in filtered)


def set_value(data: Dict[str, Any], key: str, value: Any) -> None:
    """Записывает *value* по *ключу* в *data* (in-place).

    Если часть пути отсутствует – создаёт вложенные dict / list автоматически.
    Исключений не бросает; при невозможности записи пишет предупреждение.
    """
    if key not in PATHS:
        logger.warning("Ключ '%s' не найден в PATHS", key)
        return

    path = PATHS[key]
    tokens = _split_tokens(path)

    current: Any = data
    for idx, token in enumerate(tokens):
        is_last = idx == len(tokens) - 1
        list_match = _LIST_INDEX_RE.fullmatch(token)
        if list_match:
            dict_key, index_raw = list_match.group(1), list_match.group(2)
            # Гарантируем наличие списка
            if not isinstance(current.get(dict_key, None), list):
                current[dict_key] = []
            seq = current[dict_key]
            if index_raw == 'n':
                logger.warning("Нельзя назначить значение по пути с [n]: %s", path)
                return
            index = int(index_raw)
            # Расширяем список при необходимости
            while len(seq) <= index:
                seq.append({})
            if is_last:
                seq[index] = value
            else:
                if not isinstance(seq[index], dict):
                    seq[index] = {}
                current = seq[index]
        else:
            # Обычный ключ словаря
            if is_last:
                current[token] = value
            else:
                if token not in current or not isinstance(current[token], dict):
                    current[token] = {}
                current = current[token]


# ---------------------------------------------------------------------------
# Обратное отображение «путь → ключ» (генерируется по требованию)
# ---------------------------------------------------------------------------

def reverse_lookup(path: str) -> str | None:
    """Возвращает ключ по строковому пути, если он зарегистрирован."""
    for k, v in PATHS.items():
        if v == path:
            return k
    return None 