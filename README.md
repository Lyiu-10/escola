# Escola

Estudo guiado para concursos, feito para quem se perde estudando sozinho: abre no navegador, e o botão
**Continuar** diz o que fazer agora. Hoje cobre os concursos de psicólogo das Forças Armadas (Marinha SMV e CP-T,
FAB EAOAP, Exército EsFCEx), mas o catálogo é só JSON e Markdown: outro concurso entra sem mexer no código.

O que tem:

- **Aulas em ordem:** vídeos e leituras grátis, por matéria e assunto, com o que cada edital cobra.
- **Guias:** o que as aulas grátis não ensinam e a banca cobra (`escola/guias/`).
- **Questões reais de prova** em cada aula, com a prova de origem ("CP-T 2024") e o porquê de cada alternativa
  errada. São 22 provas, das bancas dos concursos e da FGV.
- **Simulados** com cronômetro e nota por matéria (14).
- **Cronograma:** os dias e as horas de quem estuda, com revisão em +1, +7 e +21 dias e simulado semanal.
- **Caderno de erros, aquecimento do dia** (resumo, cartões e perguntas) e **Rotina** da semana.
- **Situação dos concursos:** uma busca semanal de edital e datas (precisa do Claude Code instalado).

## Rodar

Precisa do [uv](https://docs.astral.sh/uv/) e do Python 3.12.

```
uv sync
uv run escola
```

Abra http://127.0.0.1:8792/. O progresso fica em `Documentos/Escola/progresso.db`, criado na primeira vez (a pasta
muda com a variável `THALIA_ESCOLA`).

Outros comandos:

- `uv run escola conferir --perguntas`: confere o catálogo, as perguntas e o trecho de cada uma;
- `uv run escola textos`: tira o texto de cada aula (legenda do vídeo, texto do PDF), para escrever perguntas;
- `uv run escola situacao --agora`: busca edital e datas;
- `uv run pytest`: os testes.

## Onde fica cada coisa

| Pasta | O quê |
|---|---|
| `src/escola/` | o servidor (FastAPI): catálogo, progresso, cronograma, rotina, situação |
| `src/escola/web/` | a tela, sem framework (`escola.html`, `escola.js`, `escola.css`) |
| `escola/estrutura.json` | os concursos (ficha, datas, fontes), as matérias e os assuntos |
| `escola/materiais/` | as aulas e leituras de cada assunto |
| `escola/questoes/`, `simulados/`, `provinhas/` | as provas transcritas e onde cada questão entra |
| `escola/perguntas/`, `aquecimento/`, `explicacoes/` | fixação, cartões e o porquê das erradas |
| `escola/guias/` | os guias, em Markdown |
| `escola/rotina.exemplo.json` | a Rotina de exemplo; a sua vai em `escola/rotina.json`, fora do git |
| `scripts/` | montagem do catálogo (juntar provas e simulados, lotes de perguntas) |

**Fora do repositório:** os PDFs das leituras (`Documentos/Escola/arquivos`), as transcrições das aulas
(`Documentos/Escola/textos`) e o progresso. Sem os PDFs, as leituras que dependem deles não abrem.

## Avisos

- Nasceu dentro de uma assistente pessoal: o link "Voltar à Thalia" na barra lateral e a cópia diária do progresso
  para um segundo computador (`notebook`, por ssh) são dessa instalação. Sem eles, a Escola funciona igual.
- As questões são de provas públicas (SSPM, distritos navais, FGV); os gabaritos são os oficiais, e as explicações
  são nossas.
- O `DESIGN.md` é o sistema visual da assistente; a parte da Escola é a seção "Página de leitura (Escola)" e as
  cores e fontes que ela usa.
