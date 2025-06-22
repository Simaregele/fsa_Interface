import re
from typing import Any, Dict

# --- Новое: берём ключи и функции из реестра путей
from src.utils.json_path_registry import get_value as gv, reverse_lookup, PATHS



"""Содержит шаблоны предпросмотра документов.
На данном этапе значения представлены как плейсхолдеры в фигурных скобках,
которые будут подменяться данными, приходящими от сервера.
"""


DECLARATION_PREVIEW_TEMPLATE: str = (
    "Заявитель {applicant_fullname}\n"
    "Место нахождения (адрес юридического лица) и адрес места осуществления деятельности: "
    "{applicant_address}  "
    "Основной государственный регистрационный номер {applicant_ogrn}. "
    "Телефон: {applicant_phone}. "
    "Адрес электронной почты: {applicant_email}.\n"
    "в лице {organization_head_fullname_head_position} "
    "{organization_head_fullname_head_position_name} {organization_head_fullname_head_position_patronymic} {organization_head_fullname_head_position_surname}\n"
    "заявляет, что {product_fullname}, {product_name_sec_part}\n"
    "Изготовитель {product_producer_name}\n"
    "Место нахождения (адрес юридического лица) и адрес места осуществления деятельности по изготовлению продукции: "
    "{product_producer_address}\n"
    "Филиал согласно приложению № 1 на 1 листе\n"
    "Продукция изготовлена в соответствии с требованиями Директивы 2001/95/ЕС.\n"
    "Код (коды) ТН ВЭД ЕАЭС: {product_codes_tnveds}\n"
    "Серийный выпуск соответствует требованиям {products_standarts}\n"
    "Декларация о соответствии принята на основании {testing_labs}\n"
    "Дополнительная информация {standards_and_conditions_doc_name} "
    "{standards_and_conditions_storage} {standards_and_conditions_usage} {standards_and_conditions_scope}"
)

CERTIFICATE_PREVIEW_TEMPLATE: str = (
    "ЕВРАЗИЙСКИЙ ЭКОНОМИЧЕСКИЙ СОЮЗ\n\n"
    "СЕРТИФИКАТ СООТВЕТСТВИЯ\n"
    "№ ЕАЭС: {certificate_number}\n"
    "Серия RU: {batch_number}\n\n"
    "ОРГАН ПО СЕРТИФИКАЦИИ\n"
    "Орган по сертификации {certification_body_fullName} "
    "Место нахождения (адрес юридического лица): {certification_body_address} "
    "Адрес места осуществления деятельности: {certification_body_address} "
    "Аттестат аккредитации № {certification_body_attestatRegNumber} "
    "дата регистрации {certification_body_attestatRegDate} "
    "Телефон {certification_body_phone} "
    "Адрс электронной почты {certification_body_email}\n\n"
    "ЗАЯВИТЕЛЬ\n"
    "{applicant_fullname} "
    "Место нахождения (адрес юридического лица) и адрес осуществления деятельности: {applicant_address} "
    "Основной государственный регистрационный номер {applicant_ogrn} "
    "Телефон {applicant_phone} "
    "Адрес электронной почты {applicant_email}\n\n"
    "ИЗГОТОВИТЕЛЬ\n"
    "{manufacturer_fullname} "
    "Место нахождения (адрес юридического лица) и адрес осуществления деятельности: {manufacturer_address}\n\n"
    "ПРОДУКЦИЯ\n"
    "{product_description_name} {product_description_identification}\n\n"
    "КОД ТН ВЭД ЕАЭС\n"
    "{tn_ved_codes}\n\n"
    "СООТВЕТСТВУЕТ ТРЕБОВАНИЯМ\n"
    "{technical_regulation}\n\n"
    "СЕРТИФИКАТ СООТВЕТСТВИЯ ВЫДАН НА ОСНОВАНИИ\n"
    "Протокол испытаний {test_reports_number} "
    "от {test_reports_date} "
    "выданных {test_reports_fullname} "
    "Схема сертификации 1с\n\n"
    "ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ\n"
    "{standards_and_conditions_designation} "
    "{standards_and_conditions_name} "
    "Общие технические условия {standards_and_conditions_storageCondition} "
    "{standards_and_conditions_usageCondition} {standards_and_conditions_usageScope}\n\n"
    "СРОК ДЕЙСТВИЯ С {issue_date} ПО {expiry_date} ВКЛЮЧИТЕЛЬНО\n\n"
    "Руководитель (уполномоченное лицо) органа по сертификации\n"
    "{head_of_certification_body_surname} "
    "{head_of_certification_body_first_name} "
    "{head_of_certification_body_patronymic}\n\n"
    "Эксперт (эксперт-аудитор)\n"
    "{expert_name_surname} {expert_name_name} {expert_name_patronymic}\n"
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
