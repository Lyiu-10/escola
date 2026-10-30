"""A situação dos concursos: uma vez por semana o Claude procura edital, inscrição e datas, e a Escola mostra.

A tarefa "thalia escola situacao" roda todo dia, mas só busca quando a última busca boa tem 7 dias ou mais: um PC
desligado na segunda ou uma busca que falhou não deixam a semana em branco. O resultado vai para
Documentos\\Escola\\situacao.json, que a Escola lê a cada pedido. Uma novidade (o estado mudou, ou o Claude achou
algo que não estava na busca anterior) vira um cartão na central da Thalia, na frente Escola.
"""
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path

import httpx

from .catalogo import Catalogo

log = logging.getLogger(__name__)

ARQUIVO = "situacao.json"
ESTADOS = {"aguardando": "Aguardando edital", "previsto": "Edital previsto",
           "inscricoes": "Inscrições abertas", "andamento": "Seleção em andamento"}
INTERVALO = timedelta(days=7)
HISTORICO = 60  # quantas novidades ficam guardadas
CENTRAL = "http://127.0.0.1:8790"  # a Thalia mora no PC desde 28/10, junto com a Escola
INICIO = "23/10/2026"  # quando ele começou a estudar: ciclo com inscrição encerrada antes disso já não serve
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)

PEDIDO = """Você acompanha, uma vez por semana, seleções de psicólogo das Forças Armadas (concursos de carreira e o \
processo de oficiais temporários de um Distrito Naval da Marinha) para um candidato que está estudando para elas. \
Hoje é {hoje}.

Para cada concurso abaixo, procure na internet a situação atual: se saiu edital novo, se as inscrições estão \
abertas, as datas (inscrição, prova, resultado) e qualquer anúncio de edital próximo. Comece pelas fontes \
oficiais (a página oficial indicada, o Diário Oficial da União, sites .mil.br e gov.br); sites de notícias de \
concurso servem de apoio.

O que interessa é o ciclo em que ele ainda pode entrar. Um ciclo cujas inscrições terminaram antes de {inicio} \
já não serve: nesse caso o estado é "aguardando" (ou "previsto", se já houver anúncio do próximo).

Estados:
- aguardando: não há edital do próximo ciclo;
- previsto: há anúncio oficial ou notícia confiável de que o edital vai sair (autorização, calendário de concursos);
- inscricoes: inscrições abertas agora;
- andamento: inscrições do ciclo que serve já encerradas, com as etapas acontecendo (prova, resultados, etapas \
seguintes).

Regras:
- Não invente data nem link. Data que não vem de fonte oficial vai com "confirmada": false.
- "resumo": em português, uma ou duas frases com o que ele precisa saber agora (ex.: "Inscrições até 12/02/2027, \
taxa de R$ 150. Prova em 10/05/2027.").
- "novidade": só o que é novo em relação à "situacao_anterior" (que é o que você mesmo achou na semana passada); \
se nada mudou, null. Sem "situacao_anterior", null.
- "edital": o edital do ciclo que serve, se já saiu; senão null.
- "datas": só as do ciclo que serve; datas de ciclo encerrado ficam fora (cite-as no resumo, se ajudar).
- "fontes": os links que você usou.

Concursos:
{concursos}

Responda só com o JSON pedido, um objeto por id de concurso."""


class SituacaoInvalida(ValueError):
    """A busca não trouxe o que precisava: a situação anterior continua valendo."""


def ler(dados: Path) -> dict:
    try:
        lido = json.loads((dados / ARQUIVO).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        lido = {}
    return {"verificado_em": None, "tentativa_em": None, "erro": None, "concursos": {}, "historico": [],
            "pendentes": [], **lido}


def gravar(dados: Path, s: dict) -> None:
    dados.mkdir(parents=True, exist_ok=True)
    tmp = dados / (ARQUIVO + ".tmp")
    tmp.write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(dados / ARQUIVO)  # a Escola nunca lê um arquivo pela metade


def vencida(s: dict, agora: datetime) -> bool:
    return not s["verificado_em"] or agora - datetime.fromisoformat(s["verificado_em"]) >= INTERVALO


def pedido(cat: Catalogo, anterior: dict, agora: datetime) -> str:
    concursos = [{"id": c.id, "concurso": f"{c.nome} · {c.sigla}", "cargo": c.cargo, "area": "Psicologia",
                  "pagina_oficial": c.pagina_oficial or None, "ultimo_edital_conhecido": c.edital or None,
                  "situacao_anterior": anterior["concursos"].get(c.id)} for c in cat.concursos]
    return PEDIDO.format(hoje=agora.strftime("%d/%m/%Y"), inicio=INICIO,
                         concursos=json.dumps(concursos, ensure_ascii=False, indent=1))


def esquema(ids: list[str]) -> dict:
    link = {"type": "object", "required": ["titulo", "url"],
            "properties": {"titulo": {"type": "string"}, "url": {"type": "string"}}}
    um = {"type": "object", "required": ["estado", "resumo", "edital", "datas", "novidade", "fontes"],
          "properties": {"estado": {"enum": list(ESTADOS)}, "resumo": {"type": "string"},
                         "edital": {"anyOf": [link, {"type": "null"}]},
                         "datas": {"type": "array", "items": {
                             "type": "object", "required": ["evento", "data", "confirmada"],
                             "properties": {"evento": {"type": "string"}, "data": {"type": "string"},
                                            "confirmada": {"type": "boolean"}}}},
                         "novidade": {"type": ["string", "null"]},
                         "fontes": {"type": "array", "items": link}}}
    return {"type": "object", "required": ids, "properties": {i: um for i in ids}}


def _json_do_texto(texto: str) -> dict:
    """Sem a saída estruturada, o JSON vem no texto (às vezes num bloco ```json)."""
    achado = re.search(r"\{.*\}", texto or "", re.S)
    if not achado:
        raise SituacaoInvalida("a resposta não trouxe JSON")
    return json.loads(achado.group(0))


def executavel_claude() -> str:
    # A tarefa agendada roda sem o PATH da sessão: por isso o caminho da instalação nativa
    return (os.environ.get("THALIA_CLAUDE") or shutil.which("claude")
            or str(Path.home() / ".local" / "bin" / "claude.exe"))


def perguntar(texto: str, ids: list[str], *, rodar=subprocess.run, exe: str | None = None) -> dict:
    """Um `claude -p` com pesquisa na web (Sonnet, pelo plano), enxuto e fora de qualquer projeto."""
    cmd = [exe or executavel_claude(), "-p", "--model", "sonnet", "--effort", "medium", "--output-format", "json",
           "--json-schema", json.dumps(esquema(ids)), "--safe-mode", "--strict-mcp-config",
           "--disable-slash-commands", "--no-session-persistence",
           "--tools", "WebSearch,WebFetch", "--allowedTools", "WebSearch,WebFetch"]
    with tempfile.TemporaryDirectory(prefix="escola-situacao-") as pasta:
        r = rodar(cmd, input=texto, capture_output=True, text=True, encoding="utf-8", errors="replace",
                  timeout=1800, cwd=pasta, creationflags=SEM_JANELA)
    if r.returncode != 0:
        raise SituacaoInvalida(f"o claude saiu com {r.returncode}: {(r.stderr or r.stdout)[-300:]}")
    envelope = json.loads(r.stdout)
    if envelope.get("is_error"):
        raise SituacaoInvalida(f"o claude deu erro: {str(envelope.get('result'))[:300]}")
    bruto = envelope.get("structured_output")
    return bruto if isinstance(bruto, dict) else _json_do_texto(envelope.get("result", ""))


def _link(bruto) -> dict | None:
    if not isinstance(bruto, dict):
        return None
    url = str(bruto.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        return None
    return {"titulo": str(bruto.get("titulo") or "").strip() or url, "url": url}


def validar(bruto: dict, ids: list[str]) -> dict[str, dict]:
    if not isinstance(bruto, dict):
        raise SituacaoInvalida("a resposta não é um objeto")
    saida = {}
    for cid in ids:
        c = bruto.get(cid)
        if not isinstance(c, dict):
            raise SituacaoInvalida(f"faltou o concurso {cid}")
        if c.get("estado") not in ESTADOS:
            raise SituacaoInvalida(f"{cid}: estado {c.get('estado')!r}")
        resumo = str(c.get("resumo") or "").strip()
        if not resumo:
            raise SituacaoInvalida(f"{cid}: sem resumo")
        datas = [{"evento": str(d["evento"]).strip(), "data": str(d["data"]).strip(),
                  "confirmada": bool(d.get("confirmada", False))}
                 for d in c.get("datas") or [] if isinstance(d, dict) and d.get("evento") and d.get("data")]
        saida[cid] = {"estado": c["estado"], "resumo": resumo, "edital": _link(c.get("edital")), "datas": datas,
                      "novidade": str(c.get("novidade") or "").strip() or None,
                      "fontes": [f for f in map(_link, c.get("fontes") or []) if f]}
    return saida


def juntar(anterior: dict, novos: dict[str, dict], agora: datetime) -> tuple[dict, list[dict]]:
    """A situação nova e as novidades. Na primeira busca de um concurso não há novidade: só o começo."""
    hoje = agora.date().isoformat()
    concursos, novidades, historico = {}, [], []
    for cid, n in novos.items():
        a = anterior["concursos"].get(cid)
        desde = a["desde"] if a and a["estado"] == n["estado"] else hoje
        concursos[cid] = {**n, "desde": desde}
        if a is None:
            historico.append({"em": hoje, "concurso": cid, "texto": f"Começou o acompanhamento. {n['resumo']}"})
            continue
        mudou = a["estado"] != n["estado"]
        if not (mudou or n["novidade"]):
            continue
        texto = n["novidade"] or f"Agora: {ESTADOS[n['estado']].lower()}."
        if mudou and n["novidade"]:
            texto = f"{ESTADOS[n['estado']]}. {n['novidade']}"
        historico.append({"em": hoje, "concurso": cid, "texto": texto})
        novidades.append({"concurso": cid, "texto": texto, "resumo": n["resumo"],
                          "fonte": (n["edital"] or (n["fontes"] or [None])[0] or {}).get("url")})
    s = {**anterior, "verificado_em": agora.isoformat(timespec="seconds"), "erro": None, "concursos": concursos,
         "historico": (historico + anterior["historico"])[:HISTORICO]}
    return s, novidades


def cartao(nv: dict, nomes: dict[str, str]) -> dict:
    titulo = f"Escola · {nomes.get(nv['concurso'], nv['concurso'])}: {nv['texto']}"
    if len(titulo) > 140:
        titulo = titulo[:139].rstrip() + "…"
    nota = "\n".join(filter(None, [nv["resumo"], f"Fonte: {nv['fonte']}" if nv.get("fonte") else "",
                                   "Na Escola (no PC): http://127.0.0.1:8792/#/situacao"]))
    return {"titulo": titulo, "nota": nota, "frente": "Escola"}


def enviar_cartoes(cartoes: list[dict], *, post: Callable | None = None) -> list[dict]:
    """Manda os cartões para a central da Thalia e devolve os que não foram."""
    post = post or (lambda corpo: httpx.post(f"{CENTRAL}/api/tarefas", json=corpo, timeout=20))
    faltaram = []
    for c in cartoes:
        try:
            r = post(c)
            if r.status_code == 422 and c["frente"] != "Thalia":  # central antiga, sem a frente Escola
                r = post({**c, "frente": "Thalia"})
            r.raise_for_status()
        except httpx.HTTPError as e:
            log.warning("situação: o cartão não foi para a central (%s): %s", e, c["titulo"])
            faltaram.append(c)
    return faltaram


def rodada(cat: Catalogo, dados: Path, *, agora: datetime | None = None, forcar: bool = False,
           perguntar: Callable = perguntar, enviar: Callable = enviar_cartoes) -> int:
    agora = agora or datetime.now()
    s = ler(dados)
    if s["pendentes"]:  # o notebook estava fora na última vez
        s["pendentes"] = enviar(s["pendentes"])
        gravar(dados, s)
    if not forcar and not vencida(s, agora):
        log.info("situação: a última busca é de %s; nada a fazer hoje", s["verificado_em"])
        return 0
    ids = [c.id for c in cat.concursos]
    s["tentativa_em"] = agora.isoformat(timespec="seconds")
    try:
        novos = validar(perguntar(pedido(cat, s, agora), ids), ids)
    except (SituacaoInvalida, ValueError, OSError, subprocess.TimeoutExpired) as e:
        s["erro"] = str(e)[:300]
        gravar(dados, s)
        log.warning("situação: a busca falhou: %s", e)
        return 1
    s, novidades = juntar(s, novos, agora)
    nomes = {c.id: f"{c.nome} {c.sigla}" for c in cat.concursos}
    s["pendentes"] = s["pendentes"] + enviar([cartao(nv, nomes) for nv in novidades])
    gravar(dados, s)
    log.info("situação: busca feita, %d novidade(s)", len(novidades))
    return 0
