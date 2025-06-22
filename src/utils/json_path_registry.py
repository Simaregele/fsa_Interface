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

# Основные пути для сертификатов
PATHS: dict[str, str] = {
    "certificate_number": "RegistryNumber",
    "batch_number": "RegistryID",
    "certification_body_fullName": "RegistryData.certificationAuthority.fullName",
    "certification_body_address": "RegistryData.certificationAuthority.addresses[0].fullAddress",
    "certification_body_attestatRegNumber": "RegistryData.certificationAuthority.attestatRegNumber",
    "certification_body_attestatRegDate": "RegistryData.certificationAuthority.attestatRegDate",
    "certification_body_phone": "RegistryData.certificationAuthority.contacts[1].value",
    "certification_body_email": "RegistryData.certificationAuthority.contacts[0].value",
    "applicant_fullname": "RegistryData.applicant.fullName",
    "applicant_address": "RegistryData.applicant.addresses[0].fullAddress",
    "applicant_ogrn": "RegistryData.applicant.ogrn",
    "applicant_phone": "RegistryData.applicant.contacts[1].value",
    "applicant_email": "RegistryData.applicant.contacts[0].value",
    "manufacturer_fullname": "RegistryData.manufacturer.fullName",
    "manufacturer_address": "RegistryData.manufacturer.addresses[0].fullAddress",
    "product_description_name": "RegistryData.product.fullName",
    "product_description_identification": "RegistryData.product.identifications[0].name",
    "tn_ved_codes": "search_Product.Tnveds[n]",
    "technical_regulation": "RegistryData.product.identifications[0].documents[0].name",
    "test_reports_number": "RegistryData.testingLabs[n].protocols[0].number",
    "test_reports_date": "RegistryData.testingLabs[n].protocols[0].date",
    "test_reports_fullname": "RegistryData.testingLabs[n].fullName",
    "standards_and_conditions_designation": "RegistryData.product.identifications[0].standards[n].designation",
    "standards_and_conditions_name": "RegistryData.product.identifications[0].standards[n].name",
    "standards_and_conditions_storageCondition": "RegistryData.product.storageCondition",
    "standards_and_conditions_usageCondition": "RegistryData.product.usageCondition",
    "standards_and_conditions_usageScope": "RegistryData.product.usageScope",
    "issue_date": "RegistryData.certRegDate",
    "expiry_date": "RegistryData.certEndDate",
    "expert_name_surname": "RegistryData.experts[0].surname",
    "expert_name_name": "RegistryData.experts[0].firstName",
    "expert_name_patronymic": "RegistryData.experts[0].patronimyc",
    "head_of_certification_body_surname": "RegistryData.certificationAuthority.surname",
    "head_of_certification_body_first_name": "RegistryData.certificationAuthority.firstName",
    "head_of_certification_body_patronymic": "RegistryData.certificationAuthority.patronymic"
}

# Пути, специфичные для деклараций (обратите внимание на опечатку в названии переменной,
# оставляем как есть для совместимости с текущим кодом)
PATHS_DECLARAION: dict[str, str] = {
    "certificate_number": "RegistryNumber",
    "applicant_fullname": "RegistryData.applicant.fullName",
    "applicant_address": "RegistryData.applicant.addresses[0].fullAddress",
    "applicant_ogrn": "RegistryData.applicant.ogrn",
    "applicant_phone": "RegistryData.applicant.contacts[1].value",
    "applicant_email": "RegistryData.applicant.contacts[0].value",
    "organization_head_fullname_signature_name": "RegistryData.applicant.firstName",
    "organization_head_fullname_signature_surname": "RegistryData.applicant.surname",
    "organization_head_fullname_signature_patronymic": "RegistryData.applicant.patronimyc",
    "organization_head_fullname_head_position": "RegistryData.applicant.headPosition",
    "organization_head_fullname_head_position_name": "RegistryData.applicant.firstName",
    "organization_head_fullname_head_position_surname": "RegistryData.applicant.surname",
    "organization_head_fullname_head_position_patronymic": "RegistryData.applicant.patronimyc",
    
    "product_fullname": "RegistryData.product.fullName",
    "product_fullname": "RegistryData.product.fullName",
    "product_name_sec_part": "RegistryData.product.identifications[0].name",
    "product_producer_name": "RegistryData.manufacturer.fullName",
    "product_producer_address": "RegistryData.manufacturer.addresses[0].fullAddress",
    "product_codes_tnveds": "search_Product.Tnveds[n]",
    "products_standarts": "RegistryData.product.identifications[0].documents[n].name",

    "testing_labs_number": "RegistryData.testingLabs[n].protocols[0].number",
    "testing_labs_date": "RegistryData.testingLabs[n].protocols[0].date",
    "testing_labs_fullname": "RegistryData.testingLabs[n].fullName",

    "declaration_start_date": "RegistryData.declRegDate",
    "declaration_end_date": "RegistryData.declEndDate",

    "standards_and_conditions_doc_name": "RegistryData.product.identifications[0].documents[0].name",
    "standards_and_conditions_storage": "RegistryData.product.storageCondition",
    "standards_and_conditions_usage": "RegistryData.product.usageCondition",
    "standards_and_conditions_scope": "RegistryData.product.usageScope",
    "filial_table": "RegistryData.manufacturerFilials"
}

# ---------------------------------------------------------------------------
# Объединённый словарь для универсальных функций
# ---------------------------------------------------------------------------

ALL_PATHS: dict[str, str] = {
    **PATHS,            # базовые ключи
    **PATHS_DECLARAION  # ключи деклараций (при совпадении побеждает значение из декларации)
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
    """Возвращает значение по *ключу*, поддерживая индексы и [n].

    Теперь поддерживаются как ключи из `PATHS`, так и из `PATHS_DECLARAION`.
    """
    if key not in ALL_PATHS:
        logger.warning("Ключ '%s' не найден в ALL_PATHS", key)
        return default

    path = ALL_PATHS[key]
    tokens = _split_tokens(path)

    values = _traverse(data, tokens)
    filtered = [v for v in values if v not in (None, {}, [])]

    if not filtered:
        return default

    # Если единственное значение – возвращаем как есть, иначе объединяем строкой
    if len(filtered) == 1:
        return filtered[0]
    return ", ".join(str(v) for v in filtered)

# ---------------------------------------------------------------------------
# Обратное отображение «путь → ключ» (генерируется по требованию)
# ---------------------------------------------------------------------------

def reverse_lookup(path: str) -> str | None:
    """Возвращает ключ по строковому пути, если он зарегистрирован в любом из словарей."""
    for k, v in ALL_PATHS.items():
        if v == path:
            return k
    return None 