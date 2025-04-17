from abc import ABC, abstractmethod
from datetime import datetime
import json

class TokenStorage(ABC):
    @abstractmethod
    def save_token(self, token: str, expiry: datetime) -> None:
        pass
    
    @abstractmethod
    def get_stored_token(self) -> tuple[str, datetime] | None:
        pass
    
    @abstractmethod
    def clear_token(self) -> None:
        pass

class CookieTokenStorage(TokenStorage):
    def __init__(self):
        self._cookie_manager = None
        self.cookie_name = "fsa_auth_token"
        
    @property
    def cookie_manager(self):
        if self._cookie_manager is None:
            # Перемещаем импорт сюда для избежания проблем инициализации
            try:
                import extra_streamlit_components as stx
                self._cookie_manager = stx.CookieManager()
            except Exception as e:
                import streamlit as st
                st.error(f"Ошибка инициализации CookieManager: {str(e)}")
                self._cookie_manager = None
        return self._cookie_manager
    
    def save_token(self, token: str, expiry: datetime) -> None:
        data = {
            "token": token,
            "expiry": expiry.isoformat()
        }
        self.cookie_manager.set(
            self.cookie_name,
            json.dumps(data),
            expires_at=expiry
        )
    
    def get_stored_token(self) -> tuple[str, datetime] | None:
        stored = self.cookie_manager.get(self.cookie_name)
        if stored:
            try:
                data = json.loads(stored)
                return (
                    data["token"],
                    datetime.fromisoformat(data["expiry"])
                )
            except (json.JSONDecodeError, KeyError):
                return None
        return None
    
    def clear_token(self) -> None:
        self.cookie_manager.delete(self.cookie_name)