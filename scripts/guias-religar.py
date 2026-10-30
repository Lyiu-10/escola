"""Reorganiza o Português do SMV depois da revisão de 29/10: cada assunto ganha o Guia, os itens que atrapalham viram
extra, e as questões que o material não ensina vão para o Guia (até TETO por guia; as outras ficam sem aula, no
aquecimento). Questão de item que ele já respondeu não muda de lugar.

Uso: python religar.py <pasta da revisão> [--gravar]"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "src")
from escola.catalogo import id_de  # noqa: E402

R = Path(sys.argv[1])
GRAVAR = "--gravar" in sys.argv
SO = sys.argv[sys.argv.index("--so") + 1].split(",") if "--so" in sys.argv else None
TETO = 12
RESPONDIDOS = {"f10111afc7c9", "c578181996f8", "bb2dabcab50c", "ddd2a0b1f602"}  # real:<item> em respostas

# Por assunto: a ordem final dos itens PRINCIPAIS (ids; "GUIA" é o guia novo) e os que passam a extra.
# Os que não aparecem em nenhuma das duas listas ficam como estão (os extras de antes).
PLANO = {
    "l-interpretacao": {"ordem": ["f10111afc7c9", "c578181996f8", "bb2dabcab50c", "GUIA"], "rebaixar": []},
    "l-ortografia": {"ordem": ["ddd2a0b1f602", "GUIA"], "rebaixar": ["9e2fa414a0ec"]},
    "l-classes": {"ordem": ["5cdaa96fe735", "d17be26bb0cc", "GUIA"], "rebaixar": []},
    "l-verbos": {"ordem": ["a75144d91dad", "GUIA"], "rebaixar": ["1ea31de9c521", "784247ca47b1"]},
    "l-periodo-simples": {"ordem": ["5ec41e2b0191", "26b00f105f72", "GUIA"], "rebaixar": []},
    "l-periodo-composto": {"ordem": ["59153f262bfd", "72e414f47997", "GUIA"], "rebaixar": []},
    "l-concordancia": {"ordem": ["401fd75c60dc", "GUIA"], "rebaixar": ["944c27bdca0a"]},
    "l-regencia": {"ordem": ["2624e77263fd", "GUIA"], "rebaixar": ["74c97a48f5e6"]},
    "l-crase": {"ordem": ["f5782a0587df", "GUIA"], "rebaixar": ["20f0dd00f26e"]},
    "l-pontuacao": {"ordem": ["8acf1fc17c2a", "GUIA"], "rebaixar": ["3b6c2173a397"]},
    "l-coesao": {"ordem": ["ead13bec290c", "202c1252391e", "GUIA"], "rebaixar": ["340d576258a7"]},
    "l-textualidade": {"ordem": ["7731b26e9ddc", "762c5ee978b1", "GUIA"], "rebaixar": ["d6fdf6fd5518", "af095ea69123"]},
    "l-significacao": {"ordem": ["82dd71ab90e8", "c568bae4a607", "GUIA"], "rebaixar": []},
    "l-estilistica": {"ordem": ["e7395faeb33a", "da9754b35a7e", "GUIA"], "rebaixar": []},
    "l-variacao": {"ordem": ["8fa7b429a457", "50ef5b4f2cdc", "GUIA"], "rebaixar": ["1f6fb32ec6a9"]},
}
if SO:
    PLANO = {a: p for a, p in PLANO.items() if a in SO}

# Avisos na nota de itens que ensinam algo errado ou fora do ponto (achados da revisão, conferidos no texto)
AVISOS = {
    "bb2dabcab50c": "Atenção: o texto diz que o tipo expositivo dá opinião. Não dá: o expositivo só informa; quem defende opinião é o argumentativo (o guia do assunto explica).",
    "d17be26bb0cc": "Comece pela página 3 (Resumo das classes); as páginas 1 e 2 são teoria que não cai. Atenção a dois erros do PDF: \"amar, sentir\" não são substantivos abstratos (amor, sentimento são), e \"conquanto\" é concessiva, não condicional.",
    "784247ca47b1": "Atenção: no vídeo, \"tenha trazido\" aparece como indicativo; é pretérito perfeito composto do subjuntivo. Veja antes o guia de verbos, que ensina os tempos.",
    "72e414f47997": "Atenção a um erro do texto: a oração adjetiva explicativa vem entre vírgulas (só a restritiva fica sem vírgula). O texto diz que nenhuma das duas tem vírgula.",
    "8acf1fc17c2a": "Os 6 primeiros minutos são recados da live: pode pular. Este vídeo não trata da vírgula (a professora deixou para outra live); a vírgula está completa no guia de pontuação, logo depois.",
    "da9754b35a7e": "Atenção a um erro no slide 11: metonímia é troca por proximidade (autor pela obra, parte pelo todo, causa pelo efeito), não por semelhança; semelhança é metáfora.",
    "ddd2a0b1f602": "A lista das terminações das paroxítonas passa rápido (por volta de 5:50); ela está inteira, em tabela, no guia de ortografia.",
}


def numero_de(fonte: str) -> tuple[str, int] | None:
    m = re.search(r"(SMV-OF \d{4}).*?quest[aã]o (\d+)", fonte)
    return (m[1], int(m[2])) if m else None


rev: dict[tuple[str, int], dict] = {}
for g in ("smv-1", "smv-2", "smv-3"):
    for a in json.load(open(R / f"saida/{g}.json", encoding="utf-8"))["assuntos"]:
        for q in a["questoes"]:
            if (k := numero_de(q["fonte"])):
                rev[k] = q

materiais_arq = Path("escola/materiais/portugues.json")
materiais = json.loads(materiais_arq.read_text(encoding="utf-8"))
url_de = {id_de(i["url"]): i["url"] for v in materiais.values() for i in v if "url" in i}
guias_meta = {aid: json.loads((R / "guias" / f"{aid}.json").read_text(encoding="utf-8"))
              for aid in PLANO if (R / "guias" / f"{aid}.json").is_file()}
faltam = [aid for aid in PLANO if aid not in guias_meta]
if faltam:
    print("AVISO: guias ainda não escritos:", ", ".join(faltam))

# 1. Materiais: guia na ordem, rebaixados viram extra, avisos nas notas
for aid, plano in PLANO.items():
    if aid not in guias_meta:
        continue
    itens = [i for i in materiais[aid] if i.get("tipo") != "guia"]
    por_id = {id_de(i["url"]): i for i in itens}
    meta = guias_meta[aid]
    guia = {"tipo": "guia", "titulo": meta["titulo"], "fonte": "Escola: resumo de tudo o que as provas do SMV-OF cobraram",
            "guia": aid, "minutos": int(meta["minutos"]), "idioma": "pt", "extra": False,
            "nota": "Escrito a partir de todas as questões reais deste assunto nas provas de 2016 a 2026. Leia na ordem; o índice no topo leva a cada parte."}
    novos = []
    for x in plano["ordem"]:
        if x == "GUIA":
            novos.append(guia)
        else:
            novos.append({**por_id[x], "extra": False})
    for i in itens:
        iid = id_de(i["url"])
        if iid in plano["ordem"]:
            continue
        novos.append({**i, "extra": True} if iid in plano["rebaixar"] else i)
    for i in novos:
        iid = id_de(i["url"]) if "url" in i else None
        if iid in AVISOS and AVISOS[iid] not in i.get("nota", ""):
            i["nota"] = f"{i.get('nota', '').rstrip()} {AVISOS[iid]}".strip()
    materiais[aid] = novos

principais = {aid: {(id_de(f"guia:{aid}") if x == "GUIA" else x) for x in p["ordem"]} for aid, p in PLANO.items()}

# 2. Questões: para onde vai cada uma
mudancas = []
por_guia: dict[str, list] = {}
arquivos = sorted(Path("escola/questoes").glob("smv-of-*.json"))
provas = {arq: json.loads(arq.read_text(encoding="utf-8")) for arq in arquivos}
for arq, d in provas.items():
    for q in d["questoes"]:
        aid = q.get("assunto")
        if q.get("anulada") or aid not in PLANO or aid not in guias_meta:
            continue
        atual = id_de(q["item"]) if q.get("item") else None
        r = rev.get((d["prova"], q["numero"]), {})
        cob = r.get("cobertura")
        destino = atual
        if atual in RESPONDIDOS:
            pass
        elif (m := r.get("mover_para")) and m in principais[aid] and m not in RESPONDIDOS and cob != "nao_ensina":
            destino = m
        elif atual and atual in principais[aid] and cob == "ensina":
            pass
        else:
            destino = "GUIA"
        if destino == "GUIA":
            por_guia.setdefault(aid, []).append((d["prova"], q, arq, atual, cob))
        elif destino != atual:
            mudancas.append((arq, q, destino, atual, cob))

# o guia recebe primeiro as que estavam numa aula (ele precisa delas), depois as sem aula, das mais novas às mais velhas
for aid, lista in por_guia.items():
    lista.sort(key=lambda t: (t[3] is None, -int(t[0][-4:])))
    for n, (prova, q, arq, atual, cob) in enumerate(lista):
        destino = id_de(f"guia:{aid}") if n < TETO else None
        if destino != atual:
            mudancas.append((arq, q, destino, atual, cob))

for arq, q, destino, atual, cob in mudancas:
    if destino and destino.startswith("guia") is False and destino in url_de:
        q["item"] = url_de[destino]
    elif destino == id_de(f"guia:{q['assunto']}"):
        q["item"] = f"guia:{q['assunto']}"
    elif destino is None:
        q["item"] = ""
    else:
        q["item"] = url_de.get(destino, q["item"])

# 3. Resumo
from collections import Counter, defaultdict  # noqa: E402
conta = defaultdict(Counter)
for d in provas.values():
    for q in d["questoes"]:
        if q.get("assunto") in PLANO and not q.get("anulada"):
            it = q.get("item") or "(sem aula)"
            conta[q["assunto"]][it if it.startswith("guia:") or it == "(sem aula)" else id_de(it)] += 1
for aid in PLANO:
    print(aid, dict(conta[aid]))
print(len(mudancas), "questões mudam de lugar")
vazios = [(aid, x) for aid, p in PLANO.items() for x in p["ordem"] if x != "GUIA" and conta[aid][x] == 0]
print("itens principais que ficam sem questão real (mostram a fixação feita por IA, se houver):", vazios)

sem_questao = {x for _, x in vazios}
lotes = {arq: json.loads(arq.read_text(encoding="utf-8")) for arq in sorted(Path("escola/perguntas").glob("*.json"))}
tirar = {arq: [u for u in lote if id_de(u) in sem_questao] for arq, lote in lotes.items()}
print("fixação por IA que sai:", {arq.name: len(us) for arq, us in tirar.items() if us})

if GRAVAR:
    for arq, us in tirar.items():
        if us:
            for u in us:
                del lotes[arq][u]
            arq.write_bytes((json.dumps(lotes[arq], ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    materiais_arq.write_bytes((json.dumps(materiais, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    for arq, d in provas.items():
        arq.write_bytes((json.dumps(d, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    print("gravado")
