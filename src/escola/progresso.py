"""O progresso da Escola num SQLite do PC: o estado de cada item e de cada revisão, o plano de cada dia, os ajustes
do Cronograma (dias, horas e concursos), as perguntas que ele escreve em cada assunto e cada tentativa de responder
as perguntas de fixação e as provinhas, o aquecimento de cada dia (as perguntas escolhidas e a aula do resumo) e as
rodadas do caderno de erros (as perguntas de cada uma) e o simulado em andamento (quando começou e o que já
marcou). Uma cópia por dia fica em copias/."""
import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

ESTADOS = ("novo", "feito", "depois")
MINUTOS_DIA = 60  # o começo; ele muda na tela
DIAS = "0,1,2,3,4,5"  # segunda a sábado (0 é segunda)

ESQUEMA = """
CREATE TABLE IF NOT EXISTS estados (item TEXT PRIMARY KEY, estado TEXT NOT NULL, em TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS planos (dia TEXT PRIMARY KEY, itens TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS ajustes (chave TEXT PRIMARY KEY, valor TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS notas (assunto TEXT PRIMARY KEY, texto TEXT NOT NULL, em TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS respostas (alvo TEXT NOT NULL, em TEXT NOT NULL, marcadas TEXT NOT NULL,
                                      acertos INTEGER NOT NULL, total INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS respostas_alvo ON respostas (alvo);
CREATE TABLE IF NOT EXISTS aquecimentos (dia TEXT PRIMARY KEY, questoes TEXT NOT NULL, leitura TEXT);
CREATE TABLE IF NOT EXISTS rodadas (alvo TEXT PRIMARY KEY, questoes TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS simulados (item TEXT PRIMARY KEY, inicio TEXT NOT NULL, marcadas TEXT NOT NULL);
"""


class Progresso:
    def __init__(self, caminho: Path | str):
        self._conn = sqlite3.connect(caminho, check_same_thread=False)
        self._conn.executescript(ESQUEMA)
        if "leitura" not in {c[1] for c in self._conn.execute("PRAGMA table_info(aquecimentos)")}:
            self._conn.execute("ALTER TABLE aquecimentos ADD COLUMN leitura TEXT")  # a tabela de 26/10 não tinha
        self._trava = threading.Lock()

    def estados(self) -> dict[str, tuple[str, str]]:
        """item → (estado, quando). Item que não está aqui é novo."""
        with self._trava:
            return {i: (e, em) for i, e, em in self._conn.execute("SELECT item, estado, em FROM estados")}

    def marcar(self, item: str, estado: str, agora: datetime) -> None:
        if estado not in ESTADOS:
            raise ValueError(f"estado inválido: {estado}")
        with self._trava, self._conn:
            if estado == "novo":
                self._conn.execute("DELETE FROM estados WHERE item = ?", (item,))
            else:
                self._conn.execute("INSERT OR REPLACE INTO estados VALUES (?, ?, ?)",
                                   (item, estado, agora.isoformat(timespec="seconds")))

    def copiar(self, pasta: Path, dia: str, manter: int = 14) -> Path | None:
        """Guarda a cópia do dia em `pasta` (progresso-<dia>.db) e apaga as mais velhas que as `manter` mais novas.
        None quando a do dia já existe."""
        destino = pasta / f"progresso-{dia}.db"
        if destino.exists():
            return None
        pasta.mkdir(parents=True, exist_ok=True)
        provisoria = destino.with_suffix(".tmp")
        alvo = sqlite3.connect(provisoria)
        try:
            with self._trava:
                self._conn.backup(alvo)
        finally:
            alvo.close()
        provisoria.replace(destino)
        for velha in sorted(pasta.glob("progresso-*.db"))[:-manter]:
            velha.unlink()
        return destino

    def ajuste(self, chave: str, padrao: str = "") -> str:
        with self._trava:
            linha = self._conn.execute("SELECT valor FROM ajustes WHERE chave = ?", (chave,)).fetchone()
        return linha[0] if linha else padrao

    def definir(self, chave: str, valor: str) -> None:
        with self._trava, self._conn:
            self._conn.execute("INSERT OR REPLACE INTO ajustes VALUES (?, ?)", (chave, valor))

    def minutos_dia(self) -> int:
        return int(self.ajuste("minutos_dia", str(MINUTOS_DIA)))

    def definir_minutos_dia(self, minutos: int) -> None:
        self.definir("minutos_dia", str(minutos))

    def semana(self) -> dict[int, tuple[str, int]]:
        """Cada dia de estudo (0 é segunda) com a hora de começar ("" se não marcou) e os minutos. Antes de ele mexer
        dia a dia, sai dos ajustes antigos: os mesmos minutos e a mesma hora em todos os dias."""
        guardada = self.ajuste("semana")
        if guardada:
            return {int(d): (h, int(m)) for d, (h, m) in sorted(json.loads(guardada).items(), key=lambda x: int(x[0]))}
        antigos = tuple(int(d) for d in self.ajuste("dias", DIAS).split(",") if d)
        return {d: (self.ajuste("horario"), self.minutos_dia()) for d in antigos}

    def definir_semana(self, semana: dict[int, tuple[str, int]]) -> None:
        self.definir("semana", json.dumps({str(d): [h, m] for d, (h, m) in sorted(semana.items())}))

    def dias(self) -> tuple[int, ...]:
        """Os dias da semana em que ele estuda (0 é segunda)."""
        return tuple(self.semana())

    def minutos_por_dia(self) -> dict[int, int]:
        return {d: m for d, (_, m) in self.semana().items()}

    def concursos(self) -> tuple[str, ...]:
        """Os concursos que entram no Cronograma; vazio é todos."""
        return tuple(c for c in self.ajuste("concursos").split(",") if c)

    def nota(self, assunto: str) -> str:
        with self._trava:
            linha = self._conn.execute("SELECT texto FROM notas WHERE assunto = ?", (assunto,)).fetchone()
        return linha[0] if linha else ""

    def guardar_nota(self, assunto: str, texto: str, agora: datetime) -> None:
        with self._trava, self._conn:
            self._conn.execute("INSERT OR REPLACE INTO notas VALUES (?, ?, ?)",
                               (assunto, texto, agora.isoformat(timespec="seconds")))

    def responder(self, alvo: str, marcadas: list[int], acertos: int, agora: datetime) -> None:
        """Uma tentativa de responder as perguntas de um item ou a provinha de uma matéria (alvo `mod:<matéria>`)."""
        with self._trava, self._conn:
            self._conn.execute("INSERT INTO respostas VALUES (?, ?, ?, ?, ?)",
                               (alvo, agora.isoformat(timespec="seconds"), json.dumps(marcadas), acertos, len(marcadas)))

    def tentativas(self, alvo: str) -> list[dict]:
        """Da primeira à última: quando, o que marcou e quantas acertou."""
        with self._trava:
            linhas = self._conn.execute("SELECT em, marcadas, acertos, total FROM respostas WHERE alvo = ? ORDER BY rowid",
                                        (alvo,)).fetchall()
        return [{"em": em, "marcadas": json.loads(m), "acertos": a, "total": t} for em, m, a, t in linhas]

    def respostas(self) -> list[dict]:
        """Todas as tentativas, da primeira à última: o alvo, quando, o que marcou e quantas acertou."""
        with self._trava:
            linhas = self._conn.execute("SELECT alvo, em, marcadas, acertos, total FROM respostas ORDER BY rowid").fetchall()
        return [{"alvo": alvo, "em": em, "marcadas": json.loads(m), "acertos": a, "total": t}
                for alvo, em, m, a, t in linhas]

    def aquecimento(self, dia: str) -> tuple[list[tuple[str, int]], str | None] | None:
        """O aquecimento do dia, se já foi montado: as perguntas (o alvo e a posição de cada uma) e o item do
        resumo e dos cartões."""
        with self._trava:
            linha = self._conn.execute("SELECT questoes, leitura FROM aquecimentos WHERE dia = ?", (dia,)).fetchone()
        return ([(alvo, n) for alvo, n in json.loads(linha[0])], linha[1]) if linha else None

    def guardar_aquecimento(self, dia: str, questoes: list[tuple[str, int]], leitura: str | None) -> None:
        with self._trava, self._conn:
            self._conn.execute("INSERT OR IGNORE INTO aquecimentos VALUES (?, ?, ?)", (dia, json.dumps(questoes), leitura))

    def rodada(self, alvo: str) -> list[tuple[str, int]] | None:
        """As perguntas de uma rodada do caderno de erros (alvo `erros:<dia>:<n>`): o alvo e a posição de cada uma."""
        with self._trava:
            linha = self._conn.execute("SELECT questoes FROM rodadas WHERE alvo = ?", (alvo,)).fetchone()
        return [(a, n) for a, n in json.loads(linha[0])] if linha else None

    def rodadas(self, prefixo: str) -> list[str]:
        """As rodadas cujo alvo começa com `prefixo` (as de um dia), da primeira à última."""
        with self._trava:
            return [a for (a,) in self._conn.execute("SELECT alvo FROM rodadas WHERE alvo LIKE ? ORDER BY rowid",
                                                     (prefixo.replace("%", "") + "%",))]

    def guardar_rodada(self, alvo: str, questoes: list[tuple[str, int]]) -> None:
        with self._trava, self._conn:
            self._conn.execute("INSERT OR IGNORE INTO rodadas VALUES (?, ?)", (alvo, json.dumps(questoes)))

    def rascunho(self, item: str) -> dict | None:
        """O simulado em andamento: quando começou e o que já marcou (None na que ainda está em branco)."""
        with self._trava:
            linha = self._conn.execute("SELECT inicio, marcadas FROM simulados WHERE item = ?", (item,)).fetchone()
        return {"inicio": linha[0], "marcadas": json.loads(linha[1])} if linha else None

    def guardar_rascunho(self, item: str, inicio: str, marcadas: list[int | None]) -> None:
        with self._trava, self._conn:
            self._conn.execute("INSERT OR REPLACE INTO simulados VALUES (?, ?, ?)", (item, inicio, json.dumps(marcadas)))

    def apagar_rascunho(self, item: str) -> None:
        with self._trava, self._conn:
            self._conn.execute("DELETE FROM simulados WHERE item = ?", (item,))

    def ultimas(self) -> dict[str, tuple[int, int]]:
        """alvo → (acertos, total) da última tentativa."""
        with self._trava:
            return {alvo: (a, t) for alvo, a, t in self._conn.execute(
                "SELECT alvo, acertos, total FROM respostas r WHERE rowid = (SELECT max(rowid) FROM respostas WHERE alvo = r.alvo)")}

    def plano(self, dia: str) -> list[str] | None:
        with self._trava:
            linha = self._conn.execute("SELECT itens FROM planos WHERE dia = ?", (dia,)).fetchone()
        return json.loads(linha[0]) if linha else None

    def planos(self) -> dict[str, list[str]]:
        """O plano de cada dia já montado: dia → as tarefas."""
        with self._trava:
            return {dia: json.loads(itens) for dia, itens in self._conn.execute("SELECT dia, itens FROM planos")}

    def guardar_plano(self, dia: str, itens: list[str]) -> None:
        with self._trava, self._conn:
            self._conn.execute("INSERT OR REPLACE INTO planos VALUES (?, ?)", (dia, json.dumps(itens)))

    def fechar(self) -> None:
        self._conn.close()
