from datetime import datetime

import pytest

from escola_falsa import aula, montar
from escola import caminho, catalogo
from escola.progresso import MINUTOS_DIA, Progresso


@pytest.fixture
def cat(tmp_path):
    return catalogo.carregar(montar(tmp_path))


def id_(cat, titulo):
    return next(i.id for i in cat.itens.values() if i.titulo == titulo)


def titulos(cat, ids):
    return [cat.itens[i].titulo for i in ids]


def test_progresso_marca_e_desmarca(tmp_path):
    p = Progresso(tmp_path / "p.db")
    p.marcar("a", "feito", datetime(2026, 10, 24, 9, 0))
    assert p.estados() == {"a": ("feito", "2026-10-24T09:00:00")}
    p.marcar("a", "novo", datetime(2026, 10, 24, 9, 5))
    assert p.estados() == {}
    with pytest.raises(ValueError):
        p.marcar("a", "talvez", datetime(2026, 10, 24, 9, 5))
    p.fechar()


def test_progresso_guarda_tempo_e_plano(tmp_path):
    p = Progresso(tmp_path / "p.db")
    assert p.minutos_dia() == MINUTOS_DIA and p.plano("2026-10-24") is None
    p.definir_minutos_dia(90)
    p.guardar_plano("2026-10-24", ["a", "b"])
    p.fechar()
    q = Progresso(tmp_path / "p.db")
    assert q.minutos_dia() == 90 and q.plano("2026-10-24") == ["a", "b"]
    q.fechar()


def test_ordem_foco_primeiro_sem_repetir_e_sem_extras(cat):
    assert [p.item.titulo for p in caminho.passos(cat)] == ["Aula 1", "Leitura 1", "Aula 2", "Leitura 2", "Aula 3"]
    p = caminho.onde(cat)[id_(cat, "Aula 3")]
    assert (p.concurso.id, p.materia.id, p.assunto.id) == ("eb", "eb-psi", "social")
    assert caminho.onde(cat)[id_(cat, "Aula 9")].concurso.id == "mb"  # o extra também tem lugar


def test_item_extra_num_assunto_e_principal_noutro_entra_onde_e_principal(tmp_path):
    # em 25/10/2026 o temporário passou na frente, e a aula de coesão, extra no Português e principal na Redação,
    # sumiu do caminho: o CP-T nunca terminava
    cat = catalogo.carregar(montar(tmp_path, materiais={
        "etica": [aula(1), aula(3, extra=True)], "psicopatologia": [aula(2)], "social": [aula(3)]}))
    assert [p.item.titulo for p in caminho.passos(cat)] == ["Aula 1", "Aula 2", "Aula 3"]
    p = caminho.onde(cat)[id_(cat, "Aula 3")]
    assert (p.concurso.id, p.assunto.id, p.item.extra) == ("eb", "social", False)


def test_proximo_pula_feitos_e_adiados_vao_para_o_fim_na_ordem(cat):
    est = {id_(cat, "Aula 1"): ("feito", "2026-10-24T09:00:00"),
           id_(cat, "Leitura 1"): ("depois", "2026-10-24T09:10:00"),
           id_(cat, "Aula 2"): ("depois", "2026-10-24T09:05:00")}
    assert [p.item.titulo for p in caminho.caminho(cat, est)] == ["Leitura 2", "Aula 3", "Aula 2", "Leitura 1"]
    assert caminho.proximo(cat, est).item.titulo == "Leitura 2"


def test_proximo_quando_tudo_esta_feito(cat):
    assert caminho.proximo(cat, {p.item.id: ("feito", "x") for p in caminho.passos(cat)}) is None


def test_contagem_conta_o_assunto_dividido_nos_dois(cat):
    est = {id_(cat, "Aula 1"): ("feito", "x"), id_(cat, "Aula 2"): ("depois", "x")}
    assert caminho.contagem(cat, cat.concurso("eb").assuntos(), est) == (1, 3)
    assert caminho.contagem(cat, cat.concurso("mb").assuntos(), est) == (1, 4)


def test_sequencia_do_concurso_tem_os_extras_na_ordem_das_materias(cat):
    seq = caminho.sequencia(cat, cat.concurso("eb"))
    assert [p.item.titulo for p in seq] == ["Aula 1", "Leitura 1", "Aula 9", "Aula 3"]
    assert {p.materia.id for p in seq} == {"eb-psi"}


def test_vizinhos_andam_pelos_principais_sem_olhar_o_estado(cat):
    seq = caminho.sequencia(cat, cat.concurso("mb"))
    v = caminho.vizinhos(seq, id_(cat, "Leitura 1"), {id_(cat, "Aula 2"): ("feito", "x")})
    assert (v.anterior.item.titulo, v.proxima.item.titulo, v.pendente.item.titulo) == ("Aula 1", "Aula 2", "Leitura 2")
    v = caminho.vizinhos(seq, id_(cat, "Aula 9"), {})  # num extra, os vizinhos são os principais em volta
    assert (v.anterior.item.titulo, v.proxima.item.titulo) == ("Leitura 1", "Aula 2")
    assert caminho.vizinhos(seq, id_(cat, "Aula 1"), {}).anterior is None
    fim = caminho.vizinhos(seq, id_(cat, "Leitura 2"), {})
    assert fim.proxima is None and fim.pendente is None
