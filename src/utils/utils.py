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