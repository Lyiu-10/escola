"""Junta as provas transcritas e a classificação delas em escola/questoes/<prova>.json e distribui as questões pelas
aulas: no máximo POR_AULA em cada uma, da prova mais nova para a mais antiga. A que sobra numa aula, ou que não tem
aula mas tem assunto, vai para o aquecimento (sem `item`). Questão que já está numa provinha fica de fora.

Com --outra-banca (provas de outras bancas, como a FGV), a questão só entra numa aula que ainda não tem questão de
prova da banca do concurso nem questão no estilo dela: a da banca vem primeiro, e a de outra banca não a empurra para
fora. O resto vai para o aquecimento, sem o completar da aula com "(Cobra além deste material.)".

Uso: uv run python scripts/juntar-questoes.py [--outra-banca] <pasta com extraido/ e classificado/>
O relatório (o que cada aula recebeu, os temas sem assunto, as discordâncias com o gabarito) sai no terminal.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
from escola.catalogo import carregar, id_de  # noqa: E402

POR_AULA = 5


def ano(prova: str) -> int:
    return int(re.search(r"\d{4}", prova).group())


def main(pasta: Path, outra_banca: bool = False) -> None:
    cat = carregar(RAIZ / "escola")
    nas_provinhas = {(q.prova, int(m.group(1))) for qs in cat.provinhas.values() for q in qs
                     if (m := re.search(r"questão (\d+)", q.fonte))}
    provas, todas, discorda, fora = {}, [], [], defaultdict(list)
    for arq in sorted((pasta / "extraido").glob("*.json")):
        prova = json.loads(arq.read_text(encoding="utf-8"))
        classe = {c["numero"]: c for c in json.loads((pasta / "classificado" / arq.name).read_text(encoding="utf-8"))}
        for q in prova["questoes"]:
            c = classe.get(q["numero"], {})
            q.pop("obs", None)
            q.update(assunto=c.get("assunto", ""), item=c.get("item", ""), comentario=c.get("comentario", ""))
            if q["anulada"]:
                continue
            if not c.get("concorda", True):
                discorda.append(f"{prova['prova']} q{q['numero']}: {c.get('discorda', '')}")
            if not q["assunto"]:
                fora[c.get("fora") or "sem tema"].append(f"{prova['prova']} q{q['numero']}")
            elif (prova["prova"], q["numero"]) not in nas_provinhas:
                todas.append((prova["prova"], q))
        provas[arq.name] = prova

    # as aulas recebem as questões indicadas para elas, da prova mais nova para a mais antiga
    todas.sort(key=lambda par: (-ano(par[0]), par[1]["numero"]))
    desta_vez = {p["prova"] for p in provas.values()}
    ocupadas = ({iid for iid, qs in cat.reais.items() if any(q.prova not in desta_vez for q in qs)} | set(cat.estilo)
                if outra_banca else set())
    por_aula = defaultdict(list)
    sem_aula = []
    for prova, q in todas:
        if q["item"] and id_de(q["item"]) not in ocupadas and len(por_aula[q["item"]]) < POR_AULA:
            por_aula[q["item"]].append(q)
        else:
            q["item"] = ""
            sem_aula.append(q)
    # a questão do assunto que ficou sem aula completa a aula principal do mesmo assunto que tem menos; o comentário
    # avisa que ela cobra além do material, para o erro não parecer falta de atenção
    for q in sem_aula if not outra_banca else ():
        principais = [i.url for i in cat.assuntos[q["assunto"]].principais if i.tipo != "prova"]
        vagas = [u for u in principais if len(por_aula[u]) < POR_AULA]
        if vagas:
            destino = min(vagas, key=lambda u: len(por_aula[u]))
            q["item"] = destino
            q["comentario"] = f"(Cobra além deste material.) {q['comentario']}"
            por_aula[destino].append(q)

    destino = RAIZ / "escola" / "questoes"
    destino.mkdir(exist_ok=True)
    for nome, prova in provas.items():
        (destino / nome).write_text(json.dumps(prova, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"{len(todas)} questões classificadas (fora as anuladas e as das provinhas)")
    for aid, a in cat.assuntos.items():
        linhas = [(i, len(por_aula.get(i.url, []))) for i in a.itens if i.tipo != "prova"]
        extras = sum(1 for _, q in todas if q["assunto"] == aid and not q["item"])
        if any(n for _, n in linhas) or extras:
            print(f"\n{aid} ({a.nome}): {sum(n for _, n in linhas)} nas aulas, {extras} para o aquecimento")
            for i, n in linhas:
                print(f"  {n}  {'(extra) ' if i.extra else ''}{i.titulo[:80]}")
    print("\nSem assunto no catálogo:")
    for tema, qs in sorted(fora.items(), key=lambda par: -len(par[1])):
        print(f"  {len(qs)}  {tema}: {', '.join(qs)}")
    print(f"\nDiscordâncias com o gabarito ({len(discorda)}):")
    print("\n".join(f"  {d}" for d in discorda))
    principais_cpt = {i.id for c in cat.concursos if c.id == "cpt" for m in c.materias if m.nome != "Redação"
                      for aid in m.assuntos for i in cat.assuntos[aid].principais if i.tipo != "prova"}
    com = {id_de(u) for u, qs in por_aula.items() if qs} & principais_cpt
    print(f"\nAulas e leituras principais do CP-T com questão de prova: {len(com)} de {len(principais_cpt)}")


if __name__ == "__main__":
    args = sys.argv[1:]
    main(Path(next(a for a in args if not a.startswith("--"))), outra_banca="--outra-banca" in args)
