"""Um catálogo pequeno da Escola para os testes: dois concursos que dividem o assunto "etica"."""
import json
from pathlib import Path

ESTRUTURA = {
    "concursos": [
        {"id": "eb", "nome": "Exército", "sigla": "EsFCEx", "cargo": "Psicologia", "foco": False,
         "prova": "50 questões", "requisitos": ["até 32 anos"], "proximo": "março",
         "edital": {"titulo": "Edital EB", "url": "https://eb.mil.br/edital.pdf", "arquivo": "editais/eb.pdf"},
         "materias": [{"id": "eb-psi", "nome": "Psicologia", "assuntos": ["etica", "social"]}]},
        {"id": "mb", "nome": "Marinha", "sigla": "CP-T", "cargo": "Psicologia", "foco": True,
         "prova": "50 questões e redação", "requisitos": ["menos de 35"], "proximo": "janeiro",
         "edital": {"titulo": "Edital MB", "url": "https://marinha.mil.br/edital.pdf"},
         "materias": [{"id": "mb-leg", "nome": "Legislação", "assuntos": ["etica"]},
                      {"id": "mb-clin", "nome": "Clínica", "assuntos": ["psicopatologia"]}]},
    ],
    "assuntos": {
        "etica": {"nome": "Código de Ética", "edital": "código de ética"},
        "psicopatologia": {"nome": "Psicopatologia", "edital": "exame psíquico"},
        "social": {"nome": "Psicologia social", "edital": "representações sociais"},
    },
}


def aula(n, minutos=20, **mais):
    return {"tipo": "aula", "titulo": f"Aula {n}", "fonte": "Canal", "minutos": minutos,
            "url": f"https://www.youtube.com/watch?v=aula{n:07d}", **mais}


def leitura(n, minutos=30, **mais):
    return {"tipo": "leitura", "titulo": f"Leitura {n}", "fonte": "CFP", "minutos": minutos,
            "url": f"https://site.cfp.org.br/l{n}.pdf", "arquivo": f"etica/l{n}.pdf", **mais}


# Caminho (Marinha em foco): Aula 1 (20), Leitura 1 (30), Aula 2 (40), Leitura 2 (30), Aula 3 (20)
MATERIAIS = {
    "etica": [aula(1), leitura(1), aula(9, extra=True, idioma="en")],
    "psicopatologia": [aula(2, minutos=40), leitura(2, arquivo="psicopatologia/l2.pdf")],
    "social": [aula(3)],
}


# O Exército indica um livro pago e o Código, que já é a Leitura 1 (abre dentro da Escola); a Marinha não indica nada
BIBLIOGRAFIA = {
    "eb": [{"referencia": "AUTOR. Psicologia social. Editora, 2020.", "curta": "Autor, Psicologia social",
            "editora": "Editora", "assuntos": ["social"], "gratis": None},
           {"curta": "CFP, Código de Ética", "editora": "CFP", "assuntos": ["etica"],
            "gratis": "https://site.cfp.org.br/l1.pdf"}],
}


def questao(n, certa=1, **mais):
    return {"enunciado": f"Pergunta {n}?", "alternativas": ["a", "b", "c", "d"], "certa": certa,
            "comentario": f"Porque sim ({n}).", **mais}


# A Aula 1 tem duas perguntas de fixação; a Legislação da Marinha tem uma provinha de duas questões
PERGUNTAS = {"https://www.youtube.com/watch?v=aula0000001": [questao(1, trecho="o sigilo", onde=90),
                                                              questao(2, certa=3, trecho="a ética")]}
# A Aula 1 tem o material do aquecimento: o resumo, dois cartões e uma pergunta a mais
AQUECIMENTO = {"https://www.youtube.com/watch?v=aula0000001": {
    "resumo": "O sigilo protege o paciente.",
    "cartoes": [{"frente": "Frente 1?", "verso": "Verso 1.", "trecho": "o sigilo", "onde": 90},
                {"frente": "Frente 2?", "verso": "Verso 2.", "trecho": "a ética"}],
    "perguntas": [questao(3, certa=0, trecho="o sigilo", onde=90)]}}
PROVINHAS = {"mb-leg": [questao(n, certa=n % 4, fonte=f"CP-T 2019, questão {n}", prova="CP-T 2019", url="https://prova.pdf",
                                gabarito="https://gabarito.pdf") for n in (1, 2)]}


def montar(pasta: Path, materiais=None, estrutura=None, bibliografia=None, perguntas=None, provinhas=None,
           aquecimento=None, questoes=None, estilo=None) -> Path:
    (pasta / "materiais").mkdir(parents=True, exist_ok=True)
    (pasta / "estrutura.json").write_text(json.dumps(estrutura or ESTRUTURA), encoding="utf-8")
    (pasta / "materiais" / "bloco.json").write_text(
        json.dumps(MATERIAIS if materiais is None else materiais), encoding="utf-8")
    (pasta / "bibliografia.json").write_text(
        json.dumps(BIBLIOGRAFIA if bibliografia is None else bibliografia), encoding="utf-8")
    (pasta / "perguntas").mkdir(exist_ok=True)
    (pasta / "perguntas" / "bloco.json").write_text(
        json.dumps(PERGUNTAS if perguntas is None and materiais is None else perguntas or {}), encoding="utf-8")
    (pasta / "aquecimento").mkdir(exist_ok=True)
    (pasta / "aquecimento" / "bloco.json").write_text(
        json.dumps(AQUECIMENTO if aquecimento is None and materiais is None else aquecimento or {}), encoding="utf-8")
    (pasta / "provinhas").mkdir(exist_ok=True)
    for mid, qs in (PROVINHAS if provinhas is None else provinhas).items():
        (pasta / "provinhas" / f"{mid}.json").write_text(json.dumps(qs), encoding="utf-8")
    (pasta / "questoes").mkdir(exist_ok=True)
    for nome, prova in (questoes or {}).items():
        (pasta / "questoes" / f"{nome}.json").write_text(json.dumps(prova), encoding="utf-8")
    (pasta / "estilo").mkdir(exist_ok=True)
    (pasta / "estilo" / "bloco.json").write_text(json.dumps(estilo or {}), encoding="utf-8")
    return pasta


# O catálogo particular (Documentos/Escola/particular): um concurso só da Ana, com uma aula que abre fora e um PDF
PARTICULAR = {
    "perfis": ["ana"],
    "concursos": [{"id": "enem", "nome": "ENEM (Cursinho)", "sigla": "ENEM",
                   "materias": [{"id": "enem-bio", "nome": "Biologia", "assuntos": ["enem-bio-u1"]}]}],
    "assuntos": {"enem-bio-u1": {"nome": "Unidade 1: Origem da vida"}},
}
MATERIAIS_PARTICULARES = {"enem-bio-u1": [
    {"tipo": "aula", "titulo": "Teorias de evolução", "fonte": "Cursinho", "minutos": 12,
     "url": "https://cursinho.example/units/U1/blocks/B1", "nota": "Você já concluiu no Cursinho."},
    {"tipo": "leitura", "titulo": "Material Complementar", "fonte": "Cursinho", "minutos": 15,
     "url": "https://cursinho.example/units/U1/blocks/B2", "arquivo": "cursinho/bio-u1.pdf"},
], "etica": [  # num assunto do catálogo: uma aula no caminho da Ana e uma a mais
    {"tipo": "aula", "titulo": "Ética no Cursinho", "fonte": "Cursinho", "minutos": 10,
     "url": "https://cursinho.example/units/U9/blocks/B8"},
    {"tipo": "aula", "titulo": "Ética no Cursinho, a mais", "fonte": "Cursinho", "minutos": 10, "extra": True,
     "url": "https://cursinho.example/units/U9/blocks/B9"},
]}


def montar_particular(pasta: Path, estrutura=None, materiais=None) -> Path:
    (pasta / "materiais").mkdir(parents=True, exist_ok=True)
    (pasta / "estrutura.json").write_text(json.dumps(estrutura or PARTICULAR), encoding="utf-8")
    (pasta / "materiais" / "cursinho.json").write_text(json.dumps(materiais or MATERIAIS_PARTICULARES), encoding="utf-8")
    (pasta / "arquivos" / "cursinho").mkdir(parents=True, exist_ok=True)
    (pasta / "arquivos" / "cursinho" / "bio-u1.pdf").write_bytes(b"%PDF-1.4 particular")
    return pasta
