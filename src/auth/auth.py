import requests
import streamlit as st
from datetime import datetime, timedelta
from config.config import load_config
from src.auth.storage import CookieTokenStorage

config = load_config()


class Authenticator:
    def __init__(self):
        self.api_url = config['auth_url']
        self.token_key = "jwt_token"
        self.token_expiry_key = "jwt_token_expiry"
        self.storage = CookieTokenStorage()

    def _save_auth_data(self, token: str, expiry: datetime, remember: bool = False):
        """Сохраняет данные аутентификации"""
        st.session_state[self.token_key] = token
        st.session_state[self.token_expiry_key] = expiry
        st.session_state["authentication_status"] = True
        
        if remember:
            self.storage.save_token(token, expiry)

    def _check_stored_auth(self) -> bool:
        """Проверяет сохраненные данные аутентификации"""
        stored = self.storage.get_stored_token()
        if stored:
            token, expiry = stored
            if expiry > datetime.now():
                self._save_auth_data(token, expiry)
                return True
            else:
                self.storage.clear_token()
        return False

    def login(self):
        # Проверяем сохраненные данные аутентификации
        if self._check_stored_auth():
            return

        st.subheader("Вход в систему")
        username = st.text_input("Имя пользователя")
        password = st.text_input("Пароль", type="password")
        remember_me = st.checkbox("Запомнить меня", value=True)

        if st.button("Войти"):
            with st.spinner('Выполняется вход в систему...'):
                try:
                    response = requests.post(
                        self.api_url, 
                        json={"username": username, "password": password}
                    )

                    if response.status_code == 200:
                        try:
                            data = response.json()
                            token = data.get("access")
                            if token:
                                # Устанавливаем срок действия токена
                                expiry = datetime.now() + timedelta(
                                    days=30 if remember_me else 1
                                )
                                self._save_auth_data(token, expiry, remember_me)
                                st.success("Вход выполнен успешно!")
                                st.rerun()
                            else:
                                st.error("Токен отсутствует в ответе сервера")
                        except ValueError:
                            st.error("Ошибка при разборе JSON-ответа")
                    else:
                        st.error(f"Ошибка при входе: {response.status_code}")
                        st.write(f"Ответ сервера: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Ошибка при отправке запроса: {str(e)}")

    def logout(self):
        if st.button("Выйти"):
            # Очищаем данные сессии
            st.session_state[self.token_key] = None
            st.session_state[self.token_expiry_key] = None
            st.session_state["authentication_status"] = False
            
            # Очищаем сохраненные данные
            self.storage.clear_token()
            
            st.rerun()

    def is_authenticated(self):
        # Сначала проверяем текущую сессию
        if st.session_state.get("authentication_status", False):
            expiry = st.session_state.get(self.token_expiry_key)
            if expiry and expiry > datetime.now():
                return True
            
        # Если сессия истекла, проверяем сохраненные данные
        if self._check_stored_auth():
            return True
            
        # Если ничего не нашли - очищаем все данные
        st.session_state["authentication_status"] = False
        st.session_state[self.token_key] = None
        st.session_state[self.token_expiry_key] = None
        return False

    def get_token(self):
        return st.session_state.get(self.token_key)

    def login_required(self, func):
        def wrapper(*args, **kwargs):
            if self.is_authenticated():
                return func(*args, **kwargs)
            else:
                st.warning("Пожалуйста, выполните вход для доступа к этой странице.")
                self.login()
        return wrapper


authenticator = Authenticator()
