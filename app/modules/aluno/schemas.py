from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
import re


class EnderecoSchema(BaseModel):
    logradouro: str
    numero: str
    complemento: Optional[str] = None
    bairro: str
    cidade: str
    estado: str
    cep: str


class AlunoCreate(BaseModel):
    curso_id: int
    nome: str
    cpf: str
    email: EmailStr
    telefone: Optional[str] = None
    data_nascimento: Optional[date] = None
    endereco: Optional[EnderecoSchema] = None
    semestre_ingresso: str  # formato: 2024/1

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

    @field_validator("semestre_ingresso")
    @classmethod
    def validar_semestre(cls, v: str) -> str:
        if not re.match(r"^\d{4}/[12]$", v):
            raise ValueError("Semestre deve estar no formato AAAA/1 ou AAAA/2 (ex: 2024/1)")
        return v


class AlunoUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    data_nascimento: Optional[date] = None
    endereco: Optional[EnderecoSchema] = None
    status: Optional[str] = None


class AlunoResponse(BaseModel):
    id: int
    curso_id: int
    matricula: str
    nome: str
    cpf: str
    email: str
    telefone: Optional[str]
    data_nascimento: Optional[date]
    semestre_ingresso: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
