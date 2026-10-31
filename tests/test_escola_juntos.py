import asyncio

from escola.juntos import PARADA_MAX, Salas

ANA = {"id": "ana", "nome": "Ana", "cor": "#F4A259"}
BIA = {"id": "bia", "nome": "Bia", "cor": "#2FA58A"}


class Relogio:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def tudo(fila: asyncio.Queue) -> list[dict]:
    saida = []
    while not fila.empty():
        saida.append(fila.get_nowait())
    return saida


def test_uma_sala_por_video_e_quem_entra_recebe_o_estado():
    async def corpo():
        s = Salas(Relogio())
        assert s.abrir("v1", "Aula 1", ANA)["sala"] == s.abrir("v1", "Aula 1", BIA)["sala"] == "v1"
        conexao, fila = s.entrar("v1", ANA)
        (msg,) = tudo(fila)
        assert msg["tipo"] == "entrou" and msg["conexao"] == conexao and msg["tocando"] is False
        assert msg["membros"] == [ANA]
        assert s.entrar("nao-existe", ANA) is None
    asyncio.run(corpo())


def test_comando_vai_aos_outros_e_a_posicao_anda_enquanto_toca():
    async def corpo():
        r = Relogio()
        s = Salas(r)
        s.abrir("v1", "Aula 1", ANA)
        ca, fa = s.entrar("v1", ANA)
        cb, fb = s.entrar("v1", BIA)
        tudo(fa), tudo(fb)
        s.comando("v1", "play", 30.0, ANA, conexao=ca)
        assert tudo(fa) == []  # quem mandou não recebe o eco
        (msg,) = tudo(fb)
        assert (msg["tipo"], msg["tocando"], msg["posicao"], msg["por"]) == ("comando", True, 30.0, "Ana")
        r.t += 12
        assert s.estado("v1")["posicao"] == 42.0  # quem entrar agora cai em 42 s
        s.comando("v1", "pause", 42.5, BIA, conexao=cb)
        r.t += 100
        assert s.estado("v1")["posicao"] == 42.5 and not s.estado("v1")["tocando"]
    asyncio.run(corpo())


def test_o_convite_acompanha_as_salas_e_o_ultimo_a_sair_fecha():
    async def corpo():
        s = Salas(Relogio())
        n, ouvinte = s.ouvir()
        assert tudo(ouvinte) == [{"tipo": "salas", "salas": []}]
        s.abrir("v1", "Aula 1", ANA)
        ca, fa = s.entrar("v1", ANA)
        cb, fb = s.entrar("v1", BIA)
        ultima = tudo(ouvinte)[-1]["salas"]
        assert ultima[0]["aberta_por"] == ANA and ultima[0]["membros"] == [ANA, BIA]
        tudo(fa)
        s.sair("v1", cb)
        assert tudo(fa) == [{"tipo": "membros", "membros": [ANA]}]
        s.sair("v1", ca)
        assert s.estado("v1") is None and tudo(ouvinte)[-1] == {"tipo": "salas", "salas": []}
        s.parar_de_ouvir(n)
    asyncio.run(corpo())


def test_sala_parada_ou_que_ninguem_conectou_fecha():
    async def corpo():
        r = Relogio()
        s = Salas(r)
        s.abrir("v1", "Aula 1", ANA)  # ninguém conectou
        s.abrir("v2", "Aula 2", ANA)
        _, f2 = s.entrar("v2", ANA)
        r.t += 61
        s.limpar()
        assert s.estado("v1") is None and s.estado("v2") is not None
        r.t += PARADA_MAX
        s.limpar()
        assert s.estado("v2") is None and tudo(f2)[-1] == {"tipo": "fechada"}
    asyncio.run(corpo())


def test_rotas_da_sala(tmp_path):
    import json

    from fastapi.testclient import TestClient

    from escola_falsa import montar
    from escola.app import criar_escola

    app = criar_escola(montar(tmp_path / "cat"), tmp_path / "dados")
    with TestClient(app) as ana, TestClient(app) as bia:
        ana.post("/api/perfis", json={"nome": "Ana"})
        bia.post("/api/perfis", json={"nome": "Bia"})
        video = ana.get("/api/inicio").json()["continuar"]["id"]  # a Aula 1 é vídeo
        sala = ana.post("/api/juntos", json={"item": video}).json()
        assert (sala["sala"], sala["titulo"], sala["tocando"]) == (video, "Aula 1", False)
        assert ana.post("/api/juntos", json={"item": "nao-existe"}).status_code == 404
        with bia.stream("GET", f"/api/juntos/{video}/fluxo") as fluxo:
            linhas = fluxo.iter_lines()
            assert next(linhas) == "event: entrou"
            entrou = json.loads(next(linhas)[len("data: "):])
            assert entrou["membros"] == [{"id": "bia", "nome": "Bia", "cor": entrou["membros"][0]["cor"]}]
            r = ana.post(f"/api/juntos/{video}/comando", json={"acao": "play", "posicao": 12.5}).json()
            assert r["tocando"] and r["posicao"] >= 12.5
            next(linhas)  # a linha em branco que fecha o evento
            assert next(linhas) == "event: comando"
            assert json.loads(next(linhas)[len("data: "):])["por"] == "Ana"
        assert ana.get(f"/api/juntos/{video}").status_code == 404  # a Bia saiu, e era a única conectada
        assert ana.post(f"/api/juntos/{video}/comando", json={"acao": "pause", "posicao": 1}).status_code == 404
    app.state.progresso.fechar()
