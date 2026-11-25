"""Montagem do grafo.

START -> atendimento -> cardiologico -> agente_cardiologista -> END
                     -> neurologico  -> agente_neurologista  -> END
                     -> pediatrico   -> agente_pediatria     -> END
                     -> urgente      -> agente_urgencia      -> END
                     -> nao_urgente  -> END

"""

from langgraph.graph import END, START, StateGraph

from src.edges.roteamento import rotear_triagem
from src.nodes.agente_cardiologista import agente_cardiologista
from src.nodes.agente_neurologista import agente_neurologista
from src.nodes.agente_pediatria import agente_pediatria
from src.nodes.agente_urgencia import agente_urgencia
from src.nodes.atendimento import atendimento
from src.state import State

builder = StateGraph(State)

builder.add_node("atendimento", atendimento)
builder.add_node("agente_urgencia", agente_urgencia)
builder.add_node("agente_cardiologista", agente_cardiologista)
builder.add_node("agente_neurologista", agente_neurologista)
builder.add_node("agente_pediatria", agente_pediatria)

builder.add_edge(START, "atendimento")
builder.add_conditional_edges(
    "atendimento",
    rotear_triagem,
    {
        "cardiologico": "agente_cardiologista",
        "neurologico": "agente_neurologista",
        "pediatrico": "agente_pediatria",
        "urgente": "agente_urgencia",
        "nao_urgente": END,
    },
)
builder.add_edge("agente_urgencia", END)
builder.add_edge("agente_cardiologista", END)
builder.add_edge("agente_neurologista", END)
builder.add_edge("agente_pediatria", END)
grafo = builder.compile()
