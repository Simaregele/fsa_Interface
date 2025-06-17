from typing import List, Tuple

# Список пар (заголовок, путь к значению). Путь используется как ключ processed_data и для
# получения исходного значения из details/search_data. Заголовок выводится в интерфейсе.

PREVIEW_FIELDS: List[Tuple[str, str]] = [
    ("Номер реестра", "RegistryNumber"),
    ("ID реестра", "RegistryID"),

    # --- Орган по сертификации ---
    ("Орган по сертификации – название", "RegistryData.certificationAuthority.fullName"),
    ("Адрес юридического лица (ОС)", "RegistryData.certificationAuthority.addresses.0.fullAddress"),
    ("Адрес деятельности (ОС)", "RegistryData.certificationAuthority.addresses.0.fullAddress"),
    ("Аттестат аккредитации №", "RegistryData.certificationAuthority.attestatRegNumber"),
    ("Дата регистрации аттестата", "RegistryData.certificationAuthority.attestatRegDate"),
    ("Телефон ОС", "RegistryData.certificationAuthority.contacts.[1].value"),
    ("E-mail ОС", "RegistryData.certificationAuthority.contacts.[0].value"),

    # --- Заявитель ---
    ("Заявитель – название", "RegistryData.applicant.fullName"),
    ("Заявитель – адрес", "RegistryData.applicant.addresses.0.fullAddress"),
    ("Заявитель – ОГРН", "RegistryData.applicant.ogrn"),
    ("Заявитель – телефон", "RegistryData.applicant.contacts.[1].value"),
    ("Заявитель – e-mail", "RegistryData.applicant.contacts.[0].value"),

    # --- Производитель ---
    ("Производитель – название", "RegistryData.manufacturer.fullName"),
    ("Производитель – адрес", "RegistryData.manufacturer.addresses.0.fullAddress"),

    # --- Продукт ---
    ("Описание продукта", "RegistryData.product.fullName"),
    ("Идентификация продукта", "RegistryData.product.identifications.[0].name"),
    ("Коды ТН ВЭД", "search_Product.Tnveds"),
    ("Техрегламент", "RegistryData.product.identifications.[0].documents.[0].name"),

    # --- Испытания ---
    ("Номер протокола испытаний", "RegistryData.testingLabs.[0].protocols.[0].number"),
    ("Дата протокола испытаний", "RegistryData.testingLabs.[0].protocols.[0].date"),
    ("Лаборатория", "RegistryData.testingLabs.[0].fullName"),

    # --- Стандарты/условия ---
    ("Стандарт – обозначение", "RegistryData.product.identifications.[0].standards.[0].designation"),
    ("Стандарт – название", "RegistryData.product.identifications.[0].standards.[0].name"),
    ("Условия хранения", "RegistryData.product.storageCondition"),
    ("Условия использования", "RegistryData.product.usageCondition"),
    ("Сфера применения", "RegistryData.product.usageScope"),

    # --- Даты ---
    ("Дата выдачи", "RegistryData.certRegDate"),
    ("Дата окончания действия", "RegistryData.certEndDate"),

    # --- Подписи ---
    ("Эксперт ФИО", "RegistryData.experts.[0].surname"),  # будут склеены в builder
    ("Эксперт имя", "RegistryData.experts.[0].firstName"),
    ("Эксперт отчество", "RegistryData.experts.[0].patronimyc"),
    ("Руководитель ОС фамилия", "RegistryData.certificationAuthority.surname"),
    ("Руководитель ОС имя", "RegistryData.certificationAuthority.firstName"),
    ("Руководитель ОС отчество", "RegistryData.certificationAuthority.patronymic"),
] 



PREVIEW_TEMPLATE: dict[str, str] = {
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
    "test_reports": (
        "Протокол испытаний {RegistryData.testingLabs.[n].protocols.[0].number} "
        "от {RegistryData.testingLabs.[n].protocols.[0].date} "
        "выданных {RegistryData.testingLabs.[n].fullName} Схема сертификации 1с"
    ),
    "standards_and_conditions": (
        "{RegistryData.product.identifications.[0].standards.[n].designation} "
        "{RegistryData.product.identifications.[0].standards.[n].name} "
        "Общие технические условия {RegistryData.product.storageCondition} "
        "{RegistryData.product.usageCondition} {RegistryData.product.usageScope}"
    ),
    "issue_date": "{RegistryData.certRegDate}",
    "expiry_date": "{RegistryData.certEndDate}",
    "expert_name": (
        "{RegistryData.experts.[0].surname} "
        "{RegistryData.experts.[0].firstName} "
        "{RegistryData.experts.[0].patronimyc}"
    ),
    "head_of_certification_body": (
        "{RegistryData.certificationAuthority.surname} "
        "{RegistryData.certificationAuthority.firstName} "
        "{RegistryData.certificationAuthority.patronymic}"
    ),
} 


PREVIEW_VIEW = """
ЕВРАЗИЙСКИЙ ЭКОНОМИЧЕСКИЙ СОЮЗ

СЕРТИФИКАТ СООТВЕТСТВИЯ
  № ЕАЭС: {certificate_number}
  Серия RU: {batch_number}

ОРГАН ПО СЕРТИФИКАЦИИ
  {certification_body}

ЗАЯВИТЕЛЬ
  {applicant}

ИЗГОТОВИТЕЛЬ
  {manufacturer}

ПРОДУКЦИЯ
  {product_description}

КОД ТН ВЭД ЕАЭС
  {tn_ved_codes}

СООТВЕТСТВУЕТ ТРЕБОВАНИЯМ
  {technical_regulation}

СЕРТИФИКАТ СООТВЕТСТВИЯ ВЫДАН НА ОСНОВАНИИ
  {test_reports}

ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ
  {standards_and_conditions}

СРОК ДЕЙСТВИЯ С … ПО … ВКЛЮЧИТЕЛЬНО
  С: {issue_date}
  По: {expiry_date}

Руководитель (уполномоченное лицо) органа по сертификации
  {head_of_certification_body}

Эксперт (эксперт-аудитор)
  {expert_name}
"""