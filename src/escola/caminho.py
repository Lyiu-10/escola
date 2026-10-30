"""O caminho da Escola: em que ordem a matéria nova aparece (o Cronograma distribui pelos dias).

O concurso em foco vem primeiro; um assunto que cai em mais de um concurso aparece uma vez só, onde aparece
primeiro; o que ficou "para depois" vai para o fim, na ordem em que foi adiado. Extras não entram.
"""
from collections.abc import Iterable
from dataclasses import dataclass

from .catalogo import Assunto, Catalogo, Concurso, Item, Materia

Estados = dict[str, tuple[str, str]]


@dataclass(frozen=True)
class Passo:
    item: Item
    concurso: Concurso
    materia: Materia
    assunto: Assunto


@dataclass(frozen=True)
class Vizinhos:
    anterior: Passo | None
    proxima: Passo | None
    pendente: Passo | None  # o primeiro principal depois deste ainda não feito: o "Concluir e seguir"


def _guardar(achados: dict[str, Passo], p: Passo) -> None:
    """Cada item fica no primeiro lugar em que aparece; o que é extra num assunto e principal noutro vai para o
    primeiro lugar em que é principal, senão nunca entraria no caminho."""
    antes = achados.get(p.item.id)
    if antes is None:
        achados[p.item.id] = p
    elif antes.item.extra and not p.item.extra:
        del achados[p.item.id]  # sai da posição do extra e entra aqui
        achados[p.item.id] = p


def sequencia(cat: Catalogo, c: Concurso) -> list[Passo]:
    """Os itens de um concurso (os extras também) na ordem das matérias, cada um no primeiro lugar em que aparece."""
    achados: dict[str, Passo] = {}
    for m in c.materias:
        for aid in m.assuntos:
            a = cat.assuntos[aid]
            for item in a.itens:
                _guardar(achados, Passo(item, c, m, a))
    return list(achados.values())


def onde(cat: Catalogo) -> dict[str, Passo]:
    """Cada item (os extras também) no primeiro lugar em que aparece, na ordem do caminho."""
    achados: dict[str, Passo] = {}
    for c in cat.concursos:
        for p in sequencia(cat, c):
            _guardar(achados, p)
    return achados


def vizinhos(seq: list[Passo], item_id: str, estados: Estados) -> Vizinhos:
    """Anterior e próxima andam pelos principais, sem olhar o estado: é o "pular" que não marca nada."""
    n = next(k for k, p in enumerate(seq) if p.item.id == item_id)
    antes = [p for p in seq[:n] if not p.item.extra]
    depois = [p for p in seq[n + 1:] if not p.item.extra]
    pendente = next((p for p in depois if estados.get(p.item.id, ("",))[0] != "feito"), None)
    return Vizinhos(antes[-1] if antes else None, depois[0] if depois else None, pendente)


def passos(cat: Catalogo) -> list[Passo]:
    """Os itens principais, na ordem, sem repetir."""
    return [p for p in onde(cat).values() if not p.item.extra]


def caminho(cat: Catalogo, estados: Estados) -> list[Passo]:
    """O que falta: os novos na ordem; depois os adiados, do mais antigo para o mais novo."""
    todos = passos(cat)
    novos = [p for p in todos if p.item.id not in estados]
    adiados = sorted((p for p in todos if estados.get(p.item.id, ("",))[0] == "depois"),
                     key=lambda p: estados[p.item.id][1])
    return novos + adiados


def proximo(cat: Catalogo, estados: Estados) -> Passo | None:
    resto = caminho(cat, estados)
    return resto[0] if resto else None


def contagem(cat: Catalogo, assuntos: Iterable[str], estados: Estados) -> tuple[int, int]:
    """(feitos, total) dos itens principais desses assuntos."""
    ids = {i.id for aid in assuntos for i in cat.assuntos[aid].principais}
    return sum(1 for i in ids if estados.get(i, ("",))[0] == "feito"), len(ids)
