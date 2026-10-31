import copy

import pytest
from fastapi.testclient import TestClient

from escola_falsa import MATERIAIS_PARTICULARES, PARTICULAR, montar, montar_particular
from escola import catalogo
from escola.app import criar_escola

AULA = catalogo.id_de("https://cursinho.example/units/U1/blocks/B1")
PDF = catalogo.id_de("https://cursinho.example/units/U1/blocks/B2")
NO_CAMINHO = catalogo.id_de("https://cursinho.example/units/U9/blocks/B8")  # principal na Ética do catálogo
EXTRA = catalogo.id_de("https://cursinho.example/units/U9/blocks/B9")  # extra na Ética do catálogo


def test_o_catalogo_particular_entra_junto_e_guarda_de_quem_e(tmp_path):
    cat = catalogo.carregar(montar(tmp_path / "cat"), montar_particular(tmp_path / "particular"))
    enem = cat.concurso("enem")
    assert enem.perfis == ("ana",) and cat.concurso("mb").perfis == ()
    assert cat.itens[PDF].arquivo == "particular/cursinho/bio-u1.pdf"  # o PDF mora na pasta particular
    assert cat.itens[AULA].nota == "Você já concluiu no Cursinho."
    assert set(cat.donos) == {AULA, PDF, NO_CAMINHO, EXTRA} and cat.donos[EXTRA] == ("ana",)
    assert cat.itens[EXTRA] in cat.assuntos["etica"].itens and cat.itens[EXTRA].extra
    assert catalogo.carregar(tmp_path / "cat", tmp_path / "nao-existe").concurso("enem") is None


def test_o_particular_nao_repete_o_catalogo_e_sempre_diz_de_quem_e(tmp_path):
    montar(tmp_path / "cat")
    repetido = copy.deepcopy(PARTICULAR)
    repetido["assuntos"]["etica"] = {"nome": "Ética de novo"}
    with pytest.raises(catalogo.CatalogoInvalido, match="etica"):
        catalogo.carregar(tmp_path / "cat", montar_particular(tmp_path / "p1", repetido))
    sem_dono = copy.deepcopy(PARTICULAR)
    del sem_dono["perfis"]
    with pytest.raises(catalogo.CatalogoInvalido, match="perfis"):
        catalogo.carregar(tmp_path / "cat", montar_particular(tmp_path / "p2", sem_dono))


@pytest.fixture
def app(tmp_path):
    dados = tmp_path / "dados"
    montar_particular(dados / "particular")
    app = criar_escola(montar(tmp_path / "cat"), dados)
    yield app
    app.state.progresso.fechar()


def test_so_o_dono_ve_o_concurso_particular(app):
    with TestClient(app) as ana, TestClient(app) as bia:
        ana.post("/api/perfis", json={"nome": "Ana"})
        bia.post("/api/perfis", json={"nome": "Bia"})
        assert "enem" in [c["id"] for c in ana.get("/api/inicio").json()["concursos"]]
        assert "enem" in [c["id"] for c in ana.get("/api/barra").json()["concursos"]]
        assert ana.get("/api/concursos/enem").status_code == 200
        item = ana.get(f"/api/itens/{PDF}").json()
        assert item["pdf"] == "/particular/arquivos/cursinho/bio-u1.pdf"
        assert ana.get(item["pdf"]).content == b"%PDF-1.4 particular"

        assert "enem" not in [c["id"] for c in bia.get("/api/inicio").json()["concursos"]]
        assert "enem" not in [c["id"] for c in bia.get("/api/barra").json()["concursos"]]
        assert "enem" not in [c["id"] for c in bia.get("/api/situacao").json()["concursos"]]
        assert bia.get("/api/concursos/enem").status_code == 404
        assert bia.get(f"/api/itens/{AULA}").status_code == 404
        assert bia.post(f"/api/itens/{AULA}/estado", json={"estado": "feito"}).status_code == 404
        assert bia.get(item["pdf"]).status_code == 404
        assert bia.put("/api/ajustes", json={"concursos": ["enem"]}).status_code == 422
        assert TestClient(app).get(item["pdf"]).status_code == 404  # sem perfil
        def etica(cliente):  # a Ética na página da Marinha
            return next(a for m in cliente.get("/api/concursos/mb").json()["materias"] for a in m["assuntos"]
                        if a["id"] == "etica")
        de_ana, de_bia = etica(ana), etica(bia)
        assert {NO_CAMINHO, EXTRA} <= {i["id"] for i in de_ana["itens"]}
        assert not {NO_CAMINHO, EXTRA} & {i["id"] for i in de_bia["itens"]}
        assert de_ana["total"] == de_bia["total"] + 1  # a aula particular principal conta no caminho só da Ana

        def lista(cliente, iid):  # a lista da matéria, ao lado da aula aberta
            return [i["id"] for a in cliente.get(f"/api/itens/{iid}").json()["lista"]["assuntos"] for i in a["itens"]]
        aula1 = catalogo.id_de("https://www.youtube.com/watch?v=aula0000001")  # a Aula 1 também é da Ética
        assert EXTRA in lista(ana, aula1) and EXTRA not in lista(bia, aula1)
        assert bia.get(f"/api/itens/{EXTRA}").status_code == 404
        assert ana.get("/arquivos/cursinho/bio-u1.pdf").status_code == 404  # não sai pela pasta aberta


def test_o_particular_so_entra_no_cronograma_se_o_dono_escolher(app):
    with TestClient(app) as ana:
        ana.post("/api/perfis", json={"nome": "Ana"})
        inicio = ana.get("/api/inicio").json()
        assert "enem" not in inicio["hoje"]["concursos"]  # vazio é todos, menos o particular
        assert next(c for c in inicio["concursos"] if c["id"] == "enem")["no_cronograma"] is False
        r = ana.put("/api/ajustes", json={"concursos": ["mb", "enem"]})
        assert r.status_code == 200 and r.json()["hoje"]["concursos"] == ["mb", "enem"]
