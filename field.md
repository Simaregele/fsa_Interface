Конечно! Вот разделение всех используемых полей по типам документов:

---

## 1. Сертификат соответствия (`certificate`)

**Корневые поля:**
- `docType` = "certificate"
- `RegistryNumber` — номер сертификата
- `RegistryID` — внутренний идентификатор

**RegistryData:**
- `applicant`:
  - `fullName`
  - `firstName`
  - `patronymic`
  - `surname`
  - `inn`
  - `ogrn`
  - `addresses[0].fullAddress`
  - `contacts[0].value` (email)
  - `contacts[1].value` (телефон)
- `manufacturer`:
  - `fullName`
  - `addresses[0].fullAddress`
- `certificationAuthority`:
  - `fullName`
  - `attestatRegNumber`
  - `attestatRegDate`
  - `addresses[0].fullAddress`
  - `contacts[0].value` (email)
  - `contacts[1].value` (телефон)
  - `surname`
  - `firstName`
  - `patronymic`
  - `accredOrgName`
- `product`:
  - `fullName`
  - `identifications[0].name`
  - `identifications[0].documents[0].name`
  - `identifications[0].standards[n].designation`
  - `identifications[0].standards[n].name`
  - `storageCondition`
  - `usageCondition`
  - `usageScope`
- `testingLabs[n]`:
  - `fullName`
  - `protocols[0].number`
  - `protocols[0].date`
- `experts[0]`:
  - `surname`
  - `firstName`
  - `patronimyc`
- `certRegDate`
- `certEndDate`

**search_Product:**
- `Tnveds[n]` — коды ТН ВЭД

---

## 2. Декларация соответствия (`declaration`)

**Корневые поля:**
- `docType` = "declaration"
- `RegistryNumber` — номер декларации

**RegistryData:**
- `applicant`:
  - `fullName`
  - `firstName`
  - `patronymic`
  - `surname`
  - `inn`
  - `ogrn`
  - `addresses[0].fullAddress`
  - `contacts[0].value` (email)
  - `contacts[1].value` (телефон)
  - `headPosition`
- `manufacturer`:
  - `fullName`
  - `addresses[0].fullAddress`
- `product`:
  - `fullName`
  - `identifications[0].name`
  - `identifications[0].documents[n].name`
  - `storageCondition`
  - `usageCondition`
  - `usageScope`
- `manufacturerFilials[n]`:
  - `fullName`
  - `addresses[0].fullAddress`
- `testingLabs[n]`:
  - `fullName`
  - `protocols[0].number`
  - `protocols[0].date`
- `declRegDate`
- `declEndDate`

**search_Product:**
- `Tnveds[n]` — коды ТН ВЭД

---

## 3. Доверенность (`attorney`)

**Корневые поля:**
- `docType` = "attorney" (или генерируется автоматически для других типов)

**RegistryData:**
- `applicant`:
  - `fullName`
  - `inn`
  - `ogrn`
  - `firstName`
  - `patronymic`
  - `surname`
  - `addresses[n].fullAddress` (все адреса)
- `manufacturer`:
  - `fullName` (если есть)

**Дополнительно:**
- Данные доверенного лица подгружаются из файла `doc_folder/trusted_person.json` (не из API).
- В шаблоне также используется текущая дата (`today_data`).

---

### Пример структуры для каждого типа

#### Сертификат
```json
{
  "docType": "certificate",
  "RegistryNumber": "...",
  "RegistryID": "...",
  "RegistryData": {
    "applicant": { ... },
    "manufacturer": { ... },
    "certificationAuthority": { ... },
    "product": { ... },
    "testingLabs": [ ... ],
    "experts": [ ... ],
    "certRegDate": "...",
    "certEndDate": "..."
  },
  "search_Product": {
    "Tnveds": [ ... ]
  }
}
```

#### Декларация
```json
{
  "docType": "declaration",
  "RegistryNumber": "...",
  "RegistryData": {
    "applicant": { ... },
    "manufacturer": { ... },
    "product": { ... },
    "manufacturerFilials": [ ... ],
    "testingLabs": [ ... ],
    "declRegDate": "...",
    "declEndDate": "..."
  },
  "search_Product": {
    "Tnveds": [ ... ]
  }
}
```

#### Доверенность
```json
{
  "docType": "attorney",
  "RegistryData": {
    "applicant": { ... },
    "manufacturer": { ... }
  }
}
```

---

Если нужно — могу расписать пример JSON для каждого типа отдельно!  
Если есть вопросы по какому-то конкретному полю — уточни, расскажу подробнее.


Что важно

build_preview_processed 



Здесь:
processed_data_for_doc берётся из preview_jsons, сформированных функцией
preview_documents_for_selected() в src/utils/document_generator.py.
Именно она вызывает build_preview_processed() → сериализует данные в processed_data и кладёт их в preview_jsons.
Цикл по field_keys создаёт колонки st.columns() и для каждого поля рисует st.text_input().
Ключ session_state_key = f"preview_input_{doc_id}_{field_key}" запоминает введённое значение в st.session_state, что и делает поле «редактируемым».
Для филиалов (filials) выводится отдельный блок: