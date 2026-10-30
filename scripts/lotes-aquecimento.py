r"""Os lotes do material do aquecimento (escola/aquecimento/*.json) para agentes escreverem: os itens principais de um
concurso, na ordem do caminho, que têm texto e ainda não têm esse material. Escreve também o brief.txt dos agentes.

Uso: .venv\Scripts\python.exe -X utf8 scripts\lotes-aquecimento.py <de> <até> [tamanho] [concurso]
     (posições 1.. no caminho do concurso, contando só aulas e leituras com texto; tamanho 8; concurso cpt)
Depois, um agente por lote: "Leia <pasta>\brief.txt e siga; o seu lote é lote-NN". Confira com
`escola conferir --perguntas` e a posição da certa antes do commit.
"""
import json
import sys
import tempfile
from pathlib import Path

from escola import caminho, catalogo, cronograma

REPO = Path(__file__).parents[1]
TEXTOS = Path.home() / "Documents" / "Escola" / "textos"
PASTA = Path(tempfile.gettempdir()) / "aquecimento-lotes"
PULAR = ("Treino: proposta de redação",)  # só o tema da redação: não há o que resumir

BRIEF = r"""Você vai escrever o material do AQUECIMENTO DO DIA para a Escola, a plataforma de estudo que roda no PC do Péricles. Ele estuda para o CP-T (concurso de oficial psicólogo da Marinha). Toda manhã, a Escola sugere um aquecimento de uns 15 minutos com três partes:
1. o RESUMO da última aula ou leitura que ele estudou (uma leitura curtinha);
2. 5 CARTÕES de memória dessa mesma aula: ele lê a frente, tenta lembrar, depois vira e vê o verso;
3. PERGUNTAS de múltipla escolha misturadas de tudo o que ele já estudou, incluindo 5 perguntas NOVAS por aula, que você vai escrever.
O pedido dele: tudo com base no que está no material — se é vídeo, sobre o que foi falado; se é PDF, sobre o próprio PDF. Ele já respondeu as 5 perguntas de fixação de cada item logo depois de estudar; as suas perguntas novas NÃO podem repetir o que elas perguntam.

SEU LOTE: `{PASTA}\{LOTE}.json`. Cada item tem: `url` (a chave no arquivo de saída), `titulo`, `tipo` (aula = vídeo, leitura = texto), `video`, `minutos`, `concurso`, `materia`, `assunto`, `edital` (o que o edital pede desse assunto), `nota`, `texto` (o caminho do texto do material) e `fixacao` (os enunciados das 5 perguntas de fixação que já existem).
- Vídeo: o texto é a legenda ou a transcrição, em linhas que começam com o minuto, ex.: `[12:30] fala...` ou `[1:02:30] fala...`. Legenda automática tem palavras trocadas: entenda pelo contexto, mas no resumo, nos cartões e nas perguntas use o termo certo.
- PDF: o texto tem marcas de página, ex.: `[p. 14]`. Quando a URL do item tem `#page=N`, o texto começa na página N e vai até 60 páginas adiante: o item é só a parte indicada pelo título e pela nota (do tamanho que dá para ler nos `minutos` do item); use só essa parte.
- Página da web: texto corrido, sem marcas.
Leia o texto inteiro do item (ou a parte indicada) antes de escrever.

O QUE ESCREVER, para cada item:

A) `resumo`: de 60 a 110 palavras, 3 a 5 frases, em português do Brasil. O essencial que o material ensina, para ele relembrar em 1 minuto na manhã seguinte: as ideias centrais, de preferência o que o edital pede. Comece direto pelo conteúdo ("O Código de Ética do psicólogo..."), sem "Neste vídeo, a professora...". Nada que não esteja no material; não invente número, data nem nome.

B) `cartoes`: 5 cartões, cada um com:
- `frente`: uma pergunta curta e direta (até 15 palavras) que cobra UMA coisa importante: um conceito, uma definição, uma regra, um prazo, um nome, uma distinção. Ex.: "O que o psicólogo deve fazer ao encerrar o atendimento por quebra de vínculo?"
- `verso`: a resposta curta (até 25 palavras), que se entende sozinha.
- `trecho` e `onde`: como nas perguntas (abaixo).
Os 5 cartões são as 5 coisas mais importantes de lembrar do material, espalhadas por ele (começo, meio e fim). Podem tocar no mesmo assunto de uma pergunta de fixação, mas com outra pergunta.

C) `perguntas`: 5 perguntas NOVAS de múltipla escolha.
- Cada uma sobre um ponto que NÃO é o de nenhuma pergunta de `fixacao` do item, e de preferência também diferente dos cartões. Procure outras ideias, regras, exemplos ou distinções do material. Se o material for curto, pode cobrar o mesmo assunto por outro ângulo (uma situação concreta que aplica a regra, por exemplo), mas nunca a mesma pergunta.
- 4 alternativas, uma só certa, as erradas plausíveis (erros típicos de quem estudou mal). Nada de "todas/nenhuma das anteriores".
- A POSIÇÃO DA CERTA: em cada item, as 5 perguntas usam as posições 0, 1, 2 e 3 pelo menos uma vez cada (a 5ª em qualquer uma), em ordem embaralhada. Um programa confere.
- Enunciado que se entende sozinho, sem "segundo a aula" obrigatório (pode usar). Ele vai ver essas perguntas misturadas com as de outras aulas, dias depois.
- `comentario`: 1 ou 2 frases explicando por que a certa é certa, com base no material.

TRECHO E LUGAR (cartões e perguntas):
- `trecho`: uma cópia LITERAL de 8 a 40 palavras do texto do material que sustenta a resposta. Copie exatamente as palavras do arquivo, inclusive erros da legenda automática; pode tirar pontuação, mas não troque, não corrija e não junte pedaços distantes. Um programa confere que o trecho está no arquivo.
- `onde`: no vídeo, o número de SEGUNDOS da marca `[m:ss]` da linha onde o trecho está (ex.: `[12:30]` → 750; `[1:02:30]` → 3750); no PDF, o número da página da marca `[p. N]` acima do trecho; em página da web sem marcas, omita `onde`.

SAÍDA: escreva `C:\Users\peric\Desktop\Projetos\escola\escola\aquecimento\{LOTE}.json` (UTF-8, indentação 1):
{
 "<url do item, igual ao lote>": {
  "resumo": "...",
  "cartoes": [{"frente": "...", "verso": "...", "trecho": "...", "onde": 750}],
  "perguntas": [{"enunciado": "...", "alternativas": ["...", "...", "...", "..."], "certa": 2, "comentario": "...", "trecho": "...", "onde": 750}]
 }
}
`certa` é a posição da alternativa certa a partir de 0.

CONFERÊNCIA (obrigatória): no diretório `C:\Users\peric\Desktop\Projetos\escola`, rode `.venv/Scripts/python.exe -m escola conferir --perguntas` e olhe as linhas que começam com "aquecimento:" e citam os SEUS itens:
- "trecho que não está no material" (problema): o trecho não é cópia literal. Corrija.
- "o trecho está em X, não em Y": `onde` errado. Corrija.
- "resumo com N palavras": ajuste para 60 a 110.
- "pergunta igual a uma de fixação" ou "a certa cai N vezes na mesma letra": corrija.
- "N cartões e M perguntas": faltou cartão ou pergunta.
Repita até não sobrar nada dos seus itens. Se o erro for de OUTRO arquivo (há outros agentes em paralelo escrevendo outros lotes) ou de perguntas de fixação antigas, não mexa: se o catálogo não carregar por causa de outro arquivo, espere um minuto e rode de novo.

NÃO FAÇA: não edite nenhum outro arquivo, não faça commit, não use internet, não mexa na pasta de textos.

RELATÓRIO FINAL (curto, em português): quantos itens completos (resumo, 5 cartões, 5 perguntas), quais ficaram com menos e por quê, e o resultado da conferência para os seus itens.
"""


def main():
    de, ate = int(sys.argv[1]), int(sys.argv[2])
    tamanho = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    cat = catalogo.carregar(REPO / "escola")
    c = cat.concurso(sys.argv[4] if len(sys.argv) > 4 else "cpt")
    passos = [p for p in caminho.sequencia(cat, c)
              if not p.item.extra and not cronograma.eh_de_prova(p.assunto.id) and not p.item.titulo.startswith(PULAR)
              and (TEXTOS / f"{p.item.id}.txt").is_file()]
    escolhidos = [p for n, p in enumerate(passos, 1) if de <= n <= ate and p.item.id not in cat.aquecimento]
    PASTA.mkdir(exist_ok=True)
    (PASTA / "brief.txt").write_text(BRIEF.replace("{PASTA}", str(PASTA)), encoding="utf-8")
    feitos = [int(f.stem[5:]) for f in [*(REPO / "escola" / "aquecimento").glob("lote-*.json"), *PASTA.glob("lote-*.json")]]
    numero = max(feitos, default=0)
    for k in range(0, len(escolhidos), tamanho):
        numero += 1
        lote = f"lote-{numero:02d}"
        itens = [{"url": p.item.url, "titulo": p.item.titulo, "tipo": p.item.tipo,
                  "video": catalogo.youtube(p.item.url) is not None, "minutos": p.item.minutos,
                  "concurso": c.nome, "materia": p.materia.nome, "assunto": p.assunto.nome,
                  "edital": p.assunto.edital, "nota": p.item.nota, "texto": str(TEXTOS / f"{p.item.id}.txt"),
                  "fixacao": [q.enunciado for q in cat.perguntas.get(p.item.id, ())]}
                 for p in escolhidos[k:k + tamanho]]
        (PASTA / f"{lote}.json").write_text(json.dumps({"lote": lote, "saida": f"escola/aquecimento/{lote}.json",
                                                        "itens": itens}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(lote, len(itens), "itens |", itens[0]["titulo"][:40], "→", itens[-1]["titulo"][:40])
    print(f"{len(passos)} aulas e leituras com texto no caminho; brief em {PASTA / 'brief.txt'}")


if __name__ == "__main__":
    main()
