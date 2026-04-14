from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
import re


class ProfessorCreate(BaseModel):
    departamento_id: int
    nome: str
    cpf: str
    email: EmailStr
    siape: str
    titulacao: str
    regime: str = "40h"
    telefone: Optional[str] = None
    data_nascimento: Optional[date] = None

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, v: str) -> str:
        cpf = re.sub(r"\D", "", v)
        if len(cpf) != 11 or len(set(cpf)) == 1:
            raise ValueError("CPF inválido")
        for i in range(9, 11):
            soma = sum(int(cpf[j]) * (i + 1 - j) for j in range(i))
            digito = (soma * 10 % 11) % 10
            if digito != int(cpf[i]):
                raise ValueError("CPF inválido")
        return cpf


class ProfessorUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    titulacao: Optional[str] = None
    regime: Optional[str] = None
    telefone: Optional[str] = None
    status: Optional[str] = None


class ProfessorResponse(BaseModel):
    id: int
    departamento_id: int
    nome: str
    cpf: str
    email: str
    siape: str
    titulacao: str
    regime: str
    telefone: Optional[str]
    data_nascimento: Optional[date]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
