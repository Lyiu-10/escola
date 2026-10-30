"""O texto de cada aula e leitura principal, para montar e conferir as perguntas de fixação: a legenda do vídeo, com
o minuto de cada fala, e o texto do PDF ou da página, com a página. Fica em Documentos\\Escola\\textos, um arquivo
por item (<id>.txt), com as marcas que o conferir lê: [12:30] no vídeo, [p. 12] no PDF.

A legenda vem do YouTube pelo yt-dlp, uma por vez e com pausa. Se o YouTube responder "429 Too Many Requests", a
gente espera; se barrar vários vídeos seguidos, os outros ficam para outra hora. Com `ouvir`, o vídeo sem legenda
vira texto aqui mesmo: baixa só o áudio, e o Whisper transcreve no PC.
"""
import os
import re
import shutil
import subprocess
import tempfile
import time
from html.parser import HTMLParser
from pathlib import Path

import httpx
import numpy as np

from . import caminho
from .catalogo import Catalogo, Item, youtube

PAUSA = 10  # segundos entre uma legenda e a próxima
ESPERA_429 = 180  # segundos de espera quando o YouTube pede calma
SEGUIDAS_429 = 3  # vídeos seguidos barrados: o YouTube não libera tão cedo, e os outros vídeos ficam para outra hora
JANELA = 30  # segundos de fala por linha do texto
TEXTO_MIN = 500  # letras: menos que isso é só um título (legenda que não veio, PDF escaneado)
PAGINAS = 60  # quantas páginas tirar a partir do #page= (o item é um capítulo de um livro inteiro)
PDFTOTEXT_GIT = Path(r"C:\Program Files\Git\mingw64\bin\pdftotext.exe")
TEMPO = re.compile(r"(\d+):(\d{2}):(\d{2})\.\d{3} -->")
WHISPER = "large-v3-turbo"  # o mesmo do transcritor de reuniões, já baixado no PC


def _hora(segundos: int) -> str:
    h, resto = divmod(segundos, 3600)
    return f"[{h}:{resto // 60:02d}:{resto % 60:02d}]" if h else f"[{resto // 60}:{resto % 60:02d}]"


def legenda(vtt: str) -> str:
    """A legenda em linhas de JANELA segundos, cada uma com o minuto em que começa. A legenda automática repete a
    linha anterior em cada bloco: só entra a linha que ainda não entrou."""
    linhas: list[tuple[int, str]] = []
    inicio = None  # antes do primeiro tempo vem o cabeçalho (WEBVTT, Kind, Language)
    for linha in vtt.splitlines():
        if m := TEMPO.search(linha):
            inicio = int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3])
            continue
        limpa = re.sub(r"<[^>]+>", "", linha).strip()
        if inicio is not None and limpa and (not linhas or linhas[-1][1] != limpa):
            linhas.append((inicio, limpa))
    return _janelas(linhas)


def _janelas(linhas: list[tuple[int, str]]) -> str:
    """As falas, cada uma com o segundo em que começa, em linhas de JANELA segundos com o minuto na frente."""
    saida, janela, partes = [], None, []
    for inicio, texto in linhas:
        if janela is None or inicio - janela >= JANELA:
            if partes:
                saida.append(f"{_hora(janela)} {' '.join(partes)}")
            janela, partes = inicio, []
        partes.append(texto)
    if partes:
        saida.append(f"{_hora(janela)} {' '.join(partes)}")
    return "\n".join(saida)


def _yt_dlp() -> list[str]:
    """O YouTube pede um desafio em JavaScript, e sem resolver a legenda vem com "429" ou nem vem. O yt-dlp[default]
    traz o resolvedor, o curl-cffi imita o navegador, e quem roda o JavaScript é o deno, se houver, ou o node."""
    base = [achado] if (achado := shutil.which("yt-dlp")) else ["uvx", "--from", "yt-dlp[default,curl-cffi]", "yt-dlp"]
    return [*base, "--js-runtimes", "node"] if not shutil.which("deno") and shutil.which("node") else base


def baixar_legenda(url: str, tentativas: int = 3) -> str:
    """A legenda em português do vídeo (a feita por gente, se houver; senão a automática)."""
    with tempfile.TemporaryDirectory() as pasta:
        for tentativa in range(tentativas):
            r = subprocess.run([*_yt_dlp(), "--skip-download", "--write-subs", "--write-auto-subs",
                                "--sub-langs", "pt-BR,pt", "--sub-format", "vtt", "-o", "%(id)s.%(ext)s", url],
                               cwd=pasta, capture_output=True, text=True, encoding="utf-8", errors="replace")
            vtts = sorted(Path(pasta).glob("*.vtt"), key=lambda p: (".pt-BR." not in p.name, p.name))
            if vtts:
                return legenda(vtts[0].read_text(encoding="utf-8"))
            if "429" not in r.stderr or tentativa == tentativas - 1:
                raise RuntimeError(r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "sem legenda em português")
            time.sleep(ESPERA_429)
    raise RuntimeError("sem legenda em português")


_whisper = None


def _audio(arquivo: Path) -> np.ndarray:
    """O áudio em 16 kHz e mono, como o Whisper quer, pelo ffmpeg: o faster-whisper 1.2 abre o arquivo com uma opção
    que o PyAV 19 não aceita mais."""
    if not (ffmpeg := shutil.which("ffmpeg")):
        raise RuntimeError("sem o ffmpeg para ler o áudio")
    r = subprocess.run([ffmpeg, "-nostdin", "-i", str(arquivo), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
                       capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg: {r.stderr.decode('utf-8', 'replace').strip().splitlines()[-1]}")
    return np.frombuffer(r.stdout, np.int16).astype(np.float32) / 32768


def ouvir_video(url: str) -> str:
    """O que se fala no vídeo, transcrito aqui pelo Whisper a partir do áudio: para o vídeo sem legenda ou quando o
    YouTube barra as legendas (o áudio vem de outro servidor dele, que não barra)."""
    global _whisper
    with tempfile.TemporaryDirectory() as pasta:
        r = subprocess.run([*_yt_dlp(), "-f", "bestaudio[ext=m4a]/bestaudio", "-o", "audio.%(ext)s", url],
                           cwd=pasta, capture_output=True, text=True, encoding="utf-8", errors="replace")
        audios = [a for a in Path(pasta).glob("audio.*") if a.suffix != ".part"]
        if not audios:
            raise RuntimeError(r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "o áudio não veio")
        if _whisper is None:
            from faster_whisper import WhisperModel

            _whisper = WhisperModel(WHISPER, device="cpu", compute_type="int8",
                                    cpu_threads=max(1, (os.cpu_count() or 4) - 2))  # sobra CPU para o resto do PC
        segmentos, _ = _whisper.transcribe(_audio(audios[0]), language="pt", beam_size=1, vad_filter=True,
                                           condition_on_previous_text=False)
        return _janelas([(int(s.start), s.text.strip()) for s in segmentos if s.text.strip()])


def _pdftotext() -> str:
    return shutil.which("pdftotext") or str(PDFTOTEXT_GIT)


def texto_pdf(arquivo: Path, primeira: int | None = None) -> str:
    """O texto do PDF com a página de cada trecho; com `primeira`, só PAGINAS páginas a partir dela."""
    inicio = primeira or 1
    faixa = ["-f", str(inicio), "-l", str(inicio + PAGINAS - 1)] if primeira else []
    r = subprocess.run([_pdftotext(), "-enc", "UTF-8", *faixa, str(arquivo), "-"], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode("utf-8", "replace").strip() or "pdftotext falhou")
    paginas = r.stdout.decode("utf-8", "replace").split("\f")
    return "\n".join(f"[p. {inicio + n}]\n{p.strip()}" for n, p in enumerate(paginas) if p.strip())


class _Texto(HTMLParser):
    """O texto visível de uma página: sem script, estilo e menu; uma linha por bloco."""
    FORA = {"script", "style", "noscript", "nav", "header", "footer", "svg"}
    BLOCO = {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "br", "tr", "section", "article", "blockquote"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes: list[str] = []
        self.fora = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.FORA:
            self.fora += 1
        elif tag in self.BLOCO:
            self.partes.append("\n")

    def handle_endtag(self, tag):
        if tag in self.FORA and self.fora:
            self.fora -= 1
        elif tag in self.BLOCO:
            self.partes.append("\n")

    def handle_data(self, data):
        if not self.fora:
            self.partes.append(data)

    def texto(self) -> str:
        linhas = (re.sub(r"\s+", " ", linha).strip() for linha in "".join(self.partes).splitlines())
        return "\n".join(linha for linha in linhas if linha)


def _baixar(url: str, http: httpx.Client) -> bytes:
    """Alguns servidores (o do CPDOC da FGV) recusam o TLS do Python e aceitam o do Windows: aí vai pelo curl."""
    try:
        r = http.get(url)
        r.raise_for_status()
        return r.content
    except (httpx.ConnectError, httpx.TimeoutException):
        if not (curl := shutil.which("curl")):
            raise
        r = subprocess.run([curl, "-sSL", "--fail", "--max-time", "120", "-A", "Mozilla/5.0 (Escola da Thalia)", url],
                           capture_output=True)
        if r.returncode != 0:
            raise RuntimeError(f"curl: {r.stderr.decode('utf-8', 'replace').strip()}") from None
        return r.stdout


def texto_pagina(url: str, http: httpx.Client) -> str:
    conteudo = _baixar(url, http)
    if conteudo[:5] == b"%PDF-":
        with tempfile.TemporaryDirectory() as pasta:
            arq = Path(pasta) / "pagina.pdf"
            arq.write_bytes(conteudo)
            return texto_pdf(arq, _pagina(url))
    try:
        html = conteudo.decode("utf-8")
    except UnicodeDecodeError:
        html = conteudo.decode("cp1252", "replace")
    leitor = _Texto()
    leitor.feed(html)
    return leitor.texto()


def _pagina(url: str) -> int | None:
    m = re.search(r"#page=(\d+)", url)
    return int(m[1]) if m else None


def texto_de(item: Item, arquivos: Path, http: httpx.Client, ouvir: bool = False) -> str:
    if youtube(item.url) and ouvir:
        try:
            if len(texto := baixar_legenda(item.url, tentativas=1)) >= TEXTO_MIN:
                return texto
        except RuntimeError:
            pass
        return ouvir_video(item.url)
    if youtube(item.url):
        return baixar_legenda(item.url)
    if item.arquivo and (arquivos / item.arquivo).is_file():
        local = arquivos / item.arquivo
        if local.suffix.lower() == ".pdf":
            return texto_pdf(local, _pagina(item.url))
        leitor = _Texto()
        leitor.feed(local.read_text(encoding="utf-8", errors="replace"))
        return leitor.texto()
    return texto_pagina(item.url, http)


def extrair(cat: Catalogo, arquivos: Path, destino: Path, refazer: bool = False, videos: bool = True,
            ouvir: bool = False, avisar=print) -> list[str]:
    """Tira o texto de cada aula e leitura principal que ainda não tem; devolve o que falhou. Sem `videos`, só os
    PDFs e as páginas, que não esperam pelo YouTube; com `ouvir`, o vídeo sem legenda é transcrito do áudio."""
    destino.mkdir(parents=True, exist_ok=True)
    falhas, http = [], httpx.Client(timeout=60, follow_redirects=True,
                                    headers={"User-Agent": "Mozilla/5.0 (Escola da Thalia)"})
    itens = [p.item for p in caminho.passos(cat) if p.item.tipo != "prova" and not p.assunto.id.startswith("provas-")
             and (videos or not youtube(p.item.url))]
    barrados = 0  # vídeos seguidos com 429
    for n, item in enumerate(itens, 1):
        arq = destino / f"{item.id}.txt"
        if arq.is_file() and not refazer:
            continue
        if barrados >= SEGUIDAS_429 and youtube(item.url):
            falhas.append(f"{item.titulo} ({item.url}): ficou para outra hora, o YouTube está barrando")
            continue
        try:
            texto = cat.guias[item.id] if item.tipo == "guia" else texto_de(item, arquivos, http, ouvir)
            if len(texto) < TEXTO_MIN:
                raise RuntimeError(f"texto quase vazio ({len(texto)} letras): legenda que não veio ou PDF escaneado")
        except (RuntimeError, httpx.HTTPError, OSError) as e:
            falhas.append(f"{item.titulo} ({item.url}): {e}")
            avisar(f"[{n}/{len(itens)}] falhou: {item.titulo}: {e}")
            if "429" in str(e) and (barrados := barrados + 1) == SEGUIDAS_429:
                avisar(f"{SEGUIDAS_429} vídeos seguidos barrados pelo YouTube: os outros vídeos ficam para outra hora")
            continue
        if youtube(item.url):
            barrados = 0
        arq.write_text(f"# {item.titulo}\n# {item.url}\n\n{texto}\n", encoding="utf-8")
        avisar(f"[{n}/{len(itens)}] {len(texto)} letras: {item.titulo}")
        if youtube(item.url):
            time.sleep(PAUSA)
    return falhas
