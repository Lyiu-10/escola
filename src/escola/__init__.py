"""A Escola: estudo guiado para os concursos de psicólogo das Forças Armadas. Roda só no PC."""
import os
from pathlib import Path


def pasta_catalogo() -> Path:
    """O catálogo mora no repositório (escola/), versionado: estrutura e materiais são texto."""
    return Path(os.environ.get("THALIA_ESCOLA_CATALOGO", Path(__file__).resolve().parents[2] / "escola"))


def pasta_dados() -> Path:
    """Os PDFs e o progresso ficam no PC, fora do repositório."""
    return Path(os.environ.get("THALIA_ESCOLA", Path.home() / "Documents" / "Escola"))
