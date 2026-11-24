"""Padroes regex compartilhados pelos guardrails de entrada e saida (sem LLM)."""

import re
import unicodedata
from collections import Counter
from collections.abc import Callable

PADROES_SEGREDO: list[tuple[str, re.Pattern[str]]] = [
    (
        "chave_privada",
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(?:-----END [A-Z ]*PRIVATE KEY-----|\Z)",
            re.S,
        ),
    ),
    ("chave_openai", re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}")),
    ("chave_langsmith", re.compile(r"\blsv2_(?:pt|sk)_[A-Za-z0-9_]{20,}")),
    ("chave_aws", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("token_github", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("chave_google", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("token_slack", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}")),
    (
        "jwt",
        re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),
    ),
    (
        "string_conexao",
        re.compile(r"\b(?:AccountKey|SharedAccessKey|Password|Pwd)=[^;\s]{8,}", re.I),
    ),
    (
        "atribuicao_segredo",
        re.compile(
            r"\b(?:api[_-]?key|apikey|secret|client[_-]?secret|senha|password|passwd|token)"
            r"\s*[:=]\s*[\"']?(?!\[SEGREDO\])[^\s\"']{6,}",
            re.I,
        ),
    ),
    (
        "token_longo",
        re.compile(
            r"\b(?=[A-Za-z0-9+/_-]*\d)(?=[A-Za-z0-9+/_-]*[A-Za-z])[A-Za-z0-9+/_-]{40,}={0,2}"
        ),
    ),
]


def _digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto)


def _cpf_valido(texto: str) -> bool:
    d = _digitos(texto)
    if len(d) != 11 or d == d[0] * 11:
        return False
    for tamanho in (9, 10):
        soma = sum(int(d[i]) * (tamanho + 1 - i) for i in range(tamanho))
        if (soma * 10 % 11) % 10 != int(d[tamanho]):
            return False
    return True


def _cns_valido(texto: str) -> bool:
    d = _digitos(texto)
    if len(d) != 15 or d[0] not in "12789":
        return False
    return sum(int(c) * (15 - i) for i, c in enumerate(d)) % 11 == 0


PADROES_PII: list[tuple[str, re.Pattern[str], str, Callable[[str], bool] | None]] = [
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b"), "[EMAIL]", None),
    ("cnpj", re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b"), "[CNPJ]", None),
    ("cpf", re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"), "[CPF]", _cpf_valido),
    ("cns", re.compile(r"\b[12789]\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\b"), "[CNS]", _cns_valido),
    (
        "rg",
        re.compile(r"\bRG\b\s*(?:n[º°o.]?\s*)?[:\-]?\s*(?P<valor>[\d.\-]{5,12}[\dxX]?)", re.I),
        "[RG]",
        None,
    ),
    (
        "telefone",
        re.compile(r"(?:\+55\s?)?(?:\(\d{2}\)\s?|\b\d{2}\s)9?\d{4}[-\s]?\d{4}\b"),
        "[TELEFONE]",
        None,
    ),
    ("cep", re.compile(r"\b\d{5}-\d{3}\b"), "[CEP]", None),
    (
        "data_nascimento",
        re.compile(
            r"\b(?:nascid[oa]\s+em|data\s+de\s+nascimento|DN)\s*:?\s*(?P<valor>\d{1,2}/\d{1,2}/\d{2,4})",
            re.I,
        ),
        "[DATA_NASCIMENTO]",
        None,
    ),
    (
        "nome",
        re.compile(
            r"\b(?i:nome|paciente|m[aã]e|pai|respons[aá]vel)\s*:\s*"
            r"(?P<valor>[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+(?:\s+(?:d[aeo]s?\s+)?"
            r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)+)"
        ),
        "[NOME]",
        None,
    ),
]

PADROES_INJECAO: list[tuple[str, re.Pattern[str]]] = [
    (
        "ignorar_instrucoes",
        re.compile(
            r"\b(?:ignor\w*|desconsider\w*|esquec\w*|disregard|forget)\s+(?:\w+\s+){0,3}?"
            r"(?:instruc\w*|regras|ordens|prompt|instructions|rules|tudo\s+(?:o\s+que|acima))"
        ),
    ),
    (
        "troca_de_papel",
        re.compile(
            r"\b(?:voce\s+agora\s+e|a\s+partir\s+de\s+agora\s+voce|you\s+are\s+now|act\s+as|"
            r"aja\s+como|finja\s+(?:ser|que)|pretend\s+(?:to\s+be|you))\b"
        ),
    ),
    (
        "prompt_do_sistema",
        re.compile(
            r"\b(?:system\s+prompt|developer\s+message|(?:prompt|instrucoes|mensagem)\s+do\s+sistema|"
            r"(?:revele|mostre|repita|imprima)\s+(?:\w+\s+){0,3}?(?:prompt|instrucoes))\b"
        ),
    ),
    (
        "marcador_de_papel",
        re.compile(
            r"<\|?(?:im_start|im_end|system|assistant|user)\|?>|\[/?inst\]|</?system>|"
            r"^\s*#{2,}\s*(?:system|sistema|instruc\w*)\b",
            re.M,
        ),
    ),
    (
        "jailbreak",
        re.compile(r"\b(?:jailbreak|modo\s+desenvolvedor|developer\s+mode|\bdan\s+mode)\b"),
    ),
    (
        "manipular_triagem",
        re.compile(
            r"\b(?:classifique|classifica|considere|marque|trate)\s+(?:\w+\s+){0,3}?"
            r"(?:como\s+)?(?:nao\s+urgente|urgente|nao_urgente|cardiolog\w*|neurolog\w*|"
            r"dermatolog\w*|clinic\w*\s*geral|geral)\b"
        ),
    ),
    (
        "manipular_resposta",
        re.compile(
            r"\b(?:responda|retorne|devolva)\s+(?:apenas|somente|so)\b|"
            r"\bnao\s+(?:use|chame|utilize|consulte)\s+(?:a\s+)?(?:ferramenta|tool|buscar_cid10)\b|"
            r"\b(?:sugira|use|coloque|informe)\s+(?:o\s+)?(?:cid|codigo)\s+[a-z]\d{2}\b"
        ),
    ),
]


def normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acento.lower()


def mascarar_segredos(texto: str, contagem: Counter) -> str:
    for regra, padrao in PADROES_SEGREDO:
        texto, n = padrao.subn("[SEGREDO]", texto)
        if n:
            contagem[("segredo", regra)] += n
    return texto


def mascarar_pii(texto: str, contagem: Counter) -> str:
    for regra, padrao, marcador, valido in PADROES_PII:

        def trocar(achado: re.Match[str], _regra=regra, _marcador=marcador, _valido=valido) -> str:
            if _valido and not _valido(achado.group(0)):
                return achado.group(0)
            contagem[("pii", _regra)] += 1
            if "valor" in achado.re.groupindex:
                inicio, fim = achado.span("valor")
                base = achado.start()
                trecho = achado.group(0)
                return trecho[: inicio - base] + _marcador + trecho[fim - base :]
            return _marcador

        texto = padrao.sub(trocar, texto)
    return texto


def mascarar_segredos_e_pii(texto: str) -> tuple[str, Counter]:
    """Aplica mascara de segredos e depois PII; devolve texto e contagem."""
    contagem: Counter = Counter()
    sanitizado = mascarar_segredos(texto, contagem)
    sanitizado = mascarar_pii(sanitizado, contagem)
    return sanitizado, contagem
