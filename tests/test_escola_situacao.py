import json
import subprocess
from datetime import datetime

import httpx
import pytest

from escola_falsa import montar
from escola import catalogo, situacao


@pytest.fixture
def cat(tmp_path):
    return catalogo.carregar(montar(tmp_path / "cat"))


def resposta(estado_mb="aguardando", novidade=None):
    return {"mb": {"estado": estado_mb, "resumo": "Sem edital novo.", "edital": None,
                   "datas": [{"evento": "Prova", "data": "maio/2027", "confirmada": False}, {"evento": ""}],
                   "novidade": novidade, "fontes": [{"titulo": "DEnsM", "url": "https://marinha.mil.br/x"},
                                                    {"titulo": "ruim", "url": "marinha.mil.br"}]},
            "eb": {"estado": "previsto", "resumo": "Edital em março.", "edital": None, "datas": [], "novidade": None,
                   "fontes": []}}


class Carteiro:
    def __init__(self, falha=False):
        self.cartoes, self.falha = [], falha

    def __call__(self, cartoes):
        if self.falha:
            return list(cartoes)
        self.cartoes += cartoes
        return []


def test_validar_limpa_e_recusa_o_que_falta():
    ok = situacao.validar(resposta(), ["mb", "eb"])
    assert ok["mb"]["datas"] == [{"evento": "Prova", "data": "maio/2027", "confirmada": False}]
    assert ok["mb"]["fontes"] == [{"titulo": "DEnsM", "url": "https://marinha.mil.br/x"}]
    with pytest.raises(situacao.SituacaoInvalida, match="faltou o concurso eb"):
        situacao.validar({"mb": resposta()["mb"]}, ["mb", "eb"])
    with pytest.raises(situacao.SituacaoInvalida, match="estado 'talvez'"):
        situacao.validar({**resposta(), "eb": {**resposta()["eb"], "estado": "talvez"}}, ["mb", "eb"])


def test_primeira_busca_grava_sem_cartao_e_a_segunda_avisa_a_mudanca(cat, tmp_path):
    dados, carteiro = tmp_path / "dados", Carteiro()
    pedidos = []

    def perguntar(texto, ids):
        pedidos.append(texto)
        return resposta() if len(pedidos) == 1 else resposta("inscricoes", "Saiu o edital 2027.")

    assert situacao.rodada(cat, dados, agora=datetime(2026, 10, 26, 10), perguntar=perguntar, enviar=carteiro) == 0
    s = situacao.ler(dados)
    assert s["concursos"]["mb"]["estado"] == "aguardando" and s["concursos"]["mb"]["desde"] == "2026-10-26"
    assert carteiro.cartoes == [] and len(s["historico"]) == 2
    # seis dias depois ainda não é hora; no sétimo, busca de novo e manda o que achou junto da situação anterior
    situacao.rodada(cat, dados, agora=datetime(2026, 11, 1, 10), perguntar=perguntar, enviar=carteiro)
    assert len(pedidos) == 1
    situacao.rodada(cat, dados, agora=datetime(2026, 11, 2, 10), perguntar=perguntar, enviar=carteiro)
    assert '"estado": "aguardando"' in pedidos[1] and "02/11/2026" in pedidos[1]
    s = situacao.ler(dados)
    assert s["concursos"]["mb"]["desde"] == "2026-11-02" and s["concursos"]["eb"]["desde"] == "2026-10-26"
    assert [c["titulo"] for c in carteiro.cartoes] == ["Escola · Marinha CP-T: Inscrições abertas. Saiu o edital 2027."]
    assert carteiro.cartoes[0]["frente"] == "Escola" and "127.0.0.1:8792/#/situacao" in carteiro.cartoes[0]["nota"]
    assert s["historico"][0] == {"em": "2026-11-02", "concurso": "mb",
                                 "texto": "Inscrições abertas. Saiu o edital 2027."}


def test_busca_que_falha_guarda_o_erro_e_tenta_no_dia_seguinte(cat, tmp_path):
    dados = tmp_path / "dados"

    def quebrado(texto, ids):
        raise situacao.SituacaoInvalida("o claude saiu com 1: sem internet")

    assert situacao.rodada(cat, dados, agora=datetime(2026, 10, 26, 10), perguntar=quebrado) == 1
    s = situacao.ler(dados)
    assert s["erro"].endswith("sem internet") and s["verificado_em"] is None and s["tentativa_em"]
    assert situacao.rodada(cat, dados, agora=datetime(2026, 10, 27, 10), perguntar=lambda t, i: resposta(),
                           enviar=Carteiro()) == 0
    assert situacao.ler(dados)["erro"] is None


def test_cartao_que_nao_foi_fica_para_a_proxima(cat, tmp_path):
    dados = tmp_path / "dados"
    situacao.rodada(cat, dados, agora=datetime(2026, 10, 26), perguntar=lambda t, i: resposta(), enviar=Carteiro())
    fora = Carteiro(falha=True)
    situacao.rodada(cat, dados, agora=datetime(2026, 11, 2), perguntar=lambda t, i: resposta("andamento"), enviar=fora)
    assert len(situacao.ler(dados)["pendentes"]) == 1
    volta = Carteiro()
    situacao.rodada(cat, dados, agora=datetime(2026, 11, 3), perguntar=lambda t, i: resposta(), enviar=volta)
    assert len(volta.cartoes) == 1 and situacao.ler(dados)["pendentes"] == []


def test_enviar_cai_para_a_frente_thalia_numa_central_antiga():
    enviados = []

    def post(corpo):
        enviados.append(corpo["frente"])
        return httpx.Response(422 if corpo["frente"] == "Escola" else 201, request=httpx.Request("POST", "http://x"))

    assert situacao.enviar_cartoes([{"titulo": "t", "nota": "", "frente": "Escola"}], post=post) == []
    assert enviados == ["Escola", "Thalia"]

    def fora(corpo):
        raise httpx.ConnectError("sem rede")

    assert len(situacao.enviar_cartoes([{"titulo": "t", "nota": "", "frente": "Escola"}], post=fora)) == 1


def test_perguntar_le_a_saida_estruturada_ou_o_json_do_texto():
    class R:
        returncode, stderr = 0, ""

        def __init__(self, stdout):
            self.stdout = stdout

    chamadas = []

    def rodar(cmd, **kw):
        chamadas.append(cmd)
        return R(json.dumps({"is_error": False, "structured_output": {"mb": 1}}))

    assert situacao.perguntar("oi", ["mb"], rodar=rodar, exe="claude") == {"mb": 1}
    cmd = chamadas[0]
    assert cmd[cmd.index("--tools") + 1] == "WebSearch,WebFetch" and "--json-schema" in cmd
    texto = lambda cmd, **kw: R(json.dumps({"is_error": False, "result": 'Aqui:\n```json\n{"mb": 2}\n```'}))
    assert situacao.perguntar("oi", ["mb"], rodar=texto, exe="claude") == {"mb": 2}
    erro = lambda cmd, **kw: R(json.dumps({"is_error": True, "result": "limite do plano"}))
    with pytest.raises(situacao.SituacaoInvalida, match="limite do plano"):
        situacao.perguntar("oi", ["mb"], rodar=erro, exe="claude")
