import json

from escola_falsa import ESTRUTURA, MATERIAIS, montar, questao
from escola import catalogo, conferir, textos
from escola.catalogo import id_de

VTT = """WEBVTT
Kind: captions
Language: pt

00:00:01.000 --> 00:00:03.000 align:start position:0%

O<00:00:01.500><c> sigilo</c>

00:00:03.000 --> 00:00:03.010 align:start position:0%
O sigilo

00:00:03.010 --> 00:00:05.000 align:start position:0%
O sigilo
protege<00:00:04.000><c> o paciente.</c>

00:01:31.000 --> 00:01:33.000 align:start position:0%
A ética vem do código.
"""


def test_legenda_vira_linhas_com_o_minuto_sem_repetir():
    assert textos.legenda(VTT) == "[0:01] O sigilo protege o paciente.\n[1:31] A ética vem do código."


def test_trecho_tem_de_estar_no_material_e_perto_do_minuto(tmp_path):
    a1 = "https://www.youtube.com/watch?v=aula0000001"
    cat = catalogo.carregar(montar(tmp_path / "cat", perguntas={a1: [
        questao(1, trecho="O sigilo protege o paciente", onde=5),
        questao(2, trecho="a ética vem do código", onde=300),
        questao(3, trecho="o sigilo é absoluto", onde=1)]}))
    pasta = tmp_path / "textos"
    pasta.mkdir()
    (pasta / f"{id_de(a1)}.txt").write_text(f"# Aula 1\n\n{textos.legenda(VTT)}\n", encoding="utf-8")
    problemas, avisos = conferir.conferir_perguntas(cat, pasta)
    assert problemas == ["trecho que não está no material: Aula 1 › Pergunta 3?"]
    assert "o trecho está em 91, não em 300: Aula 1 › Pergunta 2?" in avisos  # mais de 2 min longe do apontado
    assert "só 3 perguntas: Aula 1" in avisos


def test_aquecimento_confere_cartoes_perguntas_e_o_resumo(tmp_path):
    a1 = "https://www.youtube.com/watch?v=aula0000001"
    pergunta = questao(1, trecho="o sigilo protege o paciente", onde=1)
    cat = catalogo.carregar(montar(tmp_path / "cat", perguntas={a1: [pergunta]}, aquecimento={a1: {
        "resumo": "Curto demais.",
        "cartoes": [{"frente": "Frente 1?", "verso": "v", "trecho": "a ética vem do código", "onde": 91},
                    {"frente": "Frente 2?", "verso": "v", "trecho": "o sigilo é absoluto", "onde": 1}],
        "perguntas": [pergunta, questao(2, trecho="o sigilo", onde=300)]}}))
    pasta = tmp_path / "textos"
    pasta.mkdir()
    (pasta / f"{id_de(a1)}.txt").write_text(f"# Aula 1\n\n{textos.legenda(VTT)}\n", encoding="utf-8")
    problemas, avisos = conferir.conferir_perguntas(cat, pasta)
    assert problemas == ["aquecimento: trecho que não está no material: Aula 1 › Frente 2?"]
    assert {"aquecimento: 2 cartões e 2 perguntas: Aula 1",
            "aquecimento: resumo com 2 palavras (o normal é de 40 a 140): Aula 1",
            "aquecimento: pergunta igual a uma de fixação: Aula 1 › Pergunta 1?",
            "aquecimento: o trecho está em 1, não em 300: Aula 1 › Pergunta 2?"} <= set(avisos)


def test_trecho_bate_com_o_acento_decomposto_do_pdf():
    assert conferir.normal("O psicólogo") in conferir.normal("O psicólogo tem o dever")


def test_a_certa_espalhada_pelas_letras(tmp_path):
    a1 = "https://www.youtube.com/watch?v=aula0000001"
    cat = catalogo.carregar(montar(tmp_path / "cat", perguntas={a1: [
        questao(n, certa=1 if n < 5 else 2, trecho="o sigilo") for n in range(1, 6)]}))
    _, avisos = conferir.conferir_perguntas(cat, tmp_path)
    assert "a certa cai 4 vezes na mesma letra: Aula 1" in avisos


def test_pagina_do_pdf_e_simulado_na_provinha(tmp_path):
    cat = catalogo.carregar(montar(tmp_path / "cat", perguntas={"https://site.cfp.org.br/l1.pdf": [
        questao(1, trecho="dever de sigilo", onde=3), questao(2, trecho="dever de sigilo", onde=2)]}))
    pasta = tmp_path / "textos"
    pasta.mkdir()
    (pasta / f"{id_de('https://site.cfp.org.br/l1.pdf')}.txt").write_text(
        "[p. 2]\nIntrodução.\n[p. 3]\nO psicólogo tem o de-\nver de sigilo.", encoding="utf-8")
    problemas, avisos = conferir.conferir_perguntas(cat, pasta)
    assert problemas == [] and "o trecho está em 3, não em 2: Leitura 1 › Pergunta 2?" in avisos


def test_questao_de_aula_nao_sai_de_prova_guardada_para_simulado(tmp_path):
    estrutura = json.loads(json.dumps(ESTRUTURA))
    estrutura["assuntos"]["provas-mb"] = {"nome": "Simulados", "edital": ""}
    estrutura["concursos"][1]["materias"].append({"id": "mb-provas", "nome": "Provas", "assuntos": ["provas-mb"]})
    simulado = {"tipo": "prova", "titulo": "ALE-AM/2025 (FGV): Psicólogo", "fonte": "FGV", "minutos": 120,
                "url": "https://fgv.br/ale-am.pdf"}
    prova = {"prova": "FGV ALE-AM 2025", "cor": "Tipo 1", "url": "https://fgv.br/ale-am.pdf", "gabarito": "https://fgv.br/gab.pdf",
             "questoes": [{"numero": 41, "assunto": "etica", "item": "", **questao(1)}]}
    cat = catalogo.carregar(montar(tmp_path / "cat", materiais={**MATERIAIS, "provas-mb": [simulado]}, estrutura=estrutura,
                                   questoes={"fgv-ale-am-2025": prova}))
    problemas, _ = conferir.conferir_perguntas(cat, tmp_path)
    assert problemas == ["questão de aula ou de aquecimento que é de um simulado: "
                         "FGV ALE-AM 2025, Psicologia (Prova Tipo 1), questão 41"]


def test_youtube_barrando_deixa_os_outros_videos_para_outra_hora(tmp_path, monkeypatch):
    cat = catalogo.carregar(montar(tmp_path / "cat"))
    tentados = []

    def texto_de(item, arquivos, http, ouvir=False):
        if catalogo.youtube(item.url):
            tentados.append(item.titulo)
            raise RuntimeError("Unable to download video subtitles for 'pt': HTTP Error 429: Too Many Requests")
        return "O psicólogo guarda sigilo. " * 30

    monkeypatch.setattr(textos, "texto_de", texto_de)
    monkeypatch.setattr(textos, "SEGUIDAS_429", 2)
    falhas = textos.extrair(cat, tmp_path / "arquivos", tmp_path / "textos", avisar=lambda _: None)
    assert tentados == ["Aula 1", "Aula 2"]  # a Aula 3 nem é tentada
    assert len(falhas) == 3 and "ficou para outra hora" in falhas[-1]
    assert len(list((tmp_path / "textos").iterdir())) == 2  # as leituras saem mesmo assim


def test_sem_legenda_o_video_e_ouvido(tmp_path, monkeypatch):
    cat = catalogo.carregar(montar(tmp_path / "cat"))
    ouvidos = []

    def sem_legenda(url, tentativas=3):
        assert tentativas == 1  # com o áudio de reserva, não vale esperar o YouTube
        raise RuntimeError("HTTP Error 429: Too Many Requests")

    def ouvir_video(url):
        ouvidos.append(url)
        return "[0:00] O psicólogo guarda sigilo. " * 30

    monkeypatch.setattr(textos, "baixar_legenda", sem_legenda)
    monkeypatch.setattr(textos, "ouvir_video", ouvir_video)
    monkeypatch.setattr(textos, "texto_pdf", lambda arquivo, primeira=None: "[p. 1] O código. " * 50)
    monkeypatch.setattr(textos, "PAUSA", 0)
    pasta = tmp_path / "arquivos"
    for nome in ("etica/l1.pdf", "psicopatologia/l2.pdf"):
        (pasta / nome).parent.mkdir(parents=True, exist_ok=True)
        (pasta / nome).write_bytes(b"%PDF-")
    assert textos.extrair(cat, pasta, tmp_path / "textos", ouvir=True, avisar=lambda _: None) == []
    assert len(ouvidos) == 3 and len(list((tmp_path / "textos").iterdir())) == 5


def test_whisper_vira_linhas_de_30_segundos():
    falas = [(0, "O sigilo"), (12, "protege o paciente."), (95, "A ética.")]
    assert textos._janelas(falas) == "[0:00] O sigilo protege o paciente.\n[1:35] A ética."
