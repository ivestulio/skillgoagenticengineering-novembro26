"""No guardrail_entrada: primeira etapa do grafo, antes de qualquer chamada ao modelo."""

from src.services.guardrail_entrada import verificar_entrada
from src.state import State


def guardrail_entrada(state: State) -> dict:
    """Mascara PII/segredos e bloqueia injecao de prompt no prontuario."""
    sanitizado, resultado = verificar_entrada(state.prontuario)
    return {"prontuario": sanitizado, "guardrail_entrada": resultado}
