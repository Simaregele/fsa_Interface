import streamlit as st
import pandas as pd
import logging
from src.utils.utils import format_date, flatten_dict, generate_fsa_url
from src.api.api import update_document
from src.manual_db_update.updater_handlers import process_table_changes
from src.api.document_updater import DocumentUpdateRequest, Product, Manufacturer, Branch
from typing import List, Dict, Any, Optional

from src.ui.model import TableColumns

# Настройка логгера
logger = logging.getLogger(__name__)

# Session state keys for tracking original and edited dataframes
_ORIGINAL_DF_KEY: str = "original_results_df"
_EDITED_DF_KEY: str = "edited_results_df"



def display_search_form():
    st.subheader("Параметры поиска")

    col1, col2, col3 = st.columns(3)

    with col1:
        rn = st.text_input("Регистрационный номер")
        country = st.text_input("Страна производителя")
        materials = st.text_input("Коды материалов (через запятую)")
        query = st.text_input("Поисковый запрос")

    with col2:
        doc_type = st.selectbox("Тип документа", ["", "C", "D"],
                                format_func=lambda
                                    x: "Сертификаты" if x == "C" else "Декларации" if x == "D" else "Все")
        manufacturer = st.text_input("Производитель")
        branch_country = st.text_input("Страна филиала производителя")
        applicant = st.text_input("Заявитель")

    with col3:
        genders = st.text_input("Коды гендеров (через запятую)")
        brand = st.text_input("Бренд")
        tnved = st.text_input("Код ТН ВЭД (поиск по началу кода)")
        product_name = st.text_input("Наименование продукции")

    return {
        "rn": rn,
        "t": doc_type,
        "country": country,
        "manufacturer": manufacturer,
        "branchCountry": branch_country,
        "q": query,
        "tnved": tnved,
        "materials": materials,
        "brand": brand,
        "genders": genders,
        "applicant": applicant,
        "product_name": product_name
    }


def format_search_results(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Форматирует результаты поиска из API в формат, подходящий для отображения в таблице.
    
    Args:
        items: Список элементов из результатов поиска API
        
    Returns:
        Список форматированных элементов для отображения в таблице
    """
    formatted_results = []
    for item in items:
        flat_item = flatten_dict(item)
        
        # Обработка списковых полей с проверкой на None
        tnveds = flat_item.get("Product_Tnveds", []) or []
        genders = flat_item.get("Product_Genders", []) or []
        brands = flat_item.get("Product_Brands", []) or []
        materials = flat_item.get("Product_Materials", []) or []
        
        # Формирование списка филиалов
        branches = []
        if "Manufacturer_Branches" in flat_item and flat_item["Manufacturer_Branches"]:
            for branch in flat_item["Manufacturer_Branches"]:
                if "Country" in branch and "Name" in branch:
                    branches.append(f"{branch['Country']}: {branch['Name']}")
                elif "Country" in branch:
                    branches.append(f"{branch['Country']}")

        formatted_item = {
            TableColumns.SELECT: False,
            TableColumns.ID: flat_item.get("ID", ""),  # Добавляем ID обратно, он нужен для обновления
            TableColumns.LINK: generate_fsa_url(flat_item.get("Type"), flat_item.get("ID")),
            TableColumns.NUMBER: flat_item.get("Number", ""),
            TableColumns.TYPE: "Д" if flat_item.get("Type") == "D" else "С",
            TableColumns.STATUS: flat_item.get("Status", ""),
            TableColumns.REGISTRATION_DATE: format_date(flat_item.get("RegistrationDate")),
            TableColumns.VALID_UNTIL: format_date(flat_item.get("ValidityPeriod")),
            TableColumns.APPLICANT: flat_item.get("Applicant", ""),
            TableColumns.MANUFACTURER: flat_item.get("Manufacturer_Name", ""),
            TableColumns.PRODUCT: flat_item.get("Product_Name", ""),
            TableColumns.DESCRIPTION: flat_item.get("Product_Description", ""),
            TableColumns.PRODUCT_COUNTRY: flat_item.get("Product_Country", ""),
            TableColumns.TNVED: ", ".join(tnveds),  # Используем обработанное значение
            TableColumns.GENDER: ", ".join(genders),  # Добавляем поле для гендеров
            TableColumns.BRANDS: brands,  # Добавляем поле для брендов как список
            TableColumns.BRANCHES: branches,  # Добавляем поле для филиалов как список
            TableColumns.MATERIALS: ", ".join(flat_item.get("Product_Materials", [])),
        }
        formatted_results.append(formatted_item)
    
    return formatted_results


def create_table_column_config() -> Dict[str, Any]:
    """
    Создает конфигурацию столбцов для таблицы результатов поиска.
    
    Returns:
        Словарь с конфигурацией столбцов для st.data_editor
    """
    return {
        TableColumns.SELECT: st.column_config.CheckboxColumn(
            TableColumns.SELECT,
            help="Выберите для просмотра подробной информации",
            default=False,
        ),
        TableColumns.ID: st.column_config.Column(
            TableColumns.ID,
            help="Идентификатор документа",
            disabled=True
        ),
        TableColumns.LINK: st.column_config.LinkColumn(
            "Ссылка на FSA",
            help="Ссылка на документ на сайте FSA",
            validate="^https://.*",
            max_chars=100,
            display_text="Открыть"
        ),
        TableColumns.PRODUCT: st.column_config.TextColumn(
            TableColumns.PRODUCT,
            help="Название продукта"
        ),
        TableColumns.DESCRIPTION: st.column_config.TextColumn(
            TableColumns.DESCRIPTION,
            help="Описание продукта",
            width="large"
        ),
        TableColumns.PRODUCT_COUNTRY: st.column_config.TextColumn(
            TableColumns.PRODUCT_COUNTRY,
            help="Страна происхождения продукта"
        ),
        TableColumns.TNVED: st.column_config.TextColumn(
            TableColumns.TNVED,
            help="Коды ТН ВЭД, разделенные запятыми"
        ),
        TableColumns.GENDER: st.column_config.TextColumn(
            TableColumns.GENDER,
            help="Коды пола, разделенные запятыми"
        ),
        TableColumns.BRANDS: st.column_config.ListColumn(
            TableColumns.BRANDS,
            help="Список брендов",
            width="medium"
        ),
        TableColumns.BRANCHES: st.column_config.ListColumn(
            TableColumns.BRANCHES,
            help="Филиалы производителя",
            width="medium"
        ),
        TableColumns.MATERIALS: st.column_config.TextColumn(
            TableColumns.MATERIALS,
            help="Материалы, разделенные запятыми"
        )
    }




def display_results_table(items: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Отображает результаты поиска в виде редактируемой таблицы.
    
    Args:
        items: Список результатов поиска из API
        
    Returns:
        DataFrame с отредактированными данными
    """
    # Форматируем результаты для отображения
    formatted_results = format_search_results(items)
    df = pd.DataFrame(formatted_results)
    
    # Создаем конфигурацию столбцов
    column_config = create_table_column_config()
    
    # Определяем редактируемые столбцы
    editable_cols = {
        TableColumns.PRODUCT, TableColumns.DESCRIPTION, TableColumns.PRODUCT_COUNTRY, 
        TableColumns.TNVED, TableColumns.GENDER, TableColumns.BRANDS, TableColumns.MATERIALS, TableColumns.BRANCHES
    }
    
    # Настраиваем остальные столбцы
    for col in df.columns:
        if col not in column_config:
            column_config[col] = st.column_config.Column(
                col,
                disabled=col not in editable_cols
            )
    
    # Отображаем редактор данных
    edited_df = st.data_editor(
        df,
        hide_index=True,
        column_config=column_config,
        use_container_width=True
    )
    
    # Сохраняем оригинальную и отредактированную таблицы в сессию
    if _ORIGINAL_DF_KEY not in st.session_state:
        st.session_state[_ORIGINAL_DF_KEY] = df.copy()
    st.session_state[_EDITED_DF_KEY] = edited_df.copy()
    
    # Кнопка отправки изменений
    if st.button("Отправить изменения"):
        original_df = st.session_state[_ORIGINAL_DF_KEY]
        
        # Обрабатываем изменения и получаем результаты
        results = process_table_changes(edited_df, original_df, editable_cols)
        
        # Обрабатываем результаты
        success_count = 0
        warning_count = 0
        error_count = 0
        
        for result in results:
            if result["success"] is True:
                success_count += 1
            elif result["success"] is False:
                error_count += 1
                if result.get("error"):
                    st.error(f"{result['message']}: {result['error']}")
                else:
                    st.error(result['message'])
            elif result["success"] is None and "не обнаружено фактических изменений" in result["message"]:
                warning_count += 1
                st.warning(result['message'])
        
        # Отображаем общую информацию о результатах
        if success_count > 0:
            st.success(f"Успешно обновлено документов: {success_count}")
        
        if error_count == 0 and warning_count == 0:
            st.success("Все изменения успешно отправлены")
        elif error_count > 0:
            st.error(f"Ошибки при обновлении {error_count} документов")
    
    return edited_df


def display_document_details(details):
    st.subheader("Подробная информация о документе")

    col1, col2 = st.columns(2)

    with col1:
        st.write("Основная информация:")
        st.write(f"ID: {details.get('ID', 'Н/Д')}")
        st.write(f"Номер: {details.get('Number', 'Н/Д')}")
        st.write(f"Тип: {'Декларация' if details.get('Type') == 'D' else 'Сертификат'}")
        st.write(f"Статус: {details.get('Status', 'Н/Д')}")
        st.write(f"Дата регистрации: {format_date(details.get('RegistrationDate', 'Н/Д'))}")
        st.write(f"Действителен до: {format_date(details.get('ValidityPeriod', 'Н/Д'))}")

    with col2:
        st.write("Информация о продукции:")
        st.write(f"Наименование: {details.get('Product', {}).get('Name', 'Н/Д')}")
        st.write(f"ТН ВЭД: {', '.join(details.get('Product', {}).get('Tnveds', []))}")
        st.write(f"Бренд: {details.get('Product', {}).get('Brand', 'Н/Д')}")
        st.write(f"Материалы: {', '.join(details.get('Product', {}).get('Materials', []))}")

    st.write("Заявитель:")
    st.write(details.get('Applicant', {}).get('Name', 'Н/Д'))

    st.write("Производитель:")
    st.write(details.get('Manufacturer', {}).get('Name', 'Н/Д'))

    if 'Certificate' in details:
        st.write("Информация о сертификате:")
        st.write(f"Схема сертификации: {details['Certificate'].get('CertificationScheme', 'Н/Д')}")
        st.write(f"Орган по сертификации: {details['Certificate'].get('CertificationBody', {}).get('Name', 'Н/Д')}")

    if 'Declaration' in details:
        st.write("Информация о декларации:")
        st.write(f"Схема декларирования: {details['Declaration'].get('DeclarationScheme', 'Н/Д')}")
        st.write(f"Основание принятия: {details['Declaration'].get('BaseDeclaration', 'Н/Д')}")


# def display_search_one_button():
#     return st.button("Поиск одного наиболее релевантного документа")


def display_generate_certificates_button():
    return st.button("Сгенерировать сертификаты для выбранных документов")
