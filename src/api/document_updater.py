import logging
import requests
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
import streamlit as st
from config.config import load_config
from src.auth.auth import authenticator

config = load_config()
logger = logging.getLogger(__name__)

class DocumentType(str, Enum):
    CERTIFICATE = "certificate"
    DECLARATION = "declaration"

class TokenRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access: str

class Branch(BaseModel):
    name: str
    country: str

class Manufacturer(BaseModel):
    branches: List[Branch]

class Product(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    country: Optional[str] = None
    tnveds: List[str] = Field(default_factory=list)
    materials: List[str] = Field(default_factory=list)
    genders: List[str] = Field(default_factory=list)
    brands: List[str] = Field(default_factory=list)

class UserData(BaseModel):
    product: Optional[Product] = None
    manufacturer: Optional[Manufacturer] = None

class Document(BaseModel):
    id: int
    type: DocumentType
    userData: Optional[UserData] = None
    registryData: Optional[Dict[str, Any]] = None
    changeLog: Optional[List[Dict[str, Any]]] = None

class DocumentResponse(BaseModel):
    success: bool
    data: Optional[Document] = None
    error: Optional[str] = None

class DocumentUpdateRequest(BaseModel):
    product: Optional[Product] = None
    manufacturer: Optional[Manufacturer] = None

    class Config:
        extra = "ignore"


def update_document(
    doc_type: str,
    doc_id: int,
    update_request: DocumentUpdateRequest
) -> Optional[DocumentResponse]:
    """Обновление документа через PUT /documents/{type}/{id}"""
    url = config.get_service_url('document', 'update_document', doc_type=doc_type, doc_id=doc_id)
    headers: Dict[str, str] = {}
    token = authenticator.get_token()
    if token:
        headers['Authorization'] = f"Bearer {token}"
    payload = update_request.model_dump(exclude_none=True)
    response = requests.put(url, json=payload, headers=headers)
    if response.status_code == 200:
        return DocumentResponse(**response.json())
    elif response.status_code == 401:
        st.error("Ошибка аутентификации. Пожалуйста, войдите в систему снова.")
        st.session_state["authentication_status"] = False
        st.rerun()
    else:
        st.error(f"Ошибка при обновлении документа: {response.status_code}")
        return None 