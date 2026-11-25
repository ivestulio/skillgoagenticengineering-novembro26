"""Observabilidade no LangSmith: anota os runs e envia a decisao humana como feedback.

O trace em si e automatico: com LANGSMITH_TRACING=true e LANGSMITH_API_KEY no ambiente,
o LangChain/LangGraph envia cada execucao sozinho. Este modulo so acrescenta
informacoes de negocio para filtrar e montar graficos no LangSmith:

- metadados e tags no run do no que esta rodando (ex.: especialidade=cardiologia,
  tag guardrail:bloqueado);
- feedback "aprovacao_humana" (1 = aprovado, 0 = rejeitado) no trace da decisao.

Sem LangSmith configurado, as funcoes nao fazem nada. Erro de rede nunca quebra o grafo.
"""

import logging
from functools import lru_cache

from langsmith import Client, get_current_run_tree
from langsmith.utils import tracing_is_enabled

logger = logging.getLogger(__name__)


def anotar_run(metadados: dict | None = None, tags: list[str] | None = None) -> None:
    """Acrescenta metadados e tags ao run do no atual (aparecem no LangSmith)."""
    run = get_current_run_tree()
    if run is None:
        return
    if metadados:
        run.add_metadata(metadados)
    if tags:
        run.add_tags(tags)


@lru_cache(maxsize=1)
def _cliente() -> Client:
    return Client()


@lru_cache(maxsize=8)
def _id_do_projeto(nome: str):
    """O feedback precisa do id do projeto do LangSmith (session_id), nao so do nome."""
    return _cliente().read_project(project_name=nome).id


def enviar_feedback(chave: str, nota: float, comentario: str | None = None) -> None:
    """Grava um feedback no trace atual (o run raiz da execucao)."""
    run = get_current_run_tree()
    if run is None or not tracing_is_enabled():
        return
    try:
        _cliente().create_feedback(
            run_id=run.trace_id,
            trace_id=run.trace_id,
            session_id=run.session_id or _id_do_projeto(run.session_name),
            key=chave,
            score=nota,
            comment=comentario,
        )
    except Exception as erro:  # observabilidade nao pode derrubar o atendimento
        logger.warning("Nao foi possivel enviar o feedback ao LangSmith: %s", erro)
