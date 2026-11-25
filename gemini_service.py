"""Integração com o Gemini (Google GenAI) para classificar mensagens."""

import os

from dotenv import load_dotenv

from prompts import PROMPT_SISTEMA, montar_prompt_usuario
from schemas import ClassificacaoIA

load_dotenv()

MODELO = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

# MODO_SIMULADO=true permite testar API + n8n sem chave/cota do Gemini.
MODO_SIMULADO = os.getenv("MODO_SIMULADO", "false").lower() in ("1", "true", "sim")

_client = None


def _obter_cliente():
    global _client
    if _client is None:
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Configure a variável de ambiente GEMINI_API_KEY.")
        _client = genai.Client(api_key=api_key)
    return _client


def classificar_com_gemini(mensagem: str) -> ClassificacaoIA:
    resposta = _obter_cliente().models.generate_content(
        model=MODELO,
        contents=montar_prompt_usuario(mensagem),
        config={
            "system_instruction": PROMPT_SISTEMA,
            "temperature": 0.1,
            "max_output_tokens": 1024,
            "response_mime_type": "application/json",
            "response_schema": ClassificacaoIA,
        },
    )

    if isinstance(resposta.parsed, ClassificacaoIA):
        return resposta.parsed

    if not resposta.text:
        raise RuntimeError("O Gemini não retornou texto.")

    return ClassificacaoIA.model_validate_json(resposta.text)
