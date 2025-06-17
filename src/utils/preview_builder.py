import re
import logging
from typing import Any, Dict

from src.templates.certificate_preview_template import PREVIEW_FIELDS, PREVIEW_TEMPLATE, PREVIEW_VIEW

logger = logging.getLogger(__name__)


def _get_by_path(data: Dict[str, Any], path: str) -> str | Any:
    """Возвращает значение из вложенного словаря/списка по пути вида 'a.b.0.c'."""
    cur: Any = data
    for part in path.split('.'):
        # --- Работаем с текущим сегментом пути ---
        # 1. Текущий уровень – список. Ожидаем числовой индекс, который может быть
        #    записан как "3" либо "[3]".
        if isinstance(cur, list):
            idx_part = part[1:-1] if part.startswith('[') and part.endswith(']') else part
            if idx_part.isdigit():
                idx = int(idx_part)
                if idx < len(cur):
                    cur = cur[idx]
                else:
                    return ''  # индекс вне диапазона
            else:
                return ''  # некорректный индекс для списка

        # 2. Текущий уровень – словарь.
        else:
            # Поддержка форматов:
            #   «contacts[1]»  – имя и индекс в одном сегменте
            #   «contacts» + последующий «[1]» – имя и индекс раздельно

            # a) Если сегмент вида "[idx]" – значит предыдущий ключ дал нам список,
            #    но этот код выполнится только если cur – dict, поэтому просто ошибка.
            if part.startswith('[') and part.endswith(']'):
                # Невозможная ситуация (список уже обработан выше)
                return ''

            # b) Сегмент содержит индекс внутри имени:  contacts[1]
            if '[' in part and ']' in part:
                matched = re.match(r"(.+)\[([0-9]+)]", part)
                if not matched:
                    return ''
                name, index = matched.groups()
                target_list = cur.get(name, []) if isinstance(cur, dict) else []
                idx = int(index)
                if idx < len(target_list):
                    cur = target_list[idx]
                else:
                    return ''
            else:
                # Обычный ключ словаря
                cur = cur.get(part, '') if isinstance(cur, dict) else ''
    return cur


def _resolve_placeholder(ph: str, details: Dict[str, Any], search_data: Dict[str, Any]) -> str:
    if ph.startswith('search_'):
        target = search_data
        path = ph[len('search_'):]
    else:
        target = details
        path = ph
    val = _get_by_path(target, path)
    return str(val)


_PLACEHOLDER_RE = re.compile(r"{([^{}]+)}")


def build_preview_processed(details: Dict[str, Any], search_data: Dict[str, Any] | None = None) -> Dict[str, str]:
    """Создаёт processed_data, подставляя значения из details/search_data в шаблон."""
    if search_data is None:
        search_data = {}

    processed: Dict[str, str] = {}
    for _label, path in PREVIEW_FIELDS:
        value = _resolve_placeholder(path, details, search_data)
        processed[path] = value

    logger.info("Сформирован локальный processed_data: %s", processed)
    return processed


def render_preview_html(processed_data: Dict[str, str]) -> str:
    """Генерирует простой HTML-превью на основе PREVIEW_TEMPLATE,
    подставляя значения из processed_data. Каждое поле выводится новой строкой."""
    # Сначала формируем значения для каждого ключа PREVIEW_TEMPLATE
    key_to_value: Dict[str, str] = {}
    for key, template in PREVIEW_TEMPLATE.items():
        def repl(match: re.Match) -> str:
            path = match.group(1)
            return processed_data.get(path, '')
        if key == 'tn_ved_codes':
            rendered = processed_data.get("search_Product.Tnveds")
            parts = rendered.strip("[]").replace("'", "").split(",")
            rendered = ", ".join(part.strip() for part in parts)
            continue

        if key == 'expert_name':
            experts = processed_data.get("RegistryData.experts")
            if experts:
                value = experts[0].get("surname")
                value += " " + experts[0].get("firstName")
                value += " " + experts[0].get("patronimyc")
            else:
                value = ""
            continue


        rendered = _PLACEHOLDER_RE.sub(repl, template)
        key_to_value[key] = rendered

    # Теперь подставляем в PREVIEW_VIEW, где плейсхолдеры вида {{certificate_number}}
    html_text = PREVIEW_VIEW
    for key, val in key_to_value.items():
        safe_val = str(val).replace("\n", "<br>")
        html_text = re.sub(rf"{{{{\s*{re.escape(key)}\s*}}}}", safe_val, html_text)

    # Переводим переводы строк в <br> для остальных частей
    html_text = html_text.replace("\n", "<br>")
    return html_text