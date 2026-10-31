# Escola

Estudo guiado para concursos, feito para quem se perde estudando sozinho: abre no navegador, e o botão
**Continuar** diz o que fazer agora. Hoje cobre os concursos de psicólogo das Forças Armadas (Marinha SMV e CP-T,
FAB EAOAP, Exército EsFCEx), mas o catálogo é só JSON e Markdown: outro concurso entra sem mexer no código.

O que tem:

- **Perfis:** várias pessoas na mesma Escola, cada uma com o seu progresso, Cronograma e Rotina. Cada aparelho
  escolhe quem está estudando numa tela de perfis (como a da Netflix) e lembra da escolha.
- **Turma:** o cartão de cada perfil (o que está estudando agora, horas na semana e no total, aulas concluídas,
  questões e acerto), que dá para ver sem entrar no perfil dos outros. As horas são estimadas: o tempo de cada aula
  concluída mais 2 minutos por questão.
- **Placar da semana:** pontos por esforço (o minuto de aula concluída vale 1, a questão vale 2 e conta uma vez na
  semana), a sequência de dias com 15 minutos ou mais (a folga não quebra) e a coroa de quem venceu a semana passada.
- **Assistir junto:** numa aula em vídeo, "Assistir junto" abre uma sala; quem está com a Escola aberta recebe o
  convite, e play, pausa e pulo de um valem para todos (o volume é de cada um).
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

Abra http://127.0.0.1:8792/ e crie o seu perfil. Os dados ficam em `Documentos/Escola` (a pasta muda com a variável
`THALIA_ESCOLA`): a lista em `perfis.json` e, de cada perfil, o progresso, a Rotina e as cópias diárias em
`perfis/<id>/`. Quem já usava a Escola antes dos perfis tem o progresso levado sozinho para o perfil `principal` na
primeira subida (com uma cópia de antes em `progresso-antes-dos-perfis.db`).

Não há senha: quem chega no endereço escolhe o perfil. Para usar com outras pessoas, deixe o endereço só para quem
deve entrar (uma rede privada como a Tailscale, por exemplo), em vez de abrir na internet.

**Catálogo particular.** O material que não pode ir para o repositório (um curso pago que só uma pessoa assina) mora
em `Documentos/Escola/particular/`, no mesmo formato do catálogo (`estrutura.json`, `materiais/`, e os PDFs em
`arquivos/`). A `estrutura.json` dele diz em `perfis` quem o vê: os outros perfis não veem os concursos, os itens nem os
PDFs dele. Ele pode ter concursos próprios ou pôr material a mais (`"extra": true`) num assunto do catálogo; nada dele
entra no Cronograma sem o dono escolher.

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
| `escola/rotina.exemplo.json` | a Rotina de exemplo; a de cada pessoa vai em `Documentos/Escola/perfis/<id>/rotina.json` |
| `scripts/` | montagem do catálogo (juntar provas e simulados, lotes de perguntas) |

**Fora do repositório:** os PDFs das leituras (`Documentos/Escola/arquivos`), as transcrições das aulas
(`Documentos/Escola/textos`) e os perfis. Sem os PDFs, as leituras que dependem deles não abrem.

## Avisos

- Nasceu dentro de uma assistente pessoal: o link "Voltar à Thalia" na barra lateral (só no primeiro perfil, o de
  quem instalou) e a cópia diária do progresso para um segundo computador (`notebook`, por ssh) são dessa instalação.
  Sem eles, a Escola funciona igual.
- As questões são de provas públicas (SSPM, distritos navais, FGV); os gabaritos são os oficiais, e as explicações
  são nossas.
- O `DESIGN.md` é o sistema visual da assistente; a parte da Escola é a seção "Página de leitura (Escola)" e as
  cores e fontes que ela usa.
