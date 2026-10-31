"""Os perfis da Escola: cada pessoa com a sua pasta em Documentos/Escola/perfis/<id>/ (progresso, Rotina, cópias).

O aparelho guarda num cookie quem está estudando. O middleware põe o Progresso desse perfil num ContextVar, e o
`DaVez` repassa cada chamada a ele: as rotas continuam escrevendo `prog.estados()`. Sem perfil válido, a API de
estudo responde 401 e a tela mostra a escolha. A lista mora em perfis.json, fora do repositório."""
import json
import re
import shutil
import threading
import unicodedata
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from starlette.requests import Request
from starlette.responses import JSONResponse

from .progresso import Progresso

COOKIE = "escola_perfil"
CORES = ("#F4A259", "#2FA58A", "#B86AD0", "#D9634E", "#5B9BD5", "#E3C567", "#8FB573", "#E07BA0")
NOME_MAX = 20
LIVRES = ("/api/saude", "/api/perfis", "/api/turma")  # a API que responde sem perfil: a escolha e a turma
PRINCIPAL = "principal"  # o perfil que recebe o progresso de antes dos perfis

_atual: ContextVar[tuple[str, Progresso] | None] = ContextVar("perfil", default=None)


def chave(nome: str) -> str:
    """O nome sem acento, sem maiúscula e sem espaço sobrando: "Péricles " e "pericles" são o mesmo nome."""
    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


class Perfis:
    def __init__(self, dados: Path, *, rotina_antiga: Path | None = None):
        self.dados = dados
        self._arq = dados / "perfis.json"
        self._abertos: dict[str, Progresso] = {}
        self._trava = threading.Lock()
        self._lista: list[dict] = []
        if self._arq.is_file():
            self._lista = json.loads(self._arq.read_text(encoding="utf-8"))
        elif (dados / "progresso.db").is_file():
            self._migrar(rotina_antiga)

    def _migrar(self, rotina_antiga: Path | None) -> None:
        """O progresso de antes dos perfis vira o perfil principal, o dono; antes de mover, fica uma cópia."""
        pasta = self.pasta(PRINCIPAL)
        pasta.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.dados / "progresso.db", self.dados / "progresso-antes-dos-perfis.db")
        (self.dados / "progresso.db").replace(pasta / "progresso.db")
        if (self.dados / "copias").is_dir():
            (self.dados / "copias").replace(pasta / "copias")
        if rotina_antiga and rotina_antiga.is_file():  # a rotina.json ficava na pasta do catálogo
            shutil.move(rotina_antiga, pasta / "rotina.json")
        self._lista = [{"id": PRINCIPAL, "nome": "Principal", "cor": CORES[0], "dono": True}]
        self._guardar()

    def _guardar(self) -> None:
        self.dados.mkdir(parents=True, exist_ok=True)
        provisorio = self._arq.with_suffix(".tmp")
        provisorio.write_text(json.dumps(self._lista, ensure_ascii=False, indent=1), encoding="utf-8")
        provisorio.replace(self._arq)

    def todos(self) -> list[dict]:
        return [dict(p) for p in self._lista]

    def achar(self, pid: str | None) -> dict | None:
        return next((dict(p) for p in self._lista if p["id"] == pid), None)

    def pasta(self, pid: str) -> Path:
        return self.dados / "perfis" / pid

    def progresso(self, pid: str) -> Progresso:
        """O SQLite do perfil, aberto uma vez e guardado."""
        with self._trava:
            if pid not in self._abertos:
                self.pasta(pid).mkdir(parents=True, exist_ok=True)
                self._abertos[pid] = Progresso(self.pasta(pid) / "progresso.db")
            return self._abertos[pid]

    def _nome_valido(self, nome: str, menos: str | None = None) -> str:
        nome = " ".join(nome.split())
        if not 1 <= len(nome) <= NOME_MAX:
            raise ValueError(f"O nome precisa ter de 1 a {NOME_MAX} letras.")
        if any(chave(p["nome"]) == chave(nome) and p["id"] != menos for p in self._lista):
            raise ValueError("Já existe um perfil com esse nome.")
        return nome

    def criar(self, nome: str, cor: str | None = None) -> dict:
        """O id sai do nome e não muda mais; o primeiro perfil é o dono (quem instalou)."""
        with self._trava:
            nome = self._nome_valido(nome)
            if cor is not None and cor not in CORES:
                raise ValueError("Essa cor não está na paleta.")
            base = re.sub(r"[^a-z0-9]+", "-", chave(nome)).strip("-") or "perfil"
            ids = {p["id"] for p in self._lista}
            pid, n = base, 2
            while pid in ids:
                pid, n = f"{base}-{n}", n + 1
            usadas = {p["cor"] for p in self._lista}
            livre = next((c for c in CORES if c not in usadas), CORES[len(self._lista) % len(CORES)])
            perfil = {"id": pid, "nome": nome, "cor": cor or livre, "dono": not self._lista}
            self._lista.append(perfil)
            self._guardar()
            return dict(perfil)

    def editar(self, pid: str, nome: str | None = None, cor: str | None = None) -> dict:
        with self._trava:
            perfil = next((p for p in self._lista if p["id"] == pid), None)
            if perfil is None:
                raise KeyError(pid)
            if cor is not None and cor not in CORES:
                raise ValueError("Essa cor não está na paleta.")
            if nome is not None:
                perfil["nome"] = self._nome_valido(nome, menos=pid)
            if cor is not None:
                perfil["cor"] = cor
            self._guardar()
            return dict(perfil)

    @contextmanager
    def usando(self, pid: str) -> Iterator[None]:
        """Aponta o `DaVez` para este perfil: no pedido do aparelho dele ou para montar o cartão da turma."""
        token = _atual.set((pid, self.progresso(pid)))
        try:
            yield
        finally:
            _atual.reset(token)

    def fechar(self) -> None:
        with self._trava:
            for p in self._abertos.values():
                p.fechar()
            self._abertos.clear()


class DaVez:
    """O Progresso de quem fez o pedido."""

    def __getattr__(self, nome: str):
        atual = _atual.get()
        if atual is None:
            raise RuntimeError("pedido sem perfil")
        return getattr(atual[1], nome)


def perfil_da_vez() -> str | None:
    atual = _atual.get()
    return atual[0] if atual else None


class PorPerfil:
    """Middleware: o cookie diz o perfil do aparelho; sem perfil válido, a API de estudo responde 401."""

    def __init__(self, app, perfis: Perfis):
        self.app = app
        self.perfis = perfis

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        pid = Request(scope).cookies.get(COOKIE)
        if self.perfis.achar(pid):
            with self.perfis.usando(pid):
                await self.app(scope, receive, send)
            return
        caminho = scope["path"]
        if caminho.startswith("/api/") and not caminho.startswith(LIVRES):
            await JSONResponse({"perfil": None}, status_code=401)(scope, receive, send)
            return
        await self.app(scope, receive, send)
