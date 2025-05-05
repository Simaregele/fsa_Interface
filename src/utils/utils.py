from datetime import datetime

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