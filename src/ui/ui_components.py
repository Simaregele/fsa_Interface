import streamlit as st
import pandas as pd
from src.utils.utils import format_date, flatten_dict


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
        country = st.text_input("Страна производства")
        materials = st.text_input("Коды материалов (через запятую)")
        query = st.text_input("Поисковый запрос")

    with col2:
        doc_type = st.selectbox("Тип документа", ["", "C", "D"],
                                format_func=lambda
                                    x: "Сертификаты" if x == "C" else "Декларации" if x == "D" else "Все")
        manufacturer = st.text_input("Производитель")
        branch_country = st.text_input("Страна филиала производителя")

    with col3:
        genders = st.text_input("Коды гендеров (через запятую)")
        brand = st.text_input("Бренд")
        tnved = st.text_input("Код ТН ВЭД (поиск по началу кода)")

    advanced = st.expander("Расширенные параметры")
    with advanced:
        applicant = st.text_input("Заявитель")
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

        formatted_item = {
            "Выбрать": False,
            "ID": flat_item.get("ID", ""),
            "Ссылка": generate_fsa_url(flat_item.get("Type"), flat_item.get("ID")),
            "Номер": flat_item.get("Number", ""),
            "Тип": "Декларация" if flat_item.get("Type") == "D" else "Сертификат",
            "Статус": flat_item.get("Status", ""),
            "Дата регистрации": format_date(flat_item.get("RegistrationDate")),
            "Действителен до": format_date(flat_item.get("ValidityPeriod")),
            "Заявитель": flat_item.get("Applicant", ""),
            "Производитель": flat_item.get("Manufacturer_Name", ""),
            "Продукция": flat_item.get("Product_Name", ""),
            "ТН ВЭД": ", ".join(tnveds),  # Используем обработанное значение
            "Бренд": flat_item.get("Brand", ""),
            "Материалы": ", ".join(flat_item.get("Materials", [])),
        }
        formatted_results.append(formatted_item)

    df = pd.DataFrame(formatted_results)

    column_config = {
        "Выбрать": st.column_config.CheckboxColumn(
            "Выбрать",
            help="Выберите для просмотра подробной информации",
            default=False,
        ),
        "Ссылка": st.column_config.LinkColumn(
            "Ссылка на FSA",
            help="Ссылка на документ на сайте FSA",
            validate="^https://.*",
            max_chars=100,
            display_text="Открыть"
        )
    }

    for col in df.columns:
        if col not in ["Выбрать", "Ссылка"]:
            column_config[col] = st.column_config.Column(
                col,
                disabled=True
            )

    return st.data_editor(
        df,
        hide_index=True,
        column_config=column_config,
        use_container_width=True
    )



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
