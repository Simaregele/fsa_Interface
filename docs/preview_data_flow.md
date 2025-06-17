# Поток данных «Интерактивный предпросмотр» и генерация документов

## 1. Сбор исходных данных
1. Пользователь выбирает строки в таблице результатов поиска.
2. Для каждой строки приложение запрашивает подробности через `get_document_details`.
3. Пара «детали + данные поиска» сохраняется в `st.session_state.selected_details` и `st.session_state.selected_search_data`.

## 2. Запрос предпросмотра
1. Пользователь нажимает кнопку **«Предпросмотр данных для выбранных»**.
2. Функция `preview_documents_for_selected` перебирает выбранные документы и вызывает
   `get_document_preview_json(details, base_api_url, search_data)`.
3. Бэкенд `/preview_documents` отвечает объектом вида:
   ```json
   {
     "processed_data": { ... },
     "template_text": "... Jinja-шаблон ..."
   }
   ```
4. Ответ кладётся в `st.session_state.preview_jsons[doc_id]`.

## 3. Отображение полей для редактирования
* Для каждого ключа из `processed_data`, кроме `filials`, в интерфейсе создаётся
  `st.text_input` (код в `fsa_search_app.py`).
* Ключи `filials` представляются парой `Описание / Адрес` на каждую запись.
* Значения виджетов хранятся в `st.session_state` под ключами вида
  `preview_input_{doc_id}_{field}` и `preview_input_{doc_id}_filial_{n}_name|address`.

## 4. Набор полей, которые видит пользователь
* Полный список исходит из `processed_data`, которое формирует бэкенд.
* Словарь `KEY_TO_PATH` в `src/utils/document_generator.py` определяет ТОЛЬКО те из
  этих полей, которые мы умеем «записать обратно» в структуру `RegistryData`.

## 5. Пользовательские изменения
* Streamlit автоматически обновляет соответствующие ключи `preview_input_*` при вводе.

## 6. Генерация документов из предпросмотра
1. Нажатие **«Сгенерировать документы из предпросмотра»** приводит к сбору всех
   текущих значений виджетов в `current_data` → далее в
   `all_preview_data_for_generation`.
2. Функция `generate_documents_from_preview_data` проходит по каждому документу:
   * Берёт `original_details` и патчит его через
     `apply_processed_to_details(original, processed_data)`.
   * Обновляет `search_data` (в т. ч. `Product.Tnveds`).
   * Вызывает `generate_documents(patched_details, search_data)`.
3. Внутри `generate_documents` выполняется `_prepare_request_data`, которое:
   * Объединяет `details` и `search_data`.
   * Кодирует данные в UTF-8 и отправляет на `/generate_documents`.
4. Ответ сервера сохраняется в `st.session_state.generated_documents[doc_id]` и
   показывается пользователю.

## 7. Кэширование
* Патч-версии `RegistryData` также кладутся в
  `st.session_state.registry_details_cache` для последующих операций. 