import json
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from escola_falsa import montar
from escola.app import criar_escola
from escola.perfis import CORES, DaVez, Perfis, chave, perfil_da_vez
from escola.progresso import Progresso


def test_chave_ignora_acento_maiuscula_e_espaco():
    assert chave("  José ") == chave("jose") == "jose"


def test_criar_da_id_pelo_nome_e_o_primeiro_e_o_dono(tmp_path):
    a = Perfis(tmp_path).criar("Ana Lú")
    assert a == {"id": "ana-lu", "nome": "Ana Lú", "cor": CORES[0], "dono": True}


def test_nome_repetido_ou_vazio_e_recusado(tmp_path):
    p = Perfis(tmp_path)
    p.criar("Ana")
    for ruim in ("ána", "   ", "x" * 21):
        with pytest.raises(ValueError):
            p.criar(ruim)


def test_id_nao_repete_e_segundo_nao_e_dono(tmp_path):
    p = Perfis(tmp_path)
    p.criar("Ana")
    p.editar("ana", nome="Bia")
    c = p.criar("Ana")  # o nome voltou a ser livre, mas o id "ana" é da Bia
    assert c["id"] == "ana-2" and c["dono"] is False and c["cor"] == CORES[1]
    assert json.loads((tmp_path / "perfis.json").read_text(encoding="utf-8"))[0]["nome"] == "Bia"


def test_editar_cor_fora_da_paleta_e_perfil_que_nao_existe(tmp_path):
    p = Perfis(tmp_path)
    p.criar("Ana")
    with pytest.raises(ValueError):
        p.editar("ana", cor="#000000")
    with pytest.raises(KeyError):
        p.editar("ninguem", nome="X")


def test_cada_perfil_tem_o_seu_progresso_e_o_da_vez_segue_o_contexto(tmp_path):
    p = Perfis(tmp_path)
    p.criar("Ana")
    p.criar("Bia")
    prog = DaVez()
    with p.usando("ana"):
        prog.marcar("aula-1", "feito", datetime(2026, 10, 30, 9))
        assert perfil_da_vez() == "ana"
    with p.usando("bia"):
        assert prog.estados() == {}
    assert perfil_da_vez() is None
    assert (tmp_path / "perfis" / "ana" / "progresso.db").is_file()
    p.fechar()


def test_migracao_leva_o_progresso_as_copias_e_a_rotina_para_o_principal(tmp_path):
    antigo = Progresso(tmp_path / "progresso.db")
    antigo.marcar("aula-1", "feito", datetime(2026, 10, 30, 9))
    antigo.fechar()
    (tmp_path / "copias").mkdir()
    (tmp_path / "copias" / "progresso-2026-10-29.db").write_bytes(b"x")
    rotina = tmp_path / "cat" / "rotina.json"
    rotina.parent.mkdir()
    rotina.write_text("{}", encoding="utf-8")
    p = Perfis(tmp_path, rotina_antiga=rotina)
    assert p.todos() == [{"id": "principal", "nome": "Principal", "cor": CORES[0], "dono": True}]
    pasta = tmp_path / "perfis" / "principal"
    assert (pasta / "copias" / "progresso-2026-10-29.db").is_file() and (pasta / "rotina.json").is_file()
    assert not (tmp_path / "progresso.db").exists() and not rotina.exists()
    assert (tmp_path / "progresso-antes-dos-perfis.db").is_file()
    assert p.progresso("principal").estados()["aula-1"][0] == "feito"
    p.fechar()
    assert Perfis(tmp_path).todos()[0]["id"] == "principal"  # a segunda subida não migra de novo


@pytest.fixture
def app(tmp_path):
    app = criar_escola(montar(tmp_path / "cat"), tmp_path / "dados")
    yield app
    app.state.progresso.fechar()


def marcar_continuar(cliente) -> str:
    item = cliente.get("/api/inicio").json()["continuar"]["id"]
    cliente.post(f"/api/itens/{item}/estado", json={"estado": "feito"})
    return item


def test_sem_perfil_a_api_de_estudo_e_401_e_a_escolha_e_livre(app):
    with TestClient(app) as c:
        assert c.get("/api/inicio").status_code == 401
        assert c.get("/").status_code == 200 and c.get("/api/saude").status_code == 200
        assert c.get("/api/perfis").json() == {"perfis": [], "atual": None, "cores": list(CORES)}


def test_criar_entra_e_cada_aparelho_ve_so_o_seu(app):
    with TestClient(app) as ana, TestClient(app) as bia:
        ana.post("/api/perfis", json={"nome": "Ana"})
        bia.post("/api/perfis", json={"nome": "Bia"})
        item = marcar_continuar(ana)
        assert ana.get("/api/inicio").json()["continuar"]["id"] != item
        assert bia.get("/api/inicio").json()["continuar"]["id"] == item  # a Bia ainda está no começo
        assert ana.get("/api/perfis").json()["atual"]["id"] == "ana"


def test_trocar_e_sair(app):
    with TestClient(app) as c:
        c.post("/api/perfis", json={"nome": "Ana"})
        c.post("/api/perfis", json={"nome": "Bia"})
        assert c.get("/api/perfis").json()["atual"]["id"] == "bia"
        assert c.post("/api/perfis/ana/entrar").json()["nome"] == "Ana"
        assert c.get("/api/perfis").json()["atual"]["id"] == "ana"
        assert c.post("/api/perfis/ninguem/entrar").status_code == 404
        c.post("/api/perfis/sair")
        assert c.get("/api/inicio").status_code == 401


def test_nome_repetido_e_editar(app):
    with TestClient(app) as c:
        c.post("/api/perfis", json={"nome": "Ana"})
        r = c.post("/api/perfis", json={"nome": "ána"})
        assert r.status_code == 422 and "nome" in r.json()["detail"]
        assert c.put("/api/perfis/ana", json={"nome": "Ana Clara", "cor": CORES[2]}).json()["cor"] == CORES[2]
        assert c.put("/api/perfis/ana", json={"cor": "#123456"}).status_code == 422
        assert c.put("/api/perfis/ninguem", json={"nome": "X"}).status_code == 404


def test_rotina_do_perfil_vale_antes_da_do_catalogo(tmp_path):
    cat = montar(tmp_path / "cat")
    (cat / "rotina.json").write_text(json.dumps({"grades": [], "regras": []}), encoding="utf-8")
    app = criar_escola(cat, tmp_path / "dados")
    with TestClient(app) as c:
        c.post("/api/perfis", json={"nome": "Ana"})
        assert c.get("/api/rotina").json()["grades"] == []  # sem rotina própria, vale a do catálogo
        util = {"nome": "Segunda a sexta", "dias": [0, 1, 2, 3, 4], "blocos": [
            {"inicio": "10:00", "fim": "1:00", "tipo": "livre", "titulo": "Livre"},
            {"inicio": "1:00", "fim": "10:00", "tipo": "sono", "titulo": "Dormir"}]}
        propria = tmp_path / "dados" / "perfis" / "ana" / "rotina.json"
        propria.write_text(json.dumps({"grades": [util], "regras": []}), encoding="utf-8")
        assert c.get("/api/rotina").json()["grades"][0]["nome"] == "Segunda a sexta"
    app.state.progresso.fechar()


def test_a_copia_vai_ao_notebook_com_o_id_do_perfil_no_nome(tmp_path, monkeypatch):
    from escola import app as app_escola

    chamadas = []
    monkeypatch.setattr(app_escola.subprocess, "run",
                        lambda cmd, **kw: chamadas.append(cmd) or type("R", (), {"returncode": 0})())
    app_escola.enviar_ao_notebook(tmp_path / "perfis" / "ana" / "copias" / "progresso-2026-10-30.db")
    assert chamadas[0][-1] == "notebook:escola-progresso-ana.db"


def test_turma_mostra_os_numeros_de_cada_um_sem_precisar_entrar(app):
    with TestClient(app) as ana, TestClient(app) as bia, TestClient(app) as visita:
        ana.post("/api/perfis", json={"nome": "Ana"})
        bia.post("/api/perfis", json={"nome": "Bia"})
        aula1 = marcar_continuar(ana)  # a Aula 1, de 20 min
        ana.post(f"/api/perguntas/{aula1}", json={"marcadas": [1, 0]})  # 2 questões, 1 certa: mais 4 min
        t = visita.get("/api/turma").json()  # um aparelho sem perfil
        assert t["eu"] is None
        a, b = t["perfis"]
        assert (a["nome"], a["concluidos"], a["questoes"], a["acertos"]) == ("Ana", 1, 2, 1)
        assert (a["minutos_total"], a["minutos_semana"]) == (24, 24)
        assert a["agora"] == {"titulo": "Leitura 1", "materia": "Legislação"} and a["ultimo"]
        assert [c["sigla"] for c in a["concursos"]] == ["CP-T", "EsFCEx"]  # o de foco primeiro, como no catálogo
        assert (b["concluidos"], b["minutos_total"], b["ultimo"]) == (0, 0, None)
        assert b["agora"]["titulo"] == "Aula 1"
        assert not {"caderno", "rotina", "notas", "respostas"} & set(a)
        assert ana.get("/api/turma").json()["eu"] == "ana"


def test_cor_padrao_e_a_primeira_que_ninguem_usa(tmp_path):
    p = Perfis(tmp_path)
    p.criar("Ana", CORES[1])
    assert p.criar("Bia")["cor"] == CORES[0]
    assert p.criar("Caio")["cor"] == CORES[2]
