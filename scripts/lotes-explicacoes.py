r"""Os lotes da explicação das erradas (escola/explicacoes/*.json) para agentes escreverem: as questões de um concurso,
na ordem do caminho (as da aula, as que sobram no assunto e a provinha no fim da matéria), que ainda não têm por que
cada alternativa errada está errada. Escreve também o brief.txt dos agentes, e confere o que eles escreveram.

Uso: .venv\Scripts\python.exe -X utf8 scripts\lotes-explicacoes.py [concurso] [tamanho]   (cpt, 75)
     .venv\Scripts\python.exe -X utf8 scripts\lotes-explicacoes.py conferir lote-NN
Depois, um agente por lote: "Leia <pasta>\brief.txt e siga; o seu lote é lote-NN". Confira cada lote com o
`conferir` e leia uma amostra antes do commit.
"""
import json
import sys
import tempfile
from pathlib import Path

from escola import caminho, catalogo

REPO = Path(__file__).parents[1]
PASTA = Path(tempfile.gettempdir()) / "explicacoes-lotes"
SAIDA = REPO / "escola" / "explicacoes"
PALAVRAS = 50  # por explicação: cabe embaixo da alternativa sem virar um parágrafo
LETRAS = "ABCDE"

BRIEF = r"""Você vai escrever, para a Escola (a plataforma de estudo que roda no PC do Péricles, que estuda para o CP-T, o concurso de oficial psicólogo da Marinha, e para o SMV-OF, de oficial temporário, com prova só de Português), POR QUE CADA ALTERNATIVA ERRADA ESTÁ ERRADA, em questões de múltipla escolha.

O pedido dele: depois de responder, a correção já mostra qual é a certa e por que ela é certa (o `comentario`). "Mas eu queria saber por que a minha está errada, o que na minha está errado, para entender legal." Quando ele erra, a Escola vai mostrar, embaixo da alternativa que ele marcou, a sua explicação dela. Ela também aparece, para quem quiser, embaixo de cada outra alternativa errada.

SEU LOTE: `{PASTA}\{LOTE}.json`. Cada questão tem: `chave` (a chave no arquivo de saída; copie exatamente), `origem` (a prova de onde veio, ex.: "CP-T 2019", ou "feita a partir da aula" / "no estilo do CP-T"), `assunto`, `texto` (o texto-base, quando há), `enunciado`, `alternativas` (com a letra na frente), `certa` (a letra do gabarito oficial) e `comentario` (por que a certa é certa). As feitas a partir de uma aula trazem também `trecho`: a passagem do material em que a resposta se apoia.

O QUE ESCREVER, para cada questão: uma explicação para cada alternativa ERRADA; para a certa, null.
- 1 ou 2 frases, até 45 palavras, em português do Brasil, texto simples (sem markdown, sem aspas de enfeite).
- Diga o que exatamente está errado NAQUELA alternativa: o termo trocado, o autor errado, o conceito invertido, a etapa fora de ordem, o prazo ou o número errado, a generalização indevida ("sempre", "somente"). E diga o que seria o certo. Ex.: "Empatia condicional contradiz a teoria: para Rogers, a aceitação do cliente é incondicional. Associação livre é técnica da psicanálise."
- Comece direto pelo conteúdo. Nada de "Esta alternativa está errada porque", "Errada:", "Incorreta.", nem repetir a alternativa inteira.
- Cada explicação precisa se entender sozinha: ele vai ler só a da alternativa que marcou.
- Não repita o comentário da certa; pode apoiar-se nele.

CASOS QUE PEDEM CUIDADO:
- Enunciado que pede a INCORRETA, a que NÃO é, EXCETO: a certa é a afirmação falsa, e as outras alternativas são verdadeiras. A explicação delas diz por que não são a resposta: "Está correta: [o fundamento]. A questão pede a incorreta."
- Sequência de V e F, ou "I, II e III": diga em que item a alternativa erra e por quê. Ex.: "Erra o item II: Spector diz que o questionário é o meio mais barato, então II é verdadeiro."
- Questão de texto (texto-base): apoie-se no texto ("o texto diz...", "no 2º parágrafo..."), mas não copie trechos dele: cite no máximo uma expressão curta (até 10 palavras). Texto de jornal, poema ou letra copiado em trecho longo faz o modelo ser bloqueado.
- Questões feitas a partir da aula (com `trecho`): apoie-se no trecho e no comentário; as erradas foram escritas como erros típicos de quem estudou mal.

O GABARITO OFICIAL MANDA: explique de acordo com a `certa`, mesmo que você ache discutível. Não escreva dúvida no texto; se achar que o gabarito está errado ou que a questão está desatualizada, liste no relatório (a chave, o porquê).

NÃO INVENTE: número de lei, artigo, ano, página, nome de autor ou de teste que você não tenha certeza. Se o motivo depende de um número de que você não tem certeza, explique pelo conceito, sem o número. Prefira a explicação curta e certa à completa e duvidosa.

SAÍDA: escreva `C:\Users\peric\Desktop\Projetos\escola\escola\explicacoes\{LOTE}.json` (UTF-8, indentação 1):
{
 "<chave>": ["explicação da A", null, "explicação da C", "explicação da D"]
}
Uma lista por questão, com tantas posições quantas alternativas (4 ou 5), na ordem delas, e null na certa. Todas as questões do lote.

CONFERÊNCIA (obrigatória): no diretório `C:\Users\peric\Desktop\Projetos\escola`, rode `.venv/Scripts/python.exe -X utf8 scripts/lotes-explicacoes.py conferir {LOTE}` e corrija o que ele apontar (chave que falta ou sobra, lista do tamanho errado, null fora da certa, explicação vazia ou longa demais). Repita até ele dizer "ok".

NÃO FAÇA: não edite nenhum outro arquivo (há outros agentes escrevendo outros lotes em paralelo), não faça commit, não use internet.

RELATÓRIO FINAL (curto, em português): quantas questões explicadas; as que você acha que têm gabarito discutível ou conteúdo desatualizado (chave, origem e o porquê, uma linha cada); e o resultado da conferência.
"""


def questoes_do_concurso(cat: catalogo.Catalogo, c: catalogo.Concurso) -> list[tuple[catalogo.Questao, str, str]]:
    """(questão, de onde veio, assunto) na ordem em que ele as encontra: as da aula, as que sobram no assunto quando
    ele aparece pela primeira vez, a provinha da matéria depois do último item dela e as do simulado, na prova."""
    lista, vistos = [], set()
    passos = caminho.sequencia(cat, c)
    for n, p in enumerate(passos):
        iid = p.item.id
        if iid in cat.simulados:
            lista += [(q, f"{q.prova} (simulado)", cat.assuntos[q.assunto].nome) for q in cat.simulados[iid]]
        elif iid in cat.reais:
            lista += [(q, q.prova, p.assunto.nome) for q in cat.reais[iid]]
        elif iid in cat.estilo:
            lista += [(q, f"no estilo do {q.estilo}", p.assunto.nome) for q in cat.estilo[iid]]
        else:
            lista += [(q, "feita a partir da aula", p.assunto.nome) for q in cat.perguntas.get(iid, ())]
        if p.assunto.id not in vistos:
            vistos.add(p.assunto.id)
            lista += [(q, q.prova, p.assunto.nome) for q in cat.extras.get(p.assunto.id, ())]
        if n + 1 == len(passos) or passos[n + 1].materia.id != p.materia.id:
            lista += [(q, q.prova, p.materia.nome) for q in cat.provinhas.get(p.materia.id, ())]
    unicas = {}
    for q, origem, assunto in lista:
        unicas.setdefault(q.chave, (q, origem, assunto))
    return list(unicas.values())


def montar(cid: str, tamanho: int) -> None:
    cat = catalogo.carregar(REPO / "escola")
    c = cat.concurso(cid)
    faltam = [x for x in questoes_do_concurso(cat, c) if x[0].chave not in cat.erradas]
    PASTA.mkdir(exist_ok=True)
    (PASTA / "brief.txt").write_text(BRIEF.replace("{PASTA}", str(PASTA)), encoding="utf-8")
    feitos = [int(f.stem[5:]) for f in [*SAIDA.glob("lote-*.json"), *PASTA.glob("lote-*.json")]]
    numero = max(feitos, default=0)
    for k in range(0, len(faltam), tamanho):
        numero += 1
        lote = f"lote-{numero:02d}"
        questoes = [{"chave": q.chave, "origem": origem, "assunto": assunto, **({"texto": q.texto} if q.texto else {}),
                     "enunciado": q.enunciado, "alternativas": [f"{LETRAS[n]}) {a}" for n, a in enumerate(q.alternativas)],
                     "certa": LETRAS[q.certa], "comentario": q.comentario, **({"trecho": q.trecho} if q.trecho else {})}
                    for q, origem, assunto in faltam[k:k + tamanho]]
        (PASTA / f"{lote}.json").write_text(json.dumps({"lote": lote, "saida": f"escola/explicacoes/{lote}.json",
                                                        "questoes": questoes}, ensure_ascii=False, indent=1),
                                            encoding="utf-8")
        print(lote, len(questoes), "questões |", questoes[0]["assunto"][:40], "→", questoes[-1]["assunto"][:40])
    print(f"{len(faltam)} questões do {c.sigla} sem a explicação das erradas; brief em {PASTA / 'brief.txt'}")


def conferir(lote: str) -> None:
    manifesto = json.loads((PASTA / f"{lote}.json").read_text(encoding="utf-8"))
    arq = SAIDA / f"{lote}.json"
    if not arq.is_file():
        sys.exit(f"falta o arquivo {arq}")
    try:
        escrito = json.loads(arq.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"JSON inválido em {arq}: {e}")
    esperadas = {q["chave"]: q for q in manifesto["questoes"]}
    erros = [f"chave que não é do lote: {k}" for k in escrito if k not in esperadas]
    for chave, q in esperadas.items():
        lista = escrito.get(chave)
        certa = LETRAS.index(q["certa"])
        if lista is None:
            erros.append(f"falta a questão {chave} ({q['enunciado'][:50]})")
        elif not isinstance(lista, list) or len(lista) != len(q["alternativas"]):
            erros.append(f"{chave}: são {len(q['alternativas'])} posições, uma por alternativa")
        elif lista[certa] is not None:
            erros.append(f"{chave}: a posição da certa ({q['certa']}) é null")
        else:
            for n, t in enumerate(lista):
                if n == certa:
                    continue
                if not isinstance(t, str) or not t.strip():
                    erros.append(f"{chave}: a {LETRAS[n]} está sem explicação")
                elif len(t.split()) > PALAVRAS:
                    erros.append(f"{chave}: a {LETRAS[n]} tem {len(t.split())} palavras (até 45)")
                elif t.strip().lower().startswith(("esta alternativa", "errada", "incorreta", "alternativa")):
                    erros.append(f"{chave}: a {LETRAS[n]} começa com rodeio; comece pelo conteúdo")
    print("\n".join(erros) if erros else f"ok: {len(esperadas)} questões")


if __name__ == "__main__":
    if sys.argv[1:2] == ["conferir"]:
        conferir(sys.argv[2])
    else:
        montar(sys.argv[1] if len(sys.argv) > 1 else "cpt", int(sys.argv[2]) if len(sys.argv) > 2 else 75)
