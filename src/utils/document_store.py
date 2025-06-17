class DocumentStore:
    """Singleton для хранения и доступа к деталям документов.

    Используется как единый источник правды – все функции получают одну и ту же
    ссылку на объект деталей, поэтому изменения отражаются во всех частях
    приложения.
    """

    _instance: "DocumentStore | None" = None
    _docs: dict[str, dict]  # doc_id -> details
    _search: dict[str, dict]  # doc_id -> search_data

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._docs = {}
            cls._instance._search = {}
        return cls._instance

    # --- API ---
    def get(self, doc_id: str) -> dict | None:
        return self._docs.get(doc_id)

    def set(self, doc_id: str, details: dict) -> dict:
        self._docs[doc_id] = details
        return details

    def update(self, doc_id: str, details_part: dict) -> dict | None:
        """Поверхностное обновление существующего словаря."""
        if doc_id not in self._docs:
            return None
        self._docs[doc_id].update(details_part)
        return self._docs[doc_id]

    def all(self) -> dict[str, dict]:
        return self._docs

    # --- Search-data API ---
    def set_search(self, doc_id: str, search_data: dict) -> dict:
        """Сохраняет данные поиска для doc_id и возвращает их."""
        self._search[doc_id] = search_data
        return search_data

    def get_search(self, doc_id: str) -> dict | None:
        return self._search.get(doc_id)

    def search_all(self) -> dict[str, dict]:
        return self._search 