"""O Cronograma: o que estudar em cada dia, pelas regras da pesquisa de 25/10/2026 (a spec da plataforma tem as
fontes). Ele escolhe os dias da semana e as horas por dia; o resto sai daqui.

- Revisão ativa espaçada: um assunto estudado (itens principais feitos) volta em +1, +7 e +21 dias; depois, a cada
  10% do tempo que falta até a prova (no mínimo 21 dias), com uma revisão garantida nas 3 últimas semanas antes da
  prova (Cepeda et al. 2008; intervalo fixo basta: Latimier et al. 2021). Revisão atrasada não recomeça a série.
- As revisões abrem o dia (a tarefa mais curta primeiro) e ocupam no máximo 30% do tempo enquanto há matéria nova; a
  que não cabe fica para o dia seguinte.
- Provas anteriores viram simulados no último dia de estudo da semana, sozinhos no dia: o primeiro quando 30% dos
  assuntos do concurso estão estudados; depois a cada 4 semanas, a cada 2 nas últimas 12 e toda semana nas últimas 4.
- Redação: uma por semana no dia do meio da semana de estudo; nas últimas 6 semanas antes da prova, mais uma no
  primeiro dia.
- O resto do tempo é matéria nova, na ordem do caminho, sem intercalar matérias (Brunmair & Richter 2019). Aula ou
  leitura com perguntas de fixação conta 1 minuto por pergunta e mais 1 de correção. O último item pode passar do
  tempo do dia, até 1,6 vez o dia; o que passaria disso abre o dia seguinte (o primeiro item novo do dia entra
  sempre, menos no dia da redação). Sem esse limite, com as aulas de 1 a 2 horas do Português (30/10/2026), o dia
  de 2 h chegava a 3h47 e o da redação a 4 h.
- A provinha de uma matéria (questões de provas anteriores) entra no primeiro dia de estudo depois que a matéria nova
  dela acaba, uma por dia, logo depois das revisões; conta 2 minutos por questão. Os tempos são escolha nossa.
"""
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, timedelta

from . import caminho
from .catalogo import Catalogo, Concurso, Item

INTERVALOS = (1, 7, 21)
FRACAO = 0.10  # o intervalo de manutenção, como fração do tempo até a prova
MANUTENCAO_MIN = 21
SEM_PROVA = 30  # o intervalo de manutenção quando não há prova marcada pela frente
JANELA_FINAL = 21
REVISAO_MIN = 15
TETO_REVISAO = 0.30
ESTOURO = 1.6  # até quanto o dia pode passar do tempo marcado com o último item novo
COBERTURA_SIMULADO = 0.30
REDACAO_MIN = 80
POR_PERGUNTA = 1  # minutos por pergunta de fixação
CORRECAO = 1  # minutos para ler a correção das perguntas de um item
POR_QUESTAO = 2  # minutos por questão de provinha
RETA_FINAL = 42  # dias: nas últimas 6 semanas, duas redações por semana
HORIZONTE = 540  # o cronograma não projeta além de um ano e meio
DIAS_PADRAO = (0, 1, 2, 3, 4, 5)  # segunda a sábado: a escolha dele em 25/10/2026
NOMES_DIAS = ("segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo")


@dataclass(frozen=True)
class Tarefa:
    id: str
    tipo: str  # aula, leitura, prova (do catálogo), revisao, redacao
    titulo: str
    minutos: int
    assunto: str | None = None
    concurso: str | None = None
    numero: int = 0  # a revisão nº


@dataclass(frozen=True)
class Dia:
    data: date
    folga: bool
    tarefas: tuple[Tarefa, ...]


def eh_de_prova(aid: str) -> bool:
    return aid.startswith("provas-")


def id_revisao(aid: str, k: int) -> str:
    return f"rev:{aid}:{k}"


def id_provinha(mid: str) -> str:
    return f"mod:{mid}"


def duracao(cat: Catalogo, item: Item) -> int:
    """O tempo do item no plano: o material e, se houver, as perguntas dele. Questão de prova, ou escrita no
    formato da banca, conta como na provinha (2 min); pergunta feita a partir da aula, 1 min."""
    reais = cat.reais.get(item.id, ()) or cat.estilo.get(item.id, ())
    if reais:
        return item.minutos + len(reais) * POR_QUESTAO + CORRECAO
    perguntas = cat.perguntas.get(item.id, ())
    return item.minutos + (len(perguntas) * POR_PERGUNTA + CORRECAO if perguntas else 0)


def provinha(cat: Catalogo, mid: str) -> Tarefa | None:
    achado = next(((c, m) for c in cat.concursos for m in c.materias if m.id == mid), None)
    if achado is None or mid not in cat.provinhas:
        return None
    c, m = achado
    return Tarefa(id_provinha(mid), "provinha", f"Provinha de {m.nome}", POR_QUESTAO * len(cat.provinhas[mid]),
                  concurso=c.id)


def _prova(c: Concurso, situacao: dict | None, hoje: date | None) -> tuple[date | None, bool]:
    for d in (situacao or {}).get("datas", []):
        achada = _data(d.get("data", ""))
        if d.get("confirmada") and "prova" in d.get("evento", "").lower() and achada and (not hoje or achada >= hoje):
            return achada, True
    if m := re.fullmatch(r"(\d{4})-(\d{2})(?:-(\d{2}))?", c.prova_prevista or ""):
        prevista = date(int(m[1]), int(m[2]), int(m[3] or 15))
        if hoje and prevista < hoje:
            return None, False  # passou: falta remontar o concurso
        return prevista, m[3] is not None
    return None, False


def data_da_prova(c: Concurso, situacao: dict | None, hoje: date | None = None) -> date | None:
    """A prova confirmada pela busca semanal (uma data que já passou é de ciclo velho e não conta); senão, a do
    catálogo: o dia, quando o edital já marcou, ou o meio do mês provável pelo histórico."""
    return _prova(c, situacao, hoje)[0]


def prova_marcada(c: Concurso, situacao: dict | None, hoje: date | None = None) -> bool:
    """A data da prova é a do edital (pela busca ou pelo catálogo), não a estimada pelo histórico."""
    return _prova(c, situacao, hoje)[1]


def _data(texto: str) -> date | None:
    if m := re.search(r"(\d{4})-(\d{2})-(\d{2})", texto):
        return date(int(m[1]), int(m[2]), int(m[3]))
    if m := re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", texto):
        return date(int(m[3]), int(m[2]), int(m[1]))
    return None


def tarefa_de(cat: Catalogo, tid: str) -> Tarefa | None:
    """Uma tarefa guardada no plano do dia, pelo id; None quando saiu do catálogo."""
    if tid.startswith("rev:"):
        _, aid, k = tid.split(":")
        a = cat.assuntos.get(aid)
        return Tarefa(tid, "revisao", f"Revisão de {a.nome}", REVISAO_MIN, assunto=aid, numero=int(k)) if a else None
    if tid.startswith("red:"):
        _, _, cid = tid.split(":")
        return Tarefa(tid, "redacao", "Redação da semana", REDACAO_MIN, concurso=cid)
    if tid.startswith("mod:"):
        return provinha(cat, tid[4:])
    i = cat.itens.get(tid)
    return Tarefa(i.id, i.tipo, i.titulo, duracao(cat, i)) if i else None


class Simulacao:
    """Anda dia a dia a partir do estado de verdade, marcando como feito o que cada dia planeja."""

    def __init__(self, cat: Catalogo, estados: dict, dias: Iterable[int], minutos: int | Mapping[int, int],
                 provas: dict[str, date | None]):
        """`minutos` é o tempo de cada dia de estudo: um número para todos, ou um por dia da semana (0 é segunda)."""
        self.cat, self.est, self.provas = cat, dict(estados), provas
        self.minutos = minutos if isinstance(minutos, Mapping) else dict.fromkeys(range(7), minutos)
        self.dias = sorted(set(dias))
        lugar = caminho.onde(cat)
        self.lugar = {i: (p.assunto.id, p.concurso.id) for i, p in lugar.items()}
        self.novos = [p.item for p in caminho.caminho(cat, estados) if not eh_de_prova(p.assunto.id)]
        self.do_concurso = {c.id: [a for a in c.assuntos() if not eh_de_prova(a) and cat.assuntos[a].principais]
                            for c in cat.concursos}
        self.concursos_de: dict[str, list[str]] = {}
        for c in cat.concursos:
            for a in self.do_concurso[c.id]:
                self.concursos_de.setdefault(a, []).append(c.id)
        self.estudaveis = list(self.concursos_de)
        self.simulados = {c.id: [i for a in c.assuntos() if eh_de_prova(a) for i in cat.assuntos[a].itens
                                 if i.tipo == "prova" and self._feito_em(i.id) is None] for c in cat.concursos}
        self.ultimo_simulado = {c.id: max((d for a in c.assuntos() if eh_de_prova(a) for i in cat.assuntos[a].itens
                                           if i.tipo == "prova" and (d := self._feito_em(i.id))), default=None)
                                for c in cat.concursos}
        self.redacao = [c.id for c in cat.concursos if any(a.startswith("r-") for a in c.assuntos())]
        self.provinhas = [(c.id, m.id, {i.id for a in m.assuntos if not eh_de_prova(a) for i in cat.assuntos[a].principais})
                          for c in cat.concursos for m in c.materias if m.id in cat.provinhas]

    def _feito_em(self, tid: str) -> date | None:
        e = self.est.get(tid)
        return date.fromisoformat(e[1][:10]) if e and e[0] == "feito" else None

    def estudado_em(self, aid: str) -> date | None:
        datas = [self._feito_em(i.id) for i in self.cat.assuntos[aid].principais]
        return max(datas) if datas and None not in datas else None

    def _prova_depois(self, aid: str, d: date) -> date | None:
        return min((p for c in self.concursos_de.get(aid, []) if (p := self.provas.get(c)) and p > d), default=None)

    def _intervalo(self, k: int, ultimo: date, aid: str) -> int:
        if k <= len(INTERVALOS):
            return INTERVALOS[k - 1]
        prova = self._prova_depois(aid, ultimo)
        if prova is None:
            return SEM_PROVA
        gap = max(MANUTENCAO_MIN, round(FRACAO * (prova - ultimo).days))
        janela = prova - timedelta(days=JANELA_FINAL)
        if ultimo < janela < ultimo + timedelta(days=gap):  # garante uma revisão nas 3 últimas semanas
            gap = max(7, (janela - ultimo).days)
        return gap

    def proxima_revisao(self, aid: str) -> tuple[int, date] | None:
        ultimo = self.estudado_em(aid)
        if ultimo is None:
            return None
        k = 1
        while (feita := self._feito_em(id_revisao(aid, k))) is not None:
            ultimo, k = feita, k + 1
        return k, ultimo + timedelta(days=self._intervalo(k, ultimo, aid))

    def _cobertura(self, cid: str) -> float:
        todos = self.do_concurso[cid]
        return sum(1 for a in todos if self.estudado_em(a)) / len(todos) if todos else 0.0

    def _simulado(self, d: date) -> Tarefa | None:
        if d.weekday() != self.dias[-1]:
            return None
        for c in self.cat.concursos:
            restantes, prova = self.simulados[c.id], self.provas.get(c.id)
            if not restantes or (prova and d > prova) or self._cobertura(c.id) < COBERTURA_SIMULADO:
                continue
            if (ultimo := self.ultimo_simulado[c.id]) is not None:
                semanas = (prova - d).days / 7 if prova else 99
                if (d - ultimo).days < (7 if semanas <= 4 else 14 if semanas <= 12 else 28):
                    continue
            i = restantes[0]
            return Tarefa(i.id, "prova", i.titulo, i.minutos, assunto=self.lugar[i.id][0], concurso=c.id)
        return None

    def _redacao(self, d: date) -> Tarefa | None:
        alvo = [c for c in self.redacao if not self.provas.get(c) or self.provas[c] >= d]
        if not alvo:
            return None
        meio = self.dias[len(self.dias) // 2]
        prova = min((self.provas[c] for c in alvo if self.provas.get(c)), default=None)
        reta = prova is not None and (prova - d).days <= RETA_FINAL
        if d.weekday() == meio or (reta and d.weekday() == self.dias[0]):
            return Tarefa(f"red:{d.isoformat()}:{alvo[0]}", "redacao", "Redação da semana", REDACAO_MIN,
                          concurso=alvo[0])
        return None

    def _provinha(self, d: date, fora: set[str]) -> Tarefa | None:
        """A primeira provinha pronta: a matéria nova dela acabou, ela não foi feita e a prova não passou."""
        for cid, mid, itens in self.provinhas:
            tid = id_provinha(mid)
            prova = self.provas.get(cid)
            if tid in fora or self._feito_em(tid) or (prova and d > prova):
                continue
            if itens and all(self._feito_em(i) for i in itens):
                return provinha(self.cat, mid)
        return None

    def planejar(self, d: date, gasto: int = 0, fora: Iterable[str] = ()) -> list[Tarefa]:
        """O dia `d`: revisões vencidas, a redação e matéria nova até o tempo do dia. `gasto` é o que já foi feito
        hoje (quando ele muda o tempo no meio do dia) e `fora`, o que não pode entrar de novo."""
        if d.weekday() not in self.dias:
            return []
        if gasto == 0 and (sim := self._simulado(d)):
            return [sim]
        fora = set(fora)
        tarefas, total = [], gasto
        minutos = self.minutos.get(d.weekday(), 0)
        teto = minutos * TETO_REVISAO if self.novos else minutos
        devidas = sorted((dev, aid, k) for aid in self.estudaveis
                         if (r := self.proxima_revisao(aid)) for k, dev in [r] if dev <= d)
        for _, aid, k in devidas:
            if id_revisao(aid, k) in fora:
                continue
            if tarefas and total - gasto + REVISAO_MIN > teto:  # pelo menos uma, mesmo num dia curto
                break
            tarefas.append(Tarefa(id_revisao(aid, k), "revisao", f"Revisão de {self.cat.assuntos[aid].nome}",
                                  REVISAO_MIN, assunto=aid, numero=k))
            total += REVISAO_MIN
        if prov := self._provinha(d, fora):
            tarefas.append(prov)
            total += prov.minutos
        redacao = self._redacao(d)
        if redacao and redacao.id not in fora:
            total += redacao.minutos
        else:
            redacao = None
        novo = False
        for i in self.novos:
            if total >= minutos and (tarefas or redacao):
                break
            if i.id in fora:
                continue
            tempo = duracao(self.cat, i)
            # A aula longa que não cabe abre o dia seguinte (30/10). Só a revisão não a segura: o dia seguinte também
            # tem revisão, e ela nunca entraria.
            if (novo or redacao) and total + tempo > minutos * ESTOURO:
                break
            novo = True
            tarefas.append(Tarefa(i.id, i.tipo, i.titulo, tempo, assunto=self.lugar[i.id][0],
                                  concurso=self.lugar[i.id][1]))
            total += tempo
        return tarefas + ([redacao] if redacao else [])

    def marcar(self, d: date, tarefas: Iterable[Tarefa]) -> None:
        feitos = set()
        for t in tarefas:
            if self._feito_em(t.id) is None:
                self.est[t.id] = ("feito", d.isoformat())
            feitos.add(t.id)
            if t.tipo == "prova":
                for c, restantes in self.simulados.items():
                    if any(i.id == t.id for i in restantes):
                        self.simulados[c] = [i for i in restantes if i.id != t.id]
                        self.ultimo_simulado[c] = d
        self.novos = [i for i in self.novos if i.id not in feitos]


def projetar(cat: Catalogo, estados: dict, dias: Iterable[int], minutos: int | Mapping[int, int],
             provas: dict[str, date | None],
             hoje: date, plano_hoje: list[Tarefa] | None = None) -> list[Dia]:
    """Do dia de hoje (com o plano já guardado, se houver) até acabar a matéria nova e passar a última prova."""
    sim = Simulacao(cat, estados, dias, minutos, provas)
    ultima = max((p for p in provas.values() if p), default=None)
    saida = []
    for n in range(HORIZONTE):
        d = hoje + timedelta(days=n)
        tarefas = plano_hoje if n == 0 and plano_hoje is not None else sim.planejar(d)
        sim.marcar(d, tarefas)
        saida.append(Dia(d, d.weekday() not in sim.dias, tuple(tarefas)))
        if not sim.novos and (ultima is None or d >= ultima):
            break
    return saida


def termino(cat: Catalogo, dias_projetados: list[Dia], estados: dict) -> dict[str, date | None]:
    """Quando a matéria nova de cada concurso termina, pelo cronograma; None se passa do horizonte."""
    faltam = {c.id: {i.id for a in c.assuntos() if not eh_de_prova(a) for i in cat.assuntos[a].principais
                     if estados.get(i.id, ("",))[0] != "feito"} for c in cat.concursos}
    fim: dict[str, date | None] = {c: (None if ids else date.min) for c, ids in faltam.items()}
    for dia in dias_projetados:
        for t in dia.tarefas:
            for c, ids in faltam.items():
                if t.id in ids:
                    ids.discard(t.id)
                    if not ids:
                        fim[c] = dia.data
    return fim
