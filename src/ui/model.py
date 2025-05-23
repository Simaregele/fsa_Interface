from enum import Enum, auto

class TableColumns(str, Enum):
    """Enum с названиями колонок в таблице результатов поиска."""
    SELECT = "Выбрать"
    ID = "ID"
    LINK = "Ссылка"
    NUMBER = "Номер"
    TYPE = "Тип"
    STATUS = "Статус"
    REGISTRATION_DATE = "Дата регистрации"
    VALID_UNTIL = "Действителен до"
    APPLICANT = "Заявитель"
    MANUFACTURER = "Производитель"
    PRODUCT = "Продукция"
    DESCRIPTION = "Описание"
    PRODUCT_COUNTRY = "Страна продукта"
    TNVED = "ТН ВЭД"
    GENDER = "Пол"
    BRANDS = "Бренды"
    BRANCHES = "Филиалы"
    MATERIALS = "Материалы"