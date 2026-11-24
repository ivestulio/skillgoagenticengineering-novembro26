"""Montagem do grafo.

START -> guardrail_entrada -> bloqueado -> END
                          -> liberado  -> atendimento
atendimento -> dermatologico -> dermatologista  -> guardrail_saida -> END
            -> cardiologico  -> cardiologista   -> guardrail_saida -> END
            -> neurologico   -> neurologista    -> guardrail_saida -> END
            -> urgente       -> agente_urgencia -> guardrail_saida -> END
            -> clinicogeral  -> clinicogeral    -> guardrail_saida -> END
"""

from langgraph.graph import END, START, StateGraph

from src.edges.roteamento import rotear_guardrail_entrada, rotear_por_urgencia
from src.nodes.agente_urgencia import agente_urgencia
from src.nodes.atendimento import atendimento
from src.nodes.cardiologista import cardiologista
from src.nodes.clinicogeral import clinicogeral
from src.nodes.dermatologista import dermatologista
from src.nodes.guardrail_entrada import guardrail_entrada
from src.nodes.guardrail_saida import guardrail_saida
from src.nodes.neurologista import neurologista
from src.state import State

builder = StateGraph(State)

builder.add_node("guardrail_entrada", guardrail_entrada)
builder.add_node("atendimento", atendimento)
builder.add_node("agente_urgencia", agente_urgencia)
builder.add_node("cardiologista", cardiologista)
builder.add_node("dermatologista", dermatologista)
builder.add_node("neurologista", neurologista)
builder.add_node("clinicogeral", clinicogeral)
builder.add_node("guardrail_saida", guardrail_saida)

builder.add_edge(START, "guardrail_entrada")
builder.add_conditional_edges(
    "guardrail_entrada",
    rotear_guardrail_entrada,
    {"liberado": "atendimento", "bloqueado": END},
)
builder.add_conditional_edges(
    "atendimento",
    rotear_por_urgencia,
    {
        "dermatologico": "dermatologista",
        "cardiologico": "cardiologista",
        "neurologico": "neurologista",
        "urgente": "agente_urgencia",
        "clinicogeral": "clinicogeral",
    },
)
builder.add_edge("agente_urgencia", "guardrail_saida")
builder.add_edge("cardiologista", "guardrail_saida")
builder.add_edge("dermatologista", "guardrail_saida")
builder.add_edge("neurologista", "guardrail_saida")
builder.add_edge("clinicogeral", "guardrail_saida")
builder.add_edge("guardrail_saida", END)

grafo = builder.compile()
