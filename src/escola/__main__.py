"""Linha de comando: escola (sobe a Escola) | conferir | textos | situacao."""
import argparse
import logging


def main(argv: list[str] | None = None):
    p = argparse.ArgumentParser(prog="escola")
    sub = p.add_subparsers(dest="comando")
    sub.add_parser("servir", help="sobe a Escola em 127.0.0.1:8792 (o padrão, sem comando)")
    conf = sub.add_parser("conferir", help="confere o catálogo (arquivos, vídeos, assuntos vazios, perguntas)")
    conf.add_argument("--perguntas", action="store_true", help="só as perguntas e as provinhas (rápido, sem internet)")
    tex = sub.add_parser("textos", help="tira o texto de cada aula e leitura (legenda do vídeo, texto do PDF)")
    tex.add_argument("--sem-videos", action="store_true", help="só PDFs e páginas (as legendas esperam pelo YouTube)")
    tex.add_argument("--ouvir", action="store_true", help="vídeo sem legenda: baixa o áudio e transcreve no PC (demora)")
    sit = sub.add_parser("situacao", help="procura edital e datas dos concursos (só se a última busca tem 7 dias)")
    sit.add_argument("--agora", action="store_true", help="busca mesmo que a última seja recente")
    args = p.parse_args(argv)

    from . import catalogo, pasta_catalogo, pasta_dados

    if args.comando == "conferir":
        from . import conferir

        cat = catalogo.carregar(pasta_catalogo())
        problemas, avisos = conferir.conferir_perguntas(cat, pasta_dados() / "textos")
        if not args.perguntas:
            outros = conferir.conferir(cat, pasta_dados() / "arquivos")
            problemas, avisos = outros[0] + problemas, outros[1] + avisos
        for a in avisos:
            print("aviso:", a)
        for p in problemas:
            print("PROBLEMA:", p)
        print(f"{len(problemas)} problemas, {len(avisos)} avisos")
        raise SystemExit(1 if problemas else 0)

    if args.comando == "textos":
        from . import textos

        dados = pasta_dados()
        falhas = textos.extrair(catalogo.carregar(pasta_catalogo()), dados / "arquivos", dados / "textos",
                                videos=not args.sem_videos, ouvir=args.ouvir, avisar=lambda s: print(s, flush=True))
        for f in falhas:
            print("FALHOU:", f)
        print(f"{len(falhas)} falhas")
        raise SystemExit(1 if falhas else 0)

    dados = pasta_dados()
    dados.mkdir(parents=True, exist_ok=True)

    if args.comando == "situacao":
        from . import situacao

        logging.basicConfig(filename=dados / "situacao.log", level=logging.INFO, encoding="utf-8",
                            format="%(asctime)s %(levelname)s %(name)s: %(message)s")
        raise SystemExit(situacao.rodada(catalogo.carregar(pasta_catalogo()), dados, forcar=args.agora))

    import uvicorn

    from .app import PORTA, criar_escola, enviar_ao_notebook

    logging.basicConfig(filename=dados / "escola.log", level=logging.INFO, encoding="utf-8",
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    uvicorn.run(criar_escola(pasta_catalogo(), dados, enviar_copia=enviar_ao_notebook), host="127.0.0.1",
                port=PORTA, log_config=None)


if __name__ == "__main__":
    main()
