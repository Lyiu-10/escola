"""A Escola: as telas e a API do estudo guiado, no PC, em 127.0.0.1:8792.

O catálogo (concursos, assuntos, materiais e fotos) vem do repositório; os PDFs, o progresso e a situação semanal
dos concursos ficam em Documentos\\Escola. A central da Thalia tem um link comum para cá (só em tela de computador).
"""
import json
import logging
import math
import random
import re
import sqlite3
import subprocess
import threading
from collections import Counter
from collections.abc import Callable
from dataclasses import replace
from datetime import date, datetime, timedelta
from functools import cache
from itertools import takewhile
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import caminho, catalogo, cronograma, rotina, situacao
from .cronograma import Tarefa
from .perfis import COOKIE, CORES, DaVez, Perfis, PorPerfil, perfil_da_vez

WEB = Path(__file__).parent / "web"


class Revalidados(StaticFiles):
    """Os arquivos da tela sem cache cego: o navegador pergunta a cada carga e recebe 304 se nada mudou.

    Sem isso, depois de uma atualização o navegador podia juntar o escola.html novo com o escola.js velho.
    """

    async def get_response(self, path, scope):
        resposta = await super().get_response(path, scope)
        resposta.headers["Cache-Control"] = "no-cache"
        return resposta

PORTA = 8792
NOVIDADE_DIAS = 14  # quanto tempo uma novidade da busca semanal fica em destaque no início
AQUECIMENTO = 10  # perguntas no aquecimento do dia
AQUECIMENTO_POR_ITEM = 3  # no máximo 3 da mesma aula ou provinha, para misturar os assuntos
RECENTES = 3  # dias: a questão que caiu num aquecimento recente não volta logo no seguinte
VIRADA = 4  # o dia do aquecimento vira às 4h: o estudo da madrugada ainda é da noite anterior
LEITURA_MIN = 2  # minutos para o resumo da última aula
CARTOES_POR_MINUTO = 2
RODADA = 10  # perguntas numa rodada do caderno de erros
FIRMAR = 2  # dias diferentes, depois do último erro, em que ele precisa acertar para a pergunta sair do caderno
HORARIO_LIVRE = "Horário livre"  # o bloco da Rotina que o início mostra
PRAZO_DIAS = 30  # a inscrição que fecha nesse prazo vira faixa no início, até ele dizer que se inscreveu
COPIA_REMOTA = "escola-progresso-{}.db"  # uma por perfil, na pasta do usuário do notebook
TIPO_RESPOSTAS = {"prova": "Simulado", "provinha": "Provinha"}  # o que ele respondeu num dia que já passou
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)  # sem isto o scp abre um console

log = logging.getLogger(__name__)


class NovoEstado(BaseModel):
    estado: Literal["novo", "feito", "depois"]


class DiaDeEstudo(BaseModel):
    dia: int = Field(ge=0, le=6)  # 0 é segunda
    inicio: str = Field("", pattern=r"^(|([01]\d|2[0-3]):[0-5]\d)$")
    minutos: int = Field(ge=15, le=480)


class Ajustes(BaseModel):
    minutos_dia: int | None = Field(None, ge=15, le=480)
    dias: list[int] | None = Field(None, min_length=1, max_length=7)
    concursos: list[str] | None = Field(None, min_length=1, max_length=10)
    horario: str | None = Field(None, max_length=5)
    semana: list[DiaDeEstudo] | None = Field(None, min_length=1, max_length=7)  # dia a dia: substitui dias e horas


# A semana em quadradinhos de meia hora, pintada na tela: sete dias de 48 quadradinhos, a partir de `inicio`. O
# rascunho não muda a Rotina; o Claude passa para a rotina.json quando ele pedir.
Quadradinho = Literal["compromisso", "pilar", "estudo", "coringa", "livre", "sono", ""]


class Quadros(BaseModel):
    inicio: str = Field(pattern=r"^([01]\d|2[0-3]):[03]0$")
    dias: list[Annotated[list[Quadradinho], Field(min_length=48, max_length=48)]] = Field(min_length=7, max_length=7)


class Nota(BaseModel):
    texto: str = Field(max_length=20000)


class Respostas(BaseModel):
    marcadas: list[int] = Field(min_length=1, max_length=40)  # a alternativa marcada em cada questão, a partir de 0


class Folha(BaseModel):
    marcadas: list[int | None] = Field(min_length=1, max_length=120)  # o simulado: None é a que ficou em branco


class NovoPerfil(BaseModel):
    nome: str = Field(max_length=60)  # o limite de verdade (20, sem os espaços sobrando) é do Perfis
    cor: str | None = None


class MudaPerfil(BaseModel):
    nome: str | None = Field(None, max_length=60)
    cor: str | None = None


def enviar_ao_notebook(arquivo: Path) -> None:
    """Leva a cópia do dia ao notebook-servidor pelo ssh da Thalia: se o disco do PC morrer, o progresso fica lá. A
    cópia mora em perfis/<id>/copias/, e o id do perfil vai no nome do arquivo de lá."""
    try:
        r = subprocess.run(["scp", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", str(arquivo),
                            f"notebook:{COPIA_REMOTA.format(arquivo.parent.parent.name)}"], capture_output=True, text=True, timeout=120,
                           creationflags=SEM_JANELA)
    except (OSError, subprocess.TimeoutExpired) as e:
        log.warning("a cópia do progresso não foi ao notebook: %s", e)
        return
    if r.returncode:
        log.warning("a cópia do progresso não foi ao notebook (%s): %s", r.returncode, r.stderr.strip()[-300:])


def criar_escola(pasta_catalogo: Path, dados: Path, *, relogio: Callable[[], datetime] = datetime.now,
                 enviar_copia: Callable[[Path], None] | None = None) -> FastAPI:
    cat = catalogo.carregar(pasta_catalogo)
    arquivos = dados / "arquivos"
    arquivos.mkdir(parents=True, exist_ok=True)
    imagens = pasta_catalogo / "imagens"
    arq_creditos = imagens / "creditos.json"  # autor e licença de cada foto (todas livres, do Wikimedia Commons)
    creditos = json.loads(arq_creditos.read_text(encoding="utf-8")) if arq_creditos.is_file() else {}
    perfis = Perfis(dados, rotina_antiga=pasta_catalogo / "rotina.json")
    prog = DaVez()  # o Progresso do perfil que fez o pedido (ver perfis.py)
    lugares = caminho.onde(cat)
    sequencias = {c.id: caminho.sequencia(cat, c) for c in cat.concursos}

    @cache
    def recorte(ids: tuple[str, ...]) -> tuple[catalogo.Catalogo, dict[str, caminho.Passo]]:
        """O catálogo só com esses concursos, e o primeiro lugar de cada item nele."""
        k = replace(cat, concursos=tuple(c for c in cat.concursos if c.id in ids))
        return k, caminho.onde(k)

    por_url: dict[str, str] = {}  # um livro grátis que já é item abre dentro da Escola
    for i in cat.itens.values():
        por_url.setdefault(i.url.split("#")[0], i.id)
    app = FastAPI(title="Escola", docs_url=None, redoc_url=None, openapi_url=None)
    app.mount("/web", Revalidados(directory=WEB), name="web")
    app.mount("/arquivos", StaticFiles(directory=arquivos), name="arquivos")
    if imagens.is_dir():
        app.mount("/imagens", StaticFiles(directory=imagens), name="imagens")
    app.add_middleware(PorPerfil, perfis=perfis)
    app.state.progresso = perfis

    def hoje() -> date:
        """O dia da Escola vira às 4h: o estudo da madrugada ainda é da noite anterior, no plano, no aquecimento e no
        caderno."""
        return (relogio() - timedelta(hours=VIRADA)).date()

    def local(rel: str | None) -> str | None:
        return f"/arquivos/{rel}" if rel and (arquivos / rel).is_file() else None

    def foto(c: catalogo.Concurso) -> str | None:
        return f"/imagens/{c.foto}" if c.foto and (imagens / c.foto).is_file() else None

    def estado_de(tid: str, est) -> str:
        return est.get(tid, ("novo",))[0]

    def concurso_curto(c: catalogo.Concurso) -> dict:
        return {"id": c.id, "nome": c.nome, "sigla": c.sigla}

    def ligados() -> tuple[str, ...]:
        """Os concursos ligados no Cronograma, na ordem do catálogo; todos, se nenhum da escolha guardada existe mais."""
        escolha = set(prog.concursos())
        return tuple(c.id for c in cat.concursos if c.id in escolha) or tuple(c.id for c in cat.concursos)

    def no_cronograma() -> catalogo.Catalogo:
        return recorte(ligados())[0]

    def passo_de(iid: str, cid: str | None) -> caminho.Passo:
        """Onde o item está: no concurso pedido (de onde ele veio), senão no primeiro lugar do caminho, que só
        passa pelos concursos ligados no Cronograma (o item que só existe nos desligados fica no primeiro deles)."""
        if cid in sequencias:
            achado = next((p for p in sequencias[cid] if p.item.id == iid), None)
            if achado:
                return achado
        return recorte(ligados())[1].get(iid) or lugares[iid]

    def item_json(item: catalogo.Item, est, passo: caminho.Passo | None = None) -> dict:
        p = passo or passo_de(item.id, None)
        return {**item.dados(), "estado": estado_de(item.id, est), "youtube": catalogo.youtube(item.url),
                "perguntas": len(questoes_de(fixacao_de(item.id))), "duracao": cronograma.duracao(cat, item),
                "pdf": local(item.arquivo), "materia": p.materia.nome, "assunto": p.assunto.nome,
                "concurso": concurso_curto(p.concurso), "rota": f"#/item/{item.id}/{p.concurso.id}",
                "tambem": [c.nome for c in cat.concursos
                           if c.id != p.concurso.id and p.assunto.id in c.assuntos()]}

    def onde_assunto(aid: str) -> tuple[catalogo.Concurso, catalogo.Materia]:
        """O primeiro concurso ligado no Cronograma que cobra o assunto; senão, o primeiro do catálogo."""
        return next((c, m) for c in (*no_cronograma().concursos, *cat.concursos) for m in c.materias
                    if aid in m.assuntos)

    def materia_de(mid: str) -> tuple[catalogo.Concurso, catalogo.Materia] | None:
        return next(((c, m) for c in cat.concursos for m in c.materias if m.id == mid), None)

    def fixacao_de(iid: str) -> str:
        """O alvo das perguntas da aula: as questões de prova (`real:<item>`) quando ela tem; senão, as feitas a
        partir dela (alvo = o id do item). São alvos diferentes para uma tentativa antiga nunca ser corrigida contra
        questões que entraram depois."""
        if iid in cat.reais:
            return f"real:{iid}"
        return f"estilo:{iid}" if iid in cat.estilo else iid

    def questoes_de(alvo: str) -> tuple[catalogo.Questao, ...]:
        """As questões de prova de uma aula (alvo `real:<item>`), as feitas a partir dela (alvo = o id do item), as de
        prova que sobram num assunto (`extra:<assunto>`), a provinha de uma matéria (`mod:<matéria>`) ou o
        aquecimento de um dia (`aq:<dia>`), uma rodada do caderno de erros (`erros:<dia>:<n>`) ou as que valem num
        simulado (`sim:<prova>`)."""
        if alvo.startswith("aq:"):
            return tuple(q for _, q in aquecimento(alvo[3:])[0])
        if alvo.startswith("erros:"):
            return tuple(questao(*k) for k in misturadas(alvo))
        if alvo.startswith("real:"):
            return cat.reais.get(alvo[5:], ())
        if alvo.startswith("extra:"):
            return cat.extras.get(alvo[6:], ())
        if alvo.startswith("estilo:"):
            return cat.estilo.get(alvo[7:], ())
        if alvo.startswith("sim:"):
            return cat.simulados.get(alvo[4:], ())
        return cat.provinhas.get(alvo[4:], ()) if alvo.startswith("mod:") else cat.perguntas.get(alvo, ())

    def vigente(alvo: str) -> bool:
        """Se as perguntas desse alvo ainda valem para o aquecimento: as a mais feitas por IA não entram, e as feitas a
        partir de uma aula que ganhou questões de prova também não."""
        if alvo.startswith("mais:"):
            return False
        return not (":" not in alvo and (alvo in cat.reais or alvo in cat.estilo))

    def banco(alvo: str) -> tuple[catalogo.Questao, ...]:
        """As perguntas que o aquecimento mistura: as de fixação, as da provinha e as a mais do aquecimento (alvo
        `mais:<item>`), que só aparecem lá."""
        if alvo.startswith("mais:"):
            return material.perguntas if (material := cat.aquecimento.get(alvo[5:])) else ()
        return () if alvo.startswith("aq:") else questoes_de(alvo)

    def questao(alvo: str, n: int) -> catalogo.Questao | None:
        qs = banco(alvo)
        return qs[n] if 0 <= n < len(qs) else None

    def misturadas(alvo: str) -> list[tuple[str, int]]:
        """De onde vem cada pergunta do aquecimento de um dia (`aq:`) ou de uma rodada do caderno (`erros:`), na ordem
        da tela: o alvo e a posição. A que saiu do catálogo fica de fora."""
        if alvo.startswith("aq:"):
            return [k for k, _ in aquecimento(alvo[3:])[0]]
        return [k for k in prog.rodada(alvo) or () if questao(*k)]

    def vezes() -> dict[tuple[str, int], list[tuple[str, int, bool]]]:
        """Cada pergunta já respondida → cada vez que ele respondeu (quando, o que marcou e se acertou), da primeira à
        última. Conta a aula, a provinha, o aquecimento e o caderno de erros."""
        todas: dict[tuple[str, int], list[tuple[str, int, bool]]] = {}
        for r in prog.respostas():
            if r["alvo"].startswith("aq:"):
                chaves = (prog.aquecimento(r["alvo"][3:]) or ([], None))[0]
            elif r["alvo"].startswith("erros:"):
                chaves = prog.rodada(r["alvo"]) or []
            else:
                chaves = [(r["alvo"], n) for n in range(len(r["marcadas"]))]
            if len(chaves) != len(r["marcadas"]):
                continue
            for (alvo, n), marcada in zip(chaves, r["marcadas"]):
                if q := questao(alvo, n):
                    todas.setdefault((alvo, n), []).append((r["em"], marcada, marcada == q.certa))
        return todas

    def historico(antes: str) -> dict[tuple[str, int], tuple[str, bool]]:
        """Cada pergunta respondida antes de `antes` (data e hora ISO) → quando foi a última vez e se acertou."""
        return {k: (v[-1][0], v[-1][2]) for k, vs in vezes().items() if (v := [x for x in vs if x[0] < antes])}

    def dia_de(em: str) -> str:
        """O dia de estudo de uma resposta: vira às 4h, como o aquecimento."""
        return (datetime.fromisoformat(em) - timedelta(hours=VIRADA)).date().isoformat()

    def materia_da_questao(q: catalogo.Questao, cid: str) -> str:
        """A matéria do concurso que cobra o assunto da questão (no simulado, é ela que dá a nota)."""
        c = cat.concurso(cid)
        return next((m.nome for m in c.materias if q.assunto in m.assuntos), "Outros assuntos") if c else "Outros assuntos"

    def materia_do_alvo(alvo: str, q: catalogo.Questao | None = None) -> str:
        if alvo.startswith("sim:") and q is not None and q.assunto:
            return materia_da_questao(q, passo_de(alvo[4:], None).concurso.id)
        if alvo.startswith("mod:"):
            return materia_de(alvo[4:])[1].nome
        if alvo.startswith("extra:"):
            return onde_assunto(alvo[6:])[1].nome
        return passo_de(alvo.split(":", 1)[-1], None).materia.nome

    def caderno() -> dict:
        """O caderno de erros: cada pergunta que ele errou fica nele até ser acertada em FIRMAR dias diferentes depois
        do último erro. O dia do erro não conta: acertar logo depois de ver a correção é memória de curto prazo. Também
        conta, por matéria, quantas perguntas ele já respondeu e quantas acertou de primeira."""
        hoje_ = dia_aquecimento()
        questoes, materias, firmadas = [], {}, 0
        for (alvo, n), vs in vezes().items():
            if not vigente(alvo):
                continue
            nome = materia_do_alvo(alvo, questao(alvo, n))
            m = materias.setdefault(nome, {"materia": nome, "respondidas": 0, "de_primeira": 0, "no_caderno": 0})
            m["respondidas"] += 1
            m["de_primeira"] += vs[0][2]
            erros = [x for x in vs if not x[2]]
            if not erros:
                continue
            em, marcada, _ = erros[-1]
            dias = {dia_de(e) for e, _, ok in vs if ok and e > em} - {dia_de(em)}
            if len(dias) >= FIRMAR:
                firmadas += 1
                continue
            m["no_caderno"] += 1
            q = questao(alvo, n)
            questoes.append({"alvo": alvo, "n": n, "materia": nome, "origem": origem(alvo), "prova": q.prova,
                             "estilo": q.estilo, "enunciado": q.enunciado, "alternativas": list(q.alternativas),
                             "marcou": marcada, "certa": q.certa, "errou_em": em, "acertos": len(dias),
                             "para_hoje": dia_de(vs[-1][0]) != hoje_})
        questoes.sort(key=lambda x: x["errou_em"])
        return {"questoes": questoes, "materias": sorted(materias.values(), key=lambda m: -m["respondidas"]),
                "firmadas": firmadas}

    def rodada_aberta() -> str | None:
        """A última rodada de hoje do caderno, se ainda não foi respondida."""
        alvos = prog.rodadas(f"erros:{dia_aquecimento()}:")
        return alvos[-1] if alvos and not prog.tentativas(alvos[-1]) else None

    def dia_aquecimento() -> str:
        return hoje().isoformat()

    def montar_aquecimento(dia: str) -> tuple[list[tuple[str, int]], str | None] | None:
        """O aquecimento é revisão do que ele já fez (pedido dele em 26/10): as questões que ele errou da última vez,
        depois as que acertou, sorteadas e sem as que caíram nos aquecimentos dos últimos RECENTES dias. Se ainda for
        pouco, completa com questões de prova que ele não viu, dos assuntos que já estudou. Nada de pergunta a mais
        feita por IA. No máximo AQUECIMENTO_POR_ITEM da mesma aula, embaralhadas. O resumo e os cartões são da última
        aula ou leitura concluída que tem esse material."""
        agora = relogio().isoformat(timespec="seconds")
        estudados = [iid for (_, iid) in sorted((em, iid) for iid, (e, em) in prog.estados().items()
                                                if e == "feito" and em < agora and iid in cat.itens)]
        leitura = next((iid for iid in reversed(estudados) if iid in cat.aquecimento), None)
        respondidas = historico(agora)
        recentes = {tuple(k) for d in range(1, RECENTES + 1)
                    for k in (prog.aquecimento((date.fromisoformat(dia) - timedelta(days=d)).isoformat()) or ([], None))[0]}
        sorteio = random.Random(dia)
        vistas = [k for k in respondidas if vigente(k[0]) and k not in recentes]
        sorteio.shuffle(vistas)
        assuntos = dict.fromkeys(passo_de(iid, None).assunto.id for iid in estudados)
        alvos = [fixacao_de(iid) for iid in estudados] + [f"extra:{aid}" for aid in assuntos if aid in cat.extras]
        novas = [(alvo, n) for alvo in alvos if alvo.startswith(("real:", "extra:"))
                 for n in range(len(banco(alvo))) if (alvo, n) not in respondidas]
        sorteio.shuffle(novas)
        fila = [k for k in vistas if not respondidas[k][1]] + [k for k in vistas if respondidas[k][1]] + novas
        por_item, chaves = Counter(), []
        for alvo, n in fila:
            dono = alvo.split(":", 1)[-1]
            if len(chaves) < AQUECIMENTO and por_item[dono] < AQUECIMENTO_POR_ITEM:
                por_item[dono] += 1
                chaves.append((alvo, n))
        sorteio.shuffle(chaves)
        if not chaves and leitura is None:
            return None  # nada ainda: o dia monta quando houver
        prog.guardar_aquecimento(dia, chaves, leitura)
        return chaves, leitura

    def aquecimento(dia: str) -> tuple[list[tuple[tuple[str, int], catalogo.Questao]], str | None]:
        """As perguntas do aquecimento do dia (a chave e a questão) e o item do resumo e dos cartões. É montado na
        primeira vez que o dia pede e fica guardado: a correção bate com o que ele viu, e o que ele estudar depois
        fica para o dia seguinte."""
        guardado = prog.aquecimento(dia)
        if guardado is None and dia == dia_aquecimento():
            guardado = montar_aquecimento(dia)
        chaves, leitura = guardado or ([], None)
        return ([((alvo, n), q) for alvo, n in chaves if (q := questao(alvo, n))],
                leitura if leitura in cat.aquecimento else None)

    def origem(alvo: str) -> dict:
        """De onde veio uma pergunta do aquecimento: a aula ou leitura, ou a provinha da matéria."""
        if alvo.startswith("mod:"):
            return {"titulo": cronograma.provinha(cat, alvo[4:]).titulo, "rota": f"#/provinha/{alvo[4:]}", "video": False}
        if alvo.startswith("extra:"):
            a = cat.assuntos[alvo[6:]]
            i = (a.principais or a.itens)[0]
            return {"titulo": a.nome, "rota": f"#/item/{i.id}/{passo_de(i.id, None).concurso.id}", "video": False}
        i = cat.itens[alvo.split(":", 1)[-1]]
        return {"titulo": i.titulo, "rota": f"#/item/{i.id}/{passo_de(i.id, None).concurso.id}",
                "video": catalogo.youtube(i.url) is not None}

    def aquecimento_resumo() -> dict | None:
        """O cartão do início: o que tem (o resumo de qual aula, quantos cartões e perguntas), quanto tempo e, se já
        respondeu hoje, quantas acertou."""
        dia = dia_aquecimento()
        questoes, leitura = aquecimento(dia)
        if not questoes and leitura is None:
            return None
        cartoes = len(cat.aquecimento[leitura].cartoes) if leitura else 0
        tentativas = prog.tentativas(f"aq:{dia}")
        minutos = ((LEITURA_MIN if leitura else 0) + math.ceil(cartoes / CARTOES_POR_MINUTO)
                   + (sum(cronograma.POR_QUESTAO if q.prova or q.estilo else cronograma.POR_PERGUNTA for _, q in questoes)
                      + cronograma.CORRECAO if questoes else 0))
        return {"perguntas": len(questoes), "cartoes": cartoes, "leitura": cat.itens[leitura].titulo if leitura else None,
                "minutos": minutos, "acertos": tentativas[-1]["acertos"] if tentativas else None}

    def correcao(questoes: tuple[catalogo.Questao, ...], marcadas: list[int]) -> list[dict]:
        return [{"marcada": m, "certa": q.certa, "acertou": m == q.certa, "comentario": q.comentario, "onde": q.onde,
                 "trecho": q.trecho, "fonte": q.fonte, "url": q.url, "gabarito": q.gabarito,
                 "erradas": list(cat.erradas.get(q.chave, ())),  # por que cada errada está errada, quando já tem
                 "ressalva": q.ressalva}
                for q, m in zip(questoes, marcadas)]

    def texto_json(q: catalogo.Questao) -> dict:
        """O texto-base. O que não foi transcrito (um poema, uma letra de música) fica como `[[... página N ...]]`: a
        tela mostra o link para aquela página da prova."""
        achado = re.match(r"\[\[.*?página (\d+).*?\]\]", q.texto)
        return {"texto": "", "texto_na_prova": {"pagina": int(achado[1]), "url": q.url}} if achado else {"texto": q.texto}

    def perguntas_json(alvo: str) -> dict | None:
        """As questões sem a resposta, as tentativas (para a taxa de melhoria) e a correção da última, se houver."""
        questoes = questoes_de(alvo)
        if not questoes:
            return None
        tentativas = prog.tentativas(alvo)
        ultima = tentativas[-1]["marcadas"] if tentativas else None
        origens = ([origem(a) for a, _ in misturadas(alvo)] if alvo.startswith(("aq:", "erros:"))
                   else [None] * len(questoes))
        return {"alvo": alvo,
                "questoes": [{**texto_json(q), "prova": q.prova, "estilo": q.estilo, "enunciado": q.enunciado,
                              "alternativas": list(q.alternativas), **({"origem": o} if o else {})}
                             for q, o in zip(questoes, origens)],
                "tentativas": [{"em": t["em"], "acertos": t["acertos"], "total": t["total"]} for t in tentativas],
                "correcao": correcao(questoes, ultima) if ultima and len(ultima) == len(questoes) else None}

    def rota_de(t: Tarefa) -> str:
        if t.tipo == "revisao":
            return f"#/revisao/{t.assunto}/{t.numero}"
        if t.tipo == "redacao":
            return f"#/redacao/{t.id.split(':')[1]}/{t.concurso}"
        if t.tipo == "provinha":
            return f"#/provinha/{t.id[4:]}"
        return f"#/item/{t.id}/{t.concurso or passo_de(t.id, None).concurso.id}"

    def tarefa_json(t: Tarefa, est) -> dict:
        if t.tipo == "revisao":
            c, m = onde_assunto(t.assunto)
            return {"id": t.id, "tipo": "revisao", "titulo": t.titulo, "minutos": t.minutos, "numero": t.numero,
                    "estado": estado_de(t.id, est), "assunto": cat.assuntos[t.assunto].nome, "materia": m.nome,
                    "concurso": concurso_curto(c), "rota": rota_de(t), "tambem": []}
        if t.tipo == "redacao":
            c = cat.concurso(t.concurso)
            return {"id": t.id, "tipo": "redacao", "titulo": t.titulo, "minutos": t.minutos,
                    "estado": estado_de(t.id, est), "concurso": concurso_curto(c), "materia": "Redação",
                    "assunto": "Texto sob tempo", "rota": rota_de(t), "tambem": []}
        if t.tipo == "provinha":
            c, m = materia_de(t.id[4:])
            return {"id": t.id, "tipo": "provinha", "titulo": t.titulo, "minutos": t.minutos,
                    "estado": estado_de(t.id, est), "concurso": concurso_curto(c), "materia": m.nome,
                    "assunto": f"{len(questoes_de(t.id))} questões de provas anteriores", "rota": rota_de(t),
                    "tambem": []}
        return item_json(cat.itens[t.id], est, passo_de(t.id, t.concurso))

    def sit_concursos() -> tuple[dict, dict]:
        s = situacao.ler(dados)
        return s, s["concursos"]

    def provas(sit: dict, k: catalogo.Catalogo = cat) -> dict[str, date | None]:
        return {c.id: cronograma.data_da_prova(c, sit.get(c.id), hoje()) for c in k.concursos}

    def simulacao(est, sit) -> cronograma.Simulacao:
        k = no_cronograma()
        return cronograma.Simulacao(k, est, prog.dias(), prog.minutos_por_dia(), provas(sit, k))

    def feitos_hoje(ids: list[str], est) -> list[str]:
        dia = hoje().isoformat()
        return [i for i in ids if est.get(i, ("", ""))[0] == "feito" and dia_de(est[i][1]) == dia]

    def plano_de_hoje(est, sit) -> list[Tarefa]:
        dia = hoje().isoformat()
        ids = prog.plano(dia)
        if hoje().weekday() not in prog.dias():  # folga: só fica o que ele já fez hoje (se virou folga no meio do dia)
            ids = feitos_hoje(ids or [], est)
        elif ids is None:  # a primeira abertura do dia monta o plano, e ele não muda até amanhã
            ids = [t.id for t in simulacao(est, sit).planejar(hoje())]
            prog.guardar_plano(dia, ids)
        return [t for i in ids if (t := cronograma.tarefa_de(cat, i))]

    def refazer_hoje() -> None:
        """Depois de mudar os ajustes: o que já foi feito hoje fica, e o resto do dia é planejado de novo."""
        est, (_, sit), dia = prog.estados(), sit_concursos(), hoje().isoformat()
        feitos = feitos_hoje(prog.plano(dia) or [], est)
        gasto = sum(t.minutos for i in feitos if (t := cronograma.tarefa_de(cat, i)))
        novos = simulacao(est, sit).planejar(hoje(), gasto=gasto, fora=feitos)
        prog.guardar_plano(dia, feitos + [t.id for t in novos])

    def pendente_no_concurso(c: catalogo.Concurso, est) -> caminho.Passo | None:
        return next((p for p in sequencias[c.id] if not p.item.extra and not cronograma.eh_de_prova(p.assunto.id)
                     and estado_de(p.item.id, est) != "feito"), None)

    def situacao_json(c: catalogo.Concurso, sit: dict) -> dict | None:
        s = sit.get(c.id)
        return {**s, "rotulo": situacao.ESTADOS[s["estado"]]} if s else None

    def resumo(c: catalogo.Concurso, est, sit: dict) -> dict:
        feitos, total = caminho.contagem(cat, c.assuntos(), est)
        pend = pendente_no_concurso(c, est)
        return {"id": c.id, "nome": c.nome, "sigla": c.sigla, "cargo": c.cargo, "foco": c.foco,
                "no_cronograma": c.id in ligados(), "proximo": c.proximo, "feitos": feitos, "total": total,
                "foto": foto(c),
                "situacao": situacao_json(c, sit),
                "continuar": f"#/item/{pend.item.id}/{c.id}" if pend else None}

    def novidades(s: dict) -> list[dict]:
        limite = (hoje() - timedelta(days=NOVIDADE_DIAS)).isoformat()
        nomes = {c.id: f"{c.nome} {c.sigla}" for c in cat.concursos}
        return [{**h, "nome": nomes.get(h["concurso"], h["concurso"])} for h in s["historico"]
                if h["em"] >= limite and not h["texto"].startswith("Começou o acompanhamento")]

    def ajustes_json() -> dict:
        """`minutos_dia` e `horario` são os de hoje (sem estudo hoje, os últimos escolhidos para todos os dias)."""
        semana = prog.semana()
        horario, minutos = semana.get(hoje().weekday(), (prog.ajuste("horario"), prog.minutos_dia()))
        return {"minutos_dia": minutos, "dias": list(semana), "concursos": list(ligados()), "horario": horario,
                "semana": [{"dia": d, "inicio": h, "minutos": m} for d, (h, m) in semana.items()]}

    def rotina_da_semana() -> dict | None:
        """A rotina.json com o estudo do Cronograma dentro. É lida a cada vez: um ajuste no arquivo vale sem reiniciar.
        Cada perfil tem a sua, na pasta dele; sem ela, vale a da instalação (escola/rotina.json, fora do repositório)
        e, sem esta, a rotina.exemplo.json."""
        arq = next((a for a in (perfis.pasta(perfil_da_vez()) / "rotina.json", pasta_catalogo / "rotina.json",
                                pasta_catalogo / "rotina.exemplo.json") if a.is_file()), None)
        return rotina.montar(json.loads(arq.read_text(encoding="utf-8")), prog.semana()) if arq else None

    def posicao(dados_item: dict) -> dict:
        """'Aula 3 de 12' na matéria, para o cartão do Continuar."""
        p = passo_de(dados_item["id"], dados_item["concurso"]["id"])
        principais = [x for x in sequencias[p.concurso.id] if x.materia.id == p.materia.id and not x.item.extra]
        return {**dados_item, "total_materia": len(principais),
                "posicao": next((n for n, x in enumerate(principais, 1) if x.item.id == p.item.id), None)}

    def inicio() -> dict:
        est = prog.estados()
        s, sit = sit_concursos()
        plano = plano_de_hoje(est, sit)
        folga = hoje().weekday() not in prog.dias()
        agora = next((t for t in plano if estado_de(t.id, est) != "feito"), None)
        if agora:
            continuar = tarefa_json(agora, est)
        else:  # plano feito ou dia de folga: o Continuar oferece adiantar o caminho
            prox = next((p for p in caminho.caminho(no_cronograma(), est) if not cronograma.eh_de_prova(p.assunto.id)),
                        None)
            continuar = item_json(prox.item, est, prox) if prox else None
        if continuar and continuar["tipo"] in ("aula", "leitura", "guia", "prova"):
            continuar = posicao(continuar)
        ajustes = ajustes_json()
        r = rotina_da_semana()
        estudo_hoje = next((e for e in r["estudo"] if e["dia"] == hoje().weekday()), None) if r else None
        erros = caderno()["questoes"]
        return {"montando": cat.vazio, "continuar": continuar, "adiantando": agora is None and continuar is not None,
                # a hora de estudar hoje: a marcada no Cronograma ou, sem ela, a da Rotina
                "hoje": {"dia": hoje().isoformat(), "folga": folga, **ajustes,
                         "hora_estudo": ajustes["horario"] or (estudo_hoje["inicio"] if estudo_hoje else ""),
                         "fim_estudo": estudo_hoje["fim"] if estudo_hoje else "",  # passada, a frase diz que volta amanhã
                         "livre": livre_hoje(r)},
                "plano": {"dia": hoje().isoformat(), "minutos_dia": ajustes["minutos_dia"], "folga": folga,
                          "itens": [tarefa_json(t, est) for t in plano]},
                "aquecimento": aquecimento_resumo(),
                "caderno": {"total": len(erros), "para_hoje": sum(x["para_hoje"] for x in erros)},
                "concursos": [resumo(c, est, sit) for c in cat.concursos],
                "novidades": novidades(s), "prazos": prazos()}

    def prazos() -> list[dict]:
        """As inscrições que fecham nos próximos PRAZO_DIAS dias, dos concursos em que ele ainda não disse que se
        inscreveu: o prazo que não volta não pode ficar só na Situação."""
        inscritos = set(filter(None, prog.ajuste("inscritos").split(",")))
        saida = []
        for c in cat.concursos:
            for e in c.cronograma_ultimo if c.id not in inscritos else ():
                texto = str(e.get("data", ""))
                datas = re.findall(r"(\d{2})/(\d{2})/(\d{4})", texto.split("(")[0])
                if not str(e.get("evento", "")).lower().startswith("inscri") or not datas:
                    continue
                d, m, a = datas[-1]
                fim = date(int(a), int(m), int(d))
                if hoje() <= fim <= hoje() + timedelta(days=PRAZO_DIAS):
                    obs = re.search(r"\((.+)\)", texto)
                    saida.append({"concurso": concurso_curto(c), "fim": fim.isoformat(), "dias": (fim - hoje()).days,
                                  "obs": obs[1] if obs else "",
                                  "fonte": e.get("fonte") or c.edital.get("url") or c.pagina_oficial})
        return sorted(saida, key=lambda p: p["fim"])

    def guardar_copia() -> None:
        """Uma cópia do progresso por dia, na primeira vez que o início abre; a do dia também vai ao notebook."""
        try:
            nova = prog.copiar(perfis.pasta(perfil_da_vez()) / "copias", hoje().isoformat())
        except (OSError, sqlite3.Error):
            log.exception("não deu para copiar o progresso")
            return
        if nova and enviar_copia:
            threading.Thread(target=enviar_copia, args=(nova,), daemon=True).start()

    def livre_hoje(r: dict | None) -> dict | None:
        """O horário livre de hoje na Rotina, já com o estudo e o coringa do dia no lugar; o dia vira às 4h, como o
        aquecimento (à meia-noite e meia, o livre ainda é o da noite)."""
        dia = date.fromisoformat(dia_aquecimento()).weekday()
        blocos = next((g["blocos"] for g in r["grades"] if dia in g["dias"]), []) if r else []
        livres = [b for b in blocos if b["tipo"] == "livre" and b.get("titulo") == HORARIO_LIVRE]
        if not livres:
            return None
        b = max(livres, key=lambda b: (rotina.minutos(b["fim"]) - rotina.minutos(b["inicio"])) % rotina.DIA)
        return {"inicio": b["inicio"], "fim": b["fim"], "nota": b.get("nota", "")}

    @app.get("/")
    def tela():
        return FileResponse(WEB / "escola.html", headers={"Cache-Control": "no-cache"})

    @app.get("/api/saude")
    def saude():
        return {"ok": True}

    # ---------- Perfis: a escolha (como a da Netflix) e o Gerenciar; o cookie diz quem estuda neste aparelho ----------

    def entrar_como(resposta: Response, pid: str) -> None:
        resposta.set_cookie(COOKIE, pid, max_age=365 * 86400, httponly=True, samesite="lax")

    @app.get("/api/perfis")
    def listar_perfis(request: Request):
        return {"perfis": perfis.todos(), "atual": perfis.achar(request.cookies.get(COOKIE)), "cores": list(CORES)}

    @app.post("/api/perfis")
    def novo_perfil(corpo: NovoPerfil, resposta: Response):
        try:
            perfil = perfis.criar(corpo.nome, corpo.cor)
        except ValueError as e:
            raise HTTPException(422, str(e)) from None
        entrar_como(resposta, perfil["id"])
        return perfil

    @app.post("/api/perfis/sair")
    def sair_do_perfil(resposta: Response):
        resposta.delete_cookie(COOKIE)
        return {"ok": True}

    @app.post("/api/perfis/{pid}/entrar")
    def entrar_no_perfil(pid: str, resposta: Response):
        perfil = perfis.achar(pid)
        if perfil is None:
            raise HTTPException(404, "esse perfil não existe")
        entrar_como(resposta, pid)
        return perfil

    @app.put("/api/perfis/{pid}")
    def editar_perfil(pid: str, corpo: MudaPerfil):
        try:
            return perfis.editar(pid, corpo.nome, corpo.cor)
        except KeyError:
            raise HTTPException(404, "esse perfil não existe") from None
        except ValueError as e:
            raise HTTPException(422, str(e)) from None

    @app.get("/api/inicio")
    def api_inicio():
        guardar_copia()
        return inicio()

    @app.post("/api/inscricoes/{cid}")
    def api_inscricao(cid: str):
        """Ele disse que já se inscreveu: a faixa do prazo sai do início."""
        if cat.concurso(cid) is None:
            raise HTTPException(404, "concurso não existe")
        inscritos = list(filter(None, prog.ajuste("inscritos").split(",")))
        prog.definir("inscritos", ",".join(dict.fromkeys([*inscritos, cid])))
        return inicio()

    @app.get("/api/barra")
    def api_barra():
        est = prog.estados()
        s, _ = sit_concursos()
        concursos = []
        for c in cat.concursos:
            feitos, total = caminho.contagem(cat, c.assuntos(), est)
            concursos.append({**concurso_curto(c), "foto": foto(c), "feitos": feitos, "total": total,
                              "no_cronograma": c.id in ligados()})
        return {"concursos": concursos, "novidades": len(novidades(s)),
                "caderno": sum(x["para_hoje"] for x in caderno()["questoes"])}

    @app.get("/api/concursos/{cid}")
    def api_concurso(cid: str):
        c = cat.concurso(cid)
        if c is None:
            raise HTTPException(404, "concurso não existe")
        est = prog.estados()
        s, sit = sit_concursos()
        ultimas = prog.ultimas()
        materias = []
        for m in c.materias:
            assuntos = []
            for aid in m.assuntos:
                a = cat.assuntos[aid]
                feitos, total = caminho.contagem(cat, [aid], est)
                assuntos.append({"id": aid, "nome": a.nome, "edital": a.edital, "feitos": feitos, "total": total,
                                 "itens": [{**item_json(i, est, passo_de(i.id, c.id)),
                                            "fixacao": ultimas.get(fixacao_de(i.id))} for i in a.itens]})
            alvos = dict.fromkeys(fixacao_de(i.id) for aid in m.assuntos for i in cat.assuntos[aid].itens)
            respondidos = [ultimas[a] for a in alvos if a in ultimas]
            fixacao = {"acertos": sum(a for a, _ in respondidos), "total": sum(t for _, t in respondidos)}
            prov = cronograma.provinha(cat, m.id)
            provinha = {"id": prov.id, "rota": rota_de(prov), "questoes": len(questoes_de(prov.id)),
                        "minutos": prov.minutos, "estado": estado_de(prov.id, est),
                        "ultima": ultimas.get(prov.id)} if prov else None
            feitos, total = caminho.contagem(cat, m.assuntos, est)
            livros = [{"referencia": li.referencia, "curta": li.curta, "editora": li.editora, "gratis": li.gratis,
                       "item": por_url.get(li.gratis) if li.gratis else None}
                      for li in c.bibliografia if set(li.assuntos) & set(m.assuntos)]
            materias.append({"id": m.id, "nome": m.nome, "feitos": feitos, "total": total, "assuntos": assuntos,
                             "livros": livros, "fixacao": fixacao, "provinha": provinha})
        prova = provas(sit)[c.id]
        return {**resumo(c, est, sit), "credito": creditos.get(c.id), "prova": c.prova, "requisitos": list(c.requisitos),
                "edital": {**c.edital, "pdf": local(c.edital.get("arquivo"))}, "materias": materias,
                "sobre": list(c.sobre), "cronograma_ultimo": list(c.cronograma_ultimo),
                "pagina_oficial": c.pagina_oficial, "prova_data": prova.isoformat() if prova else None,
                "prova_confirmada": cronograma.prova_marcada(c, sit.get(c.id), hoje()),
                "prova_prevista": c.prova_prevista, "verificado_em": s["verificado_em"]}

    @app.get("/api/itens/{iid}")
    def api_item(iid: str, concurso: str | None = None):
        if iid not in cat.itens:
            raise HTTPException(404, "item não existe")
        est = prog.estados()
        p = passo_de(iid, concurso)
        seq = sequencias[p.concurso.id]
        viz = caminho.vizinhos(seq, iid, est)
        da_materia = [x for x in seq if x.materia.id == p.materia.id]
        principais = [x for x in da_materia if not x.item.extra]
        lista = []
        for aid in p.materia.assuntos:
            itens = [x for x in da_materia if x.assunto.id == aid]
            if itens:
                lista.append({"id": aid, "nome": cat.assuntos[aid].nome,
                              "itens": [{"id": x.item.id, "titulo": x.item.titulo, "tipo": x.item.tipo,
                                         "minutos": x.item.minutos, "duracao": cronograma.duracao(cat, x.item),
                                         "extra": x.item.extra, "idioma": x.item.idioma,
                                         "estado": estado_de(x.item.id, est)} for x in itens]})

        def vizinho(v):
            return {"id": v.item.id, "titulo": v.item.titulo, "materia": v.materia.nome} if v else None

        dados_item = item_json(cat.itens[iid], est, p)
        if dados_item["tipo"] == "prova":  # o simulado abre com o gabarito dele à mão: as leituras logo depois dele
            depois = p.assunto.itens[[i.id for i in p.assunto.itens].index(iid) + 1:]
            dados_item["gabaritos"] = [{"id": i.id, "titulo": i.titulo, "pdf": local(i.arquivo), "url": i.url}
                                       for i in takewhile(lambda i: i.tipo != "prova", depois) if i.tipo == "leitura"]
        feitos = sum(1 for x in principais if estado_de(x.item.id, est) == "feito")
        prov = cronograma.provinha(cat, p.materia.id)
        return {**dados_item, "fixacao": perguntas_json(fixacao_de(iid)), "simulado": iid in cat.simulados,
                "guia": cat.guias.get(iid),
                "provinha": {"rota": rota_de(prov), "questoes": len(questoes_de(prov.id)),
                             "estado": estado_de(prov.id, est)} if prov else None,
                "lista": {"materia": p.materia.nome, "feitos": feitos, "total": len(principais), "assuntos": lista},
                "posicao": next((n for n, x in enumerate(principais, 1) if x.item.id == iid), None),
                "anterior": vizinho(viz.anterior), "proxima": vizinho(viz.proxima), "pendente": vizinho(viz.pendente)}

    @app.post("/api/itens/{iid}/estado")
    def api_estado(iid: str, novo: NovoEstado, concurso: str | None = None):
        if iid not in cat.itens:
            raise HTTPException(404, "item não existe")
        prog.marcar(iid, novo.estado, relogio())
        est = prog.estados()
        p = passo_de(iid, concurso)
        prox = caminho.vizinhos(sequencias[p.concurso.id], iid, est).pendente
        if novo.estado == "depois" or prox is None:  # o adiado vai para o fim: segue o caminho
            prox = caminho.proximo(no_cronograma(), est)
        plano = plano_de_hoje(est, sit_concursos()[1])
        resto = [t for t in plano if estado_de(t.id, est) != "feito"]
        return {"item": item_json(cat.itens[iid], est, p),
                "proximo": item_json(prox.item, est, passo_de(prox.item.id, p.concurso.id)) if prox else None,
                # o que estava no plano de hoje segue o plano (a revisão, a redação); o resto segue a matéria
                "plano": {"tinha": any(t.id == iid for t in plano), "feito": bool(plano) and not resto,
                          "seguinte": tarefa_json(resto[0], est) if resto else None}}

    @app.get("/api/revisoes/{aid}/{k}")
    def api_revisao(aid: str, k: int):
        a = cat.assuntos.get(aid)
        if a is None or not a.principais or k < 1:
            raise HTTPException(404, "revisão não existe")
        est = prog.estados()
        c, m = onde_assunto(aid)
        tid = cronograma.id_revisao(aid, k)
        return {"id": tid, "numero": k, "estado": estado_de(tid, est), "minutos": cronograma.REVISAO_MIN,
                "assunto": {"id": aid, "nome": a.nome, "edital": a.edital}, "materia": m.nome,
                "concurso": concurso_curto(c), "nota": prog.nota(aid),
                "itens": [item_json(i, est, passo_de(i.id, c.id)) for i in a.itens]}

    @app.get("/api/redacoes/{dia}/{cid}")
    def api_redacao(dia: str, cid: str):
        c = cat.concurso(cid)
        if c is None:
            raise HTTPException(404, "concurso não existe")
        est = prog.estados()
        m = next((m for m in c.materias if any(a.startswith("r-") for a in m.assuntos)), None)
        itens = [item_json(i, est, passo_de(i.id, c.id)) for aid in (m.assuntos if m else ())
                 for i in cat.assuntos[aid].itens]
        tid = f"red:{dia}:{cid}"
        return {"id": tid, "estado": estado_de(tid, est), "dia": dia, "minutos": cronograma.REDACAO_MIN,
                "concurso": concurso_curto(c), "prova": c.prova, "itens": itens}

    @app.get("/api/provinhas/{mid}")
    def api_provinha(mid: str):
        t = cronograma.provinha(cat, mid)
        if t is None:
            raise HTTPException(404, "provinha não existe")
        c, m = materia_de(mid)
        est = prog.estados()
        feitos, total = caminho.contagem(cat, m.assuntos, est)
        return {"id": t.id, "titulo": t.titulo, "minutos": t.minutos, "estado": estado_de(t.id, est),
                "materia": {"id": mid, "nome": m.nome, "feitos": feitos, "total": total},
                "concurso": concurso_curto(c), "perguntas": perguntas_json(t.id)}

    def simulado_de(iid: str) -> tuple[catalogo.Questao, ...]:
        if iid not in cat.simulados:
            raise HTTPException(404, "esse simulado não existe")
        return cat.simulados[iid]

    def resultado(iid: str, marcadas: list[int | None]) -> dict:
        """A nota do simulado: o acerto geral, por matéria do concurso e os assuntos em que ele mais errou (com a aula
        para rever). Em branco conta como erro, como na prova."""
        c = passo_de(iid, None).concurso
        questoes = cat.simulados[iid]
        por_materia: dict[str, dict] = {m.nome: {"materia": m.nome, "acertos": 0, "total": 0} for m in c.materias}
        erros, vistos = Counter(), Counter()
        for q, m in zip(questoes, marcadas):
            nome = materia_da_questao(q, c.id)
            linha = por_materia.setdefault(nome, {"materia": nome, "acertos": 0, "total": 0})
            linha["total"] += 1
            linha["acertos"] += m == q.certa
            vistos[q.assunto] += 1
            erros[q.assunto] += m != q.certa

        def rever(aid: str) -> str | None:
            i = next(iter(cat.assuntos[aid].principais), None)
            return f"#/item/{i.id}/{c.id}" if i else None

        acertos = sum(m == q.certa for q, m in zip(questoes, marcadas))
        return {"acertos": acertos, "total": len(questoes), "em_branco": sum(m is None for m in marcadas),
                "por_materia": [x for x in por_materia.values() if x["total"]],
                "piores": [{"assunto": cat.assuntos[a].nome, "erros": n, "total": vistos[a], "rota": rever(a)}
                           for a, n in erros.most_common() if n][:5]}

    def simulado_json(iid: str) -> dict:
        questoes = simulado_de(iid)
        item, p = cat.itens[iid], passo_de(iid, None)
        alvo, rascunho = f"sim:{iid}", prog.rascunho(iid)
        tentativas = prog.tentativas(alvo)
        ultima = [None if m < 0 else m for m in tentativas[-1]["marcadas"]] if tentativas else None
        return {"id": iid, "titulo": item.titulo, "minutos": item.minutos, "concurso": concurso_curto(p.concurso),
                "estado": estado_de(iid, prog.estados()), "pdf": local(item.arquivo), "url": item.url,
                "numeros": [int(m[1]) if (m := re.search(r"questão (\d+)$", q.fonte)) else None for q in questoes],
                "fora": [{"numero": n, "motivo": motivo} for n, motivo in cat.simulados_fora.get(iid, ())],
                "redacao": "redação" in p.concurso.prova.lower(),
                "rascunho": rascunho, "perguntas": perguntas_json(alvo),
                "resultado": resultado(iid, ultima) if ultima else None}

    def folha_valida(questoes: tuple[catalogo.Questao, ...], folha: Folha) -> list[int | None]:
        if len(folha.marcadas) != len(questoes) or any(
                m is not None and not 0 <= m < len(q.alternativas) for q, m in zip(questoes, folha.marcadas)):
            raise HTTPException(422, "uma marcação por questão, entre as alternativas dela, ou em branco")
        return folha.marcadas

    @app.get("/api/simulados/{iid}")
    def api_simulado(iid: str):
        return simulado_json(iid)

    @app.post("/api/simulados/{iid}/comecar")
    def api_comecar_simulado(iid: str):
        """Começa (ou retoma) o simulado: a hora do começo fica guardada, e o cronômetro conta dela."""
        questoes = simulado_de(iid)
        if prog.rascunho(iid) is None:
            prog.guardar_rascunho(iid, relogio().isoformat(timespec="seconds"), [None] * len(questoes))
        return simulado_json(iid)

    @app.put("/api/simulados/{iid}/rascunho")
    def api_rascunho_simulado(iid: str, folha: Folha):
        """O que ele já marcou, guardado a cada marcação: se o PC reiniciar no meio, nada se perde."""
        marcadas = folha_valida(simulado_de(iid), folha)
        r = prog.rascunho(iid)
        if r is None:
            raise HTTPException(409, "o simulado não começou")
        prog.guardar_rascunho(iid, r["inicio"], marcadas)
        return {"ok": True}

    @app.delete("/api/simulados/{iid}/rascunho")
    def api_desistir_simulado(iid: str):
        simulado_de(iid)
        prog.apagar_rascunho(iid)
        return simulado_json(iid)

    @app.post("/api/simulados/{iid}")
    def api_entregar_simulado(iid: str, folha: Folha):
        """Entrega: corrige, guarda a tentativa (em branco vira -1, que nunca é a certa), marca a prova como feita e
        as erradas entram no caderno de erros, como as de qualquer lugar da Escola."""
        questoes = simulado_de(iid)
        marcadas = folha_valida(questoes, folha)
        acertos = sum(m == q.certa for q, m in zip(questoes, marcadas))
        prog.responder(f"sim:{iid}", [-1 if m is None else m for m in marcadas], acertos, relogio())
        prog.marcar(iid, "feito", relogio())
        prog.apagar_rascunho(iid)
        return simulado_json(iid)

    @app.get("/api/aquecimento")
    def api_aquecimento():
        dia = dia_aquecimento()
        _, leitura = aquecimento(dia)
        material = cat.aquecimento.get(leitura) if leitura else None
        return {"dia": dia, "resumo": aquecimento_resumo(), "perguntas": perguntas_json(f"aq:{dia}"),
                "leitura": {"item": {**origem(leitura), "tipo": cat.itens[leitura].tipo}, "resumo": material.resumo,
                            "cartoes": [{"frente": c.frente, "verso": c.verso, "onde": c.onde} for c in material.cartoes]}
                if material else None}

    @app.get("/api/erros")
    def api_erros():
        """O caderno de erros: as perguntas que ele errou e ainda não firmou, o placar por matéria e a rodada de hoje
        (aberta, ou a última, já com a correção)."""
        c = caderno()
        alvos = prog.rodadas(f"erros:{dia_aquecimento()}:")
        return {**c, "para_hoje": sum(x["para_hoje"] for x in c["questoes"]), "por_rodada": RODADA, "firmar": FIRMAR,
                "rodada": perguntas_json(alvos[-1]) if alvos else None, "rodadas_hoje": len(alvos)}

    @app.post("/api/erros/rodada")
    def api_nova_rodada():
        """Uma rodada com até RODADA perguntas do caderno que ele ainda não respondeu hoje, as erradas há mais tempo
        primeiro (misturando as matérias). Se a de hoje ainda está aberta, é ela que volta."""
        aberta = rodada_aberta()
        if aberta is None:
            fila = [(x["alvo"], x["n"]) for x in caderno()["questoes"] if x["para_hoje"]][:RODADA]
            if not fila:
                raise HTTPException(409, "nada para rever hoje")
            dia = dia_aquecimento()
            aberta = f"erros:{dia}:{len(prog.rodadas(f'erros:{dia}:')) + 1}"
            prog.guardar_rodada(aberta, fila)
        return perguntas_json(aberta)

    @app.get("/api/rotina")
    def api_rotina():
        """A rotina da semana, de escola/rotina.json, com o estudo de cada dia vindo do Cronograma."""
        r = rotina_da_semana()
        if r is None:
            raise HTTPException(404, "ainda não há rotina")
        return r

    @app.get("/api/quadros")
    def api_quadros():
        """O rascunho dos quadradinhos; sem rascunho, a tela pinta a Rotina."""
        q = prog.ajuste("quadros")
        return {"rascunho": json.loads(q) if q else None}

    @app.put("/api/quadros")
    def api_guardar_quadros(q: Quadros):
        prog.definir("quadros", json.dumps({**q.model_dump(), "em": relogio().isoformat(timespec="minutes")}))
        return {"ok": True}

    @app.delete("/api/quadros")
    def api_apagar_quadros():
        prog.definir("quadros", "")
        return {"ok": True}

    @app.post("/api/perguntas/{alvo}")
    def api_responder(alvo: str, r: Respostas):
        """Corrige, guarda a tentativa e devolve a correção; responder a provinha também a marca como feita."""
        questoes = questoes_de(alvo)
        if not questoes:
            raise HTTPException(404, "essas perguntas não existem")
        if len(r.marcadas) != len(questoes) or any(not 0 <= m < len(q.alternativas) for q, m in zip(questoes, r.marcadas)):
            raise HTTPException(422, "uma resposta por questão, entre as alternativas dela")
        acertos = sum(m == q.certa for q, m in zip(questoes, r.marcadas))
        prog.responder(alvo, r.marcadas, acertos, relogio())
        if alvo.startswith("mod:"):
            prog.marcar(alvo, "feito", relogio())
        return perguntas_json(alvo)

    @app.post("/api/plano/{tid}/estado")
    def api_estado_tarefa(tid: str, novo: NovoEstado):
        """Feito ou desfeito de uma revisão ou de uma redação (os itens do catálogo usam /api/itens)."""
        if not tid.startswith(("rev:", "red:")) or cronograma.tarefa_de(cat, tid) is None:
            raise HTTPException(404, "tarefa não existe")
        prog.marcar(tid, "novo" if novo.estado == "novo" else "feito", relogio())
        return inicio()

    @app.put("/api/notas/{aid}")
    def api_nota(aid: str, nota: Nota):
        if aid not in cat.assuntos:
            raise HTTPException(404, "assunto não existe")
        prog.guardar_nota(aid, nota.texto.strip(), relogio())
        return {"ok": True}

    @app.put("/api/ajustes")
    def api_ajustes(aj: Ajustes):
        if aj.dias is not None and any(d not in range(7) for d in aj.dias):
            raise HTTPException(422, "dia da semana inválido")
        if aj.concursos is not None and any(cat.concurso(c) is None for c in aj.concursos):
            raise HTTPException(422, "concurso que não existe")
        if aj.semana is not None and len({d.dia for d in aj.semana}) != len(aj.semana):
            raise HTTPException(422, "dia repetido")
        # Tudo vira a semana dia a dia. Os ajustes antigos valem para todos os dias: as horas e o horário mudam em
        # todos, e um dia que entra ganha as últimas horas e o último horário escolhidos para todos.
        semana = prog.semana()
        if aj.semana is not None:
            semana = {d.dia: (d.inicio, d.minutos) for d in aj.semana}
        if aj.minutos_dia is not None:
            prog.definir_minutos_dia(aj.minutos_dia)
            semana = {d: (h, aj.minutos_dia) for d, (h, _) in semana.items()}
        if aj.horario is not None:
            prog.definir("horario", aj.horario.strip())
            semana = {d: (aj.horario.strip(), m) for d, (_, m) in semana.items()}
        if aj.dias is not None:
            semana = {d: semana.get(d, (prog.ajuste("horario"), prog.minutos_dia())) for d in sorted(set(aj.dias))}
        if semana != prog.semana():
            prog.definir_semana(semana)
        if aj.concursos is not None:
            prog.definir("concursos", ",".join(dict.fromkeys(aj.concursos)))
        if aj.minutos_dia is not None or aj.dias is not None or aj.concursos is not None or aj.semana is not None:
            refazer_hoje()
        return inicio()

    def tarefa_da_grade(t: Tarefa, estado: str) -> dict:
        cid = t.concurso or (onde_assunto(t.assunto)[0].id if t.tipo == "revisao" else passo_de(t.id, None).concurso.id)
        c = cat.concurso(cid)
        return {"id": t.id, "tipo": t.tipo, "titulo": t.titulo, "minutos": t.minutos, "estado": estado,
                "rota": rota_de(t), "concurso": c.nome if c else ""}

    def tarefa_do_alvo(alvo: str) -> str | None:
        """A tarefa a que pertencem as respostas de um alvo: a aula (as perguntas dela), a provinha ou o simulado."""
        if alvo.startswith(("real:", "estilo:", "sim:")):
            return alvo.split(":", 1)[1]
        if alvo.startswith("mod:"):
            return alvo
        return None if ":" in alvo else alvo

    def atividade(alvo: str, r: dict) -> dict:
        """As respostas de um dia que não são de uma tarefa daquele dia: o aquecimento, o caderno, a aula adiantada."""
        rotulo, rota = "Questões", None
        if alvo.startswith("aq:"):
            rotulo = "Aquecimento"
        elif alvo.startswith("erros:"):
            rotulo = "Caderno de erros"
        elif alvo.startswith("extra:") and (a := cat.assuntos.get(alvo[6:])):
            rotulo = f"Questões a mais: {a.nome}"
        elif (tid := tarefa_do_alvo(alvo)) and (t := cronograma.tarefa_de(cat, tid)):
            rotulo, rota = f"{TIPO_RESPOSTAS.get(t.tipo, 'Perguntas')}: {t.titulo}", rota_de(t)
        return {"rotulo": rotulo, "rota": rota, "acertos": r["acertos"], "total": r["total"]}

    def dias_passados(est) -> list[dict]:
        """Os dias que já passaram e têm registro: o que ele concluiu em cada um, o que estava no plano e ficou, e as
        questões que respondeu (a última tentativa do dia em cada alvo). O dia vira às 4h, como o plano."""
        hj = hoje().isoformat()
        feitos: dict[str, list[str]] = {}
        for i, (e, em) in sorted(est.items(), key=lambda x: x[1][1]):
            if e == "feito" and (d := dia_de(em)) < hj:
                feitos.setdefault(d, []).append(i)
        respostas: dict[str, dict[str, dict]] = {}
        for r in prog.respostas():
            if (d := dia_de(r["em"])) < hj:
                respostas.setdefault(d, {})[r["alvo"]] = r
        planos = {d: ids for d, ids in prog.planos().items() if d < hj}
        saida = []
        for d in sorted({*feitos, *respostas, *planos}):
            feitos_d, plano = feitos.get(d, []), planos.get(d, [])
            tarefas = []
            for i in plano + [i for i in feitos_d if i not in plano]:
                feito = i in feitos_d
                if not feito and est.get(i, ("", ""))[0] == "feito" and dia_de(est[i][1]) < d:
                    continue  # já tinha sido feito antes desse dia
                if t := cronograma.tarefa_de(cat, i):
                    tarefas.append(tarefa_da_grade(t, "feito" if feito else "ficou"))
            atividades = []
            for alvo, r in respostas.get(d, {}).items():
                ligada = next((t for t in tarefas if t["id"] == tarefa_do_alvo(alvo)), None)
                if ligada:
                    ligada.update(acertos=r["acertos"], total=r["total"])
                else:
                    atividades.append(atividade(alvo, r))
            saida.append({"data": d, "passado": True, "folga": False, "tarefas": tarefas, "atividades": atividades,
                          "minutos": sum(t["minutos"] for t in tarefas if t["estado"] == "feito")})
        return saida

    @app.get("/api/cronograma")
    def api_cronograma():
        est = prog.estados()
        _, sit = sit_concursos()
        k = no_cronograma()
        datas = provas(sit, k)
        dias = cronograma.projetar(k, est, prog.dias(), prog.minutos_por_dia(), datas, hoje(), plano_de_hoje(est, sit))
        fim = cronograma.termino(k, dias, est)
        semanas: list[dict] = []
        futuros = [{"data": d.data.isoformat(), "folga": d.folga, "minutos": sum(t.minutos for t in d.tarefas),
                    "tarefas": [tarefa_da_grade(t, estado_de(t.id, est)) for t in d.tarefas]} for d in dias]
        for d in dias_passados(est) + futuros:
            data = date.fromisoformat(d["data"])
            segunda = (data - timedelta(days=data.weekday())).isoformat()
            if not semanas or semanas[-1]["inicio"] != segunda:
                semanas.append({"inicio": segunda, "dias": [], "minutos": 0})
            semanas[-1]["dias"].append(d)
            semanas[-1]["minutos"] += d["minutos"]
        segunda_de_hoje = (hoje() - timedelta(days=hoje().weekday())).isoformat()
        atual = next((n for n, s in enumerate(semanas) if s["inicio"] == segunda_de_hoje), 0)
        previsao = []
        for c in k.concursos:
            f, p = fim[c.id], datas[c.id]
            previsao.append({"id": c.id, "nome": c.nome, "sigla": c.sigla, "foto": foto(c),
                             "termino": None if f in (None, date.min) else f.isoformat(),
                             "concluido": f == date.min, "prova": p.isoformat() if p else None,
                             "prova_confirmada": cronograma.prova_marcada(c, sit.get(c.id), hoje()),
                             "a_tempo": None if f is None or p is None else f == date.min or f <= p})
        r = rotina_da_semana()
        return {"ajustes": ajustes_json(), "opcoes": [concurso_curto(c) for c in cat.concursos],
                "hoje": hoje().isoformat(), "previsao": previsao, "semanas": semanas, "atual": atual,
                "rotina": {"estudo": r["estudo"], "avisos": r["avisos"]} if r else None}

    @app.get("/api/situacao")
    def api_situacao():
        s, sit = sit_concursos()
        nomes = {c.id: f"{c.nome} {c.sigla}" for c in cat.concursos}
        verificado = s["verificado_em"]
        proxima = (datetime.fromisoformat(verificado) + situacao.INTERVALO).date().isoformat() if verificado else None
        return {"verificado_em": verificado, "tentativa_em": s["tentativa_em"], "erro": s["erro"],
                "proxima_busca": proxima,
                "concursos": [{**concurso_curto(c), "cargo": c.cargo, "foto": foto(c),
                               "situacao": situacao_json(c, sit), "pagina_oficial": c.pagina_oficial,
                               "edital": c.edital} for c in cat.concursos],
                "historico": [{**h, "nome": nomes.get(h["concurso"], h["concurso"])} for h in s["historico"]]}

    return app
