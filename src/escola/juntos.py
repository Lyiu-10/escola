"""Assistir junto: uma sala por vídeo, na memória do servidor.

Quem está na sala dá play, pausa ou pula, e o comando vai a todos os outros pelo fluxo da sala (Server-Sent Events);
o volume fica com cada aparelho. O servidor guarda o estado (tocando ou pausado, a posição e quando ela foi medida),
para quem entra atrasado cair no ponto certo. Quem está com a Escola aberta ouve o fluxo das salas abertas e recebe
o convite. A sala fecha quando o último sai, ou depois de PARADA_MAX sem ninguém mexer. Tudo roda no laço do
servidor (rotas async), então as filas não precisam de trava."""
import asyncio
import itertools
import time
from collections.abc import Callable
from dataclasses import dataclass, field

PARADA_MAX = 3 * 3600  # segundos sem comando: a sala esquecida aberta à noite fecha sozinha
VAZIA_MAX = 60  # a sala aberta que ninguém conectou (a aba fechou antes) some depois disso


@dataclass
class Sala:
    item: str
    titulo: str
    aberta_por: dict  # o perfil {id, nome, cor}
    criada: float
    tocando: bool = False
    posicao: float = 0.0
    medida: float = 0.0  # quando a posição foi medida
    mexida: float = 0.0  # o último comando
    membros: dict[int, dict] = field(default_factory=dict)  # conexão → perfil
    filas: dict[int, asyncio.Queue] = field(default_factory=dict)


class Salas:
    def __init__(self, relogio: Callable[[], float] = time.monotonic):
        self._relogio = relogio
        self._salas: dict[str, Sala] = {}  # a sala tem o id do item
        self._ouvintes: dict[int, asyncio.Queue] = {}
        self._conexoes = itertools.count(1)

    def _agora(self, s: Sala) -> float:
        return s.posicao + (self._relogio() - s.medida if s.tocando else 0.0)

    def _membros(self, s: Sala) -> list[dict]:
        return list({p["id"]: p for p in s.membros.values()}.values())

    def estado(self, sala: str) -> dict | None:
        s = self._salas.get(sala)
        if s is None:
            return None
        return {"sala": sala, "item": s.item, "titulo": s.titulo, "tocando": s.tocando,
                "posicao": round(self._agora(s), 2), "membros": self._membros(s)}

    def lista(self) -> list[dict]:
        return [{"sala": k, "item": s.item, "titulo": s.titulo, "aberta_por": s.aberta_por, "membros": self._membros(s)}
                for k, s in self._salas.items()]

    def _avisar_ouvintes(self) -> None:
        msg = {"tipo": "salas", "salas": self.lista()}
        for fila in self._ouvintes.values():
            fila.put_nowait(msg)

    def _espalhar(self, s: Sala, msg: dict, menos: int | None = None) -> None:
        for conexao, fila in s.filas.items():
            if conexao != menos:
                fila.put_nowait(msg)

    def abrir(self, item: str, titulo: str, perfil: dict) -> dict:
        """A sala do vídeo; se já existe, é a mesma (uma por vídeo)."""
        self.limpar()
        if item not in self._salas:
            agora = self._relogio()
            self._salas[item] = Sala(item, titulo, perfil, criada=agora, medida=agora, mexida=agora)
            self._avisar_ouvintes()
        return self.estado(item)

    def entrar(self, sala: str, perfil: dict) -> tuple[int, asyncio.Queue] | None:
        """Liga um aparelho à sala: a fila dele já começa com o estado (para cair no ponto certo)."""
        s = self._salas.get(sala)
        if s is None:
            return None
        conexao, fila = next(self._conexoes), asyncio.Queue()
        s.membros[conexao], s.filas[conexao] = perfil, fila
        fila.put_nowait({"tipo": "entrou", "conexao": conexao, **self.estado(sala)})
        self._espalhar(s, {"tipo": "membros", "membros": self._membros(s)}, menos=conexao)
        self._avisar_ouvintes()
        return conexao, fila

    def sair(self, sala: str, conexao: int) -> None:
        s = self._salas.get(sala)
        if s is None or conexao not in s.membros:
            return
        del s.membros[conexao], s.filas[conexao]
        if s.membros:
            self._espalhar(s, {"tipo": "membros", "membros": self._membros(s)})
        else:
            del self._salas[sala]
        self._avisar_ouvintes()

    def comando(self, sala: str, acao: str, posicao: float, perfil: dict, conexao: int | None = None) -> dict | None:
        """Play ou pausa, na posição de quem mandou; vai a todos menos a ele."""
        s = self._salas.get(sala)
        if s is None:
            return None
        agora = self._relogio()
        s.tocando, s.posicao, s.medida, s.mexida = acao == "play", max(0.0, posicao), agora, agora
        self._espalhar(s, {"tipo": "comando", "por": perfil["nome"], **self.estado(sala)}, menos=conexao)
        return self.estado(sala)

    def limpar(self) -> None:
        """Fecha a sala parada há PARADA_MAX e a que ninguém conectou em VAZIA_MAX."""
        agora = self._relogio()
        for k, s in list(self._salas.items()):
            if agora - s.mexida > PARADA_MAX or (not s.membros and agora - s.criada > VAZIA_MAX):
                self._espalhar(s, {"tipo": "fechada"})
                del self._salas[k]
                self._avisar_ouvintes()

    def ouvir(self) -> tuple[int, asyncio.Queue]:
        """O fluxo das salas abertas, para o convite: começa com a lista de agora."""
        n, fila = next(self._conexoes), asyncio.Queue()
        self._ouvintes[n] = fila
        fila.put_nowait({"tipo": "salas", "salas": self.lista()})
        return n, fila

    def parar_de_ouvir(self, n: int) -> None:
        self._ouvintes.pop(n, None)
