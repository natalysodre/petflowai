"""Modelos de dados (entrada, saída da IA e resposta da API)."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Categoria(str, Enum):
    AGENDAMENTO = "Agendamento"
    SINTOMAS_URGENCIA = "Sintomas / possível urgência"
    DUVIDAS_SERVICOS = "Dúvidas sobre serviços"
    VACINACAO_EXAMES = "Vacinação e exames"
    RECLAMACOES = "Reclamações"
    FINANCEIRO = "Financeiro"


class Urgencia(str, Enum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    EMERGENCIA = "emergencia"


class ClassificacaoIA(BaseModel):
    """Estrutura que o Gemini é obrigado a devolver (response_schema).

    Sem valores padrão de propósito: a API do Gemini não aceita
    'default' no schema de resposta.
    """

    categoria: Categoria = Field(description="Uma única categoria da mensagem.")
    urgencia: Urgencia = Field(description="Nível de urgência para a saúde do animal ou para o atendimento.")
    confianca: float = Field(description="Confiança da classificação, de 0 a 1.")
    resumo: str = Field(description="Resumo objetivo da solicitação em até 20 palavras.")
    nome_tutor: str | None = Field(description="Nome do tutor, se informado; caso contrário null.")
    nome_pet: str | None = Field(description="Nome do animal, se informado; caso contrário null.")
    especie: str | None = Field(description="Espécie do animal (cão, gato, ave...), se informada ou óbvia; caso contrário null.")
    sintomas: list[str] = Field(description="Sintomas citados. Lista vazia se não houver.")
    acao_sugerida: str = Field(description="Próximo passo para o setor que vai receber a mensagem.")
    resposta_sugerida: str = Field(description="Resposta curta e cordial para o tutor, sem diagnóstico.")


class MensagemEntrada(BaseModel):
    mensagem: str = Field(min_length=3, max_length=2000, examples=["Oi, meu cachorro Thor está vomitando desde ontem"])
    canal: str | None = Field(default="webhook", examples=["whatsapp"])
    remetente: str | None = Field(default=None, examples=["Maria Souza"])


class Encaminhamento(BaseModel):
    setor: str
    fila: str
    prioridade: str
    alerta_veterinario: bool
    revisao_humana: bool
    regra_seguranca_acionada: bool


class Automacao(BaseModel):
    enviado: bool
    status_http: int | None
    detalhe: str
    resposta: dict | None  # o que o n8n devolveu (ticket, fila de destino...)


class RespostaClassificacao(BaseModel):
    id: str
    recebido_em: datetime
    canal: str | None
    remetente: str | None
    mensagem_original: str
    classificacao: ClassificacaoIA
    encaminhamento: Encaminhamento
    origem: str  # "gemini" ou "simulado"
    cache: str  # "HIT" ou "MISS"
    automacao: Automacao | None = None
