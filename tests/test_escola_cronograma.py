import copy
from datetime import date

import pytest

from escola_falsa import ESTRUTURA, MATERIAIS, montar
from escola import catalogo, cronograma
from escola.cronograma import DIAS_PADRAO, Simulacao, id_revisao

MAIO = {"mb": date(2027, 5, 15), "eb": date(2027, 7, 15)}


@pytest.fixture
def cat(tmp_path):
    return catalogo.carregar(montar(tmp_path, perguntas={}, provinhas={}))  # as perguntas têm teste próprio


def id_(cat, titulo):
    return next(i.id for i in cat.itens.values() if i.titulo == titulo)


def feito(dia):
    return ("feito", f"{dia}T09:00:00")


def nomes(tarefas):
    return [t.titulo for t in tarefas]


def com_provas_e_redacao(tmp_path):
    """A Marinha ganha duas provas anteriores (uma extra) e um assunto de redação."""
    estrutura = copy.deepcopy(ESTRUTURA)
    mb = next(c for c in estrutura["concursos"] if c["id"] == "mb")
    mb["materias"] += [{"id": "mb-red", "nome": "Redação", "assuntos": ["r-estrutura"]},
                       {"id": "mb-provas", "nome": "Provas anteriores", "assuntos": ["provas-mb"]}]
    estrutura["assuntos"] |= {"r-estrutura": {"nome": "Estrutura", "edital": "redação"},
                              "provas-mb": {"nome": "Provas da Marinha", "edital": ""}}
    materiais = {**MATERIAIS,
                 "r-estrutura": [{"tipo": "aula", "titulo": "Aula R", "url": "https://www.youtube.com/watch?v=redacao0001",
                                  "minutos": 20}],
                 "provas-mb": [{"tipo": "prova", "titulo": "Prova 2025", "url": "https://x.mil.br/p25.pdf"},
                               {"tipo": "leitura", "titulo": "Gabarito 2025", "url": "https://x.mil.br/g25.pdf",
                                "minutos": 10},
                               {"tipo": "prova", "titulo": "Prova 2024", "url": "https://x.mil.br/p24.pdf",
                                "extra": True}]}
    return catalogo.carregar(montar(tmp_path, materiais=materiais, estrutura=estrutura))


def test_revisoes_em_1_7_e_21_dias_e_depois_pela_distancia_da_prova(cat):
    est = {id_(cat, "Aula 1"): feito("2026-10-24"), id_(cat, "Leitura 1"): feito("2026-10-24")}
    sim = Simulacao(cat, est, DIAS_PADRAO, 60, MAIO)
    assert sim.proxima_revisao("etica") == (1, date(2026, 10, 25))
    assert sim.proxima_revisao("psicopatologia") is None  # ainda não estudado
    for k, dia in [(1, "2026-10-25"), (2, "2026-11-01"), (3, "2026-11-22")]:
        sim.est[id_revisao("etica", k)] = feito(dia)
    assert sim.proxima_revisao("etica") == (4, date(2026, 12, 13))  # 10% de 174 dias é menos que 21


def test_garante_uma_revisao_nas_tres_semanas_antes_da_prova(cat):
    est = {id_(cat, "Aula 1"): feito("2026-10-24"), id_(cat, "Leitura 1"): feito("2026-10-24"),
           id_revisao("etica", 1): feito("2026-10-25"), id_revisao("etica", 2): feito("2026-11-01"),
           id_revisao("etica", 3): feito("2026-11-22")}
    sim = Simulacao(cat, est, DIAS_PADRAO, 60, {"mb": date(2026, 12, 20), "eb": None})
    assert sim.proxima_revisao("etica") == (4, date(2026, 11, 29))


def test_o_dia_abre_com_a_revisao_e_completa_com_materia_nova(cat):
    est = {id_(cat, "Aula 1"): feito("2026-10-24"), id_(cat, "Leitura 1"): feito("2026-10-24")}
    sim = Simulacao(cat, est, DIAS_PADRAO, 60, MAIO)
    assert nomes(sim.planejar(date(2026, 10, 26))) == ["Revisão de Código de Ética", "Aula 2", "Leitura 2"]
    assert sim.planejar(date(2026, 11, 1)) == []  # domingo é folga


def test_revisao_atrasada_espera_e_o_teto_e_30_por_cento(cat):
    est = {i: feito("2026-10-01") for i in (id_(cat, "Aula 1"), id_(cat, "Leitura 1"), id_(cat, "Aula 3"))}
    sim = Simulacao(cat, est, DIAS_PADRAO, 60, MAIO)
    dia = sim.planejar(date(2026, 10, 26))
    assert [t.tipo for t in dia] == ["revisao", "aula", "leitura"]  # duas vencidas, cabe uma (18 de 60 min)
    sim.marcar(date(2026, 10, 26), dia)
    assert nomes(sim.planejar(date(2026, 10, 27)))[0] == "Revisão de Psicologia social"


def test_simulado_sozinho_no_sabado_depois_de_30_por_cento(tmp_path):
    cat = com_provas_e_redacao(tmp_path)
    sim = Simulacao(cat, {}, DIAS_PADRAO, 60, MAIO)
    assert "prova" not in [t.tipo for t in sim.planejar(date(2026, 10, 31))]  # nada estudado ainda
    for t in ("Aula 1", "Leitura 1"):
        sim.est[id_(cat, t)] = feito("2026-10-27")
    sabado = sim.planejar(date(2026, 10, 31))
    assert nomes(sabado) == ["Prova 2025"] and sabado[0].concurso == "mb"
    sim.marcar(date(2026, 10, 31), sabado)
    assert "prova" not in [t.tipo for t in sim.planejar(date(2026, 11, 7))]  # longe da prova: a cada 4 semanas
    assert nomes(sim.planejar(date(2026, 11, 28))) == ["Prova 2024"]  # o extra também serve de simulado


def test_redacao_no_meio_da_semana_e_duas_na_reta_final(tmp_path):
    cat = com_provas_e_redacao(tmp_path)
    sim = Simulacao(cat, {}, DIAS_PADRAO, 60, {"mb": date(2026, 12, 10), "eb": None})
    assert nomes(sim.planejar(date(2026, 10, 29)))[-1] == "Redação da semana"  # quinta
    assert "redacao" not in [t.tipo for t in sim.planejar(date(2026, 10, 26))]
    assert nomes(sim.planejar(date(2026, 11, 23)))[-1] == "Redação da semana"  # segunda, a 17 dias da prova
    quatro = Simulacao(cat, {}, (0, 2, 4, 6), 60, {"mb": None, "eb": None})
    assert "redacao" in [t.tipo for t in quatro.planejar(date(2026, 10, 30))]  # sexta é o meio de seg-qua-sex-dom


def test_cada_dia_da_semana_tem_o_proprio_tempo(cat):
    igual = Simulacao(cat, {}, DIAS_PADRAO, 60, MAIO)
    por_dia = Simulacao(cat, {}, DIAS_PADRAO, {0: 15, 1: 60}, MAIO)
    assert len(nomes(por_dia.planejar(date(2026, 10, 26)))) < len(nomes(igual.planejar(date(2026, 10, 26))))  # segunda curta
    assert nomes(por_dia.planejar(date(2026, 10, 27))) == nomes(igual.planejar(date(2026, 10, 27)))  # terça igual


def test_projecao_ate_acabar_a_materia_e_o_termino_de_cada_concurso(cat):
    dias = cronograma.projetar(cat, {}, DIAS_PADRAO, 60, {"mb": None, "eb": None}, date(2026, 10, 26))
    assert [nomes(d.tarefas) for d in dias] == [["Aula 1", "Leitura 1", "Aula 2"],
                                                ["Revisão de Código de Ética", "Leitura 2", "Aula 3"]]
    assert cronograma.termino(cat, dias, {}) == {"mb": date(2026, 10, 27), "eb": date(2026, 10, 27)}
    longa = cronograma.projetar(cat, {}, DIAS_PADRAO, 60, {"mb": date(2026, 11, 30)}, date(2026, 10, 26))
    assert longa[-1].data == date(2026, 11, 30) and longa[6].folga  # 01/11 é domingo


def test_o_plano_guardado_de_hoje_entra_na_projecao(cat):
    hoje = [cronograma.tarefa_de(cat, id_(cat, "Aula 3"))]
    dias = cronograma.projetar(cat, {}, DIAS_PADRAO, 60, {}, date(2026, 10, 26), plano_hoje=hoje)
    assert nomes(dias[0].tarefas) == ["Aula 3"] and nomes(dias[1].tarefas)[:2] == ["Revisão de Psicologia social", "Aula 1"]


def test_tarefa_de_le_os_ids_guardados(cat):
    assert cronograma.tarefa_de(cat, "rev:etica:2").titulo == "Revisão de Código de Ética"
    assert cronograma.tarefa_de(cat, "red:2026-10-29:mb").tipo == "redacao"
    assert cronograma.tarefa_de(cat, id_(cat, "Aula 1")).minutos == 20
    assert cronograma.tarefa_de(cat, "rev:sumiu:1") is None and cronograma.tarefa_de(cat, "nada") is None


def test_perguntas_somam_no_item_e_a_provinha_vem_quando_a_materia_acaba(tmp_path):
    cat = catalogo.carregar(montar(tmp_path))  # a Aula 1 tem 2 perguntas; a Legislação (só Ética) tem provinha de 2
    assert cronograma.tarefa_de(cat, id_(cat, "Aula 1")).minutos == 23  # 20 da aula, 2 das perguntas, 1 da correção
    prov = cronograma.tarefa_de(cat, "mod:mb-leg")
    assert (prov.titulo, prov.tipo, prov.minutos, prov.concurso) == ("Provinha de Legislação", "provinha", 4, "mb")
    assert cronograma.tarefa_de(cat, "mod:nada") is None
    est = {id_(cat, "Aula 1"): feito("2026-10-24")}
    assert "provinha" not in [t.tipo for t in Simulacao(cat, est, DIAS_PADRAO, 60, MAIO).planejar(date(2026, 10, 26))]
    est[id_(cat, "Leitura 1")] = feito("2026-10-24")
    sim = Simulacao(cat, est, DIAS_PADRAO, 60, MAIO)
    dia = sim.planejar(date(2026, 10, 26))
    assert nomes(dia) == ["Revisão de Código de Ética", "Provinha de Legislação", "Aula 2", "Leitura 2"]
    sim.marcar(date(2026, 10, 26), dia)
    assert "provinha" not in [t.tipo for t in sim.planejar(date(2026, 10, 27))]  # uma vez só
    passou = Simulacao(cat, est, DIAS_PADRAO, 60, {"mb": date(2026, 10, 20), "eb": None})
    assert "provinha" not in [t.tipo for t in passou.planejar(date(2026, 10, 26))]  # a prova já foi


def test_data_da_prova_confirmada_ou_pelo_historico(cat):
    mb = cat.concurso("mb")
    assert cronograma.data_da_prova(mb, None) is None
    prevista = catalogo.Concurso(**{**mb.__dict__, "prova_prevista": "2027-05"})
    assert cronograma.data_da_prova(prevista, None) == date(2027, 5, 15)
    sit = {"datas": [{"evento": "Prova objetiva", "data": "10/05/2027", "confirmada": False}]}
    assert cronograma.data_da_prova(prevista, sit) == date(2027, 5, 15)
    sit["datas"][0]["confirmada"] = True
    assert cronograma.data_da_prova(prevista, sit) == date(2027, 5, 10)
    assert cronograma.data_da_prova(prevista, sit, hoje=date(2027, 5, 12)) == date(2027, 5, 15)  # a 10/05 já passou
    assert cronograma.data_da_prova(prevista, sit, hoje=date(2027, 6, 1)) is None


def test_prova_marcada_no_edital_vale_o_dia(cat):
    mb = cat.concurso("mb")
    pelo_mes = catalogo.Concurso(**{**mb.__dict__, "prova_prevista": "2027-05"})
    assert not cronograma.prova_marcada(pelo_mes, None)
    no_edital = catalogo.Concurso(**{**mb.__dict__, "prova_prevista": "2027-02-21"})
    assert cronograma.data_da_prova(no_edital, None) == date(2027, 2, 21)
    assert cronograma.prova_marcada(no_edital, None, hoje=date(2026, 10, 25))
    assert cronograma.data_da_prova(no_edital, None, hoje=date(2027, 3, 1)) is None  # passou
    assert not cronograma.prova_marcada(no_edital, None, hoje=date(2027, 3, 1))
    sit = {"datas": [{"evento": "Prova", "data": "10/05/2027", "confirmada": True}]}
    assert cronograma.prova_marcada(pelo_mes, sit)


def test_aula_longa_que_nao_cabe_abre_o_dia_seguinte(cat):
    sim = Simulacao(cat, {}, DIAS_PADRAO, 30, MAIO)
    segunda = sim.planejar(date(2026, 10, 26))
    assert nomes(segunda) == ["Aula 1"]  # a Leitura 1 (30) levaria o dia de 30 min a 50, mais que 1,6 vez
    sim.marcar(date(2026, 10, 26), segunda)
    assert nomes(sim.planejar(date(2026, 10, 27)))[-1] == "Leitura 1"
