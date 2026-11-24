"""No guardrail_saida: ultima etapa, remascara PII/segredos antes do chat."""

from src.services.guardrail_saida import sanitizar_state_resposta
from src.state import State


def guardrail_saida(state: State) -> dict:
    """Aplica mascara de PII/segredos nos textos de resposta."""
    return sanitizar_state_resposta(state)
