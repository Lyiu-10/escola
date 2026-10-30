"""Junta as provas transcritas e a classificação delas em escola/simulados/<prova>.json, o simulado dentro da Escola.

Cada pasta tem extraido/<prova>.json (a prova, com o gabarito oficial) e classificado/<prova>.json (assunto, aula,
comentário, se discorda do gabarito, se está fora do edital ou desatualizada). A prova vira simulado do item do
catálogo cujo arquivo começa com o mesmo nome (provas-cpt/cpt-2012-prova.pdf → cpt-2012). Sai da nota, com o motivo:
a questão de assunto que é só de outro concurso (`fora_do_edital`) e a de tema que ainda não tem aula na Escola
(sem assunto; o buraco aparece na tela, e a questão volta quando a aula entrar).

Uso: uv run python scripts/juntar-simulados.py <pasta> [<pasta> ...]
O relatório (questões que valem, de fora, sem classificação) sai no terminal.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
from escola.catalogo import carregar  # noqa: E402


def provas_do_catalogo(cat) -> dict[str, tuple]:
    """nome da prova (o começo do arquivo) → (item, concurso), dos simulados de cada concurso."""
    achadas = {}
    for c in cat.concursos:
        for aid in c.assuntos():
            if not aid.startswith("provas-"):
                continue
            for i in cat.assuntos[aid].itens:
                if i.tipo == "prova" and i.arquivo:
                    nome = Path(i.arquivo).name.split("-prova")[0]
                    achadas.setdefault(nome, (i, c))
    return achadas


def main(pastas: list[Path]) -> None:
    cat = carregar(RAIZ / "escola")
    provas = provas_do_catalogo(cat)
    destino = RAIZ / "escola" / "simulados"
    destino.mkdir(exist_ok=True)
    for pasta in pastas:
        for arq in sorted((pasta / "extraido").glob("*.json")):
            classe_arq = pasta / "classificado" / arq.name
            if arq.stem not in provas:
                print(f"{arq.stem}: não é simulado de nenhum curso, fica de fora")
                continue
            if not classe_arq.is_file():
                print(f"{arq.stem}: ainda sem classificação")
                continue
            item, concurso = provas[arq.stem]
            do_concurso = set(concurso.assuntos())
            prova = json.loads(arq.read_text(encoding="utf-8"))
            classe = {c["numero"]: c for c in json.loads(classe_arq.read_text(encoding="utf-8"))}
            questoes, sem = [], []
            for q in prova["questoes"]:
                c = classe.get(q["numero"])
                if c is None and not q.get("anulada"):
                    sem.append(q["numero"])
                    continue
                c = c or {}
                assunto, fora, fora_do_edital = c.get("assunto", ""), c.get("fora", ""), False
                if assunto and assunto not in do_concurso:  # o tema é de outro concurso: não cai neste
                    fora, assunto, fora_do_edital = cat.assuntos[assunto].nome, "", True
                questoes.append({
                    "numero": q["numero"], "texto": q.get("texto", ""), "enunciado": q["enunciado"],
                    "alternativas": q["alternativas"], "certa": q["certa"], "anulada": bool(q.get("anulada")),
                    "assunto": assunto, "item": c.get("item", "") if assunto else "", "comentario": c.get("comentario", ""),
                    "concorda": c.get("concorda", True), "discorda": c.get("discorda", ""), "fora": fora,
                    "fora_do_edital": fora_do_edital,
                    "desatualizada": c.get("desatualizada", "")})
            saida = {"item": item.url, "prova": prova["prova"], "cor": prova.get("cor", ""),
                     "area": prova.get("area", "Psicologia"), "url": prova.get("url", ""),
                     "gabarito": prova.get("gabarito", ""), "questoes": questoes}
            (destino / arq.name).write_text(json.dumps(saida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            valem = [q for q in questoes if not q["anulada"] and q["assunto"] and not q["desatualizada"]]
            print(f"{arq.stem} → {concurso.sigla} › {item.titulo[:50]}: {len(valem)} valem, "
                  f"{len(questoes) - len(valem)} de fora{f', sem classificação: {sem}' if sem else ''}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main([Path(p) for p in sys.argv[1:]])
