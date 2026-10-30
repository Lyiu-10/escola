"""O catálogo da Escola: a estrutura dos concursos (estrutura.json), os materiais de cada assunto
(materiais/*.json) e as perguntas, juntos e conferidos na carga.

Questões de prova (questoes/<prova>.json): questões reais, com o gabarito oficial, classificadas por assunto e por
aula; na aula, tomam o lugar das perguntas de fixação. Perguntas de fixação (perguntas/*.json, pela URL do item):
saem do próprio material, e cada uma guarda o trecho que sustenta a resposta; ficam só para a aula que ainda não tem
questão de prova. Provinhas (provinhas/<matéria>.json): questões reais de provas publicadas, com a fonte e o
gabarito oficial. Aquecimento (aquecimento/*.json, pela URL do item): o resumo, os cartões e as perguntas a mais de
cada aula ou leitura, para o aquecimento do dia seguinte; também saem do material, com o trecho. Guias
(guias/<nome>.md): o resumo escrito por nós de tudo o que as questões reais de um assunto cobram, para ler na própria
Escola; no material, o item de tipo "guia" diz o nome do arquivo em `guia` e não tem URL.

O id de um item sai da URL: numa remontagem do catálogo, o mesmo vídeo continua feito.
"""
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

MINUTOS = {"aula": 20, "leitura": 20, "prova": 240, "guia": 20}  # quando o item não diz quanto leva
YOUTUBE = re.compile(r"(?:youtube\.com/(?:watch\?(?:[^#]*&)?v=|embed/|shorts/|live/)|youtu\.be/)([\w-]{11})")


class CatalogoInvalido(ValueError):
    """A estrutura está quebrada: a Escola não sobe com ela."""


def id_de(url: str) -> str:
    return hashlib.sha1(url.strip().encode("utf-8")).hexdigest()[:12]


def youtube(url: str) -> str | None:
    achado = YOUTUBE.search(url)
    return achado.group(1) if achado else None


@dataclass(frozen=True)
class Item:
    id: str
    tipo: str
    titulo: str
    fonte: str
    url: str
    arquivo: str | None
    minutos: int
    idioma: str
    extra: bool
    nota: str

    def dados(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Assunto:
    id: str
    nome: str
    edital: str
    itens: tuple[Item, ...]

    @property
    def principais(self) -> tuple[Item, ...]:
        return tuple(i for i in self.itens if not i.extra)


@dataclass(frozen=True)
class Livro:
    """Um livro da bibliografia do edital; `gratis` só quando o texto inteiro é aberto e legítimo."""
    referencia: str
    curta: str
    editora: str
    assuntos: tuple[str, ...]
    gratis: str | None


@dataclass(frozen=True)
class Materia:
    id: str
    nome: str
    assuntos: tuple[str, ...]


@dataclass(frozen=True)
class Concurso:
    id: str
    nome: str
    sigla: str
    cargo: str
    foco: bool
    prova: str
    requisitos: tuple[str, ...]
    proximo: str
    edital: dict
    materias: tuple[Materia, ...]
    bibliografia: tuple[Livro, ...] = ()
    pagina_oficial: str = ""  # onde o concurso é publicado: a busca semanal começa por aqui
    prova_prevista: str = ""  # "2027-05", o mês provável pelo histórico, ou "2027-02-21", o dia do edital
    foto: str = ""  # o arquivo em escola/imagens/
    sobre: tuple[dict, ...] = ()  # {"rotulo", "valor", "fonte"}: salário, onde é o curso, etapas...
    cronograma_ultimo: tuple[dict, ...] = ()  # {"evento", "data", "fonte"} do edital mais recente

    def assuntos(self) -> list[str]:
        """Os assuntos do concurso na ordem das matérias, sem repetir."""
        return list(dict.fromkeys(a for m in self.materias for a in m.assuntos))


@dataclass(frozen=True)
class Questao:
    enunciado: str
    alternativas: tuple[str, ...]
    certa: int  # a posição em `alternativas`, a partir de 0
    comentario: str
    texto: str = ""  # o texto-base, quando a questão depende de um
    onde: int | None = None  # no vídeo, o segundo em que o assunto é dito; no PDF, a página
    trecho: str = ""  # a passagem do material que sustenta a resposta (fixação)
    fonte: str = ""  # a prova e o número da questão (provinha)
    prova: str = ""  # a prova curta, como nos livros de questões: "CP-T 2019" (provinha)
    url: str = ""  # onde a prova está publicada (provinha)
    gabarito: str = ""  # onde o gabarito oficial está publicado (provinha)
    estilo: str = ""  # a banca que a questão imita ("CP-T"), quando foi escrita por nós no formato dela
    assunto: str = ""  # o assunto do catálogo que a questão cobra (simulado: dá a nota por matéria)
    ressalva: str = ""  # quando quem comentou discorda do gabarito oficial, o motivo (simulado)

    @property
    def chave(self) -> str:
        """A questão pelo que ela diz (enunciado e alternativas): é por ela que a explicação das erradas se liga. Se o
        texto mudar, a explicação antiga deixa de valer."""
        return hashlib.sha1("\n".join((self.enunciado, *self.alternativas)).encode("utf-8")).hexdigest()[:12]


@dataclass(frozen=True)
class Cartao:
    """Um cartão de memória: a pergunta curta na frente, a resposta no verso."""
    frente: str
    verso: str
    trecho: str
    onde: int | None = None


@dataclass(frozen=True)
class Aquecimento:
    """O material de um item para o aquecimento: o resumo e os cartões aparecem quando ele é a última aula
    estudada; as perguntas, que não repetem as de fixação, entram na mistura de tudo o que já foi estudado."""
    resumo: str
    cartoes: tuple[Cartao, ...]
    perguntas: tuple[Questao, ...]


@dataclass(frozen=True)
class Catalogo:
    concursos: tuple[Concurso, ...]  # o em foco primeiro, os outros na ordem do arquivo
    assuntos: dict[str, Assunto]
    itens: dict[str, Item]
    perguntas: dict[str, tuple[Questao, ...]] = field(default_factory=dict)  # id do item → fixação feita da aula
    provinhas: dict[str, tuple[Questao, ...]] = field(default_factory=dict)  # id da matéria → provinha
    aquecimento: dict[str, Aquecimento] = field(default_factory=dict)  # id do item → resumo, cartões e perguntas
    reais: dict[str, tuple[Questao, ...]] = field(default_factory=dict)  # id do item → questões de prova da aula
    extras: dict[str, tuple[Questao, ...]] = field(default_factory=dict)  # id do assunto → questões de prova que sobram
    estilo: dict[str, tuple[Questao, ...]] = field(default_factory=dict)  # id do item → questões no formato da banca
    erradas: dict[str, tuple[str | None, ...]] = field(default_factory=dict)  # chave da questão → por que cada
    # alternativa está errada, na ordem delas (None na certa)
    simulados: dict[str, tuple[Questao, ...]] = field(default_factory=dict)  # id da prova → as questões que valem
    simulados_fora: dict[str, tuple[tuple[int, str], ...]] = field(default_factory=dict)  # id da prova → (número,
    # por que ficou de fora) das anuladas, das fora do edital e das desatualizadas
    guias: dict[str, str] = field(default_factory=dict)  # id do item de tipo guia → o texto dele, em Markdown

    def concurso(self, id: str) -> Concurso | None:
        return next((c for c in self.concursos if c.id == id), None)

    @property
    def vazio(self) -> bool:
        return not self.itens


def _item(bruto: dict, onde: str) -> Item:
    tipo = bruto.get("tipo")
    if tipo not in MINUTOS:
        raise CatalogoInvalido(f"{onde}: tipo {tipo!r} (vale aula, leitura, guia ou prova)")
    if tipo == "guia":  # o guia mora em guias/<nome>.md: o endereço só serve para dar o id
        nome = str(bruto.get("guia", "")).strip()
        if not re.fullmatch(r"[a-z0-9-]+", nome):
            raise CatalogoInvalido(f"{onde}: guia sem nome de arquivo válido ({nome!r})")
        bruto = {**bruto, "url": f"guia:{nome}"}
    url = str(bruto.get("url", "")).strip()
    if not url.startswith(("http://", "https://")) and not (tipo == "guia" and url.startswith("guia:")):
        raise CatalogoInvalido(f"{onde}: URL inválida {url!r}")
    titulo = str(bruto.get("titulo", "")).strip()
    if not titulo:
        raise CatalogoInvalido(f"{onde}: item sem título ({url})")
    return Item(id=id_de(url), tipo=tipo, titulo=titulo, fonte=str(bruto.get("fonte", "")).strip(), url=url,
                arquivo=bruto.get("arquivo") or None, minutos=int(bruto.get("minutos") or MINUTOS[tipo]),
                idioma=bruto.get("idioma") or "pt", extra=bool(bruto.get("extra", False)),
                nota=str(bruto.get("nota", "")).strip())


def _livro(bruto: dict, onde: str, do_concurso: set[str]) -> Livro:
    curta = str(bruto.get("curta", "")).strip()
    if not curta:
        raise CatalogoInvalido(f"{onde}: livro sem nome")
    assuntos = tuple(bruto.get("assuntos") or ())
    fora = [a for a in assuntos if a not in do_concurso]
    if not assuntos or fora:
        raise CatalogoInvalido(f"{onde} › {curta}: assunto fora do concurso: {', '.join(fora) or 'nenhum'}")
    gratis = str(bruto.get("gratis") or "").strip() or None
    if gratis and not gratis.startswith(("http://", "https://")):
        raise CatalogoInvalido(f"{onde} › {curta}: URL inválida {gratis!r}")
    return Livro(str(bruto.get("referencia") or curta).strip(), curta, str(bruto.get("editora", "")).strip(),
                 assuntos, gratis)


def _questao(bruta: dict, onde: str, *, provinha: bool) -> Questao:
    """`provinha`: questão real de prova (provinha, aula, simulado). Ela fica fiel ao impresso, até quando a prova
    repetiu uma alternativa (CSM 2011, questão 3; SMV-OF 2020, questão 4). As escritas por nós não podem repetir."""
    enunciado = str(bruta.get("enunciado", "")).strip()
    alternativas = tuple(str(a).strip() for a in bruta.get("alternativas") or ())
    certa, comentario = bruta.get("certa"), str(bruta.get("comentario", "")).strip()
    if not enunciado or not comentario:
        raise CatalogoInvalido(f"{onde}: questão sem enunciado ou sem comentário")
    if not 4 <= len(alternativas) <= 5 or not all(alternativas) or (not provinha and len(set(alternativas)) < len(alternativas)):
        raise CatalogoInvalido(f"{onde}: são 4 ou 5 alternativas, todas diferentes ({enunciado[:60]})")
    if not isinstance(certa, int) or isinstance(certa, bool) or not 0 <= certa < len(alternativas):
        raise CatalogoInvalido(f"{onde}: 'certa' é a posição da alternativa certa, a partir de 0 ({enunciado[:60]})")
    q = Questao(enunciado, alternativas, certa, comentario, texto=str(bruta.get("texto", "")).strip(),
                onde=_onde(bruta.get("onde"), onde, enunciado), trecho=str(bruta.get("trecho", "")).strip(),
                fonte=str(bruta.get("fonte", "")).strip(), prova=str(bruta.get("prova", "")).strip(),
                url=str(bruta.get("url", "")).strip(),
                gabarito=str(bruta.get("gabarito", "")).strip(), estilo=str(bruta.get("estilo", "")).strip(),
                assunto=str(bruta.get("assunto", "")).strip(), ressalva=str(bruta.get("ressalva") or "").strip())
    if provinha and not (q.fonte and q.prova and q.url.startswith("http") and q.gabarito.startswith("http")):
        raise CatalogoInvalido(f"{onde}: questão de provinha sem fonte, prova, url ou gabarito ({enunciado[:60]})")
    if not provinha and not q.trecho:
        raise CatalogoInvalido(f"{onde}: pergunta de fixação sem o trecho do material ({enunciado[:60]})")
    return q


def _onde(valor, onde: str, texto: str) -> int | None:
    if valor is not None and (not isinstance(valor, int) or isinstance(valor, bool) or valor < 0):
        raise CatalogoInvalido(f"{onde}: 'onde' é o segundo do vídeo ou a página do PDF ({texto[:60]})")
    return valor


def _aquecimento(pasta: Path, itens: dict[str, Item]) -> dict[str, Aquecimento]:
    material: dict[str, Aquecimento] = {}
    for arq in sorted((pasta / "aquecimento").glob("*.json")):
        for url, bruto in json.loads(arq.read_text(encoding="utf-8")).items():
            iid = id_de(url)
            if iid not in itens:
                raise CatalogoInvalido(f"aquecimento/{arq.name}: item que não existe ({url})")
            onde = f"aquecimento/{arq.name} › {itens[iid].titulo[:50]}"
            resumo = str(bruto.get("resumo", "")).strip()
            if not resumo:
                raise CatalogoInvalido(f"{onde}: sem o resumo")
            cartoes = []
            for c in bruto.get("cartoes") or ():
                cartao = Cartao(str(c.get("frente", "")).strip(), str(c.get("verso", "")).strip(),
                                str(c.get("trecho", "")).strip(), _onde(c.get("onde"), onde, str(c.get("frente"))))
                if not (cartao.frente and cartao.verso and cartao.trecho):
                    raise CatalogoInvalido(f"{onde}: cartão sem frente, verso ou trecho ({cartao.frente[:60]})")
                cartoes.append(cartao)
            material[iid] = Aquecimento(resumo, tuple(cartoes), tuple(
                _questao(b, onde, provinha=False) for b in bruto.get("perguntas") or ()))
    return material


def _perguntas(pasta: Path, itens: dict[str, Item], materias: set[str]) -> tuple[dict, dict]:
    perguntas: dict[str, tuple[Questao, ...]] = {}
    for arq in sorted((pasta / "perguntas").glob("*.json")):
        for url, brutas in json.loads(arq.read_text(encoding="utf-8")).items():
            iid = id_de(url)
            if iid not in itens:
                raise CatalogoInvalido(f"perguntas/{arq.name}: item que não existe ({url})")
            perguntas[iid] = perguntas.get(iid, ()) + tuple(
                _questao(b, f"perguntas/{arq.name} › {itens[iid].titulo[:50]}", provinha=False) for b in brutas)
    provinhas: dict[str, tuple[Questao, ...]] = {}
    for arq in sorted((pasta / "provinhas").glob("*.json")):
        if arq.stem not in materias:
            raise CatalogoInvalido(f"provinhas/{arq.name}: matéria que não existe")
        provinhas[arq.stem] = tuple(_questao(b, f"provinhas/{arq.name}", provinha=True)
                                    for b in json.loads(arq.read_text(encoding="utf-8")))
    return perguntas, provinhas


def _estilo(pasta: Path, itens: dict[str, Item]) -> dict[str, tuple[Questao, ...]]:
    """As questões escritas por nós no formato da banca (estilo/*.json, pela URL do item), para a aula que não tem
    questão de prova. Saem do material da aula, com o trecho, como as perguntas de fixação."""
    estilo: dict[str, tuple[Questao, ...]] = {}
    for arq in sorted((pasta / "estilo").glob("*.json")):
        for url, brutas in json.loads(arq.read_text(encoding="utf-8")).items():
            iid = id_de(url)
            if iid not in itens:
                raise CatalogoInvalido(f"estilo/{arq.name}: item que não existe ({url})")
            onde = f"estilo/{arq.name} › {itens[iid].titulo[:50]}"
            questoes = tuple(_questao(b, onde, provinha=False) for b in brutas)
            if not all(q.estilo for q in questoes):
                raise CatalogoInvalido(f"{onde}: questão sem a banca que ela imita (campo estilo)")
            estilo[iid] = estilo.get(iid, ()) + questoes
    return estilo


def _ano(prova: str) -> int:
    achado = re.search(r"\d{4}", prova)
    return int(achado.group()) if achado else 0


def _reais(pasta: Path, itens: dict[str, Item], assuntos: dict[str, Assunto],
           provinhas: dict[str, tuple[Questao, ...]]) -> tuple[dict, dict]:
    """As questões de provas reais (questoes/<prova>.json), que tomam o lugar das perguntas feitas a partir da aula.
    Cada questão classificada vai para a aula indicada em `item` ou, sem aula, para o assunto (o aquecimento usa).
    Ficam de fora a anulada, a que ainda não tem assunto nem comentário e a que já está numa provinha."""
    nas_provinhas = {(q.prova, int(m.group(1))) for qs in provinhas.values() for q in qs
                     if (m := re.search(r"questão (\d+)", q.fonte))}
    por_item: dict[str, list[Questao]] = {}
    por_assunto: dict[str, list[Questao]] = {}
    for arq in sorted((pasta / "questoes").glob("*.json")):
        bruto = json.loads(arq.read_text(encoding="utf-8"))
        prova, cor = str(bruto.get("prova", "")).strip(), str(bruto.get("cor", "")).strip()
        area = str(bruto.get("area") or "Psicologia").strip()  # o Português do SMV também vem para as aulas
        for b in bruto.get("questoes") or ():
            numero, aid = b.get("numero"), str(b.get("assunto") or "").strip()
            if b.get("anulada") or not aid or not str(b.get("comentario") or "").strip() or (prova, numero) in nas_provinhas:
                continue
            onde = f"questoes/{arq.name} › questão {numero}"
            if aid not in assuntos:
                raise CatalogoInvalido(f"{onde}: assunto que não existe ({aid})")
            q = _questao({**b, "prova": prova, "url": bruto.get("url"), "gabarito": bruto.get("gabarito"),
                          "fonte": f"{prova}, {area}{f' (Prova {cor.capitalize()})' if cor else ''}, questão {numero}"},
                         onde, provinha=True)
            url = str(b.get("item") or "").strip()
            if not url:
                por_assunto.setdefault(aid, []).append(q)
            elif id_de(url) not in itens or itens[id_de(url)] not in assuntos[aid].itens:
                raise CatalogoInvalido(f"{onde}: a aula não existe ou não é do assunto {aid} ({url})")
            else:
                por_item.setdefault(id_de(url), []).append(q)
    def mais_nova(qs: list[Questao]) -> tuple[Questao, ...]:  # a prova mais recente primeiro
        return tuple(sorted(qs, key=lambda q: -_ano(q.prova)))

    return ({iid: mais_nova(qs) for iid, qs in por_item.items()},
            {aid: mais_nova(qs) for aid, qs in por_assunto.items()})


def _simulados(pasta: Path, itens: dict[str, Item], assuntos: dict[str, Assunto]) -> tuple[dict, dict]:
    """As provas que viram simulado dentro da Escola (simulados/<prova>.json, com a URL do item da prova em `item`).
    Valem as questões com assunto e comentário; ficam de fora, com o motivo, a anulada, a que a norma de hoje mudou
    (`desatualizada`), a de assunto que é só de outro concurso (`fora_do_edital`) e a de tema ainda sem aula: a nota
    mede o que cai hoje e o que a Escola ensina."""
    simulados: dict[str, tuple[Questao, ...]] = {}
    fora: dict[str, tuple[tuple[int, str], ...]] = {}
    for arq in sorted((pasta / "simulados").glob("*.json")):
        bruto = json.loads(arq.read_text(encoding="utf-8"))
        iid = id_de(str(bruto.get("item", "")))
        if iid not in itens or itens[iid].tipo != "prova":
            raise CatalogoInvalido(f"simulados/{arq.name}: a prova não é um item do catálogo ({bruto.get('item')})")
        prova, cor = str(bruto.get("prova", "")).strip(), str(bruto.get("cor", "")).strip()
        area = str(bruto.get("area") or "Psicologia").strip()
        validas, saem = [], []
        for b in bruto.get("questoes") or ():
            numero, aid = b.get("numero"), str(b.get("assunto") or "").strip()
            motivo = ("anulada" if b.get("anulada") else
                      f"desatualizada: {b['desatualizada']}" if str(b.get("desatualizada") or "").strip() else
                      f"não cai no edital deste concurso: {b.get('fora')}" if not aid and b.get("fora_do_edital") else
                      f"tema que a Escola não ensina: {b.get('fora') or 'sem assunto'}" if not aid else "")
            if motivo:
                saem.append((numero, motivo))
                continue
            onde = f"simulados/{arq.name} › questão {numero}"
            if aid not in assuntos:
                raise CatalogoInvalido(f"{onde}: assunto que não existe ({aid})")
            validas.append(_questao({**b, "prova": prova, "url": bruto.get("url"), "gabarito": bruto.get("gabarito"),
                                     "fonte": f"{prova}, {area}{f' (Prova {cor.capitalize()})' if cor else ''}, questão {numero}",
                                     "assunto": aid, "ressalva": "" if b.get("concorda", True) else b.get("discorda", "")},
                                    onde, provinha=True))
        if not validas:
            raise CatalogoInvalido(f"simulados/{arq.name}: nenhuma questão vale")
        simulados[iid], fora[iid] = tuple(validas), tuple(saem)
    return simulados, fora


def carregar(pasta: Path) -> Catalogo:
    estrutura = json.loads((pasta / "estrutura.json").read_text(encoding="utf-8"))
    arq_livros = pasta / "bibliografia.json"  # os livros que cada edital indica; a Aeronáutica não indica
    livros = json.loads(arq_livros.read_text(encoding="utf-8")) if arq_livros.is_file() else {}
    sobrando = sorted(set(livros) - {c["id"] for c in estrutura["concursos"]})
    if sobrando:
        raise CatalogoInvalido(f"bibliografia de concurso que não existe: {', '.join(sobrando)}")
    brutos: dict[str, list[tuple[str, dict]]] = {}
    for arq in sorted((pasta / "materiais").glob("*.json")):
        for aid, itens in json.loads(arq.read_text(encoding="utf-8")).items():
            brutos.setdefault(aid, []).extend((arq.name, i) for i in itens)

    nomes = estrutura["assuntos"]
    sobrando = sorted(set(brutos) - set(nomes))
    if sobrando:
        raise CatalogoInvalido(f"material de assunto que não existe: {', '.join(sobrando)}")

    itens: dict[str, Item] = {}
    assuntos: dict[str, Assunto] = {}
    for aid, info in nomes.items():
        do_assunto: dict[str, Item] = {}
        for arquivo, bruto in brutos.get(aid, []):
            item = _item(bruto, f"{arquivo} › {aid}")
            do_assunto.setdefault(item.id, item)
            itens.setdefault(item.id, item)
        assuntos[aid] = Assunto(aid, info["nome"], info.get("edital", ""), tuple(do_assunto.values()))

    concursos = []
    for c in estrutura["concursos"]:
        materias = []
        for m in c["materias"]:
            faltam = [a for a in m["assuntos"] if a not in assuntos]
            if faltam:
                raise CatalogoInvalido(f"{c['id']} › {m['id']}: assunto que não existe: {', '.join(faltam)}")
            materias.append(Materia(m["id"], m["nome"], tuple(m["assuntos"])))
        do_concurso = {a for m in materias for a in m.assuntos}
        bibliografia = tuple(_livro(b, f"bibliografia › {c['id']}", do_concurso) for b in livros.get(c["id"], []))
        concursos.append(Concurso(c["id"], c["nome"], c["sigla"], c.get("cargo", ""), bool(c.get("foco")),
                                  c.get("prova", ""), tuple(c.get("requisitos", [])), c.get("proximo", ""),
                                  dict(c.get("edital", {})), tuple(materias), bibliografia,
                                  pagina_oficial=c.get("pagina_oficial", ""), prova_prevista=c.get("prova_prevista", ""),
                                  foto=c.get("foto", ""), sobre=tuple(c.get("sobre", [])),
                                  cronograma_ultimo=tuple(c.get("cronograma_ultimo", []))))
    concursos.sort(key=lambda c: not c.foco)  # estável: o em foco na frente
    perguntas, provinhas = _perguntas(pasta, itens, {m.id for c in concursos for m in c.materias})
    reais, extras = _reais(pasta, itens, assuntos, provinhas)
    aquecimento, estilo = _aquecimento(pasta, itens), _estilo(pasta, itens)
    simulados, simulados_fora = _simulados(pasta, itens, assuntos)
    guias = _guias(pasta, itens)
    todas = [q for grupo in (perguntas, provinhas, reais, extras, estilo, simulados) for qs in grupo.values() for q in qs]
    todas += [q for a in aquecimento.values() for q in a.perguntas]
    return Catalogo(tuple(concursos), assuntos, itens, perguntas, provinhas, aquecimento, reais, extras, estilo,
                    _erradas(pasta, todas), simulados, simulados_fora, guias)


def _guias(pasta: Path, itens: dict[str, Item]) -> dict[str, str]:
    guias: dict[str, str] = {}
    for item in itens.values():
        if item.tipo != "guia":
            continue
        arq = pasta / "guias" / f"{item.url.removeprefix('guia:')}.md"
        if not arq.is_file():
            raise CatalogoInvalido(f"guia que falta: guias/{arq.name} ({item.titulo})")
        guias[item.id] = arq.read_text(encoding="utf-8").strip()
    return guias


def _erradas(pasta: Path, questoes: list[Questao]) -> dict[str, tuple[str | None, ...]]:
    """Por que cada alternativa errada está errada (explicacoes/*.json, pela chave da questão): uma explicação por
    alternativa, na ordem delas, e null na certa. A chave que não é de nenhuma questão (o texto mudou) fica de fora; o
    conferir avisa."""
    por_chave = {q.chave: q for q in questoes}
    erradas: dict[str, tuple[str | None, ...]] = {}
    for arq in sorted((pasta / "explicacoes").glob("*.json")):
        for chave, lista in json.loads(arq.read_text(encoding="utf-8")).items():
            q = por_chave.get(chave)
            if q is None:
                continue
            textos = tuple(None if t is None else str(t).strip() for t in lista or ())
            if (len(textos) != len(q.alternativas) or textos[q.certa] is not None
                    or not all(t for k, t in enumerate(textos) if k != q.certa)):
                raise CatalogoInvalido(f"explicacoes/{arq.name} › {chave}: é uma explicação por alternativa errada, na "
                                       f"ordem delas, e null na certa ({q.enunciado[:60]})")
            erradas[chave] = textos
    return erradas
