"""Divide os guias longos em partes de 10 a 20 min de leitura, cada uma com as suas questões reais.

Uso: python scripts/guias-dividir.py [guia ...] [--aplicar]   (sem --aplicar, só mostra o que faria)
Roda na raiz do projeto escola. Sem nome de guia, divide todos os do SPEC: rode só uma vez por guia, porque a
parte 1 sobrescreve o arquivo original. Feito em 29/10/2026 (os sete primeiros) e logo depois a Pontuação.
"""
import json
import re
import sys
from pathlib import Path

APLICAR = "--aplicar" in sys.argv
GUIAS = Path("escola/guias")
MATERIAL = Path("escola/materiais/portugues.json")

SPEC = {
    "l-interpretacao": [
        dict(nome="l-interpretacao", titulo="Guia: Interpretação, o método",
             secoes=["O método de base", "Ideia central", "Explícito", "NÃO, EXCETO", "Afirmativas", "Comparar"],
             bullets=[0, 1, 2, 3]),
        dict(nome="l-interpretacao-2", titulo="Guia: Intenção, tom e referência",
             intro="Parte 2 de 3 do guia de Interpretação: o propósito do autor, o tom, quem fala, a referência e o sentido figurado. A parte 1 foi o método.",
             secoes=["Propósito", "Quem fala", "Sentido figurado", "Provérbios"],
             bullets=["Propósito é o que o autor quer causar: imperativo orienta, perguntas ao leitor fazem refletir, tirada final diverte, tese com argumentos convence.",
                      "Ironia só existe quando o contexto mostra o contrário do que foi dito.",
                      "Referência: volte ao trecho anterior e troque o termo pelo candidato. O demonstrativo pode marcar distância afetiva (\"Aquilo\"), não física.",
                      "Símbolo: entre duas opções parecidas, fique com a que repete a ênfase do texto.",
                      7]),
        dict(nome="l-interpretacao-3", titulo="Guia: Tipos e gêneros textuais",
             intro="Parte 3 de 3 do guia de Interpretação: tipos e gêneros textuais, literário e não literário, texto verbal, não verbal e misto, e tipos de argumento.",
             secoes=["Tipos textuais", "Gêneros textuais", "Literário", "Texto verbal", "Tipos de argumento"],
             bullets=[4, 5, 6]),
    ],
    "l-ortografia": [
        dict(nome="l-ortografia", titulo="Guia: Acentuação",
             secoes=["O que a banca cobra", "1. ", "2. ", "3. ", "4. ", "5. ", "6. ", "7. ", "8. "],
             bullets=[0, 1, 2, 3]),
        dict(nome="l-ortografia-2", titulo="Guia: Hífen, grafia e maiúsculas",
             intro="Parte 2 de 2 do guia de Ortografia: hífen, letras de mesmo som, porquês, pares parecidos e maiúsculas. A parte 1 foi a acentuação.",
             secoes=["9. ", "10. ", "11. ", "12. ", "13. ", "14. ", "15. ", "16. "],
             bullets=[4, 5, 6, 7]),
    ],
    "l-classes": [
        dict(nome="l-classes", titulo="Guia: Classes, o “que” e o “se”",
             secoes=["As 10 classes", "Os usos do \"que\"", "Os usos do \"se\""],
             bullets=[0, 1, 2]),
        dict(nome="l-classes-2", titulo="Guia: Flexão nominal e mudança de classe",
             intro="Parte 2 de 3 do guia de Classes de palavras: plural, gênero e grau dos nomes, e a mudança de classe pela posição. A parte 1 foi a tabela das classes e os usos do “que” e do “se”.",
             secoes=["Flexão nominal: o plural", "Flexão nominal: o gênero", "Flexão nominal: o grau", "Posição do adjetivo"],
             bullets=[3, 4, 5, 6, "\"Certa dose\" é pronome; \"dose certa\" é adjetivo."]),
        dict(nome="l-classes-3", titulo="Guia: Pronomes, advérbios e preposições",
             intro="Parte 3 de 3 do guia de Classes de palavras: pronomes, advérbios, palavras denotativas, preposições e as conjunções que já caíram aqui.",
             secoes=["Pronomes", "Advérbios", "Preposições", "Conjunções que"],
             bullets=["Objeto direto vira o, a (lo, la depois de -r, -s, -z: equilibrá-la); objeto indireto de pessoa vira lhe. \"Vi-lhe\" e \"encontrou-lhe\" estão errados.",
                      "Este: o que vai ser dito; esse: o que já foi dito; aquele: o mais afastado de dois termos.",
                      "\"Meio\" antes de adjetivo é advérbio e não varia. \"Até\" (= inclusive) e \"também\" são inclusão; \"só\" e \"apenas\", exclusão.",
                      "Preposição: pergunte o que ela responde. Para quê? finalidade. Por quê? causa. Com quê? instrumento.",
                      "Sujeito de infinitivo não contrai: \"depois de as girafas aparecerem\"."]),
    ],
    "l-verbos": [
        dict(nome="l-verbos", titulo="Guia: Verbos, formas e grafia",
             secoes=["1. ", "2. ", "3. "],
             bullets=[0, 1, 2, 7]),
        dict(nome="l-verbos-2", titulo="Guia: Verbos, correlação, imperativo e voz",
             intro="Parte 2 de 2 do guia de Verbos: correlação de tempos, infinitivo e futuro do subjuntivo, imperativo, voz, locução e classificação. A parte 1 foi modos, tempos, irregulares e grafia.",
             secoes=["4. ", "5. ", "6. ", "7. ", "8. ", "9. "],
             bullets=[3, 4, 5, 6]),
    ],
    "l-periodo-simples": [
        dict(nome="l-periodo-simples", titulo="Guia: Os termos da oração e o sujeito",
             secoes=["1. ", "2. ", "3. ", "4. "],
             bullets=[0, 1, 2, 3, 4]),
        dict(nome="l-periodo-simples-2", titulo="Guia: Ordem, transitividade, aposto e vocativo",
             intro="Parte 2 de 2 do guia de Período simples: ordem direta e inversa, transitividade, aposto e vocativo, e os papéis do “se” e do “que”. A parte 1 foi os termos da oração e o sujeito.",
             secoes=["5. ", "6. ", "7. ", "8. ", "9. ", "10. "],
             bullets=[5, 6, 7]),
    ],
    "l-periodo-composto": [
        dict(nome="l-periodo-composto", titulo="Guia: Adverbiais e o valor das conjunções",
             secoes=["O básico", "As adverbiais", "Conjunções com mais de um valor", "Como cai: o valor da conjunção"],
             bullets=[0, 6,
                      "Causa provoca; consequência é o resultado de uma intensidade (tão, tanto... que); concessão é um fato contrário que não impede: troque por \"embora\".",
                      "Conclusão (logo, portanto) é coordenada, nunca subordinada."]),
        dict(nome="l-periodo-composto-2", titulo="Guia: Substantivas, adjetivas e coordenadas",
             intro="Parte 2 de 2 do guia de Período composto: orações substantivas, adjetivas (com os pronomes relativos), coordenadas e reduzidas. A parte 1 foi as adverbiais e o valor das conjunções.",
             secoes=["As substantivas", "As adjetivas", "As coordenadas", "Orações reduzidas", "Como cai: classificar"],
             bullets=[1, 2, 3, 4, 5, 7]),
    ],
    "l-significacao": [
        dict(nome="l-significacao", titulo="Guia: Sentido pelo contexto e conotação",
             secoes=["1. ", "2. "],
             bullets=[0, 1, 2, 3, 4]),
        dict(nome="l-significacao-2", titulo="Guia: Relações entre palavras e intertextualidade",
             intro="Parte 2 de 2 do guia de Significação: hiperonímia, homonímia e paronímia, ambiguidade e intertextualidade. A parte 1 foi o sentido pelo contexto e a conotação.",
             secoes=["3. ", "4. ", "5. "],
             bullets=[5, 6, 7]),
    ],
    "l-pontuacao": [
        dict(nome="l-pontuacao", titulo="Guia: A vírgula",
             secoes=["O que a banca cobra", "A vírgula: a regra-mãe", "Os usos da vírgula", "Como cai: vírgula"],
             bullets=[0, 1, 2, 3, 4, 5]),
        dict(nome="l-pontuacao-2", titulo="Guia: Dois-pontos, travessão e outros sinais",
             intro="Parte 2 de 2 do guia de Pontuação: dois-pontos, ponto e vírgula, travessão, parênteses, aspas e reticências. A parte 1 foi a vírgula.",
             secoes=["Dois-pontos", "Ponto e vírgula", "Travessão", "Parênteses", "Aspas", "Reticências", "Como cai: outros sinais"],
             bullets=[6, 7]),
    ],
}
ALVO = [a for a in sys.argv[1:] if not a.startswith("--")] or list(SPEC)

# Questão sem citação no guia: a parte vem daqui, pelo conteúdo que a resolve.
MANUAL = {("2018", 13): "l-ortografia-2", ("2020", 24): "l-verbos-2", ("2025", 33): "l-periodo-composto-2",
          ("2021", 21): "l-pontuacao-2"}


def partes_do(md):
    """[(titulo do ##, texto)], com o texto antes do primeiro ## como titulo ''."""
    blocos = re.split(r"(?m)^(?=## )", md)
    out = []
    for b in blocos:
        if not b.strip():
            continue
        if b.startswith("## "):
            out.append((b.splitlines()[0][3:].strip(), b.rstrip() + "\n"))
        else:
            out.append(("", b.rstrip() + "\n"))
    return out


def palavras(texto):
    return len(re.findall(r"\w+", texto))


def minutos(texto):
    return max(10, int(round(len(re.findall(r"\w+", texto)) / 105 / 5)) * 5)


questoes = {}
for f in sorted(Path("escola/questoes").glob("smv-of-*.json")):
    for q in json.loads(f.read_bytes().decode("utf-8"))["questoes"]:
        if q.get("item", "").removeprefix("guia:") in ALVO:
            questoes[(f.stem[-4:], q["numero"])] = q["item"].removeprefix("guia:")

novos = {}   # nome -> (titulo, texto, minutos)
destino = {}  # (ano, numero) -> nome da parte
for guia, partes in ((g, SPEC[g]) for g in ALVO):
    md = (GUIAS / f"{guia}.md").read_bytes().decode("utf-8").replace("\r", "")
    secs = partes_do(md)
    resumo = next(t for n, t in secs if n == "Em 1 minuto")
    balas = [l[2:] for l in resumo.splitlines() if l.startswith("- ")]
    fontes = next(t for n, t in secs if n == "Fontes")
    usadas = set()
    for k, p in enumerate(partes):
        corpo = []
        if k == 0:
            corpo += [t for n, t in secs if n == ""]
        else:
            corpo.append(p["intro"] + "\n")
        for pref in p["secoes"]:
            achou = [(n, t) for n, t in secs if n.startswith(pref)]
            assert len(achou) == 1, (guia, pref, [n for n, _ in achou])
            usadas.add(achou[0][0])
            corpo.append(achou[0][1])
        lista = [balas[b] if isinstance(b, int) else b for b in p["bullets"]]
        corpo.append("## Em 1 minuto\n\n" + "".join(f"- {b}\n" for b in lista))
        corpo.append(fontes)
        texto = "\n".join(c.rstrip() + "\n" for c in corpo)
        novos[p["nome"]] = (p["titulo"], texto, minutos(texto))
        # a questão vai para a parte que a cita
        for (ano, num), g in questoes.items():
            if g != guia:
                continue
            if re.search(rf"SMV-OF {ano}, quest(?:ão|ões) (?:\d+(?:, | e ))*{num}\b", "\n".join(t for n, t in secs if n in [x for x in usadas] and any(n.startswith(pp) for pp in p["secoes"]))):
                destino[(ano, num)] = p["nome"]  # citada em duas partes: vale a última
    faltam = {n for n, _ in secs if n not in usadas and n not in ("", "Em 1 minuto", "Fontes")}
    assert not faltam, (guia, faltam)
    usadas_b = [b for p in partes for b in p["bullets"] if isinstance(b, int)]
    # o 8º de Classes foi reescrito em duas balas novas (uma na parte 2, outra na 3)
    esperado = [b for b in range(len(balas)) if not (guia == "l-classes" and b == 7)]
    assert sorted(usadas_b) == esperado, (guia, usadas_b, len(balas))

for chave, g in questoes.items():
    if chave in MANUAL and MANUAL[chave].rsplit("-", 1)[0] in ALVO:
        destino[chave] = MANUAL[chave]
    destino.setdefault(chave, g)  # sem citação: fica na parte 1

for nome, (titulo, texto, m) in novos.items():
    n = sum(1 for d in destino.values() if d == nome)
    print(f"{nome:22} {m:3} min  {n:2} questões  {palavras(texto):5} palavras  {titulo}")
for chave in sorted(questoes):
    if destino[chave] != questoes[chave]:
        print("  move", chave, "->", destino[chave])

if APLICAR:
    for nome, (titulo, texto, m) in novos.items():
        (GUIAS / f"{nome}.md").write_bytes(texto.encode("utf-8"))
    dados = json.loads(MATERIAL.read_bytes().decode("utf-8"))
    for aid, itens in dados.items():
        saida = []
        for i in itens:
            if i.get("tipo") == "guia" and i["guia"] in ALVO:
                for p in SPEC[i["guia"]]:
                    titulo, texto, m = novos[p["nome"]]
                    saida.append({**i, "titulo": titulo, "guia": p["nome"], "minutos": m})
            else:
                saida.append(i)
        dados[aid] = saida
    MATERIAL.write_bytes((json.dumps(dados, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    for f in sorted(Path("escola/questoes").glob("smv-of-*.json")):
        d = json.loads(f.read_bytes().decode("utf-8"))
        mudou = False
        for q in d["questoes"]:
            chave = (f.stem[-4:], q["numero"])
            if chave in destino and q["item"] != f"guia:{destino[chave]}":
                q["item"] = f"guia:{destino[chave]}"
                mudou = True
        if mudou:
            f.write_bytes((json.dumps(d, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    print("aplicado")
