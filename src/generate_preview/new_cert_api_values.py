import re
from typing import Dict, Any

from src.utils.json_path_registry import get_value as _gv, reverse_lookup as _rev, ALL_PATHS


data_to_api = {
  "certificate_number": "{certificate_number}",
  "batch_number": "{batch_number}",
  "certification_body": "Орган по сертификации {certification_body_fullName} Место нахождения (адрес юридического лица): {certification_body_address} Адрес места осуществления деятельности: {certification_body_address} Аттестат аккредитации № {certification_body_attestatRegNumber} дата регистрации {certification_body_attestatRegDate} Телефон {certification_body_phone} Адрс электронной почты {certification_body_email}",
  "applicant": "{applicant_fullname} Место нахождения (адрес юридического лица) и адрес осуществления деятельности: {applicant_address} Основной государственный регистрационный номер {applicant_ogrn} Телефон {applicant_phone} Адрес электронной почты {applicant_email}",
  "manufacturer": "{manufacturer_fullname} Место нахождения (адрес юридического лица) и адрес осуществления деятельности: {manufacturer_address}",
  "product_description": "{product_description_name} {product_description_identification}",
  "tn_ved_codes": "{tn_ved_codes}",
  "technical_regulation": "{technical_regulation}",
  "test_reports": "Протокол испытаний {test_reports_number} от {test_reports_date} выданных {test_reports_fullname} Схема сертификации 1с",
  "standards_and_conditions": "{standards_and_conditions_designation} {standards_and_conditions_name} Общие технические условия {standards_and_conditions_storageCondition} {standards_and_conditions_usageCondition} {standards_and_conditions_usageScope}",
  "issue_date": "{issue_date}",
  "expiry_date": "{expiry_date}",
  "expert_name": "{expert_name_surname} {expert_name_name} {expert_name_patronymic}",
  "head_of_certification_body": "{head_of_certification_body_surname} {head_of_certification_body_first_name} {head_of_certification_body_patronymic}"
}

data_to_api_declaration = {
    "applicant_fullname":"{applicant_fullname}",
    "applicant_address":"{applicant_address}",
    "applicant_ogrn":"{applicant_ogrn}",
    "applicant_phone":"{applicant_phone}",
    "applicant_email":"{applicant_email}",
    "organization_head_fullname_head_position":"в лице {organization_head_fullname_head_position} ",
    "organization_head_fullname_head_position_name":"{organization_head_fullname_head_position_name} ",
    "organization_head_fullname_head_position_patronymic":"{organization_head_fullname_head_position_patronymic} ",
    "organization_head_fullname_head_position_surname":"{organization_head_fullname_head_position_surname}",
    "product_fullname":"{product_fullname}",
    "product_name_sec_part":"{product_name_sec_part}",
    "product_producer_name":"Изготовитель {product_producer_name}",
    "product_producer_address":"{product_producer_address}",
    "product_codes_tnveds":"{product_codes_tnveds}",
    "products_standarts":"{products_standarts}",
    "testing_labs_number":"{testing_labs_number}",
    "testing_labs_date":"{testing_labs_date}",
    "testing_labs_fullname":"{testing_labs_fullname}",
    "standards_and_conditions_doc_name":"{standards_and_conditions_doc_name}",
    "standards_and_conditions_storage":"{standards_and_conditions_storage} ",
    "standards_and_conditions_usage":"{standards_and_conditions_usage} ",
    "standards_and_conditions_scope":"{standards_and_conditions_scope}"
}


_PH_RE = re.compile(r"\{([^{}]+)\}")

def render_data_to_api(merged_data: Dict[str, Any]) -> Dict[str, str]:  # noqa: D401
    """Возвращает заполненный словарь для API в зависимости от типа документа.

    Если ``merged_data['docType']`` начинается с ``"declaration"`` (регистр
    игнорируется), используется словарь ``data_to_api_declaration``. Иначе
    применяем стандартный ``data_to_api`` (сертификат).
    """

    # Определяем, какой набор плейсхолдеров использовать
    doc_type_raw = str(merged_data.get("docType", "")).lower()
    mapping = data_to_api_declaration if doc_type_raw.startswith("declaration") else data_to_api

    def _fill(text: str) -> str:
        def _sub(m: re.Match[str]) -> str:
            ph = m.group(1)
            if ph in ALL_PATHS:
                return str(_gv(merged_data, ph, ""))
            # fallback – поддержка прямого пути
            key = _rev(ph)
            if key:
                return str(_gv(merged_data, key, ""))
            return ""

        return _PH_RE.sub(_sub, text)

    filled: Dict[str, str] = {}
    for k, v in mapping.items():
        filled[k] = _fill(v)
    return filled
