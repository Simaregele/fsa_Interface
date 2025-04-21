import streamlit as st
import pandas as pd
from src.utils.utils import format_date, flatten_dict
from src.api.api import update_document
from src.api.document_updater import DocumentUpdateRequest, Product, Manufacturer, Branch
from typing import List, Dict, Any, Optional

# Session state keys for tracking original and edited dataframes
_ORIGINAL_DF_KEY: str = "original_results_df"
_EDITED_DF_KEY: str = "edited_results_df"


def generate_fsa_url(doc_type: str, doc_id: str) -> str:
    """
    Генерирует URL для просмотра документа на сайте FSA.

    Args:
        doc_type: тип документа ('D' для декларации, 'C' для сертификата)
        doc_id: идентификатор документа

    Returns:
        str: полный URL для просмотра документа
    """
    base_url = "https://pub.fsa.gov.ru/rss"
    type_segment = "declaration" if doc_type == "D" else "certificate"
    return f"{base_url}/{type_segment}/view/{doc_id}/manufacturer"


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


def display_results_table(items):
    formatted_results = []
    for item in items:
        flat_item = flatten_dict(item)
        tnveds = flat_item.get("Product_Tnveds", [])
        # Проверка на None и преобразование в пустой список если None
        if tnveds is None:
            tnveds = []
        
        # Получаем гендеры из Product.Genders
        genders = flat_item.get("Product_Genders", [])
        if genders is None:
            genders = []
                    
        # Получаем бренды из Product.Brands
        brands = flat_item.get("Product_Brands", [])
        if brands is None:
            brands = []
            
        # Получаем филиалы из Manufacturer.Branches
        branches = []
        if "Manufacturer_Branches" in flat_item and flat_item["Manufacturer_Branches"]:
            for branch in flat_item["Manufacturer_Branches"]:
                if "Country" in branch and "Name" in branch:
                    branches.append(f"{branch['Country']}: {branch['Name']}")
                elif "Country" in branch:
                    branches.append(f"{branch['Country']}")

        formatted_item = {
            "Выбрать": False,
            "ID": flat_item.get("ID", ""),  # Добавляем ID обратно, он нужен для обновления
            "Ссылка": generate_fsa_url(flat_item.get("Type"), flat_item.get("ID")),
            "Номер": flat_item.get("Number", ""),
            "Тип": "Д" if flat_item.get("Type") == "D" else "С",
            "Статус": flat_item.get("Status", ""),
            "Дата регистрации": format_date(flat_item.get("RegistrationDate")),
            "Действителен до": format_date(flat_item.get("ValidityPeriod")),
            "Заявитель": flat_item.get("Applicant", ""),
            "Производитель": flat_item.get("Manufacturer_Name", ""),
            "Продукция": flat_item.get("Product_Name", ""),
            "Описание": flat_item.get("Product_Description", ""),
            "Страна продукта": flat_item.get("Product_Country", ""),
            "ТН ВЭД": ", ".join(tnveds),  # Используем обработанное значение
            "Пол": ", ".join(genders),  # Добавляем поле для гендеров
            "Бренды": brands,  # Добавляем поле для брендов как список
            "Филиалы": branches,  # Добавляем поле для филиалов как список
            "Материалы": ", ".join(flat_item.get("Product_Materials", [])),
        }
        formatted_results.append(formatted_item)

    df = pd.DataFrame(formatted_results)

    column_config = {
        "Выбрать": st.column_config.CheckboxColumn(
            "Выбрать",
            help="Выберите для просмотра подробной информации",
            default=False,
        ),
        "ID": st.column_config.Column(
            "ID",
            help="Идентификатор документа",
            disabled=True  # ID не должен редактироваться
        ),
        "Ссылка": st.column_config.LinkColumn(
            "Ссылка на FSA",
            help="Ссылка на документ на сайте FSA",
            validate="^https://.*",
            max_chars=100,
            display_text="Открыть"
        ),
        "Продукция": st.column_config.TextColumn(
            "Продукция",
            help="Название продукта"
        ),
        "Описание": st.column_config.TextColumn(
            "Описание",
            help="Описание продукта",
            width="large"
        ),
        "Страна продукта": st.column_config.TextColumn(
            "Страна продукта",
            help="Страна происхождения продукта"
        ),
        "ТН ВЭД": st.column_config.TextColumn(
            "ТН ВЭД",
            help="Коды ТН ВЭД, разделенные запятыми"
        ),
        "Пол": st.column_config.TextColumn(
            "Пол",
            help="Коды пола, разделенные запятыми"
        ),
        "Бренды": st.column_config.ListColumn(
            "Бренды",
            help="Список брендов",
            width="medium"
        ),
        "Филиалы": st.column_config.ListColumn(
            "Филиалы",
            help="Филиалы производителя",
            width="medium"
        ),
        "Материалы": st.column_config.TextColumn(
            "Материалы",
            help="Материалы, разделенные запятыми"
        )
    }

    # Все поля продукта теперь редактируемые
    editable_cols = {
        "Продукция", "Описание", "Страна продукта", 
        "ТН ВЭД", "Пол", "Бренды", "Материалы", "Филиалы"
    }
    
    for col in df.columns:
        if col not in column_config:
            column_config[col] = st.column_config.Column(
                col,
                disabled=col not in editable_cols
            )

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
        for idx, row in edited_df.iterrows():
            orig_row = original_df.loc[idx]
            
            # Проверяем, были ли изменения в любом из редактируемых полей
            if row["Выбрать"] and any(
                row[col] != orig_row[col] for col in editable_cols if col in row and col in orig_row
            ):
                try:
                    # Преобразуем текстовые поля в списки, где это необходимо
                    materials_list = [m.strip() for m in row["Материалы"].split(",") if m.strip()]
                    tnved_list = [t.strip() for t in row["ТН ВЭД"].split(",") if t.strip()]
                    gender_list = [g.strip() for g in row["Пол"].split(",") if g.strip()]
                    
                    # Бренды могут быть как строкой, так и списком
                    brands_list = row["Бренды"] if isinstance(row["Бренды"], list) else [row["Бренды"]] if row["Бренды"] else []
                    
                    # Обрабатываем филиалы, преобразуя их из строки формата "Страна: Название" в объекты Branch
                    branches: List[Branch] = []
                    if row["Филиалы"] and isinstance(row["Филиалы"], list):
                        for branch_str in row["Филиалы"]:
                            if ": " in branch_str:
                                country, name = branch_str.split(": ", 1)
                                branches.append(Branch(country=country, name=name))
                            else:
                                # Если нет имени, только страна
                                branches.append(Branch(country=branch_str, name=""))
                    
                    # Создаем объект Product с использованием Pydantic модели
                    product = Product(
                        name=row["Продукция"],
                        description=row["Описание"],
                        country=row["Страна продукта"],
                        tnveds=tnved_list,
                        materials=materials_list,
                        genders=gender_list,
                        brands=brands_list
                    )
                    
                    # Создаем объект Manufacturer
                    manufacturer = Manufacturer(branches=branches)
                    
                    # Создаем запрос на обновление
                    update_request = DocumentUpdateRequest(
                        product=product,
                        manufacturer=manufacturer
                    )
                    
                    # Определяем тип документа
                    doc_type_api = "declaration" if row["Тип"] == "Д" else "certificate"
                    
                    # Отправляем запрос на обновление
                    update_document(row["ID"], doc_type_api, update_request)
                    
                except Exception as e:
                    st.error(f"Ошибка при формировании запроса: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())
        
        st.success("Изменения отправлены")

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
