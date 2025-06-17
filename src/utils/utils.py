from datetime import datetime
from typing import Dict, Any

def format_date(date_string):
    if date_string:
        return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ").strftime("%d.%m.%Y")
    return ""

def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)



def generate_fsa_url(doc_type: str, doc_id: str) -> str:
    """
    Генерирует URL для просмотра документа на сайте FSA.

    Args:
        doc_type: тип документа ('D' для декларации, 'C' для сертификата)
        doc_id: идентификатор документа

    Returns:
        str: полный URL для просмотра документа
    """
    base_url = "https://pub.fsa.gov.ru/"
    rss_or_rds = "rds" if doc_type == "D" else "rss"
    type_segment = "declaration" if doc_type == "D" else "certificate"
    base_info_or_common = "common" if doc_type == "D" else "baseInfo"

    return f"{base_url}{rss_or_rds}/{type_segment}/view/{doc_id}/{base_info_or_common}"


def utf8_encode_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Рекурсивно кодирует все строковые значения в словаре в UTF-8."""
    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = value.encode('utf-8').decode('utf-8')
        elif isinstance(value, dict):
            result[key] = utf8_encode_dict(value)
        elif isinstance(value, list):
            result[key] = [
                utf8_encode_dict(item) if isinstance(item, dict)
                else item.encode('utf-8').decode('utf-8') if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            result[key] = value
    return result


def get_nested_value(data: Dict[str, Any], path: str, default: Any = '') -> Any:
    keys = path.split('.')
    value = data
    for key in keys:
        if key.endswith(']'):
            key, index = key[:-1].split('[')
            try:
                value = value.get(key, [])[int(index)]
            except (IndexError, TypeError):
                return default
        else:
            value = value.get(key, {})
        if value == {}:
            return default
    return value if value != {} else default


def stringify_values(obj):
    if isinstance(obj, dict):
        return {k: stringify_values(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [stringify_values(i) for i in obj]
    elif obj is None:
        return ''
    else:
        return str(obj)