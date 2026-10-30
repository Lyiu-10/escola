"""Confere o catálogo de verdade antes de entregar: assunto sem material, PDF que falta ou não é PDF, vídeo
do YouTube que não existe. Vídeo que não toca fora do YouTube e leitura sem PDF são avisos: a tela tem o link.

As perguntas também: o trecho de cada pergunta de fixação e de cada cartão e pergunta do aquecimento tem de estar
no texto do material (textos/<item>.txt) e perto do minuto ou na página que aponta; nenhuma questão de provinha pode
vir de um simulado."""
import re
import unicodedata
from collections import Counter
from pathlib import Path

import httpx

from .catalogo import Catalogo, youtube

OEMBED = "https://www.youtube.com/oembed"
POR_ITEM = 5  # perguntas de fixação; e cartões e perguntas do aquecimento
RESUMO = (40, 140)  # palavras do resumo do aquecimento: dá para ler em 1 ou 2 minutos
FORA = "trecho que não está no material"
PROVINHA = (10, 20)  # questões, da matéria pequena à grande
FOLGA_VIDEO = 120  # segundos entre o minuto apontado e o trecho na legenda
MARCA = re.compile(r"\[(?:p\. (\d+)|(\d+):(\d{2})(?::(\d{2}))?)\]")  # [p. 12] no PDF; [12:30] ou [1:02:30] no vídeo


def normal(texto: str) -> str:
    """Só letras e números, em minúsculas: o trecho bate mesmo com quebra de linha, hífen ou pontuação diferente, e
    com o acento decomposto que alguns PDFs trazem (o "e" seguido do acento solto)."""
    return "".join(ch for ch in unicodedata.normalize("NFC", texto).lower() if ch.isalnum())


def indice(texto: str) -> tuple[str, list[tuple[int, int]]]:
    """O texto normalizado e, para cada marca, a posição em que ela começa e o valor (segundo do vídeo ou página)."""
    partes, marcas, n, pos = [], [], 0, 0
    for m in MARCA.finditer(texto):
        parte = normal(texto[pos:m.start()])
        partes.append(parte)
        n += len(parte)
        if m[1]:
            valor = int(m[1])
        elif m[4] is None:
            valor = int(m[2]) * 60 + int(m[3])
        else:
            valor = int(m[2]) * 3600 + int(m[3]) * 60 + int(m[4])
        marcas.append((n, valor))
        pos = m.end()
    partes.append(normal(texto[pos:]))
    return "".join(partes), marcas


def erro_do_trecho(trecho: str, onde: int | None, limpo: str, marcas: list[tuple[int, int]], video: bool) -> str | None:
    """None quando o trecho está no texto e no lugar apontado; senão, o que está errado."""
    alvo, lugares = normal(trecho), []  # o mesmo trecho pode aparecer mais de uma vez (resumo e conclusão)
    achado = limpo.find(alvo)
    while achado >= 0:
        lugares.append(next((v for n, v in reversed(marcas) if n <= achado), None))
        achado = limpo.find(alvo, achado + 1)
    if not lugares:
        return FORA
    if onde is None:
        return "sem minuto ou página"
    if all(lugar is not None and (abs(lugar - onde) > FOLGA_VIDEO if video else lugar != onde) for lugar in lugares):
        return f"o trecho está em {lugares[0]}, não em {onde}"
    return None


def conferir_perguntas(cat: Catalogo, textos: Path) -> tuple[list[str], list[str]]:
    problemas: list[str] = []
    avisos: list[str] = []
    principais = {i.id: i for aid, a in cat.assuntos.items() if not aid.startswith("provas-")  # gabarito não tem
                  for i in a.principais if i.tipo != "prova"}

    def trechos(iid: str, pecas: list[tuple[str, str, int | None]], prefixo: str = "") -> None:
        """Cada peça é (o que mostrar na mensagem, o trecho, o minuto ou a página)."""
        item = cat.itens[iid]
        arq = textos / f"{iid}.txt"
        if not arq.is_file():
            avisos.append(f"{prefixo}sem o texto para conferir: {item.titulo} ({arq.name})")
            return
        limpo, marcas = indice(arq.read_text(encoding="utf-8"))
        video = youtube(item.url) is not None
        for rotulo, trecho, onde in pecas:
            erro = erro_do_trecho(trecho, onde, limpo, marcas, video)
            if erro:
                (problemas if erro == FORA else avisos).append(f"{prefixo}{erro}: {item.titulo} › {rotulo[:60]}")

    def letras(iid: str, questoes, prefixo: str = "") -> None:
        vezes = max(Counter(q.certa for q in questoes).values(), default=0)
        if len(questoes) >= POR_ITEM - 1 and vezes >= len(questoes) - 1:
            avisos.append(f"{prefixo}a certa cai {vezes} vezes na mesma letra: {cat.itens[iid].titulo}")

    for iid, questoes in cat.perguntas.items():
        if len(questoes) < POR_ITEM:
            avisos.append(f"só {len(questoes)} perguntas: {cat.itens[iid].titulo}")
        letras(iid, questoes)
        trechos(iid, [(q.enunciado, q.trecho, q.onde) for q in questoes])
    for iid, aq in cat.aquecimento.items():
        titulo, p = cat.itens[iid].titulo, "aquecimento: "
        if len(aq.cartoes) < POR_ITEM or len(aq.perguntas) < POR_ITEM:
            avisos.append(f"{p}{len(aq.cartoes)} cartões e {len(aq.perguntas)} perguntas: {titulo}")
        palavras = len(aq.resumo.split())
        if not RESUMO[0] <= palavras <= RESUMO[1]:
            avisos.append(f"{p}resumo com {palavras} palavras (o normal é de {RESUMO[0]} a {RESUMO[1]}): {titulo}")
        fixacao = {normal(q.enunciado) for q in cat.perguntas.get(iid, ())}
        avisos.extend(f"{p}pergunta igual a uma de fixação: {titulo} › {q.enunciado[:60]}"
                      for q in aq.perguntas if normal(q.enunciado) in fixacao)
        letras(iid, aq.perguntas, p)
        trechos(iid, [(c.frente, c.trecho, c.onde) for c in aq.cartoes]
                + [(q.enunciado, q.trecho, q.onde) for q in aq.perguntas], p)
    for iid, questoes in cat.reais.items():
        if len(questoes) > POR_ITEM:
            avisos.append(f"{len(questoes)} questões de prova numa aula só (o normal é até {POR_ITEM}): {cat.itens[iid].titulo}")
    for iid, questoes in cat.estilo.items():
        letras(iid, questoes, "no estilo da banca: ")
        trechos(iid, [(q.enunciado, q.trecho, q.onde) for q in questoes], "no estilo da banca: ")
    sem = [i for iid, i in principais.items() if iid not in cat.perguntas and iid not in cat.reais and iid not in cat.estilo]
    if sem:
        avisos.append(f"{len(sem)} aulas e leituras principais ainda sem perguntas")
    so_feitas = [i for iid, i in principais.items() if iid in cat.perguntas and iid not in cat.reais
                 and iid not in cat.estilo]
    if so_feitas:
        avisos.append(f"{len(so_feitas)} de {len(principais)} aulas e leituras principais só com perguntas feitas a partir"
                      " da aula, sem questão de prova")
    chaves = {q.chave for g in (cat.reais, cat.extras, cat.estilo, cat.provinhas, cat.perguntas, cat.simulados)
              for qs in g.values() for q in qs}
    if sem := len(chaves - set(cat.erradas)):
        avisos.append(f"{sem} de {len(chaves)} questões ainda sem a explicação das erradas (scripts/lotes-explicacoes.py)")
    simulados = [i for aid, a in cat.assuntos.items() if aid.startswith("provas-") for i in a.itens]
    urls = {i.url for i in simulados}
    nomes = {(m[1], m[2]) for i in simulados if i.tipo == "prova" and (m := re.match(r"(\S+?)[/ ].*?(\d{4})", i.titulo))}
    problemas.extend(f"questão de aula ou de aquecimento que é de um simulado: {q.fonte}"
                     for qs in (*cat.reais.values(), *cat.extras.values()) for q in qs if q.url in urls)
    for mid, questoes in cat.provinhas.items():
        if not PROVINHA[0] <= len(questoes) <= PROVINHA[1]:
            avisos.append(f"provinha de {mid} com {len(questoes)} questões (o normal é de {PROVINHA[0]} a {PROVINHA[1]})")
        for q in questoes:
            if q.url in urls or q.gabarito in urls:
                problemas.append(f"questão de provinha que é de um simulado: {mid} › {q.fonte}")
            elif any(re.search(rf"(?<!\w){re.escape(s)}(?!\w).*\b{a}\b", q.fonte, re.I) for s, a in nomes):
                avisos.append(f"confira se não é de um simulado: {mid} › {q.fonte}")
    return problemas, avisos


def conferir(cat: Catalogo, arquivos: Path, http: httpx.Client | None = None) -> tuple[list[str], list[str]]:
    problemas: list[str] = []
    avisos: list[str] = []
    for aid in dict.fromkeys(a for c in cat.concursos for a in c.assuntos()):
        if not cat.assuntos[aid].principais:
            problemas.append(f"sem material: {aid} ({cat.assuntos[aid].nome})")
    http = http or httpx.Client(timeout=20, follow_redirects=True)
    for item in cat.itens.values():
        if item.tipo == "guia":  # mora no próprio catálogo, que já confere se o arquivo existe
            continue
        vid = youtube(item.url)
        if item.arquivo:
            local = arquivos / item.arquivo
            if not local.is_file():
                problemas.append(f"arquivo que falta: {item.arquivo} ({item.titulo})")
            elif local.suffix.lower() == ".pdf":
                with local.open("rb") as f:
                    if f.read(5) != b"%PDF-":
                        problemas.append(f"não é PDF: {item.arquivo}")
        elif vid:
            try:
                r = http.get(OEMBED, params={"url": f"https://www.youtube.com/watch?v={vid}", "format": "json"})
            except httpx.HTTPError as e:
                problemas.append(f"não deu para conferir o vídeo: {item.titulo} ({e})")
                continue
            if r.status_code in (401, 403):
                avisos.append(f"não toca fora do YouTube: {item.titulo} ({item.url})")
            elif r.status_code != 200:
                problemas.append(f"vídeo que não abre ({r.status_code}): {item.titulo} ({item.url})")
        elif item.tipo != "aula":
            avisos.append(f"abre no site, sem PDF: {item.titulo} ({item.url})")
    return problemas, avisos
