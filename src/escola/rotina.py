"""A Rotina segue o Cronograma.

O dia vem de escola/rotina.json (acordar, trabalho, sono, o tempo livre), e o estudo de cada dia vem da semana do
Cronograma: a hora marcada lá ou, sem hora, a do estudo da própria rotina.json. O tempo livre encolhe para dar lugar
ao estudo, e o dia sem estudo devolve esse lugar ao tempo livre. Logo depois do estudo vem o coringa (o "coringa" da
rotina.json), tirado do tempo livre: se o dia atrasou, o estudo termina dentro dele; se não, ele é livre. Quando o estudo bate num compromisso (trabalho, sono,
um compromisso fixo) ou come o tempo livre do dia, a Rotina avisa e propõe outro arranjo, cada proposta já como a
semana nova do Cronograma.
"""
from dataclasses import dataclass, field, replace

DIA = 1440
LAZER_MIN = 60  # menos que isso de tempo livre no dia vira aviso: a regra 2 da rotina é o lazer com hora marcada
PASSO = 15
CURTO_MIN = 30  # proposta de estudar menos só a partir de 30 min
NOMES = ("Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo")
CURTOS = ("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")
NA = ("na segunda", "na terça", "na quarta", "na quinta", "na sexta", "no sábado", "no domingo")

Semana = dict[int, tuple[str, int]]  # dia (0 é segunda) → (hora de começar ou "", minutos)


def minutos(h: str) -> int:
    a, b = h.split(":")
    return int(a) * 60 + int(b)


def relogio(m: int) -> str:
    m %= DIA
    return f"{m // 60:02d}:{m % 60:02d}"


def hora(m: int) -> str:
    m %= DIA
    return "meia-noite" if m == 0 else f"{m // 60}h{m % 60:02d}" if m % 60 else f"{m // 60}h"


def tempo(m: int) -> str:
    if m < 60:
        return f"{m} min"
    return f"{m // 60}h{m % 60:02d}" if m % 60 else f"{m // 60}h"


@dataclass(frozen=True)
class Bloco:
    ini: int  # minutos desde o acordar do dia
    fim: int
    tipo: str
    dados: dict = field(default_factory=dict, compare=False)  # titulo, nota, rota, acao
    vago: bool = False  # o lugar do estudo na rotina.json, que agora é do Cronograma

    @property
    def dur(self) -> int:
        return self.fim - self.ini


@dataclass(frozen=True)
class Dia:
    abre: int  # o acordar, no relógio
    blocos: tuple[Bloco, ...]
    estudo: Bloco | None  # o estudo que coube
    conflitos: tuple[Bloco, ...] = ()  # os compromissos em que o estudo bateu (ele então fica de fora)
    pedido: Bloco | None = None  # onde o estudo que não coube ficaria; sem hora e sem trecho livre, nenhum lugar

    @property
    def livre(self) -> int:
        return sum(b.dur for b in self.blocos if b.tipo == "livre")

    def blocos_json(self) -> list[dict]:
        return [{"inicio": relogio(b.ini + self.abre), "fim": relogio(b.fim + self.abre), "tipo": b.tipo, **b.dados}
                for b in self.blocos]


def _linha(grade: dict) -> tuple[int, list[Bloco], Bloco | None]:
    """Os blocos da grade em minutos desde o acordar; o estudo da rotina.json vira tempo livre e fica como o lugar
    padrão do estudo."""
    abre = minutos(grade["blocos"][0]["inicio"])
    linha, padrao = [], None
    for b in grade["blocos"]:
        ini = (minutos(b["inicio"]) - abre) % DIA
        fim = (minutos(b["fim"]) - abre) % DIA or DIA
        dados = {k: b[k] for k in ("titulo", "nota", "rota", "acao") if k in b}
        if b["tipo"] == "estudo":
            padrao = padrao or Bloco(ini, fim, "estudo", dados)
            linha.append(Bloco(ini, fim, "livre", {"titulo": "Livre"}, vago=True))
        else:
            linha.append(Bloco(ini, fim, b["tipo"], dados))
    return abre, linha, padrao


def _janelas(linha: list[Bloco]) -> list[tuple[int, int]]:
    """Os trechos livres seguidos do dia, de (início, fim)."""
    jan: list[tuple[int, int]] = []
    for b in linha:
        if b.tipo != "livre":
            continue
        if jan and jan[-1][1] == b.ini:
            jan[-1] = (jan[-1][0], b.fim)
        else:
            jan.append((b.ini, b.fim))
    return jan


def _inserir(linha: list[Bloco], estudo: Bloco) -> list[Bloco]:
    """Põe o estudo no dia cortando o tempo livre que ele cobre (quem chama já conferiu que só cobre tempo livre)."""
    fora = [b for b in linha if b.fim <= estudo.ini or b.ini >= estudo.fim]
    pedacos = [p for b in linha if not (b.fim <= estudo.ini or b.ini >= estudo.fim)
               for p in (replace(b, fim=estudo.ini), replace(b, ini=estudo.fim)) if p.dur > 0]
    return sorted([*fora, *pedacos, estudo], key=lambda b: b.ini)


def _absorver(linha: list[Bloco]) -> list[Bloco]:
    """O lugar vago do estudo vira parte do tempo livre ao lado (o seguinte, senão o anterior)."""
    out = list(linha)
    i = 0
    while i < len(out):
        b = out[i]
        if b.vago:
            prox = out[i + 1] if i + 1 < len(out) else None
            ant = out[i - 1] if i else None
            if prox and prox.tipo == "livre" and not prox.vago and prox.ini == b.fim:
                out[i + 1] = replace(prox, ini=b.ini)
                del out[i]
                continue
            if ant and ant.tipo == "livre" and ant.fim == b.ini:
                out[i - 1] = replace(ant, fim=b.fim)
                del out[i]
                continue
            out[i] = replace(b, vago=False)
        i += 1
    return out


def _com_coringa(linha: list[Bloco], estudo: Bloco, coringa: dict | None) -> list[Bloco]:
    """O coringa vem logo depois do estudo, do tempo livre que vem em seguida; sem tempo livre ali, não há coringa."""
    fim = next((b for a, b in _janelas(linha) if a == estudo.fim), None) if coringa else None
    if fim is None:
        return linha
    dados = {k: coringa[k] for k in ("titulo", "nota") if k in coringa}
    return _inserir(linha, Bloco(estudo.fim, min(estudo.fim + coringa["minutos"], fim), "coringa", dados))


def encaixar(grade: dict, estudo: tuple[str, int] | None) -> Dia:
    """O dia da grade com o estudo do Cronograma dentro. Se o estudo bate num compromisso, ele fica de fora e o dia
    diz em quê bateu."""
    abre, linha, padrao = _linha(grade)
    if estudo is None:
        return Dia(abre, tuple(_absorver(linha)), None)
    inicio, m = estudo
    if inicio:
        ini = (minutos(inicio) - abre) % DIA
    elif padrao:
        ini = padrao.ini
    else:
        ini = next((a for a, b in _janelas(linha) if b - a >= m), None)
    if ini is None:
        return Dia(abre, tuple(_absorver(linha)), None)
    bloco = Bloco(ini, ini + m, "estudo", {"titulo": "Estudo", "nota": f"O Continuar da Escola, {tempo(m)} como está no "
                                           "Cronograma.", "rota": "#/", "acao": "Continuar"})
    conflitos = tuple(b for b in linha if b.tipo != "livre" and b.ini < bloco.fim and b.fim > bloco.ini)
    if conflitos or bloco.fim > DIA:
        return Dia(abre, tuple(_absorver(linha)), None, conflitos, bloco)
    return Dia(abre, tuple(_absorver(_com_coringa(_inserir(linha, bloco), bloco, grade.get("coringa")))), bloco)


def _semana_json(semana: Semana) -> list[dict]:
    return [{"dia": d, "inicio": h, "minutos": m} for d, (h, m) in sorted(semana.items())]


def _de_a(ini: int, fim: int) -> str:
    """'das 21h às 22h30', 'da 1h às 3h', 'das 23h à meia-noite'."""
    def um(m: int) -> bool:
        return (m % DIA) // 60 in (0, 1)
    return f"{'da' if um(ini) else 'das'} {hora(ini)} {'à' if um(fim) else 'às'} {hora(fim)}"


def _alvo(grade: dict, inicio: str) -> tuple[int, list[Bloco], Bloco | None, int | None]:
    abre, linha, padrao = _linha(grade)
    return abre, linha, padrao, (minutos(inicio) - abre) % DIA if inicio else padrao.ini if padrao else None


def _hora_nova(abre: int, padrao: Bloco | None, ini: int) -> str:
    """Sem hora marcada quando é o lugar padrão do estudo: assim o dia segue a Rotina."""
    return "" if padrao and ini == padrao.ini else relogio(ini + abre)


def _mover(grade: dict, inicio: str, m: int) -> tuple[str, Dia] | None:
    """O mesmo tempo no mesmo dia, noutra hora: no trecho livre mais perto da hora pedida, deixando o lazer mínimo."""
    abre, linha, padrao, alvo = _alvo(grade, inicio)
    inicios = [a if alvo is None else min(max(alvo, a), b - m) for a, b in _janelas(linha) if b - a >= m]
    for ini in sorted(inicios, key=lambda s: abs(s - alvo) if alvo is not None else s):
        h = _hora_nova(abre, padrao, ini)
        y = encaixar(grade, (h, m))
        if y.estudo and y.livre >= LAZER_MIN:
            return h, y
    return None


def _encurtar(grade: dict, inicio: str, m: int) -> tuple[str, int, Dia] | None:
    """Menos tempo no mesmo dia: a partir da hora pedida (ou do lugar padrão), senão no maior trecho livre; o maior
    tempo que cabe e ainda deixa o lazer mínimo."""
    abre, linha, padrao, ini = _alvo(grade, inicio)
    janelas = _janelas(linha)
    jan = next(((a, b) for a, b in janelas if a <= ini < b), None) if ini is not None else None
    if jan is None:
        jan = max(janelas, key=lambda j: j[1] - j[0], default=None)
        if jan is None:
            return None
        ini = jan[0]
    h = inicio or _hora_nova(abre, padrao, ini)
    tam = min(m - PASSO, jan[1] - ini) // PASSO * PASSO
    while tam >= CURTO_MIN:
        y = encaixar(grade, (h, tam))
        if y.estudo and y.livre >= LAZER_MIN:
            return h, tam, y
        tam -= PASSO
    return None


def _proposta(rotulo: str, semana: Semana) -> dict:
    return {"rotulo": rotulo, "semana": _semana_json(semana)}


def _aviso(d: int, x: Dia, semana: Semana, grades: dict[int, dict]) -> dict | None:
    inicio, m = semana[d]
    propostas = []
    if x.estudo is None:
        if x.pedido:
            p = x.pedido
            c = x.conflitos[0] if x.conflitos else None
            com = f"“{c.dados.get('titulo', c.tipo)}”, {_de_a(c.ini + x.abre, c.fim + x.abre)}" if c else "a hora de acordar"
            texto = f"{NOMES[d]}: o estudo {_de_a(p.ini + x.abre, p.fim + x.abre)} ({tempo(m)}) bate com {com}."
        else:  # sem hora e sem trecho livre do tamanho: o maior compromisso do dia explica
            maior = max((b for b in x.blocos if b.tipo not in ("livre", "sono")), key=lambda b: b.dur, default=None)
            por = f"; {_de_a(maior.ini + x.abre, maior.fim + x.abre)} é “{maior.dados.get('titulo', maior.tipo)}”" if maior else ""
            texto = f"{NOMES[d]}: a Rotina não tem {tempo(m)} livres seguidas{por}."
        if movido := _mover(grades[d], inicio, m):
            h, y = movido
            propostas.append(_proposta(f"Estudar {NA[d]} {_de_a(y.estudo.ini + y.abre, y.estudo.fim + y.abre)}",
                                       semana | {d: (h, m)}))
        for outro in ((d + k) % 7 for k in range(1, 7)):  # o dia de folga mais perto em que cabe
            if outro in semana or outro not in grades:
                continue
            y = encaixar(grades[outro], ("", m))
            if y.estudo and y.livre >= LAZER_MIN:
                nova = {k: v for k, v in semana.items() if k != d} | {outro: ("", m)}
                propostas.append(_proposta(f"Passar para {NA[outro][3:]}, "
                                           f"{_de_a(y.estudo.ini + y.abre, y.estudo.fim + y.abre)}", nova))
                break
        if not propostas and (curto := _encurtar(grades[d], inicio, m)):
            h, tam, y = curto
            propostas.append(_proposta(f"Estudar {tempo(tam)} {NA[d]}, "
                                       f"{_de_a(y.estudo.ini + y.abre, y.estudo.fim + y.abre)}", semana | {d: (h, tam)}))
        if len(semana) > 1:
            propostas.append(_proposta(f"Folga {NA[d]}", {k: v for k, v in semana.items() if k != d}))
        return {"dia": d, "tipo": "conflito", "texto": texto, "propostas": propostas}
    if x.livre < LAZER_MIN <= encaixar(grades[d], None).livre:
        sobra = "não sobra tempo livre" if x.livre == 0 else f"sobram só {tempo(x.livre)} livres"
        texto = (f"{NOMES[d]}: com {tempo(m)} de estudo, {sobra}. A regra 2 é o lazer com hora marcada: sem ele, "
                 "a madrugada costuma cobrar a conta.")
        if curto := _encurtar(grades[d], inicio, m):
            h, tam, _ = curto
            propostas.append(_proposta(f"Estudar {tempo(tam)} {NA[d]}", semana | {d: (h, tam)}))
        return {"dia": d, "tipo": "atencao", "texto": texto, "propostas": propostas}
    return None


def _nome(dias: list[int]) -> str:
    if len(dias) == 1:
        return NOMES[dias[0]]
    if len(dias) == 2:
        return f"{NOMES[dias[0]]} e {NOMES[dias[1]].lower()}"
    if dias == list(range(dias[0], dias[-1] + 1)):
        return f"{NOMES[dias[0]]} a {NOMES[dias[-1]].lower()}"
    return ", ".join(CURTOS[d] for d in dias[:-1]) + f" e {CURTOS[dias[-1]]}"


def montar(rotina: dict, semana: Semana) -> dict:
    """A rotina.json com o estudo do Cronograma dentro: as grades (os dias que ficaram iguais, juntos), o estudo de
    cada dia em que ele coube, e os avisos com as propostas."""
    coringa = rotina.get("coringa")
    grades = {d: {**g, "coringa": coringa} if coringa else g for g in rotina.get("grades", []) for d in g["dias"]}
    dias = {d: encaixar(g, semana.get(d)) for d, g in sorted(grades.items())}
    grupos: dict[tuple, list[int]] = {}
    for d, x in dias.items():
        chave = (x.abre, tuple((b.ini, b.fim, b.tipo, tuple(sorted(b.dados.items()))) for b in x.blocos))
        grupos.setdefault(chave, []).append(d)
    return {**rotina,
            "grades": [{"nome": _nome(ds), "dias": ds, "blocos": dias[ds[0]].blocos_json()} for ds in grupos.values()],
            "estudo": [{"dia": d, "inicio": relogio(x.estudo.ini + x.abre), "fim": relogio(x.estudo.fim + x.abre),
                        "minutos": x.estudo.dur, "marcada": bool(semana[d][0])}
                       for d, x in dias.items() if x.estudo],
            "avisos": [a for d in sorted(semana) if d in dias and (a := _aviso(d, dias[d], semana, grades))]}
