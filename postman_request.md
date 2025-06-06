# Команда для тестирования генерации документов в Postman

Этот документ описывает, как создать и отправить запрос в Postman для тестирования эндпоинта генерации документов.

---

### 1. Параметры запроса

- **Метод (Method):** `POST`
- **URL:** `http://91.92.136.247:8001/generate_documents` 
  - *Примечание: Эндпоинт `/generate_documents` основан на анализе кода. Если он не сработает, проверьте документацию API.*

---

### 2. Заголовки (Headers)

Необходимо добавить следующий заголовок, чтобы сервер понимал, что мы отправляем данные в формате JSON.

| Key             | Value                            |
|-----------------|----------------------------------|
| `Content-Type`  | `application/json; charset=utf-8`|

Если ваш API требует авторизации, добавьте также заголовок `Authorization`:

| Key             | Value                     |
|-----------------|---------------------------|
| `Authorization` | `Bearer <ваш_jwt_токен>` |

---

### 3. Тело запроса (Body)

Перейдите во вкладку **Body**, выберите тип **raw** и формат **JSON**. Вставьте в поле для ввода следующий JSON. 

**Важно:** Согласно коду, все данные должны быть обернуты в корневой объект с ключом `"data"`.

```json
{
  "data": {
    "RegistryID": 3568396,
    "RegistryNumber": "ЕАЭС RU С-TR.АБ47.В.05162/25",
    "RegistryData": {
        "annexes": [],
        "applicant": {
            "addlRegInfo": null,
            "addresses": [],
            "contacts": [
                {
                    "idContact": 1177476,
                    "idContactType": 4,
                    "value": "arrmo@mail.ru"
                },
                {
                    "idContact": 1177475,
                    "idContactType": 1,
                    "value": "+79184492761"
                }
            ],
            "firstName": "Армен",
            "fullName": "Погосян Армен Левонович",
            "headPosition": null,
            "idApplicantType": 1,
            "idEgrul": null,
            "idLegalForm": null,
            "idLegalSubject": 8044899,
            "idLegalSubjectType": 2,
            "idPerson": 17664833,
            "idPersonDoc": 118807,
            "inn": "231129497804",
            "isEecRegister": true,
            "kpp": null,
            "ogrn": "320237500045679",
            "ogrnAssignDate": "2020-02-04",
            "passportIssueDate": null,
            "passportIssuedBy": null,
            "passportNum": null,
            "patronymic": "Левонович",
            "regDate": "2023-12-18",
            "regOrganName": "Управление Федеральной налоговой службы по Удмуртской Республике",
            "shortName": null,
            "surname": "Погосян",
            "transnational": []
        },
        "applicantFilials": [],
        "assignRegNumber": false,
        "awaitForApprove": false,
        "awaitOperatorCheck": null,
        "batchInspection": false,
        "blankNumber": "0570396",
        "certEndDate": "2028-04-01",
        "certRegDate": "2025-04-02",
        "certificationAuthority": {
            "accredOrgName": "Федеральная служба по аккредитации",
            "addresses": [
                {
                    "flat": null,
                    "foreignCity": null,
                    "foreignDistrict": null,
                    "foreignHouse": null,
                    "foreignLocality": null,
                    "foreignStreet": null,
                    "fullAddress": "123100, РОССИЯ, Г Москва, улица Сергея Макеева, дом 7 строение 2, помещение 3/4, этаж 4, комнаты 21, 21а, 22, 23",
                    "gln": null,
                    "glonass": null,
                    "idAddrType": 3,
                    "idAddress": 23961688,
                    "idCity": null,
                    "idCodeOksm": "643",
                    "idDistrict": null,
                    "idHouse": null,
                    "idLocality": null,
                    "idStreet": null,
                    "idSubject": "0c5b2444-70a0-4932-980c-b4dc0d3f02b5",
                    "oksmShort": true,
                    "otherGln": null,
                    "postCode": "123100",
                    "uniqueAddress": "улица Сергея Макеева, дом 7 строение 2, помещение 3/4, этаж 4, комнаты 21, 21а, 22, 23"
                },
                {
                    "flat": null,
                    "foreignCity": null,
                    "foreignDistrict": null,
                    "foreignHouse": null,
                    "foreignLocality": null,
                    "foreignStreet": null,
                    "fullAddress": "125124, РОССИЯ,  Г.Москва, МУНИЦИПАЛЬНЫЙ ОКРУГ БЕГОВОЙ вн. тер. г.,   УЛ ПРАВДЫ, Д. 8, К. 27 , ПОМЕЩ.   1/1",
                    "gln": null,
                    "glonass": null,
                    "idAddrType": 1,
                    "idAddress": 23961687,
                    "idCity": null,
                    "idCodeOksm": null,
                    "idDistrict": null,
                    "idHouse": null,
                    "idLocality": null,
                    "idStreet": null,
                    "idSubject": null,
                    "oksmShort": true,
                    "otherGln": null,
                    "postCode": null,
                    "uniqueAddress": null
                }
            ],
            "attestatEndDate": null,
            "attestatRegDate": "2016-01-28",
            "attestatRegNumber": "RA.RU.11АБ47",
            "contacts": [
                {
                    "idContact": 6336032,
                    "idContactType": 5,
                    "value": "ossystema.ru"
                },
                {
                    "idContact": 6336031,
                    "idContactType": 4,
                    "value": "info.ossystema@yandex.ru"
                },
                {
                    "idContact": 6336030,
                    "idContactType": 1,
                    "value": "+74955653917"
                }
            ],
            "firstName": "Владимир",
            "fullName": "Орган по сертификации продукции общества с ограниченной ответственностью \"Система\"",
            "idCertificationAuthority": 4172614,
            "idPerson": 17664836,
            "idRal": 6788,
            "ogrn": "1136164005834",
            "patronymic": "Александрович",
            "prevAttestatRegNumber": null,
            "prevIdRal": null,
            "surname": "Кабанов"
        },
        "documents": {
            "applicantOtherDocuments": [
                {
                    "annex": false,
                    "date": "2025-03-12",
                    "id": 20423315,
                    "idCategory": 6,
                    "idTechnicalReglament": null,
                    "name": "Копии таможенной декларации или иных документов, используемых в качестве таможенной декларации, оформленных на продукцию, ввезенную для проведения исследований и испытаний в качестве проб (образцов) для целей подтверждения соответствия: Декларация на товары для экспресс-грузов №10005020/120325/0011130",
                    "number": "10005020/120325/0011130"
                }
            ]
        }
    },
    "search_Applicant": "Погосян Армен Левонович",
    "search_ID": 3568396,
    "search_Manufacturer": {
        "Address": "Турция, Mimar Kemalettin Mah, Aga Cesmesi Sok, No:4/D Laleli - Fatih - Istanbul",
        "Branches": [
            {
                "Country": "ТУРЦИЯ",
                "Name": "Адрес места осуществления деятельности по изготовлению продукции:"
            }
        ],
        "Country": "ТУРЦИЯ",
        "Name": "LARA TEKSTIL SANAYI TICARET ANONIM SIRKETI",
        "SearchName": "LARA TEKSTIL SANAYI TICARET ANONIM SIRKETI"
    },
    "search_Number": "ЕАЭС RU С-TR.АБ47.В.05162/25",
    "search_Product": {
        "Brands": [
            "трусы-шорты",
            "трусы-шорты",
            "Donella",
            "Doni",
            "Doni underwear",
            "Donella Boys",
            "Donella Man",
            "Donella Kids"
        ],
        "Country": "ТУРЦИЯ",
        "Description": "Изделия бельевые трикотажные первого слоя для детей дошкольной, школьной возрастных групп и подростков из хлопчатобумажной пряжи с вложением полиуретановых нитей, в комплектах и отдельными предметами: футболки (фуфайки), в том числе модель «лонгслив», майки, в том числе модель «топ», трусы, в том числе моделей «боксеры», «трусы-шорты»,; ",
        "Genders": [
            "дет"
        ],
        "Name": "Изделия бельевые трикотажные первого слоя для детей дошкольной, школьной возрастных групп и подростков из хлопчатобумажной пряжи с вложением полиуретановых нитей, в комплектах и отдельными предметами: футболки (фуфайки), в том числе модель «лонгслив», майки, в том числе модель «топ», трусы, в том числе моделей «боксеры», «трусы-шорты», "
    },
    "search_RegistrationDate": "2025-04-02T00:00:00Z",
    "search_Status": "Действует",
    "search_Type": "C",
    "search_ValidityPeriod": "2028-04-01T00:00:00Z"
  }
}
``` 