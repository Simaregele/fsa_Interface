from src.api.document_updater import Product, Manufacturer, Branch, DocumentUpdateRequest, update_document
from src.ui.model import TableColumns
from typing import Optional, List, Dict, Any
import logging
import pandas as pd
import json

logger = logging.getLogger(__name__)


def send_update_request(doc_id: str, doc_type: str, update_request_data: Dict[str, Any]) -> bool:
    """
    Отправляет запрос на обновление документа.
    
    Args:
        doc_id: ID документа
        doc_type: Тип документа (declaration/certificate)
        update_request_data: Данные для обновления
        
    Returns:
        True если запрос выполнен успешно, иначе False
    """
    
    
    # Создаем запрос на обновление
    update_request = DocumentUpdateRequest(**update_request_data)
    
    # Отправляем запрос на обновление
    response = update_document(doc_type, doc_id, update_request)
    if response:
        return True
    else:
        return False


def process_branches_changes(row, orig_row) -> Optional[Manufacturer]:
    """
    Обрабатывает изменения в филиалах производителя.
    
    Args:
        row: Строка с новыми значениями
        orig_row: Строка с исходными значениями
        
    Returns:
        Объект Manufacturer с изменениями или None если изменений нет
    """
    if row[TableColumns.BRANCHES] != orig_row[TableColumns.BRANCHES]:
        branches: List[Branch] = []
        if row[TableColumns.BRANCHES] and isinstance(row[TableColumns.BRANCHES], list):
            for branch_str in row[TableColumns.BRANCHES]:
                if ": " in branch_str:
                    country, name = branch_str.split(": ", 1)
                    branches.append(Branch(country=country, name=name))
                else:
                    # Если нет имени, только страна
                    branches.append(Branch(country=branch_str, name=""))
        
        # Создаем объект Manufacturer только если есть изменения в филиалах
        return Manufacturer(branches=branches)
    
    return None



def process_product_changes(row, orig_row) -> Dict[str, Any]:
    """
    Обрабатывает изменения в полях продукта.
    
    Args:
        row: Строка с новыми значениями
        orig_row: Строка с исходными значениями
        
    Returns:
        Словарь с измененными полями продукта
    """
    product_changes = {}
    
    # Проверяем и обрабатываем изменения в полях продукта
    if row[TableColumns.PRODUCT] != orig_row[TableColumns.PRODUCT]:
        product_changes["name"] = row[TableColumns.PRODUCT]
    
    if row[TableColumns.DESCRIPTION] != orig_row[TableColumns.DESCRIPTION]:
        product_changes["description"] = row[TableColumns.DESCRIPTION]
    
    if row[TableColumns.PRODUCT_COUNTRY] != orig_row[TableColumns.PRODUCT_COUNTRY]:
        product_changes["country"] = row[TableColumns.PRODUCT_COUNTRY]
    
    # Проверяем и обрабатываем изменения в ТН ВЭД
    if row[TableColumns.TNVED] != orig_row[TableColumns.TNVED]:
        tnved_list = [t.strip() for t in row[TableColumns.TNVED].split(",") if t.strip()]
        product_changes["tnveds"] = tnved_list
    
    # Проверяем и обрабатываем изменения в материалах
    if row[TableColumns.MATERIALS] != orig_row[TableColumns.MATERIALS]:
        materials_list = [m.strip() for m in row[TableColumns.MATERIALS].split(",") if m.strip()]
        product_changes["materials"] = materials_list
    
    # Проверяем и обрабатываем изменения в полях
    if row[TableColumns.GENDER] != orig_row[TableColumns.GENDER]:
        gender_list = [g.strip() for g in row[TableColumns.GENDER].split(",") if g.strip()]
        product_changes["genders"] = gender_list
    
    # Проверяем и обрабатываем изменения в брендах
    if row[TableColumns.BRANDS] != orig_row[TableColumns.BRANDS]:
        brands_list = [m.strip() for m in row[TableColumns.BRANDS].split(",") if m.strip()]
        product_changes["brands"] = brands_list
        
    return product_changes


def process_table_changes(edited_df: pd.DataFrame, original_df: pd.DataFrame, editable_cols: set) -> List[Dict[str, Any]]:
    """
    Обрабатывает изменения в таблице и отправляет запросы на обновление.
    
    Args:
        edited_df: DataFrame с отредактированными данными
        original_df: DataFrame с исходными данными
        editable_cols: Набор редактируемых столбцов
        
    Returns:
        Список результатов обработки каждой строки, содержащий:
        - row_id: ID документа
        - success: успешность операции (True/False)
        - message: сообщение о результате
        - error: информация об ошибке (если есть)
    """
    results = []
    
    for idx, row in edited_df.iterrows():
        orig_row = original_df.loc[idx]
        doc_id = row[TableColumns.SELECT]
        
        # Результат по умолчанию - пропущено (не выбрано)
        result = {
            "row_id": row[TableColumns.ID],
            "doc_type": "declaration" if row[TableColumns.TYPE] == "Д" else "certificate",
            "success": None,
            "message": "Документ не выбран для обновления",
            "error": None
        }
        
        # Проверяем, были ли изменения в любом из редактируемых полей
        if not row[TableColumns.SELECT] or not any(
            row[col] != orig_row[col] for col in editable_cols if col in row and col in orig_row
        ):
            results.append(result)
            continue
            
        # Создаем объекты для обновления только если есть изменения
        update_request_data = {}
        
        # Обрабатываем изменения в полях продукта
        product_changes = process_product_changes(row, orig_row)
        if product_changes:
            product = Product(**product_changes)
            update_request_data["product"] = product
        
        # Обрабатываем изменения в филиалах
        manufacturer = process_branches_changes(row, orig_row)
        if manufacturer:
            update_request_data["manufacturer"] = manufacturer
        
        # Отправляем запрос на обновление только если есть какие-либо изменения
        if update_request_data:
            # Определяем тип документа
            doc_type_api = "declaration" if row[TableColumns.TYPE] == "Д" else "certificate"
            
            # Отправляем запрос на обновление
            success = send_update_request(row[TableColumns.ID], doc_type_api, update_request_data)
            if success:
                result["success"] = True
                result["message"] = f"Документ {row[TableColumns.ID]} успешно обновлен"
            else:
                result["success"] = False
                result["message"] = f"Возникла проблема при обновлении документа {row[TableColumns.ID]}"
        else:
            result["success"] = None
            result["message"] = f"Для документа {row[TableColumns.ID]} не обнаружено фактических изменений"
        
        results.append(result)
    
    return results