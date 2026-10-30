"""Gera, por grupo de assuntos, um dossiê para a revisão: a ordem do curso, o edital, os itens na ordem com o texto
extraído e as questões que aparecem em cada aula (com gabarito, comentário e o porquê de cada errada)."""
import sys, json
from pathlib import Path
sys.path.insert(0, "src")
from escola.catalogo import carregar

OUT = Path(sys.argv[1])
cat = carregar(Path("escola"))
T = Path(r"C:/Users/peric/Documents/Escola/textos")
L = "ABCDE"

GRUPOS = {
    "smv-1": ["l-interpretacao", "l-ortografia", "l-formacao", "l-classes", "l-verbos"],
    "smv-2": ["l-periodo-simples", "l-periodo-composto", "l-concordancia", "l-regencia", "l-crase", "l-pontuacao", "l-colocacao"],
    "smv-3": ["l-coesao", "l-textualidade", "l-significacao", "l-estilistica", "l-variacao"],
    "cpt-1": ["p-etica", "p-documentos", "p-alcool-drogas", "p-lei-10216", "r-estrutura", "r-argumentacao", "r-coesao", "r-temas"],
    "cpt-2": ["p-psicoterapias", "p-psicanalise", "p-terapia-breve", "p-grupos", "p-avaliacao", "p-psicodiagnostico", "p-psicopatologia", "p-transtornos"],
    "cpt-3": ["p-saude", "p-saude-mental", "p-emergencias", "p-suicidio", "p-hospitalar", "p-escolar", "p-aprendizagem", "p-orientacao"],
    "cpt-4": ["p-org-trabalho", "p-recrutamento", "p-psicometria", "p-treinamento", "p-lideranca", "p-equipes", "p-cultura", "p-saude-trabalhador"],
}

def questao(q, textos, linhas):
    if q.texto:
        if q.texto not in textos:
            textos[q.texto] = len(textos) + 1
            linhas.append(f"TEXTO-BASE #{textos[q.texto]}:\n{q.texto}\n")
        else:
            linhas.append(f"(texto-base #{textos[q.texto]}, já mostrado acima)")
    linhas.append(q.enunciado)
    exp = cat.erradas.get(q.chave, ())
    for k, a in enumerate(q.alternativas):
        marca = "  <= GABARITO" if k == q.certa else ""
        linhas.append(f"  {L[k]}) {a}{marca}")
        if k < len(exp) and exp[k]:
            linhas.append(f"       por que está errada (nossa explicação): {exp[k]}")
    linhas.append(f"  COMENTÁRIO (nosso): {q.comentario}")
    if q.ressalva:
        linhas.append(f"  RESSALVA: {q.ressalva}")
    if q.trecho:
        linhas.append(f"  TRECHO DO MATERIAL QUE SUSTENTA: {q.trecho} (onde: {q.onde})")
    linhas.append("")

def ordem(cid):
    c = cat.concurso(cid)
    out = []
    for m in c.materias:
        for aid in m.assuntos:
            out.append(f"  {m.nome} › {aid} — {cat.assuntos[aid].nome}")
    return "\n".join(out)

for grupo, aids in GRUPOS.items():
    cid = "smv" if grupo.startswith("smv") else "cpt"
    linhas = [f"# Dossiê da revisão — grupo {grupo} (concurso {cid})", "",
              "## A ordem do curso inteiro (é a ordem em que ele estuda)", ordem(cid), ""]
    for aid in aids:
        a = cat.assuntos[aid]
        textos = {}
        linhas += [f"\n\n==================== ASSUNTO {aid} — {a.nome} ====================",
                   f"O que o edital pede: {a.edital}", ""]
        for n, it in enumerate(a.itens, 1):
            f = T / f"{it.id}.txt"
            linhas += [f"--- ITEM {n} [{it.tipo}{' · EXTRA (opcional, fora do plano)' if it.extra else ' · PRINCIPAL'} · {it.minutos} min] id={it.id}",
                       f"Título: {it.titulo}", f"Fonte: {it.fonte}", f"URL: {it.url}", f"Nota (o que ler/ver): {it.nota}",
                       f"Texto extraído: {f.as_posix() if f.exists() else 'NÃO HÁ (não dá para simular este item pelo texto)'}"
                       + (f" ({f.stat().st_size // 1024} KB)" if f.exists() else ""), ""]
            reais, estilo, fix = cat.reais.get(it.id, ()), cat.estilo.get(it.id, ()), cat.perguntas.get(it.id, ())
            if reais:
                linhas.append(f"QUESTÕES QUE APARECEM DEPOIS DESTE ITEM: {len(reais)} questões reais de prova")
                for q in reais:
                    linhas.append(f"### {q.fonte}")
                    questao(q, textos, linhas)
            elif estilo:
                linhas.append(f"QUESTÕES QUE APARECEM DEPOIS DESTE ITEM: {len(estilo)} questões escritas por nós no estilo da banca")
                for q in estilo:
                    linhas.append(f"### estilo {q.estilo}")
                    questao(q, textos, linhas)
            elif fix:
                linhas.append(f"QUESTÕES QUE APARECEM DEPOIS DESTE ITEM: {len(fix)} perguntas de fixação feitas por IA a partir do item (não há questão real ligada a ele)")
                for q in fix:
                    linhas.append("### fixação (IA)")
                    questao(q, textos, linhas)
            else:
                linhas.append("QUESTÕES QUE APARECEM DEPOIS DESTE ITEM: nenhuma")
            linhas.append("")
        sobra = cat.extras.get(aid, ())
        if sobra:
            linhas.append(f"--- QUESTÕES REAIS DO ASSUNTO SEM AULA (só aparecem no aquecimento): {len(sobra)}")
            for q in sobra:
                linhas.append(f"### {q.fonte}")
                questao(q, textos, linhas)
    (OUT / f"{grupo}.md").write_text("\n".join(linhas), encoding="utf-8")
    print(grupo, len("\n".join(linhas)) // 1024, "KB")
