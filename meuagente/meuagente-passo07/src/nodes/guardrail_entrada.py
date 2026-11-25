"""No guardrail_entrada: primeira etapa do grafo, antes de qualquer chamada ao modelo."""

from src.services.guardrail import verificar_prontuario
from src.services.observabilidade import anotar_run
from src.state import State


def guardrail_entrada(state: State) -> dict:
    """Mascara segredos e PII e bloqueia injecao de prompt.

    Substitui o prontuario no state pela versao sanitizada: os nos seguintes so veem o
    texto ja mascarado. Se bloqueado, o prontuario fica vazio e o grafo termina.
    """
    sanitizado, resultado = verificar_prontuario(state.prontuario)
    # No LangSmith: tag para contar bloqueios e saber quais regras dispararam
    # (so o nome da regra, nunca o valor encontrado).
    anotar_run(
        metadados={"guardrail_bloqueado": resultado.bloqueado},
        tags=[f"guardrail:{'bloqueado' if resultado.bloqueado else 'liberado'}"]
        + [f"guardrail:{achado.regra}" for achado in resultado.achados],
    )
    return {"prontuario": sanitizado, "guardrail": resultado}
