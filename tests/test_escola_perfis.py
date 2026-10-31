import json
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from escola_falsa import montar
from escola.app import criar_escola
from escola.perfis import CORES, DaVez, Perfis, chave, perfil_da_vez
from escola.progresso import Progresso


def test_chave_ignora_acento_maiuscula_e_espaco():
    assert chave("  Péricles ") == chave("pericles") == "pericles"


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
