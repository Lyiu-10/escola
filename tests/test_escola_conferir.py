import httpx

from escola_falsa import aula, leitura, montar
from escola import catalogo, conferir


def cliente(codigos):
    """O oEmbed do YouTube de mentira: id do vídeo → código HTTP (200 se não estiver no dicionário)."""
    def responder(req):
        vid = req.url.params["url"].rsplit("=", 1)[1]
        return httpx.Response(codigos.get(vid, 200), json={"title": "x"})
    return httpx.Client(transport=httpx.MockTransport(responder))


def pdfs(pasta, *rels):
    for rel in rels:
        (pasta / rel).parent.mkdir(parents=True, exist_ok=True)
        (pasta / rel).write_bytes(b"%PDF-1.7 ok")
    return pasta


def test_tudo_certo(tmp_path):
    cat = catalogo.carregar(montar(tmp_path / "cat"))
    arquivos = pdfs(tmp_path / "arq", "etica/l1.pdf", "psicopatologia/l2.pdf")
    assert conferir.conferir(cat, arquivos, cliente({})) == ([], [])


def test_acha_o_que_esta_errado(tmp_path):
    cat = catalogo.carregar(montar(tmp_path / "cat", materiais={
        "etica": [aula(1), leitura(1)],
        "psicopatologia": [aula(2), leitura(2, arquivo="psicopatologia/l2.pdf")],
        "social": [aula(9, extra=True), {"tipo": "leitura", "titulo": "Página", "url": "https://cpdoc.fgv.br/x"}]}))
    arquivos = tmp_path / "arq"
    (arquivos / "etica").mkdir(parents=True)
    (arquivos / "etica" / "l1.pdf").write_text("<html>não é pdf</html>")
    problemas, avisos = conferir.conferir(cat, arquivos, cliente({"aula0000002": 404, "aula0000001": 401}))
    assert problemas == ["não é PDF: etica/l1.pdf",
                         "vídeo que não abre (404): Aula 2 (https://www.youtube.com/watch?v=aula0000002)",
                         "arquivo que falta: psicopatologia/l2.pdf (Leitura 2)"]
    assert avisos == ["não toca fora do YouTube: Aula 1 (https://www.youtube.com/watch?v=aula0000001)",
                      "abre no site, sem PDF: Página (https://cpdoc.fgv.br/x)"]


def test_assunto_sem_material_principal(tmp_path):
    cat = catalogo.carregar(montar(tmp_path / "cat", materiais={
        "etica": [aula(1)], "psicopatologia": [aula(2)], "social": [aula(3, extra=True)]}))
    problemas, _ = conferir.conferir(cat, tmp_path, cliente({}))
    assert problemas == ["sem material: social (Psicologia social)"]


def test_sem_rede_vira_problema_e_nao_quebra(tmp_path):
    def cair(req):
        raise httpx.ConnectError("sem rede")
    cat = catalogo.carregar(montar(tmp_path / "cat", materiais={"etica": [aula(1)], "psicopatologia": [aula(2)],
                                                                 "social": [aula(3)]}))
    problemas, _ = conferir.conferir(cat, tmp_path, httpx.Client(transport=httpx.MockTransport(cair)))
    assert problemas[0].startswith("não deu para conferir o vídeo: Aula 1")
