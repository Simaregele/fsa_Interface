import re
from typing import Any, Dict

# --- Новое: берём ключи и функции из реестра путей
from src.utils.json_path_registry import get_value as gv, reverse_lookup, PATHS



"""Содержит шаблоны предпросмотра документов.
На данном этапе значения представлены как плейсхолдеры в фигурных скобках,
которые будут подменяться данными, приходящими от сервера.
"""

VALUES_TEMPLATE: str = {
        "certificate_number": "{RegistryNumber}",
        "batch_number": "{RegistryID}",
        "certification_body": (
            "Орган по сертификации {RegistryData.certificationAuthority.fullName} "
            "Место нахождения (адрес юридического лица): {RegistryData.certificationAuthority.addresses.0.fullAddress} "
            "Адрес места осуществления деятельности: {RegistryData.certificationAuthority.addresses.0.fullAddress} "
            "Аттестат аккредитации № {RegistryData.certificationAuthority.attestatRegNumber} "
            "дата регистрации {RegistryData.certificationAuthority.attestatRegDate} "
            "Телефон {RegistryData.certificationAuthority.contacts.[1].value} "
            "Адрс электронной почты {RegistryData.certificationAuthority.contacts.[0].value}"
        ),
        "applicant": (
            "{RegistryData.applicant.fullName} "
            "Место нахождения (адрес юридического лица) и адрес осуществления деятельности: "
            "{RegistryData.applicant.addresses.0.fullAddress} "
            "Основной государственный регистрационный номер {RegistryData.applicant.ogrn} "
            "Телефон {RegistryData.applicant.contacts.[1].value} "
            "Адрес электронной почты {RegistryData.applicant.contacts.[0].value}"
        ),
        "manufacturer": (
            "{RegistryData.manufacturer.fullName} "
            "Место нахождения (адрес юридического лица) и адрес осуществления деятельности: "
            "{RegistryData.manufacturer.addresses.0.fullAddress}"
        ),
        "product_description": "{RegistryData.product.fullName} {RegistryData.product.identifications.[0].name}",
        "tn_ved_codes": "{search_Product.Tnveds[n]}",
        "technical_regulation": "{RegistryData.product.identifications.[0].documents.[0].name}",
        "test_reports": "Протокол испытаний {RegistryData.testingLabs.[n].protocols.[0].number} "
                        "от {RegistryData.testingLabs.[n].protocols.[0].date} "
                        "выданных {RegistryData.testingLabs.[n].fullName} Схема сертификации 1с",
        "standards_and_conditions": (
            "{RegistryData.product.identifications.[0].standards.[n].designation} "
            "{RegistryData.product.identifications.[0].standards.[n].name} "
            "Общие технические условия {RegistryData.product.storageCondition} "
            "{RegistryData.product.usageCondition} {RegistryData.product.usageScope}"
        ),
        "issue_date": "{RegistryData.certRegDate}",
        "expiry_date": "{RegistryData.certEndDate}",
        "expert_name": "{RegistryData.experts.[0].surname} "
                       "{RegistryData.experts.[0].firstName} "
                       "{RegistryData.experts.[0].patronimyc}",
        "head_of_certification_body": "{RegistryData.certificationAuthority.surname} "
                                      "{RegistryData.certificationAuthority.firstName} "
                                      "{RegistryData.certificationAuthority.patronymic}"
    }


DECLARATION_PREVIEW_TEMPLATE: str = (
    "Заявитель {RegistryData.applicant.fullName}\n"
    "Место нахождения (адрес юридического лица) и адрес места осуществления деятельности: "
    "{RegistryData.applicant.addresses.[0].fullAddress}  "
    "Основной государственный регистрационный номер {RegistryData.applicant.ogrn}. "
    "Телефон: {RegistryData.applicant.contacts.[1].value}. "
    "Адрес электронной почты: {RegistryData.applicant.contacts.[0].value}.\n"
    "в лице {RegistryData.applicant.headPosition} "
    "{RegistryData.applicant.firstName} {RegistryData.applicant.patronymic} {RegistryData.applicant.surname}\n"
    "заявляет, что {RegistryData.product.fullName}, {RegistryData.product.identifications.[0].name}\n"
    "Изготовитель {RegistryData.manufacturer.fullName}\n"
    "Место нахождения (адрес юридического лица) и адрес места осуществления деятельности по изготовлению продукции: "
    "{RegistryData.manufacturer.addresses.[0].fullAddress}\n"
    "Филиал согласно приложению № 1 на 1 листе: {RegistryData.manufacturerFilials}\n"
    "Продукция изготовлена в соответствии с требованиями Директивы 2001/95/ЕС.\n"
    "Код (коды) ТН ВЭД ЕАЭС: {search_Product.Tnveds[n]}\n"
    "Серийный выпуск соответствует требованиям {RegistryData.product.identifications.[0].documents}\n"
    "Декларация о соответствии принята на основании {RegistryData.testingLabs[n]}\n"
    "Дополнительная информация {RegistryData.product.identifications.[0].documents.[0].name} "
    "{RegistryData.product.storageCondition} {RegistryData.product.usageCondition} {RegistryData.product.usageScope}"
)

CERTIFICATE_PREVIEW_TEMPLATE: str = (
    "ЕВРАЗИЙСКИЙ ЭКОНОМИЧЕСКИЙ СОЮЗ\n\n"
    "СЕРТИФИКАТ СООТВЕТСТВИЯ\n"
    "№ ЕАЭС: {RegistryNumber}\n"
    "Серия RU: {RegistryID}\n\n"
    "ОРГАН ПО СЕРТИФИКАЦИИ\n"
    "Орган по сертификации {RegistryData.certificationAuthority.fullName} "
    "Место нахождения (адрес юридического лица): {RegistryData.certificationAuthority.addresses.[0].fullAddress} "
    "Адрес места осуществления деятельности: {RegistryData.certificationAuthority.addresses.[0].fullAddress} "
    "Аттестат аккредитации № {RegistryData.certificationAuthority.attestatRegNumber} "
    "дата регистрации {RegistryData.certificationAuthority.attestatRegDate} "
    "Телефон {RegistryData.certificationAuthority.contacts.[1].value} "
    "Адрс электронной почты {RegistryData.certificationAuthority.contacts.[0].value}\n\n"
    "ЗАЯВИТЕЛЬ\n"
    "{RegistryData.applicant.fullName} "
    "Место нахождения (адрес юридического лица) и адрес осуществления деятельности: {RegistryData.applicant.addresses.[0].fullAddress} "
    "Основной государственный регистрационный номер {RegistryData.applicant.ogrn} "
    "Телефон {RegistryData.applicant.contacts.[1].value} "
    "Адрес электронной почты {RegistryData.applicant.contacts.[0].value}\n\n"
    "ИЗГОТОВИТЕЛЬ\n"
    "{RegistryData.manufacturer.fullName} "
    "Место нахождения (адрес юридического лица) и адрес осуществления деятельности: {RegistryData.manufacturer.addresses.[0].fullAddress}\n\n"
    "ПРОДУКЦИЯ\n"
    "{RegistryData.product.fullName} {RegistryData.product.identifications.[0].name}\n\n"
    "КОД ТН ВЭД ЕАЭС\n"
    "{search_Product.Tnveds[n]}\n\n"
    "СООТВЕТСТВУЕТ ТРЕБОВАНИЯМ\n"
    "{RegistryData.product.identifications.[0].documents.[0].name}\n\n"
    "СЕРТИФИКАТ СООТВЕТСТВИЯ ВЫДАН НА ОСНОВАНИИ\n"
    "Протокол испытаний {RegistryData.testingLabs.[n].protocols.[0].number} "
    "от {RegistryData.testingLabs.[n].protocols.[0].date} "
    "выданных {RegistryData.testingLabs.[n].fullName} "
    "Схема сертификации 1с\n\n"
    "ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ\n"
    "{RegistryData.product.identifications.[0].standards.[n].designation} "
    "{RegistryData.product.identifications.[0].standards.[n].name} "
    "Общие технические условия {RegistryData.product.storageCondition} "
    "{RegistryData.product.usageCondition} {RegistryData.product.usageScope}\n\n"
    "СРОК ДЕЙСТВИЯ С {RegistryData.certRegDate} ПО {RegistryData.certEndDate} ВКЛЮЧИТЕЛЬНО\n\n"
    "Руководитель (уполномоченное лицо) органа по сертификации\n"
    "{RegistryData.certificationAuthority.surname} "
    "{RegistryData.certificationAuthority.firstName} "
    "{RegistryData.certificationAuthority.patronymic}\n\n"
    "Эксперт (эксперт-аудитор)\n"
    "{RegistryData.experts.[0].surname} {RegistryData.experts.[0].firstName} {RegistryData.experts.[0].patronimyc}\n"
)

# ---------------------------------------------------------------------------
# Заполнение шаблона значениями
# ---------------------------------------------------------------------------


# Паттерн для поиска плейсхолдеров вида {path.to.value}
_PLACEHOLDER_RE = re.compile(r"\{([^{}]+)\}")

# При импорте здесь возможен цикл, поэтому делаем ленивый импорт внутри функции


def _normalize_path(path: str) -> str:
    """Удаляет лишнюю точку перед квадратной скобкой: `.foo.[0]` → `foo[0]`."""
    return path.replace('.[', '[')


def _resolve_path(data: Dict[str, Any], path: str) -> str:
    """Возвращает строковое значение по заданному пути.

    Поддерживает:
    • индексы вида `[0]`, `[1]` — обращение к конкретному элементу массива;
    • маркер `[n]` — перебор всех элементов массива с последующим объединением
      строковых представлений через запятую.
    """

    def _traverse(current: Any, tokens: list[str]) -> list[Any]:
        if not tokens:
            return [current]

        token = tokens[0]

        # Обработка токена вида key[n] (взять все элементы списка)
        match_all = re.fullmatch(r'(\w+)\[n\]', token)
        if match_all:
            key = match_all.group(1)
            next_current = []
            if isinstance(current, dict):
                next_current = current.get(key, [])
            if isinstance(next_current, list):
                results: list[Any] = []
                for item in next_current:
                    results.extend(_traverse(item, tokens[1:]))
                return results
            return []

        # Обработка индекса, например protocols[0]
        match = re.fullmatch(r'(\w+)\[(\d+)\]', token)
        if match:
            key, idx_str = match.group(1), match.group(2)
            idx = int(idx_str)
            next_current = {}
            if isinstance(current, dict):
                next_current = current.get(key, [])
            if isinstance(next_current, list) and 0 <= idx < len(next_current):
                return _traverse(next_current[idx], tokens[1:])
            return []

        # Обычный ключ словаря
        if isinstance(current, dict):
            return _traverse(current.get(token, ''), tokens[1:])

        return []

    tokens = _normalize_path(path).split('.')
    values = _traverse(data, tokens)

    # Фильтруем пустые и преобразуем к строке
    str_values = [str(v) for v in values if v not in (None, {}, [])]
    return ', '.join(str_values)


def render_certificate_preview(merged_data: Dict[str, Any]) -> str:
    """Подставляет данные из *merged_data* в подходящий текстовый шаблон.

    Если в данных присутствует ``docType == 'declaration'`` — берётся
    ``DECLARATION_PREVIEW_TEMPLATE``; иначе используется
    ``CERTIFICATE_PREVIEW_TEMPLATE``.
    """

    # Определяем тип документа
    doc_type_raw = str(merged_data.get("docType", "")).lower()
    use_declaration = doc_type_raw.startswith("declaration")

    template = DECLARATION_PREVIEW_TEMPLATE if use_declaration else CERTIFICATE_PREVIEW_TEMPLATE

    def _replace(match: re.Match[str]) -> str:  # noqa: D401
        placeholder_path = match.group(1)

        # 0) Если в PATHS уже есть такой ключ, берём сразу
        if placeholder_path in PATHS:
            return str(gv(merged_data, placeholder_path, ''))

        # 1) Пытаемся найти ключ по путю и взять значение напрямую
        key = reverse_lookup(placeholder_path)
        if key:
            return str(gv(merged_data, key, ''))

        # 2) Fallback – старый механизм прямого разбора пути
        return _resolve_path(merged_data, placeholder_path)

    filled = _PLACEHOLDER_RE.sub(_replace, template)
    return filled
