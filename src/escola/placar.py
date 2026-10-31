"""O placar entre os perfis: pontos da semana, a sequência de dias (o foguinho) e quem venceu cada semana.

Pontos são minutos estimados de estudo: a aula, a leitura ou o guia concluídos valem os minutos do item, e cada
questão vale 2. A questão conta uma vez por semana (refazer a mesma lista não soma) e, para a sequência, uma vez por
dia. O dia e a semana viram às 4h, como o resto da Escola. Tudo sai do progresso de cada um: nada novo é guardado."""
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timedelta

PONTOS_POR_QUESTAO = 2
MINIMO_DIA = 15  # pontos (minutos) para o dia valer na sequência
VIRADA = 4


@dataclass
class Registros:
    """O que um perfil fez: (quando concluiu, minutos) de cada aula e (quando respondeu, "alvo#posição") de cada
    questão respondida."""
    aulas: list[tuple[datetime, int]]
    questoes: list[tuple[datetime, str]]


def dia_de(quando: datetime) -> date:
    return (quando - timedelta(hours=VIRADA)).date()


def segunda_de(dia: date) -> date:
    return dia - timedelta(days=dia.weekday())


def pontos_da_semana(r: Registros, segunda: date) -> int:
    aulas = sum(m for quando, m in r.aulas if segunda_de(dia_de(quando)) == segunda)
    questoes = {q for quando, q in r.questoes if segunda_de(dia_de(quando)) == segunda}
    return aulas + PONTOS_POR_QUESTAO * len(questoes)


def pontos_por_dia(r: Registros) -> dict[date, int]:
    pontos: Counter[date] = Counter()
    for quando, m in r.aulas:
        pontos[dia_de(quando)] += m
    for d, _ in {(dia_de(quando), q) for quando, q in r.questoes}:
        pontos[d] += PONTOS_POR_QUESTAO
    return dict(pontos)


def sequencia(por_dia: dict[date, int], hoje: date, dias_de_estudo: set[int], limite: int = 400) -> int:
    """Dias seguidos que valeram, de hoje para trás. Hoje ainda sem os 15 não quebra; dia de folga (fora do
    Cronograma) também não, e conta se a pessoa estudou nele."""
    vale = lambda d: por_dia.get(d, 0) >= MINIMO_DIA  # noqa: E731
    n = 1 if vale(hoje) else 0
    d = hoje - timedelta(days=1)
    for _ in range(limite):
        if vale(d):
            n += 1
        elif d.weekday() in dias_de_estudo:
            break
        d -= timedelta(days=1)
    return n


def semanas(registros: dict[str, Registros], hoje: date) -> dict[date, dict[str, int]]:
    """Os pontos de cada perfil em cada semana que já acabou, da primeira com estudo até a passada."""
    datas = [dia_de(q) for r in registros.values() for q, _ in (*r.aulas, *r.questoes)]
    if not datas:
        return {}
    atual = segunda_de(hoje)
    s, saida = segunda_de(min(datas)), {}
    while s < atual:
        saida[s] = {pid: pontos_da_semana(r, s) for pid, r in registros.items()}
        s += timedelta(days=7)
    return saida


def vencedores(pontos: dict[str, int]) -> set[str]:
    """Quem fez mais pontos (empate coroa todos). Só há disputa se pelo menos dois pontuaram: quem estudou sozinho,
    antes de os amigos chegarem, não venceu ninguém."""
    if sum(p > 0 for p in pontos.values()) < 2:
        return set()
    melhor = max(pontos.values())
    return {pid for pid, p in pontos.items() if p == melhor}
