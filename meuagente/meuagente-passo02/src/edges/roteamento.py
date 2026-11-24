"""Arestas condicionais: decidem o proximo passo a partir do state, sem chamar o LLM."""

from typing import Literal

from src.state import State

Destino = Literal[
    "dermatologico", "cardiologico", "neurologico", "urgente", "clinicogeral"
]


def rotear_guardrail_entrada(state: State) -> Literal["liberado", "bloqueado"]:
    """So segue para a triagem se o guardrail de entrada liberou."""
    if state.guardrail_entrada is not None and not state.guardrail_entrada.bloqueado:
        return "liberado"
    return "bloqueado"


def rotear_por_urgencia(state: State) -> Destino:
    """Segue o ramo definido pelo atendimento. Sem classificacao, trata como urgente."""
    if state.destino in (
        "dermatologico",
        "cardiologico",
        "neurologico",
        "urgente",
        "clinicogeral",
    ):
        return state.destino
    return "clinicogeral" if state.urgencia == "nao_urgente" else "urgente"
