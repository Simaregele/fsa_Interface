from __future__ import annotations

"""Справочник строковых путей, используемых в проекте.

Пути записываются в *bracket notation* — индексы массивов оформлены как
``key[0]``. Это упрощает сравнение с результатом функции
``_flatten_with_paths`` и совместимо с новой утилитой ``get_value``.
"""

from typing import Final, List, Set

# ---------------------------------------------------------------------------
# Сертификат: интересующие пользователя поля
# ---------------------------------------------------------------------------
# При добавлении нового пути редактируем список ниже и перезапускаем Streamlit.
# Названия (human-readable) пока не нужны, поэтому храним просто список строк.
# Если в будущем потребуется подписывать поля, стоит заменить на dict.

CERTIFICATE_USER_PATHS: Final[List[str]] = [
    "RegistryData.applicant.fullName",
    "RegistryData.applicant.addresses[0].fullAddress",
    "RegistryData.applicant.ogrn",
    "RegistryData.applicant.contacts[0].value",
    "RegistryData.applicant.contacts[1].value",
    "RegistryData.applicant.firstName",
    "RegistryData.applicant.patronymic",
    "RegistryData.applicant.surname",
    "RegistryData.applicant.headPosition",
    # duplicate applicant names intentionally kept unique list still fine
    "RegistryData.product.fullName",
    "RegistryData.product.identifications[0].name",
    "RegistryData.manufacturer.fullName",
    "RegistryData.manufacturer.addresses[0].fullAddress",
    "search_Product.Tnveds",
    "RegistryData.product.identifications[0].documents",
    "RegistryData.testingLabs",
    "RegistryData.declRegDate",
    "RegistryData.declEndDate",
    "RegistryData.product.identifications[0].documents[0].name",
    "RegistryData.product.storageCondition",
    "RegistryData.product.usageCondition",
    "RegistryData.product.usageScope",
    "RegistryNumber",
    "RegistryData.manufacturerFilials",
]

# Устанавливаем в множество для быстрых проверок ``in``
CERTIFICATE_ALLOWED_PATHS: Final[Set[str]] = set(CERTIFICATE_USER_PATHS)

__all__ = [
    "CERTIFICATE_ALLOWED_PATHS",
] 