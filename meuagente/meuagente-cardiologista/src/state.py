from typing import Literal

from pydantic import BaseModel, Field


class CidSugerido(BaseModel):
    """Categoria do CID-10 sugerida para um sintoma."""

    sintoma: str = Field(description="Sintoma ou sinal clinico do prontuario")
    codigo: str = Field(description="Codigo da categoria no CID-10, ex.: R07")
    descricao: str = Field(description="Descricao da categoria no CID-10")

class ParecerCardiologico(BaseModel):
    """Parecer emitido pelo agente cardiologista."""

    hipotese_diagnostica: str = Field(description="Hipotese diagnostica cardiologica principal")
    risco: Literal["alto", "moderado", "baixo"] = Field(description="Nivel de risco cardiovascular imediato")
    condutas: list[str] = Field(description="Condutas e exames iniciais sugeridos, ex.: ECG, troponina")


class ParecerNeurologico(BaseModel):
    """Parecer emitido pelo agente neurologista."""

    hipotese_diagnostica: str = Field(description="Hipotese diagnostica neurologica principal")
    risco: Literal["alto", "moderado", "baixo"] = Field(description="Nivel de risco Neurologico imediato")
    condutas: list[str] = Field(
        description="Condutas e exames iniciais sugeridos, ex.: TC de cranio sem contraste, escala NIHSS, "
        "glicemia capilar, avaliacao de janela para trombolise, EEG se suspeita de crise convulsiva"
    )

class ParecerPediatrico(BaseModel):
    """Parecer emitido pelo agente pediatrico."""

    hipotese_diagnostica: str = Field(description="Hipotese diagnostica pediatrica principal")
    risco: Literal["alto", "moderado", "baixo"] = Field(description="Nivel de risco Pediatrico imediato")
    condutas: list[str] = Field(
        description="Condutas e exames iniciais sugeridos, ex.: sinais vitais ajustados a idade, "
        "avaliacao do grau de desidratacao, hemograma, antitermico com dose por peso (mg/kg), "
        "verificacao do cartao vacinal"
    )




class State(BaseModel):
    """Atendimento de Prontuarios medicos"""

    paciente_id: str = Field(..., description="ID do paciente")
    prontuario: str = Field(..., description="Conteudo do prontuario medico")
    # Preenchidos pelo no de atendimento (triagem): nao vem na entrada.
    urgencia: Literal["urgente", "nao_urgente"] | None = Field(None, description="Nivel de urgencia do atendimento")
    especialidade: Literal["cardiologia", "neurologia", "pediatria", "geral"] | None = Field(None, description="Especialidade indicada pela triagem")
    justificativa: str | None = Field(None, description="Motivo da classificacao de urgencia")
    # Preenchidos pelo no agente_urgencia: so quando o prontuario e urgente.
    sintomas: list[str] = Field(default_factory=list, description="Sintomas separados do prontuario")
    cids_sugeridos: list[CidSugerido] = Field(default_factory=list, description="Categorias do CID-10 sugeridas por sintoma")
    # Preenchido pelo no agente_cardiologista: so quando o caso e cardiologico.
    parecer_cardiologico: ParecerCardiologico | None = Field(None, description="Parecer do agente cardiologista")
    data_atualizacao: str = Field(..., description="Data da ultima atualizacao do prontuario")

    # Preenchido pelo no agente_neurologico: so quando o caso e neurologico.
    parecer_neurologico: ParecerNeurologico | None = Field(None, description="Parecer do agente neurologista")
    data_atualizacao: str = Field(..., description="Data da ultima atualizacao do prontuario")

    # Preenchido pelo no agente_pediatrico: so quando o caso e pediatrico.
    parecer_pediatrico: ParecerPediatrico | None = Field(None, description="Parecer do agente pediatrico")
    data_atualizacao: str = Field(..., description="Data da ultima atualizacao do prontuario")