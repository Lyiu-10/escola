"""Para cada assunto do SMV, o pacote do redator do guia: o que o edital pede, a revisão do assunto e TODAS as
questões reais do assunto (aulas, sem aula e simulados), com gabarito e comentário."""
import sys, json
from pathlib import Path
sys.path.insert(0, "src")
from escola.catalogo import carregar
R = Path(sys.argv[1])
cat = carregar(Path("escola"))
L = "ABCDE"
rev = {}
for g in ("smv-1", "smv-2", "smv-3"):
    for a in json.load(open(R / f"saida/{g}.json", encoding="utf-8"))["assuntos"]:
        rev[a["id"]] = a
brutas = []
for arq in sorted(Path("escola/questoes").glob("smv-*.json")) + sorted(Path("escola/simulados").glob("smv-*.json")):
    d = json.loads(arq.read_text(encoding="utf-8"))
    for q in d["questoes"]:
        if q.get("anulada") or not q.get("assunto"):
            continue
        brutas.append((d["prova"], arq.parent.name, q))
ordem = cat.concurso("smv").materias[0].assuntos
for aid in ordem:
    a = cat.assuntos[aid]
    r = rev[aid]
    qs = [(p, onde, q) for p, onde, q in brutas if q["assunto"] == aid]
    precisa = {x["fonte"]: x for x in r["questoes"]}
    out = [f"# Pacote do guia: {aid} — {a.nome}", "",
           f"Posição no curso: assunto {ordem.index(aid) + 1} de {len(ordem)}. Antes dele vêm: {', '.join(cat.assuntos[x].nome for x in ordem[:ordem.index(aid)]) or 'nada'}.",
           f"Depois dele vêm: {', '.join(cat.assuntos[x].nome for x in ordem[ordem.index(aid) + 1:]) or 'nada'}.", "",
           "## O que o edital pede", a.edital, "",
           "## O que a revisão achou (o material atual e o que falta)",
           f"Veredito: {r['veredito']}. {r['resumo']}", f"Edital: {r['edital']}", f"Ordem: {r['ordem']}", "",
           "Melhorias pedidas pelo revisor:"]
    out += [f"- ({m['prioridade']}) {m['o_que']} — {m['por_que']}" for m in r["melhorias"]]
    out += ["", "O que cada questão exige, segundo o revisor (fonte → exige):"]
    out += [f"- {x['fonte']} → {x['precisa']}" + (f" [PROBLEMA APONTADO: {x['problema']}]" if x.get("problema") not in (None, "", "null") else "") for x in r["questoes"]]
    out += ["", f"## Todas as questões reais deste assunto ({len(qs)}), das provas do SMV-OF", ""]
    textos = {}
    for prova, onde, q in qs:
        out.append(f"### {prova}, questão {q['numero']} ({'simulado' if onde == 'simulados' else 'aula'})")
        t = (q.get("texto") or "").strip()
        if t:
            if t not in textos:
                textos[t] = len(textos) + 1
                out.append(f"TEXTO-BASE #{textos[t]}:\n{t}\n")
            else:
                out.append(f"(texto-base #{textos[t]}, já mostrado)")
        out.append(q["enunciado"])
        for k, alt in enumerate(q["alternativas"]):
            out.append(f"  {L[k]}) {alt}{'  <= GABARITO' if k == q['certa'] else ''}")
        out.append(f"  Comentário: {q['comentario']}")
        if q.get("concorda") is False and q.get("discorda"):
            out.append(f"  Ressalva: {q['discorda']}")
        out.append("")
    (R / "guias-in" / f"{aid}.md").write_text("\n".join(out), encoding="utf-8")
    print(aid, len(qs), "questões,", len("\n".join(out)) // 1024, "KB")
