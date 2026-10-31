import json
import time
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from escola_falsa import ESTRUTURA, MATERIAIS, montar, questao
from escola import app as app_escola
from escola.app import criar_escola
from escola.catalogo import id_de
from escola.progresso import Progresso


class Relogio:
    def __init__(self):
        self.agora = datetime(2026, 10, 24, 9, 0)

    def __call__(self):
        return self.agora


@pytest.fixture
def escola(tmp_path):
    relogio = Relogio()
    dados = tmp_path / "dados"
    (dados / "arquivos" / "etica").mkdir(parents=True)
    (dados / "arquivos" / "etica" / "l1.pdf").write_bytes(b"%PDF-1.4 teste")
    app = criar_escola(montar(tmp_path / "cat"), dados, relogio=relogio)
    with TestClient(app) as cliente:
        entrar(cliente)
        cliente.relogio = relogio
        yield cliente
    app.state.progresso.fechar()


def entrar(cliente):
    """Cada aparelho estuda num perfil; o primeiro criado já fica escolhido."""
    cliente.post("/api/perfis", json={"nome": "Teste"})


def continuar(escola):
    return escola.get("/api/inicio").json()["continuar"]["id"]


def test_inicio_mostra_continuar_plano_e_concursos(escola):
    d = escola.get("/api/inicio").json()
    c = d["continuar"]
    assert (c["titulo"], c["youtube"], c["concurso"]["nome"], c["tambem"]) == \
        ("Aula 1", "aula0000001", "Marinha", ["Exército"])
    assert (c["materia"], c["assunto"], c["estado"]) == ("Legislação", "Código de Ética", "novo")
    assert [i["titulo"] for i in d["plano"]["itens"]] == ["Aula 1", "Leitura 1", "Aula 2"]
    assert d["plano"]["minutos_dia"] == 60 and d["plano"]["dia"] == "2026-10-24" and not d["montando"]
    assert [(c["id"], c["feitos"], c["total"]) for c in d["concursos"]] == [("mb", 0, 4), ("eb", 0, 3)]


def test_pdf_que_existe_vira_link_local_e_o_que_falta_nao(escola):
    l1 = escola.get(f"/api/itens/{id_de('https://site.cfp.org.br/l1.pdf')}").json()
    l2 = escola.get(f"/api/itens/{id_de('https://site.cfp.org.br/l2.pdf')}").json()
    assert l1["pdf"] == "/arquivos/etica/l1.pdf" and l2["pdf"] is None and l1["youtube"] is None
    assert escola.get("/arquivos/etica/l1.pdf").content.startswith(b"%PDF")


def test_feito_devolve_o_proximo_e_o_plano_do_dia_nao_muda(escola):
    r = escola.post(f"/api/itens/{continuar(escola)}/estado", json={"estado": "feito"}).json()
    assert r["item"]["estado"] == "feito" and r["proximo"]["titulo"] == "Leitura 1"
    assert r["plano"]["tinha"] and not r["plano"]["feito"] and r["plano"]["seguinte"]["titulo"] == "Leitura 1"
    d = escola.get("/api/inicio").json()
    assert [(i["titulo"], i["estado"]) for i in d["plano"]["itens"]] == \
        [("Aula 1", "feito"), ("Leitura 1", "novo"), ("Aula 2", "novo")]
    assert [c["feitos"] for c in d["concursos"]] == [1, 1]  # o assunto dividido conta nos dois


def test_depois_vai_para_o_fim_e_desmarcar_volta(escola):
    a1 = continuar(escola)
    assert escola.post(f"/api/itens/{a1}/estado", json={"estado": "depois"}).json()["proximo"]["titulo"] == "Leitura 1"
    escola.post(f"/api/itens/{a1}/estado", json={"estado": "novo"})
    assert continuar(escola) == a1


def test_dia_novo_plano_novo_e_domingo_e_folga(escola):
    escola.post(f"/api/itens/{continuar(escola)}/estado", json={"estado": "feito"})
    escola.relogio.agora = datetime(2026, 10, 25, 8, 0)
    d = escola.get("/api/inicio").json()
    assert d["plano"]["folga"] and d["plano"]["itens"] == []
    assert d["adiantando"] and d["continuar"]["titulo"] == "Leitura 1"  # na folga, o Continuar é adiantar
    escola.relogio.agora = datetime(2026, 10, 26, 8, 0)
    d = escola.get("/api/inicio").json()
    assert d["plano"]["dia"] == "2026-10-26" and not d["plano"]["folga"]
    assert [i["titulo"] for i in d["plano"]["itens"]] == ["Leitura 1", "Aula 2"]
    assert d["continuar"]["titulo"] == "Leitura 1" and (d["continuar"]["posicao"], d["continuar"]["total_materia"]) == (2, 2)


def test_mudar_o_tempo_refaz_o_plano_e_guarda_os_feitos_de_hoje(escola):
    escola.post(f"/api/itens/{continuar(escola)}/estado", json={"estado": "feito"})
    d = escola.put("/api/ajustes", json={"minutos_dia": 30}).json()
    assert d["plano"]["minutos_dia"] == 30
    assert [i["titulo"] for i in d["plano"]["itens"]] == ["Aula 1", "Leitura 1"]
    assert escola.put("/api/ajustes", json={"minutos_dia": 5}).status_code == 422


def test_concurso_traz_ficha_materias_e_assuntos(escola):
    c = escola.get("/api/concursos/eb").json()
    assert (c["prova"], c["requisitos"], c["proximo"]) == ("50 questões", ["até 32 anos"], "março")
    assert c["edital"] == {"titulo": "Edital EB", "url": "https://eb.mil.br/edital.pdf",
                           "arquivo": "editais/eb.pdf", "pdf": None}
    m = c["materias"][0]
    assert (m["nome"], m["feitos"], m["total"]) == ("Psicologia", 0, 3)
    assert [a["id"] for a in m["assuntos"]] == ["etica", "social"]
    assert [i["titulo"] for i in m["assuntos"][0]["itens"]] == ["Aula 1", "Leitura 1", "Aula 9"]
    assert m["assuntos"][0]["edital"] == "código de ética"
    assert [(li["curta"], li["item"]) for li in m["livros"]] == \
        [("Autor, Psicologia social", None), ("CFP, Código de Ética", id_de("https://site.cfp.org.br/l1.pdf"))]
    assert all(m["livros"] == [] for m in escola.get("/api/concursos/mb").json()["materias"])
    assert escola.get("/api/concursos/nada").status_code == 404
    assert c["credito"] is None and c["foto"] is None  # o catálogo falso não tem fotos


def test_item_que_nao_existe_e_404(escola):
    assert escola.get("/api/itens/nada").status_code == 404
    assert escola.post("/api/itens/nada/estado", json={"estado": "feito"}).status_code == 404


def test_saude(escola):
    assert escola.get("/api/saude").json() == {"ok": True}


def test_catalogo_vazio_sobe_e_avisa(tmp_path):
    app = criar_escola(montar(tmp_path / "cat", materiais={}), tmp_path / "dados")
    with TestClient(app) as cliente:
        entrar(cliente)
        d = cliente.get("/api/inicio").json()
    app.state.progresso.fechar()
    assert d["montando"] and d["continuar"] is None and d["plano"]["itens"] == []


def test_simulado_abre_so_com_o_proprio_gabarito(tmp_path):
    estrutura = json.loads(json.dumps(ESTRUTURA))
    estrutura["assuntos"]["provas-mb"] = {"nome": "Simulados", "edital": ""}
    estrutura["concursos"][1]["materias"].append({"id": "mb-provas", "nome": "Provas", "assuntos": ["provas-mb"]})
    simulados = [{"tipo": t, "titulo": f"{nome} {ano}", "fonte": "SSPM", "minutos": 10, "url": f"https://mb/{ano}-{t}.pdf"}
                 for ano in (2012, 2015) for t, nome in (("prova", "CP-T"), ("leitura", "Gabarito"))]
    app = criar_escola(montar(tmp_path / "cat", materiais={**MATERIAIS, "provas-mb": simulados}, estrutura=estrutura),
                       tmp_path / "dados")
    with TestClient(app) as cliente:
        entrar(cliente)
        d = cliente.get(f"/api/itens/{id_de('https://mb/2015-prova.pdf')}").json()
    app.state.progresso.fechar()
    assert [g["titulo"] for g in d["gabaritos"]] == ["Gabarito 2015"]


def test_tela_e_arquivos_da_web(escola):
    assert "Escola" in escola.get("/").text
    assert escola.get("/web/escola.js").status_code == 200 and escola.get("/web/escola.css").status_code == 200


def test_item_aberto_tem_a_lista_da_materia_e_anda_sem_marcar(escola):
    l1 = id_de("https://site.cfp.org.br/l1.pdf")
    d = escola.get(f"/api/itens/{l1}?concurso=eb").json()
    assert d["concurso"]["id"] == "eb" and d["materia"] == "Psicologia" and d["rota"] == f"#/item/{l1}/eb"
    assert [a["nome"] for a in d["lista"]["assuntos"]] == ["Código de Ética", "Psicologia social"]
    assert (d["posicao"], d["lista"]["total"]) == (2, 3)
    assert (d["anterior"]["titulo"], d["proxima"]["titulo"]) == ("Aula 1", "Aula 3")  # na Marinha seria a Aula 2
    assert escola.get(f"/api/itens/{l1}").json()["proxima"]["titulo"] == "Aula 2"
    assert escola.get("/api/inicio").json()["plano"]["itens"][1]["estado"] == "novo"  # andar não marca nada


def test_feito_no_contexto_do_concurso_segue_dentro_dele(escola):
    a1 = id_de("https://www.youtube.com/watch?v=aula0000001")
    escola.post(f"/api/itens/{id_de('https://site.cfp.org.br/l1.pdf')}/estado", json={"estado": "feito"})
    r = escola.post(f"/api/itens/{a1}/estado?concurso=eb", json={"estado": "feito"}).json()
    assert r["proximo"]["titulo"] == "Aula 3" and r["proximo"]["concurso"]["id"] == "eb"


def test_revisao_aparece_no_dia_seguinte_e_se_marca_pelo_plano(escola):
    for url in ("https://www.youtube.com/watch?v=aula0000001", "https://site.cfp.org.br/l1.pdf"):
        escola.post(f"/api/itens/{id_de(url)}/estado", json={"estado": "feito"})
    escola.relogio.agora = datetime(2026, 10, 26, 8, 0)
    plano = escola.get("/api/inicio").json()["plano"]["itens"]
    assert plano[0]["tipo"] == "revisao" and plano[0]["rota"] == "#/revisao/etica/1"
    r = escola.get("/api/revisoes/etica/1").json()
    assert r["assunto"]["nome"] == "Código de Ética" and len(r["itens"]) == 3 and r["nota"] == ""
    assert escola.put("/api/notas/etica", json={"texto": " O que é sigilo? "}).json() == {"ok": True}
    assert escola.get("/api/revisoes/etica/1").json()["nota"] == "O que é sigilo?"
    d = escola.post("/api/plano/rev:etica:1/estado", json={"estado": "feito"}).json()
    assert d["plano"]["itens"][0]["estado"] == "feito" and d["continuar"]["tipo"] == "provinha"  # a Ética acabou
    assert escola.post("/api/plano/rev:nada:1/estado", json={"estado": "feito"}).status_code == 404
    assert escola.get("/api/revisoes/nada/1").status_code == 404


def test_ajustes_de_dias_e_horario(escola):
    d = escola.put("/api/ajustes", json={"dias": [0, 2, 4], "horario": "19:00"}).json()
    assert d["hoje"]["dias"] == [0, 2, 4] and d["hoje"]["horario"] == "19:00" and "local" not in d["hoje"]
    assert d["plano"]["folga"] and d["plano"]["itens"] == []  # sábado saiu dos dias de estudo


def test_semana_dia_a_dia_com_hora_e_tempo_proprios(escola):
    escola.relogio.agora = datetime(2026, 10, 26, 8, 0)  # segunda
    semana = [{"dia": 0, "inicio": "21:00", "minutos": 90}, {"dia": 6, "inicio": "14:00", "minutos": 120}]
    d = escola.put("/api/ajustes", json={"semana": semana}).json()
    assert d["hoje"]["dias"] == [0, 6] and d["hoje"]["semana"] == semana
    assert d["hoje"]["horario"] == "21:00" and d["plano"]["minutos_dia"] == 90
    assert escola.get("/api/cronograma").json()["ajustes"]["semana"] == semana
    d = escola.put("/api/ajustes", json={"dias": [0, 2, 6]}).json()  # o dia que entra ganha o tempo padrão
    assert [(s["dia"], s["minutos"]) for s in d["hoje"]["semana"]] == [(0, 90), (2, 60), (6, 120)]
    repetido = [{"dia": 0, "minutos": 30}, {"dia": 0, "minutos": 45}]
    assert escola.put("/api/ajustes", json={"semana": repetido}).status_code == 422
    assert escola.put("/api/ajustes", json={"semana": [{"dia": 0, "inicio": "25:00", "minutos": 30}]}).status_code == 422


def test_folga_ignora_o_plano_guardado_mas_mostra_o_que_ja_foi_feito(escola):
    a1 = continuar(escola)
    escola.post(f"/api/itens/{a1}/estado", json={"estado": "feito"})
    d = escola.put("/api/ajustes", json={"dias": [0]}).json()
    assert [(i["titulo"], i["estado"]) for i in d["plano"]["itens"]] == [("Aula 1", "feito")]
    assert d["adiantando"] and d["continuar"]["titulo"] == "Leitura 1"
    assert escola.put("/api/ajustes", json={"dias": [7]}).status_code == 422
    assert escola.put("/api/ajustes", json={"dias": []}).status_code == 422


def test_cronograma_projeta_as_semanas_e_o_termino(escola):
    c = escola.get("/api/cronograma").json()
    assert c["hoje"] == "2026-10-24" and c["ajustes"]["dias"] == [0, 1, 2, 3, 4, 5]
    primeiro = c["semanas"][0]["dias"][0]
    assert primeiro["data"] == "2026-10-24" and [t["titulo"] for t in primeiro["tarefas"]] == ["Aula 1", "Leitura 1", "Aula 2"]
    assert c["semanas"][0]["dias"][1]["folga"]  # domingo
    termino = {p["id"]: p["termino"] for p in c["previsao"]}
    assert termino == {"mb": "2026-10-26", "eb": "2026-10-26"}


def test_cronograma_guarda_o_que_ele_fez_nos_dias_que_passaram(escola):
    a1, l1 = id_de("https://www.youtube.com/watch?v=aula0000001"), id_de("https://site.cfp.org.br/l1.pdf")
    escola.get("/api/inicio")  # monta o plano do sábado: Aula 1, Leitura 1, Aula 2
    escola.post(f"/api/itens/{a1}/estado", json={"estado": "feito"})
    escola.post(f"/api/perguntas/{a1}", json={"marcadas": [1, 0]})
    escola.post("/api/perguntas/mod:mb-leg", json={"marcadas": [1, 0]})  # a provinha, fora do plano
    escola.relogio.agora = datetime(2026, 10, 25, 2, 30)  # de madrugada ainda é sábado
    escola.post(f"/api/itens/{l1}/estado", json={"estado": "feito"})
    escola.relogio.agora = datetime(2026, 10, 26, 10, 0)
    c = escola.get("/api/cronograma").json()
    assert c["atual"] == 1 and c["semanas"][1]["inicio"] == "2026-10-26" and c["semanas"][1]["dias"][0]["data"] == "2026-10-26"
    sabado = c["semanas"][0]["dias"][0]
    assert sabado["data"] == "2026-10-24" and sabado["passado"] and len(c["semanas"][0]["dias"]) == 1  # o domingo não tem registro
    assert [(t["titulo"], t["estado"], t.get("acertos")) for t in sabado["tarefas"]] == \
        [("Aula 1", "feito", 1), ("Leitura 1", "feito", None), ("Aula 2", "ficou", None), ("Provinha de Legislação", "feito", 1)]
    assert sabado["minutos"] == sum(t["minutos"] for t in sabado["tarefas"] if t["estado"] == "feito")
    escola.post(f"/api/perguntas/{a1}", json={"marcadas": [1, 3]})  # a aula de sábado, refeita na segunda
    escola.relogio.agora = datetime(2026, 10, 27, 10, 0)
    c = escola.get("/api/cronograma").json()
    segunda = c["semanas"][c["atual"]]["dias"][0]
    assert segunda["data"] == "2026-10-26" and segunda["atividades"] == \
        [{"rotulo": "Perguntas: Aula 1", "rota": f"#/item/{a1}/mb", "acertos": 2, "total": 2}]


def test_concursos_do_cronograma_guiam_plano_continuar_e_previsao(escola):
    a1, l1 = id_de("https://www.youtube.com/watch?v=aula0000001"), id_de("https://site.cfp.org.br/l1.pdf")
    assert escola.get("/api/inicio").json()["hoje"]["concursos"] == ["mb", "eb"]  # começa com todos
    d = escola.put("/api/ajustes", json={"concursos": ["eb"]}).json()
    assert d["hoje"]["concursos"] == ["eb"]
    assert [i["titulo"] for i in d["plano"]["itens"]] == ["Aula 1", "Leitura 1", "Aula 3"]  # sem a Psicopatologia
    assert d["plano"]["itens"][0]["rota"] == f"#/item/{a1}/eb" and d["continuar"]["concurso"]["id"] == "eb"
    assert [(c["id"], c["no_cronograma"]) for c in d["concursos"]] == [("mb", False), ("eb", True)]
    assert [(c["id"], c["no_cronograma"]) for c in escola.get("/api/barra").json()["concursos"]] == [("mb", False), ("eb", True)]
    escola.post(f"/api/itens/{a1}/estado", json={"estado": "feito"})
    assert escola.post(f"/api/itens/{l1}/estado", json={"estado": "feito"}).json()["proximo"]["titulo"] == "Aula 3"
    c = escola.get("/api/cronograma").json()
    assert [p["id"] for p in c["previsao"]] == ["eb"] and c["ajustes"]["concursos"] == ["eb"]
    assert [o["id"] for o in c["opcoes"]] == ["mb", "eb"]
    escola.relogio.agora = datetime(2026, 10, 26, 8, 0)
    revisao = escola.get("/api/inicio").json()["plano"]["itens"][0]
    assert revisao["tipo"] == "revisao" and revisao["concurso"]["id"] == "eb"
    assert escola.put("/api/ajustes", json={"concursos": ["nada"]}).status_code == 422
    assert escola.put("/api/ajustes", json={"concursos": []}).status_code == 422


def test_perguntas_de_fixacao_corrigem_e_guardam_cada_tentativa(escola):
    a1 = id_de("https://www.youtube.com/watch?v=aula0000001")
    f = escola.get(f"/api/itens/{a1}").json()["fixacao"]
    assert len(f["questoes"]) == 2 and "certa" not in f["questoes"][0] and f["correcao"] is None and f["tentativas"] == []
    r = escola.post(f"/api/perguntas/{a1}", json={"marcadas": [1, 0]}).json()
    assert [(c["acertou"], c["certa"], c["trecho"], c["onde"]) for c in r["correcao"]] == \
        [(True, 1, "o sigilo", 90), (False, 3, "a ética", None)]
    r = escola.post(f"/api/perguntas/{a1}", json={"marcadas": [1, 3]}).json()
    assert [(t["acertos"], t["total"]) for t in r["tentativas"]] == [(1, 2), (2, 2)]  # a melhoria sai daqui
    assert escola.get(f"/api/itens/{a1}").json()["fixacao"]["correcao"][1]["acertou"]  # a última fica à mostra
    assert escola.post(f"/api/perguntas/{a1}", json={"marcadas": [1]}).status_code == 422
    assert escola.post(f"/api/perguntas/{a1}", json={"marcadas": [1, 4]}).status_code == 422
    assert escola.post("/api/perguntas/nada", json={"marcadas": [0]}).status_code == 404
    assert escola.get(f"/api/itens/{id_de('https://site.cfp.org.br/l1.pdf')}").json()["fixacao"] is None


def test_provinha_da_materia_marca_feita_ao_responder(escola):
    p = escola.get("/api/provinhas/mb-leg").json()
    assert (p["titulo"], p["estado"], p["minutos"], len(p["perguntas"]["questoes"])) == ("Provinha de Legislação", "novo", 4, 2)
    assert p["perguntas"]["questoes"][0]["prova"] == "CP-T 2019"  # vai na frente do enunciado, antes de responder
    r = escola.post("/api/perguntas/mod:mb-leg", json={"marcadas": [1, 0]}).json()
    assert [c["acertou"] for c in r["correcao"]] == [True, False] and r["correcao"][0]["fonte"] == "CP-T 2019, questão 1"
    assert escola.get("/api/provinhas/mb-leg").json()["estado"] == "feito"
    escola.post(f"/api/perguntas/{id_de('https://www.youtube.com/watch?v=aula0000001')}", json={"marcadas": [1, 3]})
    leg = escola.get("/api/concursos/mb").json()["materias"][0]
    assert leg["provinha"]["estado"] == "feito" and leg["provinha"]["ultima"] == [1, 2]
    assert leg["fixacao"] == {"acertos": 2, "total": 2} and leg["assuntos"][0]["itens"][0]["fixacao"] == [2, 2]
    assert escola.get("/api/provinhas/nada").status_code == 404


def test_situacao_e_novidades(escola, tmp_path):
    from escola import situacao
    dados = tmp_path / "dados"
    s = situacao.ler(dados)
    s["verificado_em"] = "2026-10-20T10:00:00"
    s["concursos"] = {"mb": {"estado": "inscricoes", "resumo": "Até 12/02.", "edital": None, "fontes": [],
                             "datas": [{"evento": "Prova objetiva", "data": "10/05/2027", "confirmada": True}],
                             "novidade": None, "desde": "2026-10-20"}}
    s["historico"] = [{"em": "2026-10-20", "concurso": "mb", "texto": "Inscrições abertas."}]
    situacao.gravar(dados, s)
    d = escola.get("/api/inicio").json()
    assert d["novidades"] == [{"em": "2026-10-20", "concurso": "mb", "texto": "Inscrições abertas.", "nome": "Marinha CP-T"}]
    assert d["concursos"][0]["situacao"]["rotulo"] == "Inscrições abertas"
    assert escola.get("/api/barra").json()["novidades"] == 1
    sit = escola.get("/api/situacao").json()
    assert sit["proxima_busca"] == "2026-10-27" and sit["concursos"][0]["situacao"]["estado"] == "inscricoes"
    assert escola.get("/api/concursos/mb").json()["prova_data"] == "2027-05-10"


def test_aquecimento_comeca_pelo_que_errou_e_nao_muda_no_dia(escola, monkeypatch):
    monkeypatch.setattr(app_escola, "AQUECIMENTO", 1)
    aula = id_de("https://www.youtube.com/watch?v=aula0000001")
    a = escola.get("/api/aquecimento").json()
    assert a["perguntas"] is None and a["leitura"] is None  # nada estudado ainda
    escola.post(f"/api/perguntas/{aula}", json={"marcadas": [1, 0]})  # acerta a 1ª, erra a 2ª
    escola.post("/api/perguntas/mod:mb-leg", json={"marcadas": [1, 2]})  # acerta as duas

    escola.relogio.agora = datetime(2026, 10, 25, 11, 0)
    a = escola.get("/api/aquecimento").json()
    [q] = a["perguntas"]["questoes"]
    assert q["enunciado"] == "Pergunta 2?" and q["origem"]["titulo"] == "Aula 1" and q["origem"]["video"]
    assert escola.get("/api/inicio").json()["aquecimento"] == \
        {"perguntas": 1, "cartoes": 0, "leitura": None, "minutos": 2, "acertos": None}
    r = escola.post(f"/api/perguntas/{a['perguntas']['alvo']}", json={"marcadas": [3]}).json()
    assert r["correcao"][0]["acertou"] and r["questoes"][0]["origem"]["rota"].startswith(f"#/item/{aula}/")
    assert escola.get("/api/inicio").json()["aquecimento"]["acertos"] == 1

    escola.relogio.agora = datetime(2026, 10, 25, 22, 0)  # o mesmo dia: as mesmas perguntas
    assert escola.get("/api/aquecimento").json()["perguntas"]["questoes"] == [q]
    escola.relogio.agora = datetime(2026, 10, 26, 2, 0)  # de madrugada ainda é o dia anterior
    assert escola.get("/api/aquecimento").json()["dia"] == "2026-10-25"
    escola.relogio.agora = datetime(2026, 10, 26, 11, 0)  # a que caiu ontem não volta logo: sai outra, sorteada
    [q2] = escola.get("/api/aquecimento").json()["perguntas"]["questoes"]
    assert (q2["origem"]["titulo"], q2["enunciado"]) != ("Aula 1", "Pergunta 2?")


def test_aquecimento_traz_o_resumo_da_ultima_aula_e_so_revisa_o_que_ja_fez(escola):
    aula = id_de("https://www.youtube.com/watch?v=aula0000001")
    escola.relogio.agora = datetime(2026, 10, 24, 21, 0)
    escola.post(f"/api/itens/{aula}/estado", json={"estado": "feito"})  # estudou e não respondeu nada

    escola.relogio.agora = datetime(2026, 10, 25, 11, 0)
    a = escola.get("/api/aquecimento").json()
    assert (a["leitura"]["item"]["titulo"], a["leitura"]["item"]["tipo"], a["leitura"]["resumo"]) == \
        ("Aula 1", "aula", "O sigilo protege o paciente.")
    assert a["leitura"]["cartoes"] == [{"frente": "Frente 1?", "verso": "Verso 1.", "onde": 90},
                                       {"frente": "Frente 2?", "verso": "Verso 2.", "onde": None}]
    assert a["perguntas"] is None  # não respondeu nada, e a pergunta a mais feita por IA não entra
    assert escola.get("/api/inicio").json()["aquecimento"] == \
        {"perguntas": 0, "cartoes": 2, "leitura": "Aula 1", "minutos": 3, "acertos": None}

    escola.relogio.agora = datetime(2026, 10, 25, 21, 0)
    escola.post(f"/api/itens/{id_de('https://site.cfp.org.br/l1.pdf')}/estado", json={"estado": "feito"})
    escola.relogio.agora = datetime(2026, 10, 26, 11, 0)  # a Leitura 1 não tem resumo: fica o da última que tem
    assert escola.get("/api/aquecimento").json()["leitura"]["item"]["titulo"] == "Aula 1"


def test_aquecimento_e_montado_com_o_que_ha_ate_a_primeira_vez_do_dia(escola):
    escola.post("/api/perguntas/mod:mb-leg", json={"marcadas": [1, 2]})
    escola.relogio.agora = datetime(2026, 10, 25, 11, 0)
    assert escola.get("/api/aquecimento").json()["leitura"] is None  # montado hoje, só com a provinha
    escola.relogio.agora = datetime(2026, 10, 26, 1, 0)  # estudou de madrugada: ainda é o dia 25
    escola.post(f"/api/itens/{id_de('https://www.youtube.com/watch?v=aula0000001')}/estado", json={"estado": "feito"})
    assert escola.get("/api/aquecimento").json()["leitura"] is None
    escola.relogio.agora = datetime(2026, 10, 26, 10, 45)
    assert escola.get("/api/aquecimento").json()["leitura"]["item"]["titulo"] == "Aula 1"


def test_progresso_de_26_10_ganha_a_aula_do_resumo(tmp_path):
    import sqlite3
    conn = sqlite3.connect(tmp_path / "p.db")
    conn.executescript("""CREATE TABLE aquecimentos (dia TEXT PRIMARY KEY, questoes TEXT NOT NULL);
                          INSERT INTO aquecimentos VALUES ('2026-10-26', '[["x", 0]]');""")
    conn.close()
    p = Progresso(tmp_path / "p.db")
    assert p.aquecimento("2026-10-26") == ([("x", 0)], None)
    p.guardar_aquecimento("2026-10-27", [], "abc")
    assert p.aquecimento("2026-10-27") == ([], "abc")
    p.fechar()


def test_aquecimento_mistura_as_aulas(escola, monkeypatch):
    monkeypatch.setattr(app_escola, "AQUECIMENTO_POR_ITEM", 1)
    aula = id_de("https://www.youtube.com/watch?v=aula0000001")
    escola.post(f"/api/perguntas/{aula}", json={"marcadas": [0, 0]})
    escola.post("/api/perguntas/mod:mb-leg", json={"marcadas": [0, 0]})
    escola.relogio.agora = datetime(2026, 10, 25, 11, 0)
    qs = escola.get("/api/aquecimento").json()["perguntas"]["questoes"]
    assert sorted(q["origem"]["titulo"] for q in qs) == ["Aula 1", "Provinha de Legislação"]
    assert next(q for q in qs if q["origem"]["rota"] == "#/provinha/mb-leg")["prova"] == "CP-T 2019"
    assert escola.post("/api/perguntas/aq:2026-10-30", json={"marcadas": [0]}).status_code == 404  # dia sem aquecimento


def test_rotina_vem_do_arquivo_do_catalogo_e_vale_sem_reiniciar(escola, tmp_path):
    assert escola.get("/api/rotina").status_code == 404
    assert escola.get("/api/cronograma").json()["rotina"] is None
    (tmp_path / "cat" / "rotina.json").write_text(json.dumps({"grades": [], "regras": []}), encoding="utf-8")
    assert escola.get("/api/rotina").json() == {"grades": [], "regras": [], "estudo": [], "avisos": []}


def test_rotina_segue_o_cronograma_e_o_inicio_usa_a_hora_dela(escola, tmp_path):
    escola.relogio.agora = datetime(2026, 10, 26, 8, 0)  # segunda
    util = {"nome": "Segunda a sexta", "dias": [0, 1, 2, 3, 4], "blocos": [
        {"inicio": "10:00", "fim": "21:00", "tipo": "trabalho", "titulo": "Trabalho"},
        {"inicio": "21:00", "fim": "22:00", "tipo": "estudo", "titulo": "Estudo"},
        {"inicio": "22:00", "fim": "1:00", "tipo": "livre", "titulo": "Livre"},
        {"inicio": "1:00", "fim": "10:00", "tipo": "sono", "titulo": "Dormir"}]}
    (tmp_path / "cat" / "rotina.json").write_text(json.dumps({"grades": [util], "regras": []}), encoding="utf-8")
    escola.put("/api/ajustes", json={"semana": [{"dia": 0, "minutos": 120}, {"dia": 1, "inicio": "12:00", "minutos": 60}]})
    r = escola.get("/api/rotina").json()
    assert r["estudo"] == [{"dia": 0, "inicio": "21:00", "fim": "23:00", "minutos": 120, "marcada": False}]
    assert [a["dia"] for a in r["avisos"]] == [1]  # terça ao meio-dia bate no trabalho
    assert escola.get("/api/cronograma").json()["rotina"]["avisos"] == r["avisos"]
    assert escola.get("/api/inicio").json()["hoje"]["hora_estudo"] == "21:00"  # sem hora no Cronograma, vale a da Rotina


def prova_real(questoes):
    return {"prova": "CP-T 2024", "cor": "AMARELA", "url": "https://marinha/prova.zip", "gabarito": "https://marinha/gab.pdf",
            "questoes": questoes}


def real(n, **mais):
    return {"numero": n, "texto": "", "enunciado": f"Questão real {n}?", "alternativas": ["a", "b", "c", "d", "e"],
            "certa": 4, "anulada": False, "comentario": f"Porque a banca disse ({n}).", **mais}


def test_questoes_de_prova_tomam_o_lugar_das_perguntas_da_aula(tmp_path):
    a1 = "https://www.youtube.com/watch?v=aula0000001"
    questoes = {"cpt-2024": prova_real([
        real(1, assunto="etica", item=a1), real(2, assunto="etica", item=a1),
        real(3, assunto="etica"),  # sem aula: sobra para o aquecimento
        real(4, assunto="etica", item=a1, anulada=True, certa=-1),  # anulada não entra
        real(5),  # ainda sem assunto: não entra
    ]), "cpt-2019": {**prova_real([real(1, assunto="etica", item=a1)]), "prova": "CP-T 2019"}}  # já é da provinha
    relogio = Relogio()
    app = criar_escola(montar(tmp_path / "cat", questoes=questoes), tmp_path / "dados", relogio=relogio)
    with TestClient(app) as escola:
        entrar(escola)
        aula = id_de(a1)
        escola.post(f"/api/perguntas/{aula}", json={"marcadas": [1, 3]})  # respondeu as feitas da aula antes
        i = escola.get(f"/api/itens/{aula}").json()
        f = i["fixacao"]
        assert f["alvo"] == f"real:{aula}" and [q["prova"] for q in f["questoes"]] == ["CP-T 2024", "CP-T 2024"]
        assert f["correcao"] is None and f["tentativas"] == []  # a tentativa antiga não vale para as questões novas
        assert i["perguntas"] == 2 and i["duracao"] == 20 + 2 * 2 + 1  # 2 min por questão de prova, como a provinha
        r = escola.post(f"/api/perguntas/real:{aula}", json={"marcadas": [4, 0]}).json()
        assert [c["acertou"] for c in r["correcao"]] == [True, False]
        assert r["correcao"][0]["fonte"] == "CP-T 2024, Psicologia (Prova Amarela), questão 1"
        assert escola.get("/api/concursos/mb").json()["materias"][0]["fixacao"] == {"acertos": 1, "total": 2}

        relogio.agora = datetime(2026, 10, 24, 21, 0)
        escola.post(f"/api/itens/{aula}/estado", json={"estado": "feito"})
        relogio.agora = datetime(2026, 10, 25, 11, 0)
        qs = escola.get("/api/aquecimento").json()["perguntas"]["questoes"]
        assert sorted(q["enunciado"] for q in qs) == ["Questão real 1?", "Questão real 2?", "Questão real 3?"]
        assert next(q for q in qs if q["enunciado"] == "Questão real 3?")["origem"]["titulo"] == "Código de Ética"
    app.state.progresso.fechar()


def test_aula_sem_questao_de_prova_usa_as_escritas_no_estilo_da_banca(tmp_path):
    a2 = "https://www.youtube.com/watch?v=aula0000002"
    estilo = {a2: [{**questao(n, trecho="o exame", estilo="CP-T"), "alternativas": ["a", "b", "c", "d", "e"]}
                   for n in (1, 2, 3)]}
    app = criar_escola(montar(tmp_path / "cat", estilo=estilo), tmp_path / "dados", relogio=Relogio())
    with TestClient(app) as escola:
        entrar(escola)
        i = escola.get(f"/api/itens/{id_de(a2)}").json()
        assert i["fixacao"]["alvo"] == f"estilo:{id_de(a2)}" and i["fixacao"]["questoes"][0]["estilo"] == "CP-T"
        assert i["fixacao"]["questoes"][0]["prova"] == "" and i["duracao"] == 40 + 3 * 2 + 1
        r = escola.post(f"/api/perguntas/estilo:{id_de(a2)}", json={"marcadas": [1, 1, 0]}).json()
        assert [c["acertou"] for c in r["correcao"]] == [True, True, False]
    app.state.progresso.fechar()


def test_rascunho_dos_quadradinhos_guarda_valida_e_apaga(escola):
    assert escola.get("/api/quadros").json() == {"rascunho": None}
    semana = [["sono"] * 18 + ["estudo"] * 30] * 7
    assert escola.put("/api/quadros", json={"inicio": "10:30", "dias": semana}).status_code == 200
    r = escola.get("/api/quadros").json()["rascunho"]
    assert r["inicio"] == "10:30" and r["dias"] == semana and r["em"]
    assert escola.put("/api/quadros", json={"inicio": "10:30", "dias": semana[:6]}).status_code == 422
    assert escola.put("/api/quadros", json={"inicio": "10:30", "dias": [["jogo"] * 48] * 7}).status_code == 422
    assert escola.put("/api/quadros", json={"inicio": "10:15", "dias": semana}).status_code == 422  # meia hora cheia
    assert escola.delete("/api/quadros").status_code == 200
    assert escola.get("/api/quadros").json() == {"rascunho": None}


def test_caderno_de_erros_guarda_a_errada_e_ela_sai_com_acerto_em_dois_dias(escola):
    a1 = id_de("https://www.youtube.com/watch?v=aula0000001")
    escola.post(f"/api/perguntas/{a1}", json={"marcadas": [1, 0]})  # sábado: acerta a 1ª, erra a 2ª
    escola.post(f"/api/perguntas/{a1}", json={"marcadas": [1, 3]})  # refaz na hora e acerta: o mesmo dia não conta
    c = escola.get("/api/erros").json()
    assert [(q["alvo"], q["n"], q["acertos"], q["para_hoje"]) for q in c["questoes"]] == [(a1, 1, 0, False)]
    assert c["materias"] == [{"materia": "Legislação", "respondidas": 2, "de_primeira": 1, "no_caderno": 1}]
    assert "certa" in c["questoes"][0] and c["rodada"] is None
    assert escola.post("/api/erros/rodada").status_code == 409  # o erro de hoje volta amanhã
    assert escola.get("/api/barra").json()["caderno"] == 0

    escola.relogio.agora = datetime(2026, 10, 25, 9, 0)
    assert escola.get("/api/inicio").json()["caderno"] == {"total": 1, "para_hoje": 1}
    r = escola.post("/api/erros/rodada").json()
    assert r["alvo"] == "erros:2026-10-25:1" and r["questoes"][0]["enunciado"] == "Pergunta 2?"
    assert r["questoes"][0]["origem"]["titulo"] == "Aula 1"
    assert escola.post("/api/erros/rodada").json()["alvo"] == r["alvo"]  # aberta: volta a mesma
    r = escola.post(f"/api/perguntas/{r['alvo']}", json={"marcadas": [3]}).json()
    assert r["correcao"][0]["acertou"]
    c = escola.get("/api/erros").json()
    assert [(q["acertos"], q["para_hoje"]) for q in c["questoes"]] == [(1, False)]
    assert c["rodada"]["correcao"] and c["rodadas_hoje"] == 1

    escola.relogio.agora = datetime(2026, 10, 26, 9, 0)
    r = escola.post("/api/erros/rodada").json()
    assert r["alvo"] == "erros:2026-10-26:1"
    escola.post(f"/api/perguntas/{r['alvo']}", json={"marcadas": [3]})
    c = escola.get("/api/erros").json()
    assert c["questoes"] == [] and c["firmadas"] == 1


def test_errar_de_novo_no_caderno_recomeca_a_conta(escola):
    a1 = id_de("https://www.youtube.com/watch?v=aula0000001")
    escola.post(f"/api/perguntas/{a1}", json={"marcadas": [1, 0]})
    escola.relogio.agora = datetime(2026, 10, 25, 9, 0)
    escola.post(f"/api/perguntas/{escola.post('/api/erros/rodada').json()['alvo']}", json={"marcadas": [3]})
    escola.relogio.agora = datetime(2026, 10, 26, 9, 0)
    escola.post(f"/api/perguntas/{escola.post('/api/erros/rodada').json()['alvo']}", json={"marcadas": [2]})
    [q] = escola.get("/api/erros").json()["questoes"]
    assert (q["acertos"], q["marcou"], q["errou_em"][:10]) == (0, 2, "2026-10-26")


def test_correcao_traz_por_que_cada_errada_esta_errada(tmp_path):
    from escola import catalogo
    pasta = montar(tmp_path / "cat")
    q1 = catalogo.Questao("Pergunta 1?", ("a", "b", "c", "d"), 1, "")  # a certa é a b
    (pasta / "explicacoes").mkdir()
    (pasta / "explicacoes" / "lote.json").write_text(
        json.dumps({q1.chave: ["Erra o a.", None, "Erra o c.", "Erra o d."], "chave-que-mudou": ["x"]}), encoding="utf-8")
    app = criar_escola(pasta, tmp_path / "dados", relogio=Relogio())
    with TestClient(app) as escola:
        entrar(escola)
        r = escola.post(f"/api/perguntas/{id_de('https://www.youtube.com/watch?v=aula0000001')}",
                        json={"marcadas": [0, 0]}).json()
        assert [c["erradas"] for c in r["correcao"]] == [["Erra o a.", None, "Erra o c.", "Erra o d."], []]
    app.state.progresso.fechar()
    (pasta / "explicacoes" / "lote.json").write_text(json.dumps({q1.chave: ["Erra o a.", "b", None, "d"]}), encoding="utf-8")
    with pytest.raises(catalogo.CatalogoInvalido, match="null na certa"):
        catalogo.carregar(pasta)


def test_inicio_mostra_o_horario_livre_de_hoje(escola, tmp_path):
    escola.relogio.agora = datetime(2026, 10, 26, 8, 0)  # segunda
    util = {"nome": "Segunda a sexta", "dias": [0, 1, 2, 3, 4], "blocos": [
        {"inicio": "10:00", "fim": "21:00", "tipo": "trabalho", "titulo": "Trabalho"},
        {"inicio": "21:00", "fim": "22:00", "tipo": "estudo", "titulo": "Estudo"},
        {"inicio": "22:00", "fim": "1:00", "tipo": "livre", "titulo": "Horário livre", "nota": "É seu."},
        {"inicio": "1:00", "fim": "10:00", "tipo": "sono", "titulo": "Dormir"}]}
    (tmp_path / "cat" / "rotina.json").write_text(json.dumps({"grades": [util], "regras": []}), encoding="utf-8")
    escola.put("/api/ajustes", json={"semana": [{"dia": 0, "minutos": 120}]})
    assert escola.get("/api/inicio").json()["hoje"]["livre"] == {"inicio": "23:00", "fim": "01:00", "nota": "É seu."}
    escola.relogio.agora = datetime(2026, 10, 27, 0, 30)  # meia-noite e meia de terça: ainda é a noite de segunda
    assert escola.get("/api/inicio").json()["hoje"]["livre"]["inicio"] == "23:00"
    escola.relogio.agora = datetime(2026, 10, 31, 8, 0)  # sábado: a grade não tem sábado
    assert escola.get("/api/inicio").json()["hoje"]["livre"] is None


def test_de_madrugada_o_plano_ainda_e_o_da_noite_anterior(escola):
    escola.relogio.agora = datetime(2026, 10, 25, 1, 30)
    d = escola.get("/api/inicio").json()
    assert d["plano"]["dia"] == d["hoje"]["dia"] == "2026-10-24"
    escola.relogio.agora = datetime(2026, 10, 25, 4, 0)
    assert escola.get("/api/inicio").json()["plano"]["dia"] == "2026-10-25"


def test_prazo_de_inscricao_vira_faixa_ate_ele_dizer_que_se_inscreveu(tmp_path):
    estrutura = json.loads(json.dumps(ESTRUTURA))
    estrutura["concursos"][1]["cronograma_ultimo"] = [
        {"evento": "Aviso publicado", "data": "17/09/2026", "fonte": "https://marinha.mil.br/aviso"},
        {"evento": "Inscrições", "data": "18/09/2026 a 10/11/2026 (taxa de R$ 150 até 11/11)",
         "fonte": "https://marinha.mil.br/aviso.pdf"}]
    relogio = Relogio()
    app = criar_escola(montar(tmp_path / "cat", estrutura=estrutura), tmp_path / "dados", relogio=relogio)
    with TestClient(app) as escola:
        entrar(escola)
        [p] = escola.get("/api/inicio").json()["prazos"]
        assert (p["concurso"]["sigla"], p["fim"], p["dias"], p["obs"], p["fonte"]) ==             ("CP-T", "2026-11-10", 17, "taxa de R$ 150 até 11/11", "https://marinha.mil.br/aviso.pdf")
        relogio.agora = datetime(2026, 10, 1, 12, 0)  # falta mais de um mês: ainda não incomoda
        assert escola.get("/api/inicio").json()["prazos"] == []
        relogio.agora = datetime(2026, 11, 11, 12, 0)  # fechou
        assert escola.get("/api/inicio").json()["prazos"] == []
        relogio.agora = datetime(2026, 10, 24, 9, 0)
        assert escola.post("/api/inscricoes/mb").json()["prazos"] == []
        assert escola.post("/api/inscricoes/xx").status_code == 404
    app.state.progresso.fechar()


def test_uma_copia_do_progresso_por_dia_guarda_14_e_vai_ao_notebook(tmp_path):
    enviadas = []
    relogio = Relogio()
    dados = tmp_path / "dados"
    app = criar_escola(montar(tmp_path / "cat"), dados, relogio=relogio, enviar_copia=enviadas.append)
    with TestClient(app) as escola:
        entrar(escola)
        escola.post(f"/api/itens/{continuar(escola)}/estado", json={"estado": "feito"})
        escola.get("/api/inicio")  # a segunda vez no mesmo dia não copia de novo
        for _ in range(100):
            if enviadas:
                break
            time.sleep(0.01)
        assert [c.name for c in enviadas] == ["progresso-2026-10-24.db"]
        copia = Progresso(enviadas[0])
        assert copia.estados() == {}  # é a do primeiro início do dia, antes de marcar a aula
        copia.fechar()
        for n in range(1, 17):
            relogio.agora = datetime(2026, 10, 24, 9, 0) + timedelta(days=n)
            escola.get("/api/inicio")
        nomes = sorted(c.name for c in (dados / "perfis" / "teste" / "copias").glob("progresso-*.db"))
        assert len(nomes) == 14 and nomes[0] == "progresso-2026-10-27.db" and nomes[-1] == "progresso-2026-11-09.db"
    app.state.progresso.fechar()



def escola_com_simulado(tmp_path, relogio):
    """A Marinha com um simulado dentro da Escola: 4 questões, uma anulada e uma de assunto que é só do Exército."""
    estrutura = json.loads(json.dumps(ESTRUTURA))
    estrutura["concursos"][1]["materias"].append({"id": "mb-provas", "nome": "Provas anteriores", "assuntos": ["provas-mb"]})
    estrutura["assuntos"]["provas-mb"] = {"nome": "Provas anteriores", "edital": ""}
    prova = {"tipo": "prova", "titulo": "CP-T 2012", "fonte": "SSPM", "url": "https://sspm.mil.br/cpt-2012.pdf",
             "arquivo": "provas/cpt-2012-prova.pdf", "minutos": 180}
    pasta = montar(tmp_path / "cat", estrutura=estrutura, materiais={**MATERIAIS, "provas-mb": [prova]})
    q = lambda n, certa, assunto, **mais: {"numero": n, "texto": "", "enunciado": f"Simulado {n}?",  # noqa: E731
                                          "alternativas": ["a", "b", "c", "d", "e"], "certa": certa, "anulada": False,
                                          "assunto": assunto, "comentario": f"Explica a {n}.", **mais}
    (pasta / "simulados").mkdir()
    (pasta / "simulados" / "cpt-2012.json").write_text(json.dumps({
        "item": prova["url"], "prova": "CP-T 2012", "cor": "AMARELA", "area": "Psicologia",
        "url": prova["url"], "gabarito": "https://sspm.mil.br/gab-2012.pdf",
        "questoes": [q(1, 1, "etica"), q(2, 2, "psicopatologia", concorda=False, discorda="Seria a D."),
                     q(3, -1, "", anulada=True), q(4, 0, "", fora="Psicologia social", fora_do_edital=True),
                     q(5, 3, "etica")]}), encoding="utf-8")
    return criar_escola(pasta, tmp_path / "dados", relogio=relogio), id_de(prova["url"])


def test_simulado_comeca_guarda_o_rascunho_e_entrega_com_nota_por_materia(tmp_path):
    relogio = Relogio()
    app, sid = escola_com_simulado(tmp_path, relogio)
    with TestClient(app) as escola:
        entrar(escola)
        s = escola.get(f"/api/simulados/{sid}").json()
        assert [x["enunciado"] for x in s["perguntas"]["questoes"]] == ["Simulado 1?", "Simulado 2?", "Simulado 5?"]
        assert s["numeros"] == [1, 2, 5] and s["redacao"] and s["minutos"] == 180
        assert [(f["numero"], f["motivo"]) for f in s["fora"]] == \
            [(3, "anulada"), (4, "não cai no edital deste concurso: Psicologia social")]
        assert s["rascunho"] is None and s["resultado"] is None and escola.get(f"/api/itens/{sid}").json()["simulado"]

        assert escola.put(f"/api/simulados/{sid}/rascunho", json={"marcadas": [1, None, 0]}).status_code == 409
        s = escola.post(f"/api/simulados/{sid}/comecar").json()
        assert s["rascunho"] == {"inicio": "2026-10-24T09:00:00", "marcadas": [None, None, None]}
        assert escola.put(f"/api/simulados/{sid}/rascunho", json={"marcadas": [1, None]}).status_code == 422
        assert escola.put(f"/api/simulados/{sid}/rascunho", json={"marcadas": [1, None, 9]}).status_code == 422
        escola.put(f"/api/simulados/{sid}/rascunho", json={"marcadas": [1, None, 0]})
        relogio.agora = datetime(2026, 10, 24, 10, 0)  # recomeçar não zera o cronômetro nem o que marcou
        assert escola.post(f"/api/simulados/{sid}/comecar").json()["rascunho"] == \
            {"inicio": "2026-10-24T09:00:00", "marcadas": [1, None, 0]}

        s = escola.post(f"/api/simulados/{sid}", json={"marcadas": [1, None, 0]}).json()
        r = s["resultado"]
        assert (r["acertos"], r["total"], r["em_branco"]) == (1, 3, 1)
        assert r["por_materia"] == [{"materia": "Legislação", "acertos": 1, "total": 2},
                                    {"materia": "Clínica", "acertos": 0, "total": 1}]
        assert [(x["assunto"], x["erros"], x["total"]) for x in r["piores"]] == \
            [("Código de Ética", 1, 2), ("Psicopatologia", 1, 1)]
        assert r["piores"][0]["rota"].startswith("#/item/") and s["rascunho"] is None and s["estado"] == "feito"
        c = s["perguntas"]["correcao"]
        assert [x["marcada"] for x in c] == [1, -1, 0] and c[1]["acertou"] is False

        # as erradas e a em branco vão para o caderno, pela matéria do assunto delas
        erros = escola.get("/api/erros").json()
        assert sorted((x["n"], x["materia"]) for x in erros["questoes"]) == [(1, "Clínica"), (2, "Legislação")]
    app.state.progresso.fechar()


def test_texto_base_que_ficou_na_prova_vira_link_para_a_pagina(tmp_path):
    relogio = Relogio()
    app, sid = escola_com_simulado(tmp_path, relogio)
    arq = tmp_path / "cat" / "simulados" / "cpt-2012.json"
    bruto = json.loads(arq.read_text(encoding="utf-8"))
    bruto["questoes"][0]["texto"] = "[[texto-base na página 6 da prova]]"
    arq.write_text(json.dumps(bruto), encoding="utf-8")
    app = criar_escola(tmp_path / "cat", tmp_path / "dados2", relogio=relogio)
    with TestClient(app) as escola:
        entrar(escola)
        q = escola.get(f"/api/simulados/{sid}").json()["perguntas"]["questoes"][0]
        assert q["texto"] == "" and q["texto_na_prova"] == {"pagina": 6, "url": "https://sspm.mil.br/cpt-2012.pdf"}
    app.state.progresso.fechar()


def test_o_guia_vem_com_o_texto_e_sem_pdf(tmp_path):
    materiais = {**MATERIAIS, "etica": [*MATERIAIS["etica"], {"tipo": "guia", "titulo": "Guia: ética", "guia": "etica"}]}
    pasta = montar(tmp_path / "cat", materiais=materiais)
    (pasta / "guias").mkdir()
    (pasta / "guias" / "etica.md").write_text("## O sigilo\n\n| caso | regra |\n|---|---|\n| a | b |\n", encoding="utf-8")
    app = criar_escola(pasta, tmp_path / "dados", relogio=Relogio())
    with TestClient(app) as cliente:
        entrar(cliente)
        g = cliente.get(f"/api/itens/{id_de('guia:etica')}").json()
        aula1 = cliente.get(f"/api/itens/{id_de('https://www.youtube.com/watch?v=aula0000001')}").json()
    app.state.progresso.fechar()
    assert (g["tipo"], g["pdf"], g["youtube"]) == ("guia", None, None)
    assert g["guia"].startswith("## O sigilo") and aula1["guia"] is None
