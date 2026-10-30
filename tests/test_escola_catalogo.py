import copy
import re
from pathlib import Path

import pytest

from escola_falsa import ESTRUTURA, aula, montar, questao
from escola import catalogo
from escola.catalogo import CatalogoInvalido, id_de


def test_junta_estrutura_e_materiais_com_o_foco_na_frente(tmp_path):
    cat = catalogo.carregar(montar(tmp_path))
    assert [c.id for c in cat.concursos] == ["mb", "eb"]
    etica = cat.assuntos["etica"]
    assert [i.titulo for i in etica.itens] == ["Aula 1", "Leitura 1", "Aula 9"]
    assert [i.titulo for i in etica.principais] == ["Aula 1", "Leitura 1"]
    assert len(cat.itens) == 6 and not cat.vazio
    assert cat.concurso("eb").assuntos() == ["etica", "social"] and cat.concurso("xx") is None


def test_id_sai_da_url_e_os_padroes(tmp_path):
    cat = catalogo.carregar(montar(tmp_path, materiais={
        "etica": [{"tipo": "leitura", "titulo": "X", "url": " https://a.b/x.pdf "}]}))
    item = cat.assuntos["etica"].itens[0]
    assert item.id == id_de("https://a.b/x.pdf") and item.url == "https://a.b/x.pdf"
    assert (item.minutos, item.idioma, item.extra, item.arquivo) == (20, "pt", False, None)


def test_url_repetida_no_mesmo_assunto_entra_uma_vez(tmp_path):
    cat = catalogo.carregar(montar(tmp_path, materiais={"etica": [aula(1), aula(1)]}))
    assert len(cat.assuntos["etica"].itens) == 1


def test_assunto_sem_material_nao_e_erro(tmp_path):
    cat = catalogo.carregar(montar(tmp_path, materiais={}))
    assert cat.vazio and cat.assuntos["social"].itens == ()


@pytest.mark.parametrize("materiais, erro", [
    ({"inexistente": [aula(1)]}, "assunto que não existe: inexistente"),
    ({"etica": [{"tipo": "podcast", "titulo": "X", "url": "https://a.b"}]}, "tipo 'podcast'"),
    ({"etica": [{"tipo": "aula", "titulo": "X", "url": "ftp://a.b"}]}, "URL inválida"),
    ({"etica": [{"tipo": "aula", "titulo": " ", "url": "https://a.b"}]}, "sem título"),
])
def test_material_quebrado_nao_carrega(tmp_path, materiais, erro):
    with pytest.raises(CatalogoInvalido, match=erro):
        catalogo.carregar(montar(tmp_path, materiais=materiais))


def test_materia_com_assunto_que_nao_existe_nao_carrega(tmp_path):
    estrutura = copy.deepcopy(ESTRUTURA)
    estrutura["concursos"][0]["materias"][0]["assuntos"].append("fantasma")
    with pytest.raises(CatalogoInvalido, match="eb › eb-psi: assunto que não existe: fantasma"):
        catalogo.carregar(montar(tmp_path, materiais={}, estrutura=estrutura))


def test_a_bibliografia_vai_para_o_concurso(tmp_path):
    cat = catalogo.carregar(montar(tmp_path))
    pago, codigo = cat.concurso("eb").bibliografia
    assert (pago.curta, pago.assuntos, pago.gratis) == ("Autor, Psicologia social", ("social",), None)
    assert codigo.referencia == "CFP, Código de Ética" and codigo.gratis == "https://site.cfp.org.br/l1.pdf"
    assert cat.concurso("mb").bibliografia == ()


@pytest.mark.parametrize("bibliografia, erro", [
    ({"fab": []}, "bibliografia de concurso que não existe: fab"),
    ({"mb": [{"curta": "X", "assuntos": ["social"]}]}, "assunto fora do concurso: social"),
    ({"mb": [{"curta": "X", "assuntos": []}]}, "assunto fora do concurso: nenhum"),
    ({"mb": [{"curta": " ", "assuntos": ["etica"]}]}, "livro sem nome"),
    ({"mb": [{"curta": "X", "assuntos": ["etica"], "gratis": "www.x.com"}]}, "URL inválida"),
])
def test_bibliografia_quebrada_nao_carrega(tmp_path, bibliografia, erro):
    with pytest.raises(CatalogoInvalido, match=erro):
        catalogo.carregar(montar(tmp_path, bibliografia=bibliografia))


def test_perguntas_de_fixacao_e_provinhas(tmp_path):
    cat = catalogo.carregar(montar(tmp_path))
    fixacao = cat.perguntas[id_de("https://www.youtube.com/watch?v=aula0000001")]
    assert [(q.enunciado, q.certa, q.trecho, q.onde) for q in fixacao] == \
        [("Pergunta 1?", 1, "o sigilo", 90), ("Pergunta 2?", 3, "a ética", None)]
    assert [(q.fonte, q.prova, q.certa) for q in cat.provinhas["mb-leg"]] ==         [("CP-T 2019, questão 1", "CP-T 2019", 1), ("CP-T 2019, questão 2", "CP-T 2019", 2)]
    assert len(cat.perguntas) == 1 and list(cat.provinhas) == ["mb-leg"]


def test_o_material_do_aquecimento(tmp_path):
    aq = catalogo.carregar(montar(tmp_path)).aquecimento[id_de("https://www.youtube.com/watch?v=aula0000001")]
    assert aq.resumo == "O sigilo protege o paciente."
    assert [(c.frente, c.verso, c.trecho, c.onde) for c in aq.cartoes] == \
        [("Frente 1?", "Verso 1.", "o sigilo", 90), ("Frente 2?", "Verso 2.", "a ética", None)]
    assert [(q.enunciado, q.certa) for q in aq.perguntas] == [("Pergunta 3?", 0)]


A1 = "https://www.youtube.com/watch?v=aula0000001"


@pytest.mark.parametrize("aquecimento, erro", [
    ({"https://nada.com/x": {"resumo": "r"}}, "item que não existe"),
    ({A1: {"resumo": " ", "cartoes": []}}, "sem o resumo"),
    ({A1: {"resumo": "r", "cartoes": [{"frente": "f", "verso": "v"}]}}, "cartão sem frente, verso ou trecho"),
    ({A1: {"resumo": "r", "cartoes": [{"frente": "f", "verso": "v", "trecho": "t", "onde": -1}]}}, "'onde'"),
    ({A1: {"resumo": "r", "perguntas": [questao(1)]}}, "sem o trecho"),
])
def test_aquecimento_quebrado_nao_carrega(tmp_path, aquecimento, erro):
    with pytest.raises(CatalogoInvalido, match=erro):
        catalogo.carregar(montar(tmp_path, aquecimento=aquecimento))


@pytest.mark.parametrize("perguntas, provinhas, erro", [
    ({"https://nada.com/x": [questao(1, trecho="t")]}, {}, "item que não existe"),
    ({"https://www.youtube.com/watch?v=aula0000001": [questao(1)]}, {}, "sem o trecho"),
    ({"https://www.youtube.com/watch?v=aula0000001": [questao(1, certa=4, trecho="t")]}, {}, "'certa'"),
    ({"https://www.youtube.com/watch?v=aula0000001": [{**questao(1, trecho="t"), "alternativas": ["a", "b", "c"]}]},
     {}, "4 ou 5 alternativas"),
    ({"https://www.youtube.com/watch?v=aula0000001": [questao(1, trecho="t", onde="1:30")]}, {}, "'onde'"),
    ({}, {"mb-leg": [questao(1, fonte="CP-T", url="https://p.pdf")]}, "sem fonte, prova, url ou gabarito"),
    ({}, {"mb-leg": [questao(1, fonte="CP-T 2019, questão 1", url="https://p.pdf", gabarito="https://g.pdf")]},
     "sem fonte, prova, url ou gabarito"),
    ({}, {"nada": []}, "matéria que não existe"),
])
def test_pergunta_quebrada_nao_carrega(tmp_path, perguntas, provinhas, erro):
    with pytest.raises(CatalogoInvalido, match=erro):
        catalogo.carregar(montar(tmp_path, perguntas=perguntas, provinhas=provinhas))


def test_youtube_acha_o_id_nos_formatos_comuns():
    assert catalogo.youtube("https://www.youtube.com/watch?v=abcdefghijk&t=10") == "abcdefghijk"
    assert catalogo.youtube("https://www.youtube.com/watch?feature=x&v=abcdefghijk") == "abcdefghijk"
    assert catalogo.youtube("https://youtu.be/abcdefghijk") == "abcdefghijk"
    assert catalogo.youtube("https://site.cfp.org.br/x.pdf") is None


def test_o_catalogo_de_verdade_carrega():
    cat = catalogo.carregar(Path(__file__).parents[1] / "escola")
    assert [c.id for c in cat.concursos] == ["smv", "cpt", "eaoap", "esfcex"]  # o temporário primeiro: prova em fev/2027
    assert len(cat.assuntos) == 81
    assert [len(c.bibliografia) for c in cat.concursos] == [5, 31, 0, 57]


def test_o_catalogo_de_verdade_nao_tem_acento_quebrado():
    # "ServiÃ§o" é UTF-8 lido como Latin-1; em 24/10 um bloco chegou assim
    quebrado = re.compile("[ÂÃ][\u0080-¿]")
    pasta = Path(__file__).parents[1] / "escola"
    for arq in [pasta / "estrutura.json", pasta / "bibliografia.json", *sorted((pasta / "materiais").glob("*.json")),
                *sorted((pasta / "perguntas").glob("*.json")), *sorted((pasta / "provinhas").glob("*.json")),
                *sorted((pasta / "aquecimento").glob("*.json"))]:
        assert not quebrado.search(arq.read_text(encoding="utf-8")), arq.name


def test_o_guia_mora_em_guias_e_o_id_sai_do_nome(tmp_path):
    pasta = montar(tmp_path, materiais={"etica": [aula(1), {"tipo": "guia", "titulo": "Guia: ética", "guia": "etica",
                                                            "minutos": 25}]})
    (pasta / "guias").mkdir()
    (pasta / "guias" / "etica.md").write_text("## O sigilo\n\nÉ a regra.\n", encoding="utf-8")
    cat = catalogo.carregar(pasta)
    guia = cat.assuntos["etica"].itens[1]
    assert (guia.tipo, guia.url, guia.id, guia.minutos) == ("guia", "guia:etica", id_de("guia:etica"), 25)
    assert cat.guias == {guia.id: "## O sigilo\n\nÉ a regra."}


@pytest.mark.parametrize("bruto, erro", [
    ({"tipo": "guia", "titulo": "Guia", "guia": "falta"}, "guia que falta: guias/falta.md"),
    ({"tipo": "guia", "titulo": "Guia", "guia": "../fora"}, "guia sem nome de arquivo válido"),
    ({"tipo": "guia", "titulo": "Guia"}, "guia sem nome de arquivo válido"),
    ({"tipo": "aula", "titulo": "X", "url": "guia:etica"}, "URL inválida"),
])
def test_guia_quebrado_nao_carrega(tmp_path, bruto, erro):
    with pytest.raises(CatalogoInvalido, match=erro):
        catalogo.carregar(montar(tmp_path, materiais={"etica": [bruto]}))
