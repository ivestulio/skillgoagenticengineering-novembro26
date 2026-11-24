from typing import Literal

from pydantic import BaseModel, Field


class AchadoGuardrail(BaseModel):
    """Problema encontrado pelo guardrail (sem o valor bruto encontrado)."""

    tipo: Literal["segredo", "pii", "injecao", "tamanho"] = Field(
        description="Categoria do achado"
    )
    regra: str = Field(description="Regra que encontrou, ex.: cpf, chave_openai")
    quantidade: int = Field(description="Quantas ocorrencias foram encontradas")


class ResultadoGuardrail(BaseModel):
    """Resultado de um guardrail de entrada ou saida."""

    bloqueado: bool = Field(description="True se o fluxo deve ser interrompido")
    motivo: str | None = Field(None, description="Motivo do bloqueio, se houver")
    achados: list[AchadoGuardrail] = Field(
        default_factory=list, description="Achados mascarados ou bloqueantes"
    )


class CidSugerido(BaseModel):
    """Categoria do CID-10 sugerida para um sintoma."""

    sintoma: str = Field(description="Sintoma ou sinal clinico do prontuario")
    codigo: str = Field(description="Codigo da categoria no CID-10, ex.: R07")
    descricao: str = Field(description="Descricao da categoria no CID-10")


class State(BaseModel):
    """Atendimento de Prontuarios medicos"""

    paciente_id: str = Field(..., description="ID do paciente")
    prontuario: str = Field(..., description="Conteudo do prontuario medico")
    # Guardrails
    guardrail_entrada: ResultadoGuardrail | None = Field(
        None, description="Resultado do guardrail de entrada"
    )
    guardrail_saida: ResultadoGuardrail | None = Field(
        None, description="Resultado do guardrail de saida (somente mascara)"
    )
    # Preenchidos pelo no de atendimento (triagem): nao vem na entrada.
    urgencia: Literal["urgente", "nao_urgente"] | None = Field(
        None, description="Nivel de urgencia do atendimento"
    )
    destino: Literal[
        "dermatologico", "cardiologico", "neurologico", "urgente", "clinicogeral"
    ] | None = Field(
        None,
        description="Destino da triagem: dermatologista, cardiologista, neurologista, urgencia ou clinico geral",
    )
    justificativa: str | None = Field(None, description="Motivo da classificacao de urgencia")
    # Preenchidos pelo especialista ou pela urgencia que atender o caso.
    sintomas: list[str] = Field(default_factory=list, description="Sintomas separados do prontuario")
    cids_sugeridos: list[CidSugerido] = Field(
        default_factory=list, description="Categorias do CID-10 sugeridas por sintoma"
    )
    # Preenchidos pelo no cardiologista.
    avaliacao_cardiologica: str | None = Field(None, description="Parecer clinico cardiologico")
    conduta_sugerida: str | None = Field(
        None, description="Conduta ou proximos passos sugeridos pelo cardiologista"
    )
    # Preenchidos pelo no dermatologista.
    avaliacao_dermatologica: str | None = Field(None, description="Parecer clinico dermatologico")
    conduta_dermatologica: str | None = Field(
        None, description="Conduta ou proximos passos sugeridos pelo dermatologista"
    )
    # Preenchidos pelo no neurologista.
    avaliacao_neurologica: str | None = Field(None, description="Parecer clinico neurologico")
    conduta_neurologica: str | None = Field(
        None, description="Conduta ou proximos passos sugeridos pelo neurologista"
    )
    # Preenchidos pelo no clinicogeral.
    avaliacao_clinica: str | None = Field(
        None, description="Parecer de clinica geral / atencao primaria"
    )
    conduta_clinica: str | None = Field(
        None, description="Conduta ou proximos passos sugeridos pelo clinico geral"
    )
    data_atualizacao: str = Field(..., description="Data da ultima atualizacao do prontuario")
