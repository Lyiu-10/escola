// A Escola: barra lateral, Início (Continuar, Plano de hoje, cursos), Cronograma, Situação dos concursos, o curso
// aberto, a aula com a lista da matéria ao lado e as perguntas de fixação, a provinha de cada matéria, a revisão e a
// redação. As rotas vivem no # da URL.
const pagina = document.getElementById("pagina");
const anuncio = document.getElementById("anuncio");
const barraLateral = document.getElementById("barra");
const veu = document.getElementById("veu");
const botaoMenu = document.getElementById("abrir-menu");
let recado = ""; // aparece uma vez, na tela seguinte (depois de concluir ou de mudar o cronograma)
let relogio = null; // o cronômetro da revisão ou da redação; para quando a tela muda

const svg = (corpo, tam = 20) => `<svg width="${tam}" height="${tam}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${corpo}</svg>`;
const ICONE = {
  aula: svg('<rect x="2.5" y="5" width="19" height="14" rx="3"/><path d="M10 9.2v5.6l4.8-2.8z"/>'),
  leitura: svg('<path d="M12 6.5C10.3 5.2 7.9 4.5 4 4.5v13c3.9 0 6.3.7 8 2 1.7-1.3 4.1-2 8-2v-13c-3.9 0-6.3.7-8 2z"/><path d="M12 6.5v13"/>'),
  guia: svg('<path d="M6 3.5h9l3.5 3.5v13.5H6z"/><path d="M14.5 3.5V7.5h4M9 11h6M9 14.5h6M9 18h3.5"/>'),
  prova: svg('<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V3h6v1"/><path d="M8.5 12.5l2.5 2.5 4.5-5"/>'),
  revisao: svg('<path d="M4 12a8 8 0 1 0 2.4-5.7"/><path d="M4 4.5v3.8h3.8"/><path d="M12 8v4l2.5 1.6"/>'),
  redacao: svg('<path d="M14.5 4.5l5 5L9 20H4v-5z"/><path d="M12.5 6.5l5 5"/>'),
  provinha: svg('<rect x="4" y="3.5" width="16" height="17" rx="2.5"/><path d="M8 8.5h1.5M8 12h1.5M8 15.5h1.5M12 8.5h4M12 12h4M12 15.5h4"/>'),
  feito: svg('<path d="M5 12.5l4.5 4.5L19 7.5"/>'),
  depois: svg('<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>'),
  tocando: svg('<path d="M8 5.5v13l10.5-6.5z"/>'),
  seta: svg('<path d="M5 12h14M13 6l6 6-6 6"/>', 18),
  desce: svg('<path d="M12 5v14M6 13l6 6 6-6"/>', 18),
  voltar: svg('<path d="M19 12H5M11 6l-6 6 6 6"/>', 18),
  anterior: svg('<path d="M15 6l-6 6 6 6"/>', 18),
  proxima: svg('<path d="M9 6l6 6-6 6"/>', 18),
  migalha: svg('<path d="M9 6l6 6-6 6"/>', 14),
  fora: svg('<path d="M14 4h6v6M20 4l-9 9"/><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>', 16),
  abrir: svg('<path d="M6 9l6 6 6-6"/>', 18),
  relogio: svg('<circle cx="12" cy="13" r="7.5"/><path d="M12 9.5V13l2.2 1.4M9.5 3h5"/>', 18),
  sino: svg('<path d="M6 8.5a6 6 0 0 1 12 0c0 6.5 2.5 8 2.5 8h-17S6 15 6 8.5z"/><path d="M10 20a2.2 2.2 0 0 0 4 0"/>', 18),
  aquecimento: svg('<path d="M12 21a6 6 0 0 0 6-6c0-4-3-6.5-4.5-9.5-.6 2.4-2 3.6-3.4 4.6C8.6 11.2 6 12.6 6 15a6 6 0 0 0 6 6z"/><path d="M12 21a2.5 2.5 0 0 1-2.5-2.5c0-1.6 1.4-2.4 2.5-3.8 1.1 1.4 2.5 2.2 2.5 3.8A2.5 2.5 0 0 1 12 21z"/>'),
  cartoes: svg('<rect x="3" y="7.5" width="13" height="13" rx="2"/><path d="M8 7.5V5.5a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-3"/>', 18),
  marcado: svg('<path d="M5 12.5l4.5 4.5L19 7.5"/>', 16),
  menos: svg('<path d="M6 12h12"/>', 16),
  mais: svg('<path d="M12 6v12M6 12h12"/>', 16),
  coroa: svg('<path d="M3.5 8.5l4.5 3.8 4-6.8 4 6.8 4.5-3.8-2 10.5h-13z"/>'),
  caderno: svg('<path d="M6.5 3.5h11a1.5 1.5 0 0 1 1.5 1.5v14a1.5 1.5 0 0 1-1.5 1.5h-11z"/><path d="M6.5 3.5v17M4.5 8h4M4.5 12h4M4.5 16h4"/><path d="M11.5 9.5l4 4M15.5 9.5l-4 4"/>'),
};
const TIPO = { aula: "Aula", leitura: "Leitura", guia: "Guia", prova: "Simulado", revisao: "Revisão", redacao: "Redação", provinha: "Provinha" };
const ACAO = { aula: "Assistir à aula", leitura: "Ler agora", guia: "Ler o guia", prova: "Fazer o simulado", revisao: "Fazer a revisão", redacao: "Escrever a redação", provinha: "Fazer a provinha" };
const LETRAS = "ABCDE";
const MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];
const DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]; // 0 é segunda, como no servidor
const DIAS_CURTOS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"];
const CENTRAL = "https://desktop-aijqsic.tailcee703.ts.net/central";

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

// Título de vídeo todo em maiúsculas vira frase normal; as siglas continuam maiúsculas.
const SIGLAS = new Set(["CFP", "CRP", "SUS", "CAPS", "RAPS", "DSM", "CID", "TCC", "POT", "SATEPSI", "MS", "OMS", "OPAS",
  "IBGE", "FGV", "FEB", "ENEM", "EAOAP", "ESFCEX", "CP-T", "QVT", "RH", "TDAH", "TEA", "ABA", "UFRGS", "USP", "UFC",
  "II", "III", "IV", "XVIII", "XIX", "XX", "XXI", "DSM-5", "DSM-5-TR", "CID-10", "CID-11"]);
function suave(t) {
  const letras = String(t ?? "").replace(/[^\p{L}]/gu, "");
  const maiusculas = letras.replace(/[^\p{Lu}]/gu, "").length;
  if (letras.length < 8 || maiusculas / letras.length < 0.8) return t;
  const frase = t.toLowerCase().replace(/(^|[.!?:|–-]\s*)(\p{L})/gu, (_, antes, letra) => antes + letra.toUpperCase());
  return frase.split(/(\s+)/).map((p) => (SIGLAS.has(p.toUpperCase().replace(/[^\p{L}\d-]/gu, "")) ? p.toUpperCase() : p)).join("");
}
const titulo = (t) => esc(suave(t));
const tempo = (n) => (n >= 60 ? `${Math.floor(n / 60)} h${n % 60 ? ` ${n % 60} min` : ""}` : `${n} min`);
const tempoCurto = (n) => (n >= 60 ? `${Math.floor(n / 60)}h${n % 60 ? dois(n % 60) : ""}` : `${n}min`); // "2h30", para caber no seletor
const pct = (a, t) => (t ? Math.round((a / t) * 100) : 0);
const minSeg = (s) => `${Math.floor(s / 60)}:${dois(s % 60)}`;
// Texto de questão: o destaque da prova chega como **termo** (negrito) ou _termo_ (sublinhado); a lacuna "___" de
// completar fica como está; a quebra de linha fica.
const rico = (s) => esc(s)
  .replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>")
  .replace(/(?<![_\p{L}\d])_([^_\n]+)_(?![_\p{L}\d])/gu, "<u>$1</u>")
  .replace(/\n/g, "<br>");
// Uma linha do texto-base: além do destaque da prova, o *título da obra* na fonte vem em itálico.
const ricoLinha = (s) => esc(s)
  .replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>")
  .replace(/(?<![*\p{L}\d])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![*\p{L}\d])/gu, "<em>$1</em>")
  .replace(/(?<![_\p{L}\d])_([^_\n]+)_(?![_\p{L}\d])/gu, "<u>$1</u>");
const falar = (texto) => { anuncio.textContent = texto; };

// Datas: o servidor manda AAAA-MM-DD; a tela fala em português.
const dataDe = (iso) => { const [a, m, d] = iso.slice(0, 10).split("-").map(Number); return new Date(a, m - 1, d); };
const diaSemana = (d) => (d.getDay() + 6) % 7;
const dois = (n) => String(n).padStart(2, "0");
const dataCurta = (iso) => { const d = dataDe(iso); return `${dois(d.getDate())}/${dois(d.getMonth() + 1)}`; };
const dataCompleta = (iso) => `${dataCurta(iso)}/${iso.slice(0, 4)}`;
const dataLonga = (iso) => { const d = dataDe(iso); return `${DIAS[diaSemana(d)]}, ${d.getDate()} de ${MESES[d.getMonth()]}`; };
const mesAno = (iso) => `${MESES[Number(iso.slice(5, 7)) - 1]} de ${iso.slice(0, 4)}`;
const semanasEntre = (de, ate) => Math.floor((dataDe(ate) - dataDe(de)) / (7 * 864e5));

async function api(caminho, opcoes = {}) {
  const r = await fetch(caminho, { headers: { "Content-Type": "application/json" }, ...opcoes });
  if (r.status === 401) { abrirPerfis(); throw new Error("401"); } // este aparelho não escolheu perfil (ou ele sumiu)
  if (!r.ok) throw new Error(String(r.status));
  return r.json();
}
const enviar = (caminho, metodo, corpo) => api(caminho, { method: metodo, body: JSON.stringify(corpo) });

function erro(texto) {
  let el = pagina.querySelector(".erro");
  if (!el) {
    el = document.createElement("p");
    el.className = "erro";
    el.setAttribute("role", "alert");
    pagina.prepend(el);
  }
  el.textContent = texto;
}

function aviso() {
  if (!recado) return "";
  const texto = recado;
  recado = "";
  return `<p class="recado" role="status">${ICONE.feito}<span>${esc(texto)}</span></p>`;
}

function barra(feitos, total) {
  const p = total ? Math.round((feitos / total) * 100) : 0;
  return `<span class="trilho" role="img" aria-label="${feitos} de ${total} feitos"><span class="barra" style="width:${p}%"></span></span>`;
}

// Nas listas, só o que ajuda a escolher: o tipo, o tempo e se é extra ou em inglês. A fonte fica na aula aberta, e
// as perguntas, no bloco delas. O tempo é o do Cronograma (`duracao`, com as questões), o mesmo em toda tela.
function metaCurta(i) {
  const partes = [TIPO[i.tipo], tempo(i.duracao ?? i.minutos)];
  if (i.idioma === "en") partes.push("em inglês");
  if (i.extra) partes.push("extra");
  return partes.join(" · ");
}

// Na aula aberta, o tempo diz o que tem dentro: "49 min com as 5 questões".
function meta(i) {
  const n = i.fixacao?.questoes.length;
  const curta = n && i.duracao ? metaCurta(i).replace(tempo(i.duracao), `${tempo(i.duracao)} com ${n === 1 ? "a questão" : `as ${n} questões`}`)
    : metaCurta(i);
  return i.fonte && i.tipo !== "guia" ? `${curta} · ${esc(i.fonte)}` : curta;  // o guia é nosso: não tem fonte a citar
}

function marcaEstado(i) {
  return i.estado === "feito" ? ICONE.feito : i.estado === "depois" ? ICONE.depois : ICONE[i.tipo];
}

// "feito" se diz pela marca verde; o texto fica para o leitor de tela.
const feitoLeitor = (i) => (i.estado === "feito" ? '<span class="so-leitor"> (feito)</span>' : "");

// Uma linha de lista: aula, leitura, simulado, revisão ou redação. `onde` é o que vem depois da meta.
function linha(i, { onde = true } = {}) {
  const lugar = onde ? (["revisao", "redacao", "provinha"].includes(i.tipo) ? i.materia : i.assunto) : "";
  return `<li class="linha ${i.estado} tipo-${i.tipo}"><a href="${esc(i.rota)}">
    <span class="marca-estado">${marcaEstado(i)}</span>
    <span class="linha-texto">
      <span class="linha-titulo">${titulo(i.titulo)}${feitoLeitor(i)}</span>
      <span class="meta">${metaCurta(i)}${i.estado === "depois" ? " · para depois" : ""}${lugar && lugar !== TIPO[i.tipo] ? ` · ${esc(lugar)}` : ""}</span>
    </span></a></li>`;
}

// Os extras ficam fechados no fim do assunto (29/10): misturados ao caminho, com o mesmo peso, pareciam tarefa.
function listaComExtras(itens, linhaDe, { classe = "", aberto = false } = {}) {
  const ol = (xs) => `<ol${classe ? ` class="${classe}"` : ""}>${xs.map(linhaDe).join("")}</ol>`;
  const caminho = itens.filter((x) => !x.extra);
  const extras = itens.filter((x) => x.extra);
  return `${caminho.length ? ol(caminho) : ""}${extras.length ? `<details class="extras"${aberto ? " open" : ""}>
      <summary>${extras.length === 1 ? "1 extra" : `${extras.length} extras`}, se quiser ir além <span class="seta-abrir">${ICONE.abrir}</span></summary>
      ${ol(extras)}</details>` : ""}`;
}

function livro(l) {
  const abrir = l.item
    ? `<a class="link-fora" href="#/item/${l.item}">Grátis: abrir aqui</a>`
    : l.gratis
      ? `<a class="link-fora" href="${esc(l.gratis)}" target="_blank" rel="noopener">Grátis: abrir no site ${ICONE.fora}</a>`
      : '<span class="pago">Pago</span>';
  return `<li class="livro">
    <span class="livro-texto"><span class="livro-nome">${esc(l.curta)}</span><span class="meta">${esc(l.referencia)}</span></span>
    ${abrir}</li>`;
}

function links(fontes) {
  return (fontes || []).map((f) => `<a class="fonte" href="${esc(f.url)}" target="_blank" rel="noopener">${esc(f.titulo)} ${ICONE.fora}</a>`).join("");
}

// O estado do concurso diz em texto e em cor: inscrição aberta pede atenção (prazo), o resto é andamento ou espera.
function selo(s, { neutro = true } = {}) {
  if (!s) return "";
  const tom = { inscricoes: "atencao", previsto: "andando", andamento: "andando" }[s.estado] || "neutro";
  return tom === "neutro" && !neutro ? "" : `<span class="selo selo-${tom}">${esc(s.rotulo)}</span>`;
}

// Os cursos do cronograma vêm antes; os outros continuam abertos, mais apagados.
const naOrdem = (cursos) => [...cursos].sort((a, b) => (b.no_cronograma !== false) - (a.no_cronograma !== false));

// O Voltar volta um passo do que ele fez na Escola; aberta de fora (atalho, link da central), vai para a tela de cima.
function voltar(pai) {
  return `<button class="voltar" type="button" data-pai="${esc(pai)}">${ICONE.voltar}<span>Voltar</span></button>`;
}
document.addEventListener("click", (e) => {
  const b = e.target.closest(".voltar");
  if (!b) return;
  if (window.navigation?.canGoBack) history.back();
  else location.hash = b.dataset.pai;
});
// Os atalhos "Texto 1 · Texto 2" do texto-base levam ao começo de cada texto (na tela larga, dentro da coluna dele).
document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-ir-texto]");
  if (!b) return;
  b.closest(".texto-base").querySelectorAll(".tb-texto")[Number(b.dataset.irTexto)]?.scrollIntoView({
    block: "start", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
});

function migalhas(partes) {
  return `<nav class="migalhas" aria-label="Onde você está">${partes.map(([texto, href]) => (href
    ? `<a href="${esc(href)}">${esc(texto)}</a>` : `<span>${esc(texto)}</span>`)).join(ICONE.migalha)}</nav>`;
}

/* ---------- Barra lateral ---------- */

async function atualizarBarra(rota, cid) {
  barraLateral.querySelectorAll(".nav-link").forEach((a) => {
    if (a.dataset.rota === rota) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  try {
    const b = await api("/api/barra");
    document.getElementById("novidades").hidden = !b.novidades;
    document.querySelector('[data-rota="situacao"]').setAttribute("aria-label",
      b.novidades ? `Situação dos concursos: ${b.novidades} novidade${b.novidades > 1 ? "s" : ""}` : "Situação dos concursos");
    const conta = document.getElementById("caderno-conta");
    conta.hidden = !b.caderno;
    conta.textContent = b.caderno || "";
    document.querySelector('[data-rota="erros"]').setAttribute("aria-label",
      b.caderno ? `Caderno de erros: ${b.caderno} para rever hoje` : "Caderno de erros");
    document.getElementById("cursos-barra").innerHTML = naOrdem(b.concursos).map((c) => `
      <li><a class="curso-barra${c.no_cronograma === false ? " desligado" : ""}" href="#/concurso/${c.id}" title="${esc(c.nome)} ${esc(c.sigla)}"${c.id === cid ? ' aria-current="page"' : ""}>
        ${c.foto ? `<img src="${esc(c.foto)}" alt="" width="36" height="36">` : '<span class="foto-vazia"></span>'}
        <span class="curso-barra-texto">
          <span class="curso-barra-nome">${esc(c.nome)}</span>
          <span class="meta">${esc(c.sigla)} · ${c.feitos} de ${c.total}${c.no_cronograma === false ? '<span class="so-leitor">, fora do cronograma</span>' : ""}</span>
        </span></a></li>`).join("");
  } catch { /* a página em si mostra o erro */ }
}

function menu(aberto) {
  document.body.classList.toggle("menu-aberto", aberto);
  veu.hidden = !aberto;
  botaoMenu.setAttribute("aria-expanded", String(aberto));
  if (aberto) barraLateral.querySelector(".nav-link")?.focus();
}
botaoMenu.addEventListener("click", () => menu(true));
veu.addEventListener("click", () => menu(false));

// Na tela larga, o botão de três linhas recolhe a barra para uma faixa de ícones (o nome aparece ao passar o mouse);
// a escolha fica guardada neste navegador. No celular, a barra já é a gaveta do topo.
const app = document.querySelector(".app");
const botaoRecolher = document.getElementById("recolher");
function recolher(sim) {
  app.classList.toggle("recolhida", sim);
  const rotulo = sim ? "Abrir o menu" : "Recolher o menu";
  botaoRecolher.setAttribute("aria-expanded", String(!sim));
  botaoRecolher.title = rotulo;
  botaoRecolher.querySelector(".so-leitor").textContent = rotulo;
  try { localStorage.setItem("escola.barra", sim ? "recolhida" : "aberta"); } catch { /* sem guardar, vale até recarregar */ }
}
botaoRecolher.addEventListener("click", () => recolher(!app.classList.contains("recolhida")));
recolher(app.classList.contains("recolhida"));
addEventListener("keydown", (e) => { if (e.key === "Escape" && document.body.classList.contains("menu-aberto")) { menu(false); botaoMenu.focus(); } });

/* ---------- Início ---------- */

// A capa do Continuar: a miniatura do vídeo; sem vídeo, a foto do curso com o ícone do tipo por cima.
function capa(i, foto) {
  if (i.youtube) return `<span class="capa"><img src="https://i.ytimg.com/vi/${encodeURIComponent(i.youtube)}/mqdefault.jpg" alt="" loading="lazy"><span class="capa-play">${ICONE.tocando}</span></span>`;
  return `<span class="capa capa-${i.tipo}">${foto ? `<img src="${esc(foto)}" alt="" loading="lazy">` : ""}<span class="capa-play">${ICONE[i.tipo]}</span></span>`;
}

// "Leitura · 9 min · 3 de 11 em Legislação": o que é, quanto leva e onde está, numa linha só.
function metaContinuar(c) {
  const tipo = c.tipo === "revisao" ? `Revisão nº ${c.numero}` : TIPO[c.tipo];
  const lugar = c.posicao ? `${c.posicao} de ${c.total_materia} em ${c.materia}` : c.materia;
  return [tipo, tempo(c.duracao ?? c.minutos), lugar !== TIPO[c.tipo] ? lugar : ""].filter(Boolean).map(esc).join(" · ");
}

// O dia da Escola vira às 4h, como no servidor: à 1h ainda é a noite de ontem. `doDia` põe uma hora "HH:MM" nessa
// régua (minutos desde as 4h), para comparar 23h30 com meia-noite e meia sem errar.
const doDia = (h) => (minutosDe(h) - 240 + 1440) % 1440;
const agoraDoDia = () => { const a = new Date(); return (a.getHours() * 60 + a.getMinutes() - 240 + 1440) % 1440; };

// A frase do dia diz uma coisa só, e olha o relógio: folga, plano feito, quando começar, hora de estudar ou, passada
// a hora, que o que ficou volta amanhã (sem estudar de madrugada para compensar).
function frasePlano(d) {
  const c = d.continuar;
  if (d.hoje.folga) return `Hoje é folga: descansar também faz parte, a memória se firma entre as sessões.${c ? " Se quiser, dá para adiantar o próximo." : ""}`;
  if (d.adiantando) return "Plano de hoje feito. Se quiser, adiante o próximo.";
  if (!c) return "";
  if (!d.hoje.hora_estudo) return `Marque no <a href="#/cronograma">Cronograma</a> a hora em que você começa hoje: decidir antes ajuda a começar.`;
  const agora = agoraDoDia();
  if (d.hoje.livre && agora >= doDia(d.hoje.livre.fim)) return "Agora é hora de desligar e dormir. O que ficou do plano volta amanhã.";
  if (d.hoje.fim_estudo && agora >= doDia(d.hoje.fim_estudo)) return "A hora do estudo de hoje já passou. O que ficou do plano volta amanhã: não precisa compensar de madrugada.";
  if (agora >= doDia(d.hoje.hora_estudo)) return `Agora é a hora do estudo: ${c.tipo === "revisao" ? "comece pela revisão, a tarefa mais curta do dia" : "abra a primeira tarefa do plano"}.`;
  const plano = `Às ${esc(hora(d.hoje.hora_estudo))}, ${c.tipo === "revisao" ? "comece pela revisão, a tarefa mais curta do dia" : "abra a primeira tarefa do plano"}.`;
  return aquecerAgora(d) ? `Agora, o aquecimento. ${plano}` : plano;
}

// De manhã, antes da hora de estudar, o aquecimento é o que vale agora e leva o botão cheio; depois, é o Continuar.
// Um botão cheio por vez: o olho sabe por onde começar.
function aquecerAgora(d) {
  const aq = d.aquecimento;
  if (!aq || aq.acertos != null) return false;
  const agora = new Date();
  const m = agora.getHours() * 60 + agora.getMinutes();
  return m >= 240 && m < minutosDe(d.hoje.hora_estudo || "18:00");
}

function cartaoAquecimento(aq, principal) {
  if (!aq) return "";
  const feito = aq.acertos != null;
  const partes = [
    aq.leitura ? [ICONE.leitura, `Resumo de <em>${esc(suave(aq.leitura))}</em>`] : null,
    aq.leitura && aq.cartoes ? [ICONE.cartoes, `${aq.cartoes} cartões para virar`] : null,
    aq.perguntas ? [ICONE.provinha, `${aq.perguntas} pergunta${aq.perguntas === 1 ? "" : "s"} do que você já estudou`] : null,
  ].filter(Boolean);
  return `<a class="aquecer${principal ? " em-foco" : ""}${feito ? " feito" : ""}" href="#/aquecimento">
      <span class="aquecer-cabeca">
        <span class="aquecer-icone">${feito ? ICONE.feito : ICONE.aquecimento}</span>
        <span class="aquecer-titulos"><span class="aquecer-titulo">Aquecimento do dia</span>
          <span class="meta">${feito ? `Feito hoje: ${aq.acertos} de ${aq.perguntas} certas` : `Uns ${tempo(aq.minutos)} · sugestão do dia`}</span></span>
      </span>
      ${feito ? "" : `<ul class="aquecer-partes">${partes.map(([i, t]) => `<li>${i}<span>${t}</span></li>`).join("")}</ul>`}
      <span class="botao${principal ? " primario" : ""}">${feito ? "Ver de novo" : "Aquecer"} ${ICONE.seta}</span>
    </a>`;
}

// Os cursos numa lista compacta: foto, nome, quanto falta e o estado do concurso.
function cursosCompactos(concursos) {
  return `<ul class="cursos">${naOrdem(concursos).map((k) => `
    <li class="curso${k.no_cronograma ? "" : " desligado"}"><a href="#/concurso/${k.id}">
      ${k.foto ? `<img src="${esc(k.foto)}" alt="" width="56" height="56" loading="lazy">` : '<span class="foto-vazia"></span>'}
      <span class="curso-corpo">
        <span class="curso-nome">${esc(k.nome)} <span class="sigla">${esc(k.sigla)}</span></span>
        <span class="progresso">${barra(k.feitos, k.total)}<span class="meta">${k.feitos} de ${k.total}</span></span>
        <span class="curso-marcas">${selo(k.situacao, { neutro: false })}${k.no_cronograma ? "" : '<span class="meta">Fora do cronograma</span>'}</span>
      </span></a></li>`).join("")}</ul>`;
}

async function inicio() {
  const d = await api("/api/inicio");
  const c = d.continuar;
  const aquecer = aquecerAgora(d);
  const fotoDe = (cid) => d.concursos.find((k) => k.id === cid)?.foto;
  const continuar = c
    ? `<a class="proximo" href="${esc(c.rota)}">
        ${capa(c, fotoDe(c.concurso.id))}
        <span class="proximo-texto">
          <span class="proximo-titulo">${titulo(c.titulo)}</span>
          <span class="meta">${metaContinuar(c)}</span>
          <span class="botao grande${aquecer ? "" : " primario"}">${ACAO[c.tipo]} ${ICONE.seta}</span>
        </span>
      </a>`
    : `<p class="sub largo">${d.montando
      ? "O material ainda está sendo montado. Os concursos e os assuntos do edital já estão nos cursos; quando as aulas e os PDFs chegarem, o primeiro aparece aqui."
      : "Você terminou tudo o que está no caminho. Os extras continuam dentro de cada curso."}</p>`;

  const p = d.plano;
  const feitos = p.itens.filter((i) => i.estado === "feito").length;
  const soma = p.itens.reduce((s, i) => s + (i.duracao ?? i.minutos), 0);
  const plano = p.itens.length || !p.folga
    ? `<section class="plano" aria-labelledby="t-plano">
      <div class="secao-cabeca">
        <div class="secao-titulo"><h2 id="t-plano" class="titulo-secao">Plano de hoje</h2>
          ${p.itens.length ? `<span class="meta">${feitos} de ${p.itens.length} feitos · ${tempo(soma)}</span>` : ""}</div>
        <a class="link-seta" href="#/cronograma">Ver a semana ${ICONE.seta}</a>
      </div>
      ${p.itens.length ? `${barra(feitos, p.itens.length)}<ol class="lista">${p.itens.map((i) => linha(i)).join("")}</ol>` : '<p class="sub">Sem itens hoje: o material ainda está sendo montado.</p>'}
    </section>`
    : ""; // dia de folga sem nada feito: a frase do dia já diz

  const novidades = d.novidades.length
    ? `<a class="novidade" href="#/situacao">
        <span class="ponto-novo" aria-hidden="true"></span>
        <span class="novidade-texto"><strong>${esc(d.novidades[0].nome)}:</strong> ${esc(d.novidades[0].texto)}${d.novidades.length > 1 ? ` <span class="meta">e mais ${d.novidades.length - 1}</span>` : ""}</span>
        <span class="link-seta">Ver situação ${ICONE.seta}</span></a>`
    : "";

  // O horário livre de hoje, da Rotina: tem hora para começar e para acabar, e por isso fica à vista. Depois que acaba,
  // sai; enquanto dura, diz até quando.
  const l = d.hoje.livre;
  const agora = agoraDoDia();
  const livre = l && agora < doDia(l.fim)
    ? `<p class="livre-hoje"><span class="amostra tipo-livre" aria-hidden="true"></span><span><strong>Horário livre</strong> ${agora >= doDia(l.inicio) ? `agora, termina ${aHora(l.fim)}` : `hoje, ${daHora(l.inicio)} ${aHora(l.fim)}`}</span></p>`
    : "";

  // A inscrição que fecha logo fica no topo até ele dizer que se inscreveu: é o prazo que não volta.
  const prazos = (d.prazos || []).map((p) => `<div class="faixa-prazo" role="note">
      <span class="faixa-prazo-texto"><strong>Inscrição no ${esc(p.concurso.sigla)} até ${dataCurta(p.fim)}</strong>${p.obs ? ` (${esc(p.obs)})` : ""} · ${p.dias === 0 ? "fecha hoje" : p.dias === 1 ? "falta 1 dia" : `faltam ${p.dias} dias`}</span>
      ${p.fonte ? `<a class="link-fora" href="${esc(p.fonte)}" target="_blank" rel="noopener">Ver o aviso ${ICONE.fora}</a>` : ""}
      <button class="link-botao" type="button" data-inscrevi="${esc(p.concurso.id)}">Já me inscrevi</button>
    </div>`).join("");
  const k = d.caderno;
  const caderno = k.total
    ? `<a class="caderno-atalho" href="#/erros">
        <span class="caderno-icone">${ICONE.caderno}</span>
        <span class="caderno-texto"><span class="caderno-titulo">Caderno de erros</span>
          <span class="meta">${k.total} ${k.total === 1 ? "questão" : "questões"} · ${k.para_hoje ? `${k.para_hoje} para rever hoje` : "voltam outro dia"}</span></span>
        <span class="link-seta">${k.para_hoje ? "Rever" : "Ver"} ${ICONE.seta}</span>
      </a>`
    : "";

  document.title = "Escola";
  const placarCartao = d.placar ? cartaoPlacar(d.placar) : "";
  pagina.innerHTML = `
    ${aviso()}
    ${prazos}
    ${novidades}
    <header class="cabeca hoje-cabeca">
      <h1>${esc(dataLonga(d.hoje.dia).replace(/^./, (l) => l.toUpperCase()))}</h1>
      ${frasePlano(d) ? `<p class="sub largo">${frasePlano(d)}</p>` : ""}
      ${livre}
    </header>
    <div class="painel">
      <section class="continuar" aria-label="Continuar">${continuar}</section>
      ${cartaoAquecimento(d.aquecimento, aquecer)}
      ${plano}
      <div class="lado-painel">
        ${placarCartao}
        ${caderno}
        <section class="cursos-painel" aria-labelledby="t-cursos">
          <h2 id="t-cursos" class="titulo-secao">Meus cursos</h2>
          ${cursosCompactos(d.concursos)}
        </section>
      </div>
    </div>`;
  pagina.querySelectorAll("[data-inscrevi]").forEach((b) => b.addEventListener("click", async () => {
    b.disabled = true;
    try {
      await enviar(`/api/inscricoes/${encodeURIComponent(b.dataset.inscrevi)}`, "POST", {});
      recado = "Anotado: a faixa do prazo saiu do Início.";
      falar(recado);
      await inicio();
    } catch {
      b.disabled = false;
      erro("Não deu para salvar. Confira se a Escola está ligada e tente de novo.");
    }
  }));
}

/* ---------- Aula aberta (item) ---------- */

function palco(i) {
  if (i.youtube) {
    return `<div class="video"><iframe src="https://www.youtube-nocookie.com/embed/${encodeURIComponent(i.youtube)}?rel=0" title="${esc(i.titulo)}" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>`;
  }
  if (i.pdf) {
    const pag = i.url.match(/#page=(\d+)/);
    return `<iframe class="pdf" src="${esc(i.pdf)}${pag ? `#page=${pag[1]}` : ""}" title="${esc(i.titulo)}"></iframe>`;
  }
  return `<div class="fora"><p>Este material abre no site de origem, numa aba nova.</p><a class="botao primario" href="${esc(i.url)}" target="_blank" rel="noopener">Abrir no site ${ICONE.fora}</a></div>`;
}

function abrirFora(i) {
  if (i.guia) return "";
  if (i.youtube) return `<a class="link-fora" href="${esc(i.url)}" target="_blank" rel="noopener">Abrir no YouTube ${ICONE.fora}</a>`;
  if (i.pdf) return `<a class="link-fora" href="${esc(i.pdf)}" target="_blank" rel="noopener">Abrir o PDF numa aba ${ICONE.fora}</a>`;
  return ""; // o palco já tem o botão para o site
}

function listaDaMateria(i) {
  const l = i.lista;
  return `<aside class="lista-materia" aria-labelledby="t-lista">
    <div class="lista-cabeca">
      <h2 id="t-lista" class="lista-nome">${esc(l.materia)}</h2>
      <span class="progresso">${barra(l.feitos, l.total)}<span class="meta">${l.feitos} de ${l.total}</span></span>
    </div>
    <div class="lista-rolagem">${l.assuntos.map((a) => `
      <section class="lista-assunto">
        <h3>${esc(a.nome)}</h3>
        ${listaComExtras(a.itens, (x) => {
          const atual = x.id === i.id;
          const marca = atual ? ICONE.tocando : x.estado === "feito" ? ICONE.feito : x.estado === "depois" ? ICONE.depois : ICONE[x.tipo];
          return `<li class="item-lista ${x.estado}${atual ? " atual" : ""}"><a href="#/item/${x.id}/${i.concurso.id}"${atual ? ' aria-current="page"' : ""}>
            <span class="item-lista-marca">${marca}</span>
            <span class="item-lista-texto"><span class="item-lista-titulo">${titulo(x.titulo)}${feitoLeitor(x)}</span>
            <span class="meta">${metaCurta(x)}</span></span></a></li>`;
        }, { aberto: a.itens.some((x) => x.extra && x.id === i.id) })}
      </section>`).join("")}
      ${i.provinha ? `<a class="lista-provinha ${i.provinha.estado}" href="${esc(i.provinha.rota)}">
        <span class="item-lista-marca">${i.provinha.estado === "feito" ? ICONE.feito : ICONE.provinha}</span>
        <span class="item-lista-texto"><span class="item-lista-titulo">Provinha do módulo</span>
        <span class="meta">${i.provinha.questoes} questões de provas anteriores${i.provinha.estado === "feito" ? " · feita" : ""}</span></span></a>` : ""}</div>
  </aside>`;
}

/* ---------- Perguntas: as de fixação de cada aula e leitura, e as provinhas de cada matéria ---------- */

function melhoria(tentativas) {
  const [antes, agora] = tentativas.slice(-2);
  const d = pct(agora.acertos, agora.total) - pct(antes.acertos, antes.total);
  const base = `Na vez anterior: ${antes.acertos} de ${antes.total} (${pct(antes.acertos, antes.total)}%).`;
  if (d > 0) return `${base} Subiu ${d} pontos.`;
  if (d < 0) return `${base} Caiu ${-d} pontos: releia os trechos das que errou.`;
  return `${base} Ficou igual.`;
}

// A prova de onde a questão veio vai na frente do enunciado, como nos livros de questões. No aquecimento, que mistura
// tudo, a pergunta feita a partir de uma aula diz isso no mesmo lugar, para nunca passar por questão de prova.
function enunciado(q, alvo = "") {
  const origem = q.prova ? `<span class="prova">${esc(q.prova)}</span> `
    : q.estilo ? `<span class="prova feita">No estilo do ${esc(q.estilo)}</span> `
      : alvo.startsWith("aq:") ? '<span class="prova feita">Feita a partir da aula</span> ' : "";
  return `<span class="enunciado">${origem}${rico(q.enunciado)}</span>`;
}

// O texto-base aparece uma vez, antes da primeira questão que o usa. O que não foi transcrito (um poema, uma letra de
// música) vira o link para a página da prova.
function textoBase(q, anterior) {
  if (q.texto_na_prova) {
    return anterior?.texto_na_prova?.pagina === q.texto_na_prova.pagina ? "" : blocoTexto(q);
  }
  return q.texto && q.texto !== anterior?.texto ? blocoTexto(q) : "";
}

function blocoTexto(q) {
  const p = q.texto_na_prova;
  if (p) {
    return `<p class="texto-base na-prova">O texto desta questão está na página ${p.pagina} da prova.
      <a class="link-fora" href="${esc(p.url.split("#")[0])}#page=${p.pagina}" target="_blank" rel="noopener">Abrir a prova ${ICONE.fora}</a></p>`;
  }
  return q.texto ? paginaTexto(q.texto) : "";
}

// O texto-base como página de livro: ele pediu em 29/10 "a mesma ideia do Kindle", porque texto miúdo e corrido cansa a
// vista dele. Cada "Texto 1" da prova vira uma seção com nome, e, quando são vários, um atalho para cada um no topo.
// Dentro: título, autor, parágrafos com o número na margem, versos em estrofes e a fonte no pé. As questões citam
// "5º §": em 29/10, 140 de 142 citações conferíveis bateram com esta contagem (as 2 que não batem são erro da prova).
const ROTULO_TEXTO = /^texto\s+(\d+|[ivx]+)$/i;
const AUTOR_TEXTO = /^[A-ZÁÉÍÓÚÂÊÔ][\p{L}.'’]+(?: (?:de|da|do|dos|das|e|[A-ZÁÉÍÓÚÂÊÔ][\p{L}.'’]+)){1,4}$/u;
const ehTitulo = (l) => (l.length <= 60 && !/[.!?:;,]$/.test(l)) || (l.endsWith("...") && l.length <= 40);
const ehFonte = (l) => /^\(?[A-ZÁÉÍÓÚÂÊÔÃÕÇ]{2,}[A-ZÁÉÍÓÚÂÊÔÃÕÇ' -]*,\s/.test(l) || /^\([^)]{3,60}\)$/.test(l)
  || /^\[?(fonte:|adaptado d|disponível em)/i.test(l);
// Estrofe: versos curtos, que não são falas de diálogo
const ehVerso = (b) => b.length > 1 && b.every((l) => l.length <= 70) && b.filter((l) => /^[-–—]/.test(l)).length < b.length / 2;

function secaoTexto({ nome, linhas }) {
  const corpo = [...linhas];
  while (corpo.length && !corpo[0]) corpo.shift();
  while (corpo.length && !corpo.at(-1)) corpo.pop();
  const obra = corpo.length > 1 && ehTitulo(corpo[0]) ? corpo.shift() : "";
  const autor = obra && corpo.length > 1 && corpo[0].length <= 40 && AUTOR_TEXTO.test(corpo[0]) ? corpo.shift() : "";
  const fontes = [];
  while (corpo.length > 1 && (!corpo.at(-1) || ehFonte(corpo.at(-1)))) {
    const l = corpo.pop();
    if (l) fontes.unshift(l);
  }
  const blocos = [];
  let bloco = [];
  for (const l of [...corpo, ""]) {
    if (l) bloco.push(l);
    else if (bloco.length) { blocos.push(bloco); bloco = []; }
  }
  const paragrafos = blocos.filter((b) => !ehVerso(b)).flat().filter((l) => l !== "[...]" && !l.startsWith("* ")).length;
  let n = 0;
  const miolo = blocos.map((b) => (ehVerso(b) ? `<p class="tb-estrofe">${b.map(ricoLinha).join("<br>")}</p>`
    : b.map((l) => (l === "[...]" ? '<p class="tb-corte">[...]</p>'
      : l.startsWith("* ") ? `<p class="tb-nota">${ricoLinha(l)}</p>`
        : `<p class="tb-par"${paragrafos > 1 ? ` data-n="${++n}"` : ""}>${ricoLinha(l)}</p>`)).join(""))).join("");
  const caixaAlta = obra && obra === obra.toLocaleUpperCase("pt-BR") ? " caixa-alta" : "";
  const cabeca = nome || obra ? `<header class="tb-cabeca">
      ${nome ? `<h3 class="tb-nome">${esc(nome)}</h3>` : ""}
      ${obra ? (nome ? `<p class="tb-obra${caixaAlta}">${ricoLinha(obra)}</p>` : `<h3 class="tb-nome${caixaAlta}">${ricoLinha(obra)}</h3>`) : ""}
      ${autor ? `<p class="tb-autor">${esc(autor)}</p>` : ""}
    </header>` : "";
  return `<section class="tb-texto">${cabeca}${miolo}${fontes.length ? `<p class="tb-fonte">${fontes.map(ricoLinha).join("<br>")}</p>` : ""}</section>`;
}

function paginaTexto(texto) {
  const secoes = [];
  for (const linha of texto.split("\n")) {
    const l = linha.trim();
    if (ROTULO_TEXTO.test(l)) secoes.push({ nome: l, linhas: [] });
    else if (secoes.length) secoes.at(-1).linhas.push(l);
    else secoes.push({ nome: "", linhas: [l] });
  }
  const textos = secoes.filter((s) => s.nome || s.linhas.some(Boolean));
  const saltos = textos.length > 1 ? `<nav class="tb-saltos" aria-label="Ir para o texto">${textos.map((s, k) =>
    `<button type="button" class="tb-salto" data-ir-texto="${k}">${esc(s.nome || `Texto ${k + 1}`)}</button>`).join("")}</nav>` : "";
  return `<div class="texto-base"><div class="tb-barra">${saltos}<span class="tb-acoes">
      <button type="button" class="tb-acao" data-trocar-papel>${rotuloPapel()}</button>
      <button type="button" class="tb-acao" data-trocar-texto aria-expanded="${LEITURA.texto !== "minimizado"}">${rotuloTexto()}</button>
    </span></div>${textos.map(secaoTexto).join("")}</div>`;
}

// O guia do assunto (29/10): o resumo que escrevemos a partir de todas as questões reais do assunto, porque o vídeo e a
// leitura grátis davam a visão geral e a banca cobra a regra exata. Fica no mesmo papel do texto-base, que é leitura
// longa. Lê um Markdown restrito: ## e ###, parágrafo, lista (- ou 1.), tabela, box ("> **Pegadinha:** …") e, dentro
// do texto, o negrito, o itálico e o sublinhado do ricoLinha. As seções ## viram o índice do topo.
// A palavra com hífen não quebra no fim da linha: num guia que ensina hífen, "super-" numa linha e "homem" na outra
// confunde (e pelo Acordo o hífen se repetiria na linha de baixo).
const linhaGuia = (s) => ricoLinha(s.replace(/[\p{L}]+(?:-[\p{L}]+)+/gu, "$&"))
  .replaceAll("", '<span class="inteira">').replaceAll("", "</span>");

function blocosGuia(linhas) {
  const html = [];
  let k = 0;
  const lista = (re, tag) => {
    const itens = [];
    while (k < linhas.length && re.test(linhas[k])) itens.push(`<li>${linhaGuia(linhas[k++].replace(re, ""))}</li>`);
    html.push(`<${tag}>${itens.join("")}</${tag}>`);
  };
  while (k < linhas.length) {
    const l = linhas[k];
    if (!l.trim()) { k++; continue; }
    if (/^\s*[-*]\s+/.test(l)) { lista(/^\s*[-*]\s+/, "ul"); continue; }
    if (/^\s*\d+[.)]\s+/.test(l)) { lista(/^\s*\d+[.)]\s+/, "ol"); continue; }
    const par = [];
    while (k < linhas.length && linhas[k].trim() && !/^\s*([-*]|\d+[.)])\s+/.test(linhas[k])) par.push(linhas[k++].trim());
    html.push(`<p>${par.map(linhaGuia).join(" ")}</p>`);
  }
  return html.join("");
}

function paginaGuia(md) {
  const linhas = md.replace(/\r/g, "").split("\n");
  const celulas = (l) => l.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());
  const html = [];
  const secoes = [];
  let k = 0;
  while (k < linhas.length) {
    const l = linhas[k];
    let m;
    if (!l.trim()) { k++; continue; }
    if ((m = l.match(/^(#{2,3})\s+(.+)/))) {
      if (m[1].length === 2) {
        secoes.push(m[2]);
        html.push(`<h2 class="gu-h2" id="guia-${secoes.length}" tabindex="-1">${linhaGuia(m[2])}</h2>`);
      } else html.push(`<h3 class="gu-h3">${linhaGuia(m[2])}</h3>`);
      k++;
    } else if (/^\s*\|/.test(l) && /^\s*\|?\s*:?-{3,}/.test(linhas[k + 1] ?? "")) {
      const cabeca = celulas(l);
      const corpo = [];
      k += 2;
      while (k < linhas.length && /^\s*\|/.test(linhas[k])) corpo.push(celulas(linhas[k++]));
      html.push(`<div class="gu-tabela" tabindex="0"><table><thead><tr>${cabeca.map((c) => `<th scope="col">${linhaGuia(c)}</th>`).join("")}</tr></thead>
        <tbody>${corpo.map((r) => `<tr>${r.map((c, n) => `<td data-rotulo="${esc(cabeca[n] ?? "").replace(/\*\*/g, "")}">${linhaGuia(c)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`);
    } else if (/^>/.test(l)) {
      const caixa = [];
      while (k < linhas.length && /^>/.test(linhas[k])) caixa.push(linhas[k++].replace(/^>\s?/, ""));
      const tipo = caixa[0].match(/^\*\*([^*]+?):?\*\*/)?.[1] ?? "";
      const classe = /pegadinha|aten[çc]/i.test(tipo) ? " pegadinha" : /como cai/i.test(tipo) ? " como-cai" : "";
      html.push(`<div class="gu-box${classe}">${blocosGuia(caixa)}</div>`);
    } else {
      const bloco = [];
      while (k < linhas.length && linhas[k].trim() && !/^(#{2,3}\s|>)/.test(linhas[k])
        && !(/^\s*\|/.test(linhas[k]) && /^\s*\|?\s*:?-{3,}/.test(linhas[k + 1] ?? ""))) bloco.push(linhas[k++]);
      html.push(blocosGuia(bloco));
    }
  }
  // O índice fica fechado (29/10): aberto, eram 19 botões, uma tela inteira antes da primeira linha do guia.
  const indice = secoes.length > 2 ? `<details class="gu-indice"><summary>Índice <span class="gu-indice-n">${secoes.length} partes</span>
      <span class="seta-abrir">${ICONE.abrir}</span></summary>
    <ul>${secoes.map((s, n) => `<li><button type="button" class="gu-ir" data-ir-secao="${n + 1}">${linhaGuia(s)}</button></li>`).join("")}</ul></details>` : "";
  return `<article class="guia" aria-label="Guia">
    <div class="gu-topo">${indice}<button type="button" class="tb-acao" data-trocar-papel>${rotuloPapel()}</button></div>
    ${html.join("")}</article>`;
}
document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-ir-secao]");
  if (!b) return;
  const h = document.getElementById(`guia-${b.dataset.irSecao}`);
  b.closest("details")?.removeAttribute("open");
  h?.scrollIntoView({ block: "start", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  h?.focus({ preventScroll: true });
});

// Como ele quer ler o texto-base, só neste navegador (pedido dele em 29/10): o fundo, bege ou azul bem escuro, e o
// tamanho, inteiro ou minimizado numa janela com rolagem própria, para a página não ficar comprida. Vale para todos.
const LEITURA = { papel: "bege", texto: "inteiro" };
try { Object.assign(LEITURA, JSON.parse(localStorage.getItem("escola:leitura") || "{}")); } catch { /* sem armazenamento: fica o padrão */ }
const ICONE_FUNDO = svg('<circle cx="12" cy="12" r="8.5"/><path d="M12 3.5a8.5 8.5 0 0 1 0 17z" fill="currentColor"/>', 16);
const ICONE_MINIMIZAR = svg('<path d="M8 4.5l4 4 4-4M8 19.5l4-4 4 4"/>', 16);
const ICONE_EXPANDIR = svg('<path d="M8 8.5l4-4 4 4M8 15.5l4 4 4-4"/>', 16);
const rotuloPapel = () => `${ICONE_FUNDO}<span>${LEITURA.papel === "azul" ? "Fundo bege" : "Fundo azul"}</span>`;
const rotuloTexto = () => (LEITURA.texto === "minimizado" ? `${ICONE_EXPANDIR}<span>Expandir</span>` : `${ICONE_MINIMIZAR}<span>Minimizar</span>`);
function aplicarLeitura() {
  document.documentElement.dataset.papel = LEITURA.papel;
  document.documentElement.dataset.texto = LEITURA.texto;
  document.querySelectorAll("[data-trocar-papel]").forEach((b) => { b.innerHTML = rotuloPapel(); });
  document.querySelectorAll("[data-trocar-texto]").forEach((b) => {
    b.innerHTML = rotuloTexto();
    b.setAttribute("aria-expanded", String(LEITURA.texto !== "minimizado"));
  });
}
aplicarLeitura();
document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-trocar-papel], [data-trocar-texto]");
  if (!b) return;
  const tamanho = b.matches("[data-trocar-texto]");
  if (tamanho) LEITURA.texto = LEITURA.texto === "minimizado" ? "inteiro" : "minimizado";
  else LEITURA.papel = LEITURA.papel === "azul" ? "bege" : "azul";
  try { localStorage.setItem("escola:leitura", JSON.stringify(LEITURA)); } catch { /* sem armazenamento: vale só nesta página */ }
  aplicarLeitura();
  if (tamanho) { // volta ao começo do texto, e não ao meio de onde ele estava
    const t = b.closest(".texto-base");
    t.scrollTop = 0;
    if (t.getBoundingClientRect().top < 0) t.scrollIntoView({ block: "start" });
  }
});

// A canetinha ao lado de cada alternativa risca a que ele já descartou, como no caderno da prova (pedido dele em 29/10).
// É só para os olhos: não marca nem desmarca, não vai ao servidor e some quando a tela é desenhada de novo.
const ICONE_RISCAR = svg('<path d="M14.5 4.5l5 5L9 20H4v-5z"/><path d="M12.5 6.5l5 5"/>', 18);
const alternativa = (n, k, a, marcada = false) => `
  <div class="alternativa-linha"><label class="alternativa"><input type="radio" name="q${n}" value="${k}"${marcada ? " checked" : ""}><span class="letra">${LETRAS[k]}</span><span class="alt-texto">${rico(a)}</span></label><button type="button" class="riscar" data-riscar aria-pressed="false" aria-label="Riscar a ${LETRAS[k]}" title="Riscar">${ICONE_RISCAR}</button></div>`;
const riscar = (linha, sim) => {
  linha.classList.toggle("riscada", sim);
  linha.querySelector("[data-riscar]").setAttribute("aria-pressed", String(sim));
};
document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-riscar]");
  if (b) riscar(b.parentElement, !b.parentElement.classList.contains("riscada"));
});
document.addEventListener("change", (e) => { // marcar a riscada tira o risco: ele mudou de ideia
  const linha = e.target.closest(".alternativa-linha.riscada");
  if (linha) riscar(linha, false);
});

// Uma questão por vez (aquecimento e rodadas do caderno): a lista inteira continua na página, só a atual aparece. Os
// números em cima levam a qualquer uma e mostram a marcada ou, na correção, a certa e a errada.
function trilhaQuestoes(f, correcao, rotulos) {
  return `<ol class="trilha-questoes" aria-label="Questões">${f.questoes.map((_, n) => {
    const r = correcao?.[n];
    const numero = rotulos?.[n] ?? n + 1; // no simulado, o número da questão na prova
    const rotulo = `Questão ${numero}${r ? (r.acertou ? ", certa" : r.marcada < 0 ? ", em branco" : ", errada") : ""}`;
    return `<li><button type="button" class="ir-questao${r ? (r.acertou ? " certa" : " errada") : ""}" data-passo="${n}" aria-label="${rotulo}">${numero}</button></li>`;
  }).join("")}</ol>`;
}

const navQuestoes = () => `<span class="questoes-nav">
    <button class="botao" type="button" data-passo-ir="-1">${ICONE.anterior} Anterior</button>
    <button class="botao" type="button" data-passo-ir="1">Próxima ${ICONE.proxima}</button></span>`;

function formPerguntas(f, opcoes = {}) {
  const uma = opcoes.umaPorVez && f.questoes.length > 1;
  return `<form class="questoes${uma ? " uma-por-vez" : ""}" novalidate>
    ${uma ? trilhaQuestoes(f, null, opcoes.rotulos) : ""}
    <ol class="questoes-lista">${f.questoes.map((q, n) => `
      <li class="questao"${uma && n ? " hidden" : ""}>
        ${uma ? blocoTexto(q) : textoBase(q, f.questoes[n - 1])}
        <fieldset>
          <legend><span class="numero">${opcoes.rotulos?.[n] ?? n + 1}</span>${enunciado(q, f.alvo)}</legend>
          <div class="alternativas">${q.alternativas.map((a, k) => alternativa(n, k, a)).join("")}</div>
        </fieldset>
      </li>`).join("")}</ol>
    <div class="questoes-rodape">
      ${uma ? navQuestoes() : ""}
      <button class="botao primario" type="submit" disabled>Responder</button>
      <span class="meta" data-faltam aria-live="polite">Faltam ${f.questoes.length}</span>
    </div>
  </form>`;
}

function irPara(r, opcoes) {
  if (r.onde == null || !opcoes.ir) return "";
  return `<button class="link-botao" type="button" data-ir="${r.onde}">${opcoes.video ? `Ver no vídeo, aos ${minSeg(r.onde)}` : `Ver na página ${r.onde}`}</button>`;
}

// Na correção, cada explicação fica dentro da alternativa que ela explica: na que ele marcou errado, por que ela está
// errada; na certa, por que é a certa (com o trecho do material, quando há). As outras erradas ficam mais apagadas, e o
// erro delas aparece num toque. A fonte vai numa linha só, no pé.
function porque(rotulo, corpo, { oculto = false } = {}) {
  return `<div class="porque"${oculto ? " data-outra hidden" : ""}><span class="porque-rotulo">${rotulo}</span>${corpo}</div>`;
}

function correcaoQuestao(q, r, n, f, opcoes) {
  const erradas = r.erradas || [];
  const outras = erradas.filter((t, k) => t && k !== r.marcada).length;
  const certa = porque(r.acertou ? "Por que você acertou" : "Por que é a certa",
    `<p>${esc(r.comentario)}</p>${r.trecho ? `<blockquote>“${esc(r.trecho)}”</blockquote>` : ""}${irPara(r, opcoes)}${r.ressalva ? `<p class="ressalva"><strong>Gabarito discutível:</strong> ${esc(r.ressalva)}</p>` : ""}`);
  const pe = [
    q.origem ? `De <a href="${esc(q.origem.rota)}">${titulo(q.origem.titulo)}</a>${r.onde == null ? "" : q.origem.video ? `, aos ${minSeg(r.onde)}` : `, na página ${r.onde}`}` : "",
    r.fonte ? `${esc(r.fonte)} · <a class="fonte" href="${esc(r.url)}" target="_blank" rel="noopener">prova ${ICONE.fora}</a> <a class="fonte" href="${esc(r.gabarito)}" target="_blank" rel="noopener">gabarito ${ICONE.fora}</a>` : "",
  ].filter(Boolean);
  const uma = opcoes.umaPorVez && f.questoes.length > 1;
  return `<li class="questao ${r.acertou ? "certa" : "errada"}"${uma && n ? " hidden" : ""}>
    ${uma ? blocoTexto(q) : textoBase(q, f.questoes[n - 1])}
    <p class="questao-enunciado"${uma ? ' tabindex="-1"' : ""}><span class="numero">${opcoes.rotulos?.[n] ?? n + 1}</span>${enunciado(q, f.alvo)}</p>
    ${r.marcada < 0 ? '<p class="em-branco">Você deixou em branco: na prova, conta como erro.</p>' : ""}
    <p class="so-leitor">${r.acertou ? `Você acertou: a ${LETRAS[r.certa]}.` : r.marcada < 0 ? `A certa é a ${LETRAS[r.certa]}.` : `Você marcou a ${LETRAS[r.marcada]}; a certa é a ${LETRAS[r.certa]}.`}</p>
    <ul class="alternativas corrigidas">${q.alternativas.map((a, k) => {
      const papel = k === r.certa ? "correta" : k === r.marcada ? "marcada" : "outra";
      const selo = k === r.marcada ? `<span class="sua">${k === r.certa ? "sua resposta · certa" : "sua resposta"}</span>`
        : k === r.certa ? '<span class="sua">a certa</span>' : "";
      const explica = k === r.certa ? certa
        : erradas[k] ? porque("Por que está errada", `<p>${esc(erradas[k])}</p>`, { oculto: k !== r.marcada }) : "";
      return `
      <li class="alternativa ${papel}${k === r.marcada ? " marcada" : ""}"><span class="letra">${LETRAS[k]}</span><span class="alt-texto">${rico(a)}</span>${selo}${explica}</li>`;
    }).join("")}</ul>
    ${outras || pe.length ? `<div class="questao-pe">
      ${outras ? `<button class="link-botao" type="button" data-outras aria-expanded="false">Ver o erro das outras ${outras}</button>` : ""}
      ${pe.length ? `<p class="meta">${pe.join(" · ")}</p>` : ""}
    </div>` : ""}
  </li>`;
}

function correcaoPerguntas(f, opcoes) {
  const c = f.correcao;
  const uma = opcoes.umaPorVez && f.questoes.length > 1;
  const acertos = c.filter((r) => r.acertou).length;
  const erros = c.length - acertos;
  const lista = `${uma ? trilhaQuestoes(f, c, opcoes.rotulos) : ""}
    <ol class="questoes-lista">${f.questoes.map((q, n) => correcaoQuestao(q, c[n], n, f, opcoes)).join("")}</ol>
    ${uma ? `<div class="questoes-rodape">${navQuestoes()}</div>` : ""}`;
  if (opcoes.placar === false) return lista; // o simulado já mostra a nota em cima
  return `<div class="placar" role="status">
      <p class="placar-nota"><span class="placar-pct">${pct(acertos, c.length)}%</span>
        <span>${acertos} certa${acertos === 1 ? "" : "s"} e ${erros} errada${erros === 1 ? "" : "s"}${f.tentativas.length > 1 ? ` · ${f.tentativas.length}ª vez` : ""}</span></p>
      ${f.tentativas.length > 1 ? `<p class="meta">${esc(melhoria(f.tentativas))}</p>` : ""}
      ${erros && !f.alvo.startsWith("erros:") ? '<p class="meta">As erradas já foram para o <a href="#/erros">Caderno de erros</a>.</p>' : ""}
      <span class="placar-acoes">
        ${opcoes.refazer === false ? "" : '<button class="botao" type="button" data-refazer>Refazer</button>'}
        ${opcoes.concluir ? `<button class="botao primario" type="button" data-estado="feito">${ICONE.feito} Concluir e seguir</button>` : ""}
      </span>
    </div>
    ${lista}`;
}

function blocoPerguntas(f, opcoes) {
  return `<section class="fixacao" aria-labelledby="t-fixacao">
    <div class="fixacao-cabeca">
      <h2 id="t-fixacao" class="titulo-bloco">${esc(opcoes.titulo)}</h2>
      <span class="meta">${esc(opcoes.sub)}</span>
    </div>
    <div class="fixacao-corpo">${f.correcao ? correcaoPerguntas(f, opcoes) : formPerguntas(f, opcoes)}</div>
  </section>`;
}

// Liga o bloco já desenhado: o Responder só acende com todas marcadas; a correção vem do servidor.
function ligarPerguntas(f, opcoes = {}) {
  const secao = pagina.querySelector(".fixacao");
  if (!secao) return;
  const corpo = secao.querySelector(".fixacao-corpo");
  // Uma por vez: mostra a questão n, marca o número dela e leva o foco junto (à marcada, ou à primeira alternativa).
  const passo = (n) => {
    const lista = [...corpo.querySelectorAll(".questoes-lista > .questao")];
    if (!corpo.querySelector(".trilha-questoes") || !lista[n]) return;
    lista.forEach((li, k) => { li.hidden = k !== n; });
    corpo.querySelectorAll("[data-passo]").forEach((b) => {
      if (Number(b.dataset.passo) === n) b.setAttribute("aria-current", "step");
      else b.removeAttribute("aria-current");
    });
    corpo.querySelector('[data-passo-ir="-1"]').disabled = n === 0;
    corpo.querySelector('[data-passo-ir="1"]').disabled = n === lista.length - 1;
    corpo.dataset.atual = n;
    return lista[n];
  };
  const andar = (n) => {
    const li = passo(n);
    if (!li) return;
    (li.querySelector("input:checked") || li.querySelector("input") || li.querySelector(".questao-enunciado"))?.focus({ preventScroll: true });
    corpo.querySelector(".trilha-questoes").scrollIntoView({ block: "nearest" });
  };
  const ligar = (dados) => {
    passo(0);
    corpo.querySelectorAll("[data-passo]").forEach((b) => b.addEventListener("click", () => andar(Number(b.dataset.passo))));
    corpo.querySelectorAll("[data-passo-ir]").forEach((b) => b.addEventListener("click", () => andar(Number(corpo.dataset.atual) + Number(b.dataset.passoIr))));
    const form = corpo.querySelector("form");
    if (form) {
      const botao = form.querySelector("[type=submit]");
      const faltam = form.querySelector("[data-faltam]");
      const marcadas = () => dados.questoes.map((_, n) => form.querySelector(`input[name="q${n}"]:checked`));
      form.addEventListener("change", () => {
        const m = marcadas();
        const resta = m.filter((x) => !x).length;
        botao.disabled = resta > 0;
        faltam.textContent = resta ? `Faltam ${resta}` : "Pode responder";
        corpo.querySelectorAll("[data-passo]").forEach((b, n) => b.classList.toggle("marcada", Boolean(m[n])));
      });
      form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const m = marcadas();
        if (m.some((x) => !x)) return;
        botao.disabled = true;
        try {
          const novo = await enviar(`/api/perguntas/${encodeURIComponent(dados.alvo)}`, "POST", { marcadas: m.map((x) => Number(x.value)) });
          const certas = novo.correcao.filter((r) => r.acertou).length;
          corpo.innerHTML = correcaoPerguntas(novo, opcoes);
          ligar(novo);
          falar(`${certas} de ${novo.correcao.length} certas.`);
          secao.scrollIntoView({ block: "start" });
          opcoes.depois?.(novo);
        } catch {
          botao.disabled = false;
          erro("Não deu para corrigir agora. Confira se a Escola está ligada e tente de novo.");
        }
      });
    }
    corpo.querySelector("[data-refazer]")?.addEventListener("click", () => {
      corpo.innerHTML = formPerguntas(dados, opcoes);
      ligar(dados);
      corpo.querySelector("input")?.focus();
    });
    corpo.querySelectorAll("[data-ir]").forEach((b) => b.addEventListener("click", () => opcoes.ir(Number(b.dataset.ir))));
    corpo.querySelectorAll("[data-outras]").forEach((b) => b.addEventListener("click", () => {
      const abrir = b.getAttribute("aria-expanded") !== "true";
      b.closest(".questao").querySelectorAll("[data-outra]").forEach((x) => { x.hidden = !abrir; });
      b.setAttribute("aria-expanded", String(abrir));
      b.textContent = abrir ? "Esconder o erro das outras" : `Ver o erro das outras ${b.closest(".questao").querySelectorAll("[data-outra]").length}`;
    }));
  };
  ligar(f);
}

function dicaDoItem(i) {
  if (i.tipo === "prova") {
    return `<section class="passos" aria-labelledby="t-simulado">
      <h2 id="t-simulado" class="titulo-bloco">Como fazer o simulado</h2>
      <ol>
        <li>Separe ${tempo(i.minutos)} sem interrupção e marque o tempo. Se não der de uma vez, faça em dois blocos.</li>
        <li>Responda sem consultar nada. Chute só no fim, e marque os chutes.</li>
        <li>Corrija pelo gabarito (abaixo). Para cada erro ou chute, anote o assunto: ele volta para a revisão.</li>
      </ol>
      ${i.gabaritos?.length ? `<p class="gabaritos">${i.gabaritos.map((g) => `<a class="link-fora" href="#/item/${g.id}/${i.concurso.id}">${titulo(g.titulo)}</a>`).join("")}</p>` : ""}
    </section>`;
  }
  if (["aula", "leitura", "guia"].includes(i.tipo) && !i.fixacao) {
    return `<p class="dica">${ICONE.redacao}<span><strong>Quando terminar:</strong> feche ${materialDe(i)} e escreva por 5 minutos tudo o que lembra, sem olhar. Depois confira. Puxar da memória fixa mais do que rever.</span></p>`;
  }
  return "";
}

const materialDe = (i) => ({ aula: "o vídeo", guia: "o guia" })[i.tipo] ?? "o texto";

// Questões de prova quando a aula tem; senão, as feitas a partir dela, e o bloco diz qual é o caso.
function perguntasDaAula(i) {
  const n = i.fixacao.questoes.length;
  const material = materialDe(i);
  if (i.fixacao.alvo.startsWith("real:")) {
    return { titulo: "Questões de prova", sub: `${n === 1 ? "Uma questão que já caiu" : `${n} questões que já caíram`} sobre este assunto, com o gabarito oficial. Quando terminar ${material}, responda sem voltar a ele.` };
  }
  if (i.fixacao.alvo.startsWith("estilo:")) {
    return { titulo: "Questões no estilo da banca", sub: `Ainda não achei questão de prova sobre esta aula: estas ${n} foram escritas no formato do ${esc(i.fixacao.questoes[0].estilo)}, a partir do conteúdo dela. Quando terminar ${material}, responda sem voltar a ele.` };
  }
  return { titulo: "Perguntas de fixação", sub: `Ainda não achei questão de prova sobre esta aula: estas foram feitas a partir dela. Quando terminar ${material}, responda as ${n} sem voltar a ele. Se errar, a correção mostra o trecho e ${i.youtube ? "o minuto" : "a página"}.` };
}

async function item(id, cid) {
  const i = await api(`/api/itens/${encodeURIComponent(id)}${cid ? `?concurso=${encodeURIComponent(cid)}` : ""}`);
  if (i.tipo === "prova" && i.simulado) return simuladoTela(i);
  const c = i.concurso.id;
  const ant = i.anterior ? `<a class="botao" href="#/item/${i.anterior.id}/${c}" title="${esc(suave(i.anterior.titulo))}">${ICONE.anterior} Anterior</a>` : `<span class="botao inativo" aria-disabled="true">${ICONE.anterior} Anterior</span>`;
  const prox = i.proxima ? `<a class="botao" href="#/item/${i.proxima.id}/${c}" title="${esc(suave(i.proxima.titulo))}">Próxima ${ICONE.proxima}</a>` : "";
  // Com questões ainda sem resposta, o botão laranja leva a elas: concluir sem responder fica possível, mas discreto.
  // Depois do placar, o Concluir volta a ser o botão principal (em cima e no placar).
  const pendentes = i.estado !== "feito" && i.fixacao && !i.fixacao.correcao ? i.fixacao.questoes.length : 0;
  const concluir = i.estado === "feito"
    ? `<span class="feito-msg">${ICONE.feito}<span>Feito</span></span>
       <button class="link-botao" type="button" data-estado="novo">Desmarcar</button>`
    : pendentes
      ? `<button class="botao primario" type="button" data-ir-questoes>${ICONE.desce} Responder ${pendentes === 1 ? "a questão" : `as ${pendentes} questões`}</button>`
      : `<button class="botao primario" type="button" data-estado="feito">${ICONE.feito} Concluir e seguir</button>`;
  const depois = (i.estado === "feito" || i.estado === "depois" ? "" : '<button class="link-botao" type="button" data-estado="depois">Deixar para depois</button>')
    + (pendentes ? '<button class="link-botao" type="button" data-estado="feito" data-sem-responder>Concluir sem responder</button>' : "");
  document.title = `${suave(i.titulo)} · Escola`;
  pagina.innerHTML = `
    ${aviso()}
    <div class="sala">
      <div class="sala-principal">
        <div class="trilha-topo">${voltar(`#/concurso/${c}`)}${migalhas([[i.concurso.nome, `#/concurso/${c}`], [i.materia], [i.assunto]])}</div>
        ${i.guia ? "" : palco(i)}
        <header class="cabeca-item">
          <h1 class="titulo-item">${titulo(i.titulo)}</h1>
          <p class="meta">${meta(i)}${i.estado === "depois" ? " · para depois" : ""}</p>
        </header>
        <div class="acoes">
          <div class="acoes-andar">${ant}${concluir}${prox}</div>
          <div class="acoes-mais">${depois}${botaoJuntos(i)}${abrirFora(i)}</div>
        </div>
        ${i.nota || (i.tambem.length && !i.guia) ? `<div class="sobre-item">
          ${i.nota ? `<p class="nota">${esc(i.nota)}</p>` : ""}
          ${i.tambem.length ? `<p class="meta">Também cai em: ${i.tambem.map(esc).join(", ")}.</p>` : ""}
        </div>` : ""}
        ${i.guia ? paginaGuia(i.guia) : ""}
        ${dicaDoItem(i)}
        ${i.fixacao ? blocoPerguntas(i.fixacao, { ...perguntasDaAula(i), concluir: i.estado !== "feito" }) : ""}
      </div>
      ${listaDaMateria(i)}
    </div>`;
  pagina.querySelector(".item-lista.atual")?.scrollIntoView({ block: "nearest" });
  ligarJuntos(i);
  if (i.fixacao) {
    // "Ver no vídeo" começa 5 s antes: a legenda marca a fala um pouco depois de ela começar
    const ir = (onde) => {
      const video = pagina.querySelector(".video iframe");
      const pdf = pagina.querySelector("iframe.pdf");
      if (juntos) { juntos.player.seekTo(Math.max(0, onde - 5), true); juntos.player.playVideo(); pagina.querySelector(".video").scrollIntoView({ block: "center" }); return; }
      if (video) video.src = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(i.youtube)}?rel=0&autoplay=1&start=${Math.max(0, onde - 5)}`;
      else if (pdf) pdf.src = `${i.pdf}?v=${Date.now()}#page=${onde}`;
      else { window.open(`${i.url.split("#")[0]}#page=${onde}`, "_blank", "noopener"); return; }
      (video || pdf).scrollIntoView({ block: "center" });
    };
    // Respondeu: o botão de cima vira o Concluir, e o "Concluir sem responder" perde o sentido.
    const respondeu = () => {
      pagina.querySelector("[data-ir-questoes]")?.replaceWith(Object.assign(document.createElement("span"), {
        innerHTML: `<button class="botao primario" type="button" data-estado="feito">${ICONE.feito} Concluir e seguir</button>` }).firstChild);
      pagina.querySelector("[data-sem-responder]")?.remove();
    };
    ligarPerguntas(i.fixacao, { video: Boolean(i.youtube), ir, concluir: i.estado !== "feito", depois: respondeu });
  }

  // Os botões de estado mudam de lugar (o Concluir aparece no placar depois de responder): um ouvinte só, na sala.
  const sala = pagina.querySelector(".sala");
  sala.addEventListener("click", async (e) => {
    if (e.target.closest("[data-ir-questoes]")) {
      const s = pagina.querySelector(".fixacao");
      s.scrollIntoView({ block: "start", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
      s.querySelector("input")?.focus({ preventScroll: true });
      return;
    }
    const b = e.target.closest("[data-estado]");
    if (!b) return;
    const botoes = [...sala.querySelectorAll("[data-estado]")];
    const estado = b.dataset.estado;
    botoes.forEach((x) => { x.disabled = true; });
    try {
      const r = await enviar(`/api/itens/${encodeURIComponent(i.id)}/estado?concurso=${encodeURIComponent(c)}`, "POST", { estado });
      if (estado === "novo") {
        falar("Desmarcado.");
        await item(i.id, c);
        return;
      }
      let destino;
      if (estado === "feito" && r.plano.tinha && r.plano.feito) {
        recado = "Plano de hoje feito. Bom trabalho: o resto fica para o próximo dia de estudo.";
        destino = "#/";
      } else if (estado === "feito" && r.plano.tinha && r.plano.seguinte) {
        recado = `Feito. Agora, no plano de hoje: ${suave(r.plano.seguinte.titulo)}`;
        destino = r.plano.seguinte.rota;
      } else {
        const p = r.proximo && r.proximo.id !== i.id ? r.proximo : null;
        recado = estado === "feito"
          ? (p ? `Feito. Agora: ${suave(p.titulo)}` : "Feito. Você terminou o caminho.")
          : (p ? `Ficou para depois. Agora: ${suave(p.titulo)}` : "Ficou para depois.");
        destino = p ? p.rota : "#/";
      }
      falar(recado);
      location.hash = destino;
    } catch {
      botoes.forEach((x) => { x.disabled = false; });
      erro("Não deu para salvar. Confira se a Escola está ligada e tente de novo.");
    }
  });
}

/* ---------- Simulado dentro da Escola ---------- */

// A prova inteira, com cronômetro e a folha guardada a cada marcação; ao entregar, a nota por matéria e a correção.
// Abre pela própria prova do curso: #/item/<prova>. Quem preferir o papel ainda tem o PDF.
async function simuladoTela(i) {
  const s = await api(`/api/simulados/${encodeURIComponent(i.id)}`);
  document.title = `${suave(i.titulo)} · Escola`;
  if (s.rascunho) return provaEmAndamento(i, s);
  if (s.resultado) return resultadoSimulado(i, s);
  return aberturaSimulado(i, s);
}

function cabecaSimulado(i, s, rotulo) {
  return `<div class="trilha-topo">${voltar(`#/concurso/${s.concurso.id}`)}${migalhas([[i.concurso.nome, `#/concurso/${s.concurso.id}`], [i.materia]])}</div>
    <header class="cabeca">
      <h1>${titulo(i.titulo)}</h1>
      <p class="rotulo">${rotulo}</p>
    </header>`;
}

function foraDaNota(s) {
  if (!s.fora.length) return "";
  return `<details class="como fora-da-nota"><summary>${s.fora.length === 1 ? "Uma questão da prova ficou" : `${s.fora.length} questões da prova ficaram`} de fora da nota</summary>
    <ul>${s.fora.map((f) => `<li><strong>${f.numero}:</strong> ${esc(f.motivo)}</li>`).join("")}</ul></details>`;
}

async function comecarSimulado(i) {
  await enviar(`/api/simulados/${encodeURIComponent(i.id)}/comecar`, "POST", {});
  await simuladoTela(i);
  window.scrollTo(0, 0);
}

function aberturaSimulado(i, s) {
  const n = s.perguntas.questoes.length;
  pagina.innerHTML = `
    ${aviso()}
    ${cabecaSimulado(i, s, `Simulado · ${n} questões · ${tempo(s.minutos)}`)}
    <section class="passos" aria-labelledby="t-como-simulado">
      <h2 id="t-como-simulado" class="titulo-bloco">Como funciona</h2>
      <ol>
        <li>Separe ${tempo(s.minutos)} sem interrupção. O cronômetro começa no botão abaixo e segue contando se a página fechar: o que você marcou fica guardado.</li>
        <li>Responda sem consultar nada. Em branco conta como erro, como na prova: se faltar tempo, chute no fim.</li>
        <li>Ao entregar, a nota sai na hora, por matéria, com a correção de cada questão. As erradas vão para o Caderno de erros.</li>
      </ol>
      ${s.redacao ? '<p class="meta">A redação desta prova fica para o treino de redação: aqui é só a parte objetiva.</p>' : ""}
      ${foraDaNota(s)}
      <div class="acoes-andar">
        <button class="botao primario grande" type="button" data-comecar>Começar o simulado ${ICONE.seta}</button>
        ${s.pdf ? `<a class="link-fora" href="${esc(s.pdf)}" target="_blank" rel="noopener">Prefiro no papel: abrir o PDF ${ICONE.fora}</a>` : ""}
      </div>
    </section>`;
  pagina.querySelector("[data-comecar]").addEventListener("click", async (e) => {
    const b = e.currentTarget;
    b.disabled = true;
    try { await comecarSimulado(i); } catch {
      b.disabled = false;
      erro("Não deu para começar. Confira se a Escola está ligada e tente de novo.");
    }
  });
}

// "1:42:05" ou "42:05"; passado do tempo, "+3:10"
function relogioDe(segundos) {
  const t = Math.abs(segundos);
  const h = Math.floor(t / 3600), m = Math.floor((t % 3600) / 60), s = t % 60;
  return `${segundos < 0 ? "+" : ""}${h ? `${h}:${dois(m)}` : m}:${dois(s)}`;
}

function provaEmAndamento(i, s) {
  const f = s.perguntas;
  const marcadas = [...s.rascunho.marcadas];
  const limite = new Date(s.rascunho.inicio).getTime() + s.minutos * 60000;
  pagina.innerHTML = `
    <div class="simulado-barra">
      <span class="simulado-nome">${titulo(i.titulo)}</span>
      <span class="simulado-tempo" role="timer" aria-live="off" data-tempo></span>
      <span class="meta" data-respondidas aria-live="polite"></span>
      <button class="botao primario" type="button" data-entregar>Entregar</button>
    </div>
    <form class="questoes uma-por-vez simulado-folha" novalidate>
      ${trilhaQuestoes(f, null, s.numeros)}
      <ol class="questoes-lista">${f.questoes.map((q, n) => `
        <li class="questao"${n ? " hidden" : ""}>
          ${blocoTexto(q)}
          <fieldset>
            <legend><span class="numero">${s.numeros[n] ?? n + 1}</span>${enunciado(q, f.alvo)}</legend>
            <div class="alternativas">${q.alternativas.map((a, k) => alternativa(n, k, a, marcadas[n] === k)).join("")}</div>
          </fieldset>
          <button class="link-botao" type="button" data-branco="${n}">Deixar em branco</button>
        </li>`).join("")}</ol>
      <div class="questoes-rodape">${navQuestoes()}<span class="meta" data-salvo aria-live="polite"></span></div>
    </form>
    <p class="simulado-pe"><button class="link-botao" type="button" data-desistir>Desistir e apagar o que marquei</button></p>`;

  const corpo = pagina.querySelector(".simulado-folha");
  const tempoEl = pagina.querySelector("[data-tempo]");
  const respondidas = pagina.querySelector("[data-respondidas]");
  const salvo = pagina.querySelector("[data-salvo]");
  const entregar = pagina.querySelector("[data-entregar]");
  let confirmar = false;

  // o mesmo andar das questões uma por vez do aquecimento: números em cima, Anterior e Próxima embaixo
  const passo = (n) => {
    const lista = [...corpo.querySelectorAll(".questoes-lista > .questao")];
    if (!lista[n]) return;
    lista.forEach((li, k) => { li.hidden = k !== n; });
    corpo.querySelectorAll("[data-passo]").forEach((b) => (Number(b.dataset.passo) === n ? b.setAttribute("aria-current", "step") : b.removeAttribute("aria-current")));
    corpo.querySelector('[data-passo-ir="-1"]').disabled = n === 0;
    corpo.querySelector('[data-passo-ir="1"]').disabled = n === lista.length - 1;
    corpo.dataset.atual = n;
    (lista[n].querySelector("input:checked") || lista[n].querySelector("input"))?.focus({ preventScroll: true });
    corpo.querySelector(".trilha-questoes").scrollIntoView({ block: "nearest" });
  };
  const contar = () => {
    const feitas = marcadas.filter((m) => m != null).length;
    respondidas.textContent = `${feitas} de ${marcadas.length} marcadas`;
    corpo.querySelectorAll("[data-passo]").forEach((b, n) => b.classList.toggle("marcada", marcadas[n] != null));
    confirmar = false;
    entregar.textContent = "Entregar";
  };
  const tique = () => {
    const resta = Math.round((limite - Date.now()) / 1000);
    tempoEl.textContent = relogioDe(resta);
    tempoEl.classList.toggle("estourou", resta < 0);
    tempoEl.setAttribute("aria-label", resta < 0 ? "O tempo da prova acabou" : `Faltam ${relogioDe(resta)}`);
    if ([1800, 600, 0].includes(resta)) falar(resta ? `Faltam ${resta / 60} minutos.` : "O tempo da prova acabou. Entregue quando quiser.");
  };
  let guardar = null;
  const salvar = () => {
    clearTimeout(guardar);
    salvo.textContent = "";
    guardar = setTimeout(async () => {
      try {
        await enviar(`/api/simulados/${encodeURIComponent(i.id)}/rascunho`, "PUT", { marcadas });
        salvo.textContent = "Guardado";
      } catch { salvo.textContent = "Não deu para guardar: confira se a Escola está ligada."; }
    }, 400);
  };

  corpo.addEventListener("change", (e) => {
    const n = Number(e.target.name.slice(1));
    marcadas[n] = Number(e.target.value);
    contar();
    salvar();
  });
  corpo.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    if (b.dataset.passo != null) passo(Number(b.dataset.passo));
    else if (b.dataset.passoIr) passo(Number(corpo.dataset.atual) + Number(b.dataset.passoIr));
    else if (b.dataset.branco != null) {
      const n = Number(b.dataset.branco);
      corpo.querySelectorAll(`input[name="q${n}"]`).forEach((x) => { x.checked = false; });
      marcadas[n] = null;
      contar();
      salvar();
    }
  });
  entregar.addEventListener("click", async () => {
    const brancos = marcadas.filter((m) => m == null).length;
    if (brancos && !confirmar) { // entregar com questão em branco pede um segundo toque: o botão diz quantas
      confirmar = true;
      entregar.textContent = `Entregar com ${brancos} em branco`;
      falar(`${brancos} ${brancos === 1 ? "questão está" : "questões estão"} em branco. Toque de novo para entregar assim.`);
      return;
    }
    entregar.disabled = true;
    clearTimeout(guardar);
    try {
      await enviar(`/api/simulados/${encodeURIComponent(i.id)}`, "POST", { marcadas });
      if (relogio) { clearInterval(relogio); relogio = null; }
      recado = "Simulado entregue. A nota e a correção estão abaixo.";
      falar(recado);
      await simuladoTela(i);
      window.scrollTo(0, 0);
    } catch {
      entregar.disabled = false;
      erro("Não deu para entregar. O que você marcou está guardado; confira se a Escola está ligada e tente de novo.");
    }
  });
  pagina.querySelector("[data-desistir]").addEventListener("click", async (e) => {
    const b = e.currentTarget;
    if (!b.dataset.certeza) { b.dataset.certeza = "1"; b.textContent = "Apagar mesmo? Toque de novo"; return; }
    if (relogio) { clearInterval(relogio); relogio = null; }
    await api(`/api/simulados/${encodeURIComponent(i.id)}/rascunho`, { method: "DELETE" });
    await simuladoTela(i);
  });

  contar();
  passo(0);
  tique();
  relogio = setInterval(tique, 1000); // o render para o cronômetro quando a tela muda
}

function resultadoSimulado(i, s) {
  const r = s.resultado;
  const t = s.perguntas.tentativas.at(-1);
  pagina.innerHTML = `
    ${aviso()}
    ${cabecaSimulado(i, s, `Simulado feito em ${dataCurta(t.em)}${s.perguntas.tentativas.length > 1 ? ` · ${s.perguntas.tentativas.length}ª vez` : ""}`)}
    <section class="simulado-nota" aria-labelledby="t-nota">
      <h2 id="t-nota" class="so-leitor">A nota</h2>
      <p class="placar-nota"><span class="placar-pct">${pct(r.acertos, r.total)}%</span>
        <span>${r.acertos} de ${r.total} certas${r.em_branco ? ` · ${r.em_branco} em branco` : ""}</span></p>
      <table class="placar-materias">
        <thead><tr><th scope="col">Matéria</th><th scope="col">Certas</th><th scope="col">Acerto</th></tr></thead>
        <tbody>${r.por_materia.map((m) => `<tr><th scope="row">${esc(m.materia)}</th><td>${m.acertos} de ${m.total}</td><td>${pct(m.acertos, m.total)}%</td></tr>`).join("")}</tbody>
      </table>
      ${r.piores.length ? `<h3 class="titulo-bloco">Onde você mais perdeu pontos</h3>
        <ul class="piores">${r.piores.map((x) => `<li><span class="piores-nome">${esc(x.assunto)}</span>
          <span class="meta">errou ${x.erros} de ${x.total}</span>${x.rota ? `<a class="link-seta" href="${esc(x.rota)}">Rever a aula ${ICONE.seta}</a>` : ""}</li>`).join("")}</ul>` : ""}
      <p class="meta">As erradas${r.em_branco ? " e as em branco" : ""} já estão no <a href="#/erros">Caderno de erros</a>.</p>
      ${foraDaNota(s)}
    </section>
    ${blocoPerguntas(s.perguntas, { titulo: "Correção", sub: "Uma por vez · os números mostram a certa e a errada", refazer: false, umaPorVez: true, rotulos: s.numeros, placar: false })}
    <p class="simulado-pe"><button class="link-botao" type="button" data-de-novo>Fazer de novo, do zero</button></p>`;
  ligarPerguntas(s.perguntas, { refazer: false, umaPorVez: true, rotulos: s.numeros, placar: false });
  pagina.querySelector("[data-de-novo]").addEventListener("click", () => comecarSimulado(i));
}

/* ---------- Revisão e redação ---------- */

function cronometro(minutos, rotulo) {
  return `<div class="cronometro" data-minutos="${minutos}">
    <button class="botao" type="button" data-cronometro>${ICONE.relogio}<span>${esc(rotulo)}</span></button>
    <span class="cronometro-tempo" role="timer" aria-live="off">${dois(minutos)}:00</span>
  </div>`;
}

function ligarCronometros() {
  pagina.querySelectorAll(".cronometro").forEach((caixa) => {
    const botao = caixa.querySelector("[data-cronometro]");
    const mostrador = caixa.querySelector(".cronometro-tempo");
    const rotulo = botao.querySelector("span").textContent;
    botao.addEventListener("click", () => {
      if (relogio) {
        clearInterval(relogio);
        relogio = null;
        botao.querySelector("span").textContent = rotulo;
        caixa.classList.remove("correndo");
        return;
      }
      let resta = Number(caixa.dataset.minutos) * 60;
      caixa.classList.add("correndo");
      botao.querySelector("span").textContent = "Parar";
      relogio = setInterval(() => {
        resta -= 1;
        mostrador.textContent = `${dois(Math.floor(resta / 60))}:${dois(resta % 60)}`;
        if (resta <= 0) {
          clearInterval(relogio);
          relogio = null;
          caixa.classList.remove("correndo");
          caixa.classList.add("acabou");
          botao.querySelector("span").textContent = rotulo;
          mostrador.textContent = "Tempo!";
          falar("Tempo. Pode passar para o próximo passo.");
        }
      }, 1000);
    });
  });
}

async function marcarTarefa(tid, estado, botao) {
  botao.disabled = true;
  try {
    const d = await enviar(`/api/plano/${encodeURIComponent(tid)}/estado`, "POST", { estado });
    if (estado === "novo") {
      falar("Desmarcado.");
      render();
      return;
    }
    if (d.adiantando || !d.continuar) {
      recado = "Plano de hoje feito. Bom trabalho: o resto fica para o próximo dia de estudo.";
      location.hash = "#/";
    } else {
      recado = `Feito. Agora: ${suave(d.continuar.titulo)}`;
      location.hash = d.continuar.rota;
    }
    falar(recado);
  } catch {
    botao.disabled = false;
    erro("Não deu para salvar. Confira se a Escola está ligada e tente de novo.");
  }
}

function acoesTarefa(t, rotulo) {
  return t.estado === "feito"
    ? `<span class="feito-msg">${ICONE.feito}<span>Feito</span></span><button class="link-botao" type="button" data-tarefa="novo">Desmarcar</button>`
    : `<button class="botao primario" type="button" data-tarefa="feito">${ICONE.feito} ${esc(rotulo)}</button>`;
}

async function revisao(aid, k) {
  const r = await api(`/api/revisoes/${encodeURIComponent(aid)}/${encodeURIComponent(k)}`);
  const temPerguntas = r.nota.trim().length > 0;
  document.title = `Revisão de ${r.assunto.nome} · Escola`;
  pagina.innerHTML = `
    ${aviso()}
    <div class="trilha-topo">${voltar("#/")}${migalhas([[r.concurso.nome, `#/concurso/${r.concurso.id}`], [r.materia], [r.assunto.nome]])}</div>
    <header class="cabeca">
      <h1>Revisão de ${esc(r.assunto.nome)}</h1>
      <p class="rotulo">Revisão nº ${r.numero} · ${tempo(r.minutos)}</p>
      <p class="sub largo">Revisar é puxar da memória, não reler. É isso que mais segura o assunto até a prova.</p>
    </header>
    <div class="dupla">
      <section class="passos" aria-labelledby="t-passos">
        <h2 id="t-passos" class="titulo-bloco">Os passos</h2>
        <ol>
          ${temPerguntas ? "<li>Responda de cabeça as suas perguntas (ao lado), sem abrir nada.</li>" : ""}
          <li>Feche o material. Por 5 minutos, escreva numa folha tudo o que lembra deste assunto.</li>
          <li>Abra o material (abaixo) e confira. Marque o que faltou ou saiu errado.</li>
          <li>Para cada lacuna, escreva uma pergunta com a resposta, até 5, no quadro ao lado. Elas voltam na próxima revisão.</li>
          <li>Releia só o trecho das lacunas, não o material todo.</li>
        </ol>
        ${cronometro(5, "Começar os 5 minutos")}
        <p class="edital"><strong>O que o edital pede:</strong> ${esc(r.assunto.edital)}</p>
      </section>
      <section class="perguntas" aria-labelledby="t-perguntas">
        <h2 id="t-perguntas" class="titulo-bloco">Suas perguntas deste assunto</h2>
        <label class="so-leitor" for="nota">Perguntas e respostas, uma por linha</label>
        <textarea id="nota" rows="10" placeholder="Ex.: O que o Código de Ética diz sobre sigilo? Resposta: …">${esc(r.nota)}</textarea>
        <p class="meta" id="nota-estado">Uma por linha. Guarda sozinho enquanto você escreve.</p>
      </section>
    </div>
    <section aria-labelledby="t-material">
      <h2 id="t-material" class="titulo-bloco">Material para conferir</h2>
      <ol class="lista">${r.itens.map((i) => linha(i, { onde: false })).join("")}</ol>
    </section>
    <div class="acoes"><div class="acoes-andar">${acoesTarefa(r, "Revisão feita")}</div></div>`;
  ligarCronometros();
  pagina.querySelectorAll("[data-tarefa]").forEach((b) => b.addEventListener("click", () => marcarTarefa(r.id, b.dataset.tarefa, b)));
  const campo = pagina.querySelector("#nota");
  const estadoNota = pagina.querySelector("#nota-estado");
  let espera = null;
  campo.addEventListener("input", () => {
    clearTimeout(espera);
    estadoNota.textContent = "Guardando…";
    espera = setTimeout(async () => {
      try {
        await enviar(`/api/notas/${encodeURIComponent(aid)}`, "PUT", { texto: campo.value });
        estadoNota.textContent = "Guardado.";
      } catch {
        estadoNota.textContent = "Não deu para guardar agora. Copie o texto antes de sair da página.";
      }
    }, 700);
  });
}

async function redacao(dia, cid) {
  const r = await api(`/api/redacoes/${encodeURIComponent(dia)}/${encodeURIComponent(cid)}`);
  document.title = "Redação da semana · Escola";
  pagina.innerHTML = `
    ${aviso()}
    <div class="trilha-topo">${voltar("#/")}${migalhas([[r.concurso.nome, `#/concurso/${r.concurso.id}`], ["Redação"]])}</div>
    <header class="cabeca">
      <h1>Redação da semana</h1>
      <p class="rotulo">${esc(dataLonga(r.dia).replace(/^./, (l) => l.toUpperCase()))} · 60 min de escrita e 20 de correção</p>
      <p class="sub largo">Escrever toda semana, sob tempo e com correção, é o treino que mais se parece com a prova.</p>
    </header>
    <section class="passos" aria-labelledby="t-passos">
      <h2 id="t-passos" class="titulo-bloco">Os passos</h2>
      <ol>
        <li>Escolha um tema que você ainda não usou (há sugestões no material de temas, abaixo).</li>
        <li>Escreva um texto dissertativo-argumentativo de 15 a 30 linhas, à mão, em 60 minutos e sem consultar nada.</li>
        <li>Corrija com calma: o texto atende ao tema? Tem introdução, desenvolvimento e conclusão? Os argumentos se sustentam? E o português? Se alguém puder ler, melhor.</li>
        <li>Reescreva o parágrafo mais fraco.</li>
      </ol>
      ${cronometro(60, "Começar os 60 minutos")}
    </section>
    <section aria-labelledby="t-material">
      <h2 id="t-material" class="titulo-bloco">Material de redação</h2>
      <ol class="lista">${r.itens.map((i) => linha(i)).join("")}</ol>
    </section>
    <div class="acoes"><div class="acoes-andar">${acoesTarefa(r, "Redação feita")}</div></div>`;
  ligarCronometros();
  pagina.querySelectorAll("[data-tarefa]").forEach((b) => b.addEventListener("click", () => marcarTarefa(r.id, b.dataset.tarefa, b)));
}

async function provinhaTela(mid) {
  const p = await api(`/api/provinhas/${encodeURIComponent(mid)}`);
  const n = p.perguntas.questoes.length;
  const falta = p.materia.total - p.materia.feitos;
  document.title = `${p.titulo} · Escola`;
  pagina.innerHTML = `
    ${aviso()}
    <div class="trilha-topo">${voltar(`#/concurso/${p.concurso.id}`)}${migalhas([[p.concurso.nome, `#/concurso/${p.concurso.id}`], [p.materia.nome], ["Provinha"]])}</div>
    <header class="cabeca">
      <h1>${esc(p.titulo)}</h1>
      <p class="rotulo">Provinha do módulo · ${n} questões · ${tempo(p.minutos)}</p>
      <p class="sub largo">Questões que já caíram em prova, com o gabarito oficial. Faça sem consultar nada e de olho no tempo. Errar aqui é bom: a correção mostra o que revisar antes da prova de verdade.</p>
    </header>
    ${falta > 0 ? `<p class="dica">${ICONE.depois}<span>Ainda faltam ${falta} de ${p.materia.total} aulas e leituras de ${esc(p.materia.nome)}. Dá para fazer agora, mas a provinha rende mais no fim do módulo.</span></p>` : ""}
    ${p.perguntas.correcao ? "" : cronometro(p.minutos, "Começar o tempo")}
    ${blocoPerguntas(p.perguntas, { titulo: "Questões", sub: "De provas anteriores, cada uma com a prova e o gabarito de onde veio" })}`;
  ligarCronometros();
  ligarPerguntas(p.perguntas, {
    depois: () => {
      if (relogio) { clearInterval(relogio); relogio = null; }
      pagina.querySelector(".cronometro")?.remove();
    },
  });
}

/* ---------- Curso (concurso) ---------- */

// O edital do assunto junta o texto de cada concurso ("Aeronáutica: … Marinha (temporário): …"). No curso, fica só o
// trecho dele (29/10): os outros eram três ou quatro linhas cinzentas em cada assunto. Sem o rótulo dele, vai inteiro.
const FORCA = "(?:Aeronáutica|Exército|Marinha(?: \\(temporário\\))?)";
const ROTULO_EDITAL = new RegExp(`(?:^|(?<=\\. ))(${FORCA}(?: e ${FORCA})*): `, "g");
function editalDo(texto, nome) {
  const rotulos = [...texto.matchAll(ROTULO_EDITAL)];
  const k = rotulos.findIndex((r) => r[1].split(" e ").includes(nome));
  if (k < 0) return texto;
  return texto.slice(rotulos[k].index + rotulos[k][0].length, rotulos[k + 1]?.index ?? texto.length).trim()
    .replace(/^./, (l) => l.toUpperCase());
}

function aulasDoCurso(c) {
  const pendente = c.materias.findIndex((m) => m.feitos < m.total);
  const aberta = pendente < 0 ? 0 : pendente;
  return `<section class="materias" aria-label="Matérias do edital">${c.materias.map((m, n) => `
    <details class="materia"${n === aberta ? " open" : ""}>
      <summary>
        <span class="materia-nome">${esc(m.nome)}${m.fixacao.total ? `<span class="meta materia-acerto">${pct(m.fixacao.acertos, m.fixacao.total)}% de acerto nas perguntas</span>` : ""}</span>
        <span class="progresso">${barra(m.feitos, m.total)}<span class="meta">${m.feitos} de ${m.total}</span></span>
        <span class="seta-abrir">${ICONE.abrir}</span>
      </summary>
      <ol class="assuntos">${m.assuntos.map((a) => `
        <li class="assunto">
          <div class="assunto-cabeca"><h3>${esc(a.nome)}</h3>${a.total ? `<span class="meta">${a.feitos} de ${a.total}</span>` : ""}</div>
          <p class="edital">${esc(editalDo(a.edital, c.nome))}</p>
          ${a.itens.length ? listaComExtras(a.itens, (i) => linha(i, { onde: false }), { classe: "lista" }) : '<p class="vazio">Material em montagem.</p>'}
        </li>`).join("")}</ol>
      ${m.provinha ? `<div class="provinha-cartao${m.provinha.estado === "feito" ? " feito" : ""}">
        <span class="provinha-icone">${m.provinha.estado === "feito" ? ICONE.feito : ICONE.provinha}</span>
        <div class="provinha-texto">
          <h3>Provinha do módulo</h3>
          <p class="meta">${m.provinha.questoes} questões de provas anteriores · ${tempo(m.provinha.minutos)}${m.provinha.ultima ? ` · da última vez, ${m.provinha.ultima[0]} de ${m.provinha.ultima[1]} (${pct(...m.provinha.ultima)}%)` : ""}</p>
        </div>
        <a class="botao" href="${esc(m.provinha.rota)}">${m.provinha.ultima ? "Ver ou refazer" : "Fazer a provinha"}</a>
      </div>` : ""}
      ${m.livros.length ? `<details class="livros">
        <summary><span class="livros-nome">Livros que o edital indica</span>
          <span class="meta">${m.livros.length} · os grátis abrem aqui; os pagos, numa biblioteca</span><span class="seta-abrir">${ICONE.abrir}</span></summary>
        <ul class="livros-lista">${m.livros.map(livro).join("")}</ul>
      </details>` : ""}
    </details>`).join("")}
  </section>`;
}

function situacaoBloco(s, verificado, oficial, { cabeca = true } = {}) {
  if (!s) {
    return `<p class="sub">Ainda sem a primeira busca. Ela roda sozinha às 10h (ou quando o PC ligar) e depois toda semana.</p>`;
  }
  const nenhuma = s.datas.length > 1 && s.datas.every((d) => !d.confirmada);
  const fontes = s.fontes.filter((f) => f.url !== s.edital?.url && f.url !== oficial);
  return `<div class="situacao-corpo">
    ${cabeca ? `<p>${selo(s)} <span class="meta">desde ${dataCurta(s.desde)}</span></p>` : ""}
    <p class="situacao-resumo">${esc(s.resumo)}</p>
    ${s.datas.length ? `<ul class="datas">${s.datas.map((d) => `<li><span>${esc(d.evento)}</span><span class="data">${esc(d.data)}${d.confirmada || nenhuma ? "" : ' <span class="meta">(não confirmada)</span>'}</span></li>`).join("")}</ul>
      ${nenhuma ? '<p class="meta">Datas ainda não confirmadas no aviso oficial.</p>' : ""}` : ""}
    ${s.edital ? `<a class="link-fora" href="${esc(s.edital.url)}" target="_blank" rel="noopener">${esc(s.edital.titulo)} ${ICONE.fora}</a>` : ""}
    ${fontes.length ? `<p class="fontes"><span class="meta">Fontes:</span> ${links(fontes)}</p>` : ""}
    ${verificado ? `<p class="meta">Verificado em ${dataCompleta(verificado)} às ${verificado.slice(11, 16)}.</p>` : ""}
  </div>`;
}

function sobreDoCurso(c) {
  const edital = c.edital.pdf || c.edital.url;
  return `<div class="sobre">
    <div class="sobre-principal">
      <section aria-labelledby="t-prova"><h2 id="t-prova" class="titulo-bloco">A prova</h2><p>${esc(c.prova)}</p></section>
      <section aria-labelledby="t-req"><h2 id="t-req" class="titulo-bloco">Requisitos</h2><ul class="marcadores">${c.requisitos.map((r) => `<li>${esc(r)}</li>`).join("")}</ul></section>
      <section aria-labelledby="t-ficha"><h2 id="t-ficha" class="titulo-bloco">O concurso em detalhe</h2>
        <dl class="ficha">${c.sobre.map((s) => `<div><dt>${esc(s.rotulo)}</dt><dd>${esc(s.valor)}${s.fontes.length ? `<span class="fontes">${links(s.fontes)}</span>` : ""}</dd></div>`).join("")}</dl>
      </section>
    </div>
    <div class="sobre-lado">
      <section class="caixa" aria-labelledby="t-agora"><h2 id="t-agora" class="titulo-bloco">Situação agora</h2>${situacaoBloco(c.situacao, c.verificado_em, c.pagina_oficial)}</section>
      <section class="caixa" aria-labelledby="t-ultimo"><h2 id="t-ultimo" class="titulo-bloco">Datas do último edital</h2>
        <ol class="linha-do-tempo">${c.cronograma_ultimo.map((e) => `<li><span class="data">${esc(e.data)}</span><span>${esc(e.evento)}</span></li>`).join("")}</ol>
        <p class="links-caixa">
          ${edital ? `<a class="link-fora" href="${esc(edital)}" target="_blank" rel="noopener">${esc(c.edital.titulo)} ${ICONE.fora}</a>` : ""}
          ${c.pagina_oficial ? `<a class="link-fora" href="${esc(c.pagina_oficial)}" target="_blank" rel="noopener">Página oficial ${ICONE.fora}</a>` : ""}
        </p>
      </section>
      <p class="meta">${esc(c.proximo)}</p>
    </div>
  </div>`;
}

async function concurso(id, aba) {
  const c = await api(`/api/concursos/${encodeURIComponent(id)}`);
  const prova = c.prova_data
    ? (c.prova_confirmada ? `Prova em ${dataCompleta(c.prova_data)}` : `Prova prevista para ${mesAno(c.prova_data)}`)
    : "";
  const sobre = aba === "sobre";
  document.title = `${c.nome} · Escola`;
  pagina.innerHTML = `
    ${aviso()}
    <div class="trilha-topo">${voltar("#/")}</div>
    <header class="capa-curso">
      ${c.foto ? `<img src="${esc(c.foto)}" alt="" class="capa-curso-foto">` : ""}
      <div class="capa-curso-texto">
        <p class="capa-selos">${selo(c.situacao)}${prova ? `<span class="selo selo-neutro">${esc(prova)}</span>` : ""}</p>
        <h1>${esc(c.nome)} <span class="sigla">${esc(c.sigla)}</span></h1>
        <p class="sub">${esc(c.cargo)}</p>
        <div class="capa-curso-rodape">
          <span class="progresso">${barra(c.feitos, c.total)}<span class="meta">${c.feitos} de ${c.total} feitos</span></span>
          ${c.continuar ? `<a class="botao primario" href="${esc(c.continuar)}">Continuar este curso ${ICONE.seta}</a>` : ""}
        </div>
      </div>
      ${c.credito ? `<a class="credito" href="${esc(c.credito.pagina)}" target="_blank" rel="noopener" title="${esc(c.credito.mostra)}">Foto: ${esc(c.credito.autor)}, ${esc(c.credito.licenca)}</a>` : ""}
    </header>
    <nav class="abas" aria-label="Partes do curso">
      <a href="#/concurso/${c.id}"${sobre ? "" : ' aria-current="page"'}>Aulas</a>
      <a href="#/concurso/${c.id}/sobre"${sobre ? ' aria-current="page"' : ""}>Sobre o concurso</a>
    </nav>
    ${sobre ? sobreDoCurso(c) : aulasDoCurso(c)}`;
}

/* ---------- Cronograma ---------- */

const REGRAS = [
  ["Matéria nova na ordem do edital, uma matéria por vez.", "Intercalar matérias ajuda a separar categorias parecidas, mas não mostrou ganho com texto.", "moderada", [["Brunmair & Richter, 2019", "https://doi.org/10.1037/bul0000209"]]],
  ["Revisão ativa, não releitura: escrever de memória e conferir.", "Testar-se rende mais retenção do que reler, mesmo parecendo mais difícil.", "forte", [["Roediger & Karpicke, 2006", "https://doi.org/10.1111/j.1467-9280.2006.01693.x"], ["Karpicke & Blunt, 2011", "https://doi.org/10.1126/science.1199327"], ["Yang et al., 2021", "https://doi.org/10.1037/bul0000309"]]],
  ["Cada assunto volta em 1, 7 e 21 dias; depois, a cada 10% do tempo até a prova, com uma revisão nas 3 últimas semanas.", "O intervalo ideal cresce com o prazo até a prova, e intervalos fixos funcionam tão bem quanto crescentes. Os números exatos são uma escolha minha a partir disso.", "forte para espaçar; os números são escolha", [["Cepeda et al., 2008", "https://doi.org/10.1111/j.1467-9280.2008.02209.x"], ["Cepeda et al., 2006", "https://doi.org/10.1037/0033-2909.132.3.354"], ["Latimier et al., 2021", "https://doi.org/10.1007/s10648-020-09572-8"]]],
  ["A revisão abre o dia e ocupa no máximo 30% dele enquanto houver matéria nova.", "Começar pela tarefa mais curta facilita começar; o teto é uma decisão de projeto.", "decisão de projeto", []],
  ["Provas anteriores viram simulados: o primeiro com 30% dos assuntos estudados, depois a cada 4 semanas, a cada 2 nas últimas 12 e toda semana nas últimas 4.", "Fazer prova é a maior das revisões ativas, e corrigir pelo gabarito aumenta o efeito. A frequência é convenção de cursinho.", "forte para testar-se; a frequência é convenção", [["Rowland, 2014", "https://doi.org/10.1037/a0037559"], ["Yang et al., 2021", "https://doi.org/10.1037/bul0000309"]]],
  ["Uma redação por semana, com correção; duas nas últimas 6 semanas.", "Correção com critérios melhora a escrita (estudado em alunos mais novos). A frequência é convenção.", "moderada", [["Graham, Hebert & Harris, 2015", "https://acuresearchbank.acu.edu.au/item/86vq0/formative-assessment-and-writing-a-meta-analysis"]]],
  ["Cada aula e leitura termina com perguntas sobre o próprio material, e cada matéria, com uma provinha de questões que já caíram.", "Responder logo depois de estudar fixa mais do que reler, e ver a resposta certa na hora aumenta o ganho. A quantidade (5 por item, 10 a 20 na provinha) é escolha nossa.", "forte para testar-se; a quantidade é escolha", [["Rowland, 2014", "https://doi.org/10.1037/a0037559"], ["Yang et al., 2021", "https://doi.org/10.1037/bul0000309"]]],
  ["Hora fixa para começar.", "Decidir antes o “quando” ajuda a cumprir uma meta.", "moderada", [["Gollwitzer & Sheeran, 2006", "https://doi.org/10.1016/S0065-2601(06)38002-1"]]],
];

function previsaoTexto(p) {
  if (p.concluido) return "A matéria nova está toda feita. Daqui para a frente é revisão e simulado.";
  if (!p.termino) return "No ritmo de agora, a matéria nova passa de um ano e meio.";
  const prova = p.prova ? (p.prova_confirmada ? `A prova é em ${dataCompleta(p.prova)}.` : `A prova deve ser em ${mesAno(p.prova)}, pelo histórico.`) : "Ainda sem data de prova.";
  let folga = "";
  if (p.a_tempo === true) {
    const s = semanasEntre(p.termino, p.prova);
    folga = s >= 1 ? ` Sobram ${s} semana${s > 1 ? "s" : ""} só para revisão e simulados.` : " Termina em cima da prova.";
  }
  return `A matéria nova termina em ${dataCompleta(p.termino)}. ${prova}${folga}`;
}

function contagemSemana(s) {
  const conta = { revisao: 0, prova: 0, redacao: 0, provinha: 0, nova: 0 };
  s.dias.forEach((d) => d.tarefas.forEach((t) => { if (t.estado !== "ficou") conta[t.tipo in conta ? t.tipo : "nova"] += 1; }));
  const partes = [];
  if (conta.nova) partes.push(`${conta.nova} de matéria nova`);
  if (conta.revisao) partes.push(`${conta.revisao} revis${conta.revisao > 1 ? "ões" : "ão"}`);
  if (conta.prova) partes.push(`${conta.prova} simulado${conta.prova > 1 ? "s" : ""}`);
  if (conta.redacao) partes.push(`${conta.redacao} redaç${conta.redacao > 1 ? "ões" : "ão"}`);
  if (conta.provinha) partes.push(`${conta.provinha} provinha${conta.provinha > 1 ? "s" : ""}`);
  return partes.join(" · ");
}

// O tempo de um dia anda de 15 em 15 min até 2 h, de 30 em 30 até 6 h, e de hora em hora até 8 h.
function passoDeTempo(m, dir) {
  const ref = dir > 0 ? m : m - 1;
  const passo = ref < 120 ? 15 : ref < 360 ? 30 : 60;
  return Math.min(480, Math.max(15, m + dir * passo));
}
const fimDe = (inicio, minutos) => { const m = (minutosDe(inicio) + minutos) % 1440; return `${Math.floor(m / 60)}:${dois(m % 60)}`; };

// Onde o estudo do dia cai na Rotina: o horário (sem hora marcada, vale o da Rotina) ou "não cabe".
const encaixeDe = (rot, i) => {
  if (!rot) return null;
  if (rot.avisos.some((a) => a.dia === i && a.tipo === "conflito")) return { fora: true };
  return rot.estudo.find((e) => e.dia === i) || null;
};
function fimDoDia(s, e) {
  if (e?.fora) return '<span class="meta dia-fim alerta">não cabe na Rotina</span>';
  if (s.inicio) return `<span class="meta dia-fim">até ${hora(fimDe(s.inicio, s.minutos))}</span>`;
  if (e) return `<span class="meta dia-fim">sem hora: segue a Rotina, ${daHora(e.inicio)} ${aHora(fimDe(e.inicio, s.minutos))}</span>`;
  return '<span class="meta dia-fim">sem hora marcada</span>';
}

// Uma coluna por dia da semana: o que ele marcou (começo e tempo) ou folga.
function editorDia(i, s, e) {
  const ligado = Boolean(s);
  return `<li class="dia-ajuste${ligado ? " ligado" : ""}" data-dia="${i}">
      <button type="button" class="dia-chip" aria-pressed="${ligado}" aria-label="Estudar na ${DIAS[i]}">${DIAS_CURTOS[i]}</button>
      ${ligado ? `<label class="campo-hora"><span class="so-leitor">Começa às, na ${DIAS[i]}</span><input type="time" value="${esc(s.inicio)}"></label>
      <span class="passo" role="group" aria-label="Tempo de estudo na ${DIAS[i]}">
        <button type="button" data-passo="-1" aria-label="Menos tempo na ${DIAS[i]}"${s.minutos <= 15 ? " disabled" : ""}>${ICONE.menos}</button>
        <output>${tempoCurto(s.minutos)}</output>
        <button type="button" data-passo="1" aria-label="Mais tempo na ${DIAS[i]}"${s.minutos >= 480 ? " disabled" : ""}>${ICONE.mais}</button>
      </span>
      ${fimDoDia(s, e)}`
      : '<span class="meta dia-folga">Folga</span>'}
    </li>`;
}

// O que do Cronograma não cabe (ou aperta) na Rotina: o aviso e as propostas. Cada proposta já é a semana nova do
// Cronograma; um clique aplica.
function avisosRotina(avisos) {
  return `<ul class="encaixe-lista">${avisos.map((a, i) => `
      <li class="encaixe-aviso">
        <p>${esc(a.texto)}</p>
        ${a.propostas.length ? `<div class="encaixe-propostas">${a.propostas.map((p, j) => `
          <button type="button" class="botao pequeno" data-proposta="${i}:${j}">${esc(p.rotulo)}</button>`).join("")}</div>` : ""}
      </li>`).join("")}</ul>`;
}
const propostaDe = (avisos, botao) => { const [i, j] = botao.dataset.proposta.split(":").map(Number); return avisos[i].propostas[j]; };

function encaixeCronograma(rot) {
  if (!rot) return "";
  if (!rot.avisos.length) return `<p class="meta encaixe-ok">${ICONE.marcado} Tudo cabe na sua <a href="#/rotina">Rotina</a>: ela se ajusta sozinha a cada mudança.</p>`;
  return `<section class="encaixe" aria-labelledby="t-encaixe">
      <h3 id="t-encaixe" class="ajuste-nome">Na sua <a href="#/rotina">Rotina</a></h3>
      ${avisosRotina(rot.avisos)}
    </section>`;
}

// A previsão numa linha do tempo: de hoje ao fim da matéria nova (laranja) e daí até a prova (revisão e simulados).
function previsaoBloco(previsao, hoje) {
  return previsao.map((p) => {
    const fim = p.prova && p.termino && p.termino > p.prova ? p.termino : p.prova || p.termino;
    let linhaPrazo = "";
    if (fim && p.termino && fim > hoje) {
      const total = dataDe(fim) - dataDe(hoje);
      const ate = Math.min(100, ((dataDe(p.termino) - dataDe(hoje)) / total) * 100);
      linhaPrazo = `<div class="prazo" aria-hidden="true">
          <span class="prazo-trilho"><span class="prazo-nova" style="width:${ate}%"></span></span>
          <span class="prazo-marca prazo-inicio" style="left:0">Hoje</span>
          <span class="prazo-marca prazo-meio" style="left:${ate}%">Matéria nova até ${dataCurta(p.termino)}</span>
          ${p.prova ? `<span class="prazo-marca prazo-fim" style="left:100%">${p.prova_confirmada ? `Prova ${dataCurta(p.prova)}` : `Prova ~${mesAno(p.prova).replace(" de ", "/")}`}</span>` : ""}
        </div>`;
    }
    return `<div class="previsao${p.a_tempo === false ? " atrasada" : ""}">
        <div class="previsao-texto"><h3>${esc(p.nome)} <span class="sigla">${esc(p.sigla)}</span></h3>
          <p>${esc(previsaoTexto(p))}</p>
          ${p.a_tempo === false ? '<p class="alerta">Termina depois da prova. Ponha mais tempo ou mais dias na sua semana.</p>' : ""}</div>
        ${linhaPrazo}
      </div>`;
  }).join("");
}

const certas = (a) => `${a.acertos}/${a.total} certas`;

// A semana aberta, em 7 colunas de segunda a domingo. Nos dias que já passaram fica o que ele fez: o que concluiu, o
// que estava no plano e ficou, e as questões que respondeu.
function gradeSemana(s, hoje) {
  const segunda = dataDe(s.inicio);
  const porData = new Map(s.dias.map((d) => [d.data, d]));
  const colunas = DIAS_CURTOS.map((nome, n) => {
    const data = new Date(segunda.getTime() + n * 864e5);
    const iso = `${data.getFullYear()}-${dois(data.getMonth() + 1)}-${dois(data.getDate())}`;
    const dia = porData.get(iso);
    const ehHoje = iso === hoje;
    const atividades = dia?.atividades || [];
    const vazio = iso < hoje && !(dia?.tarefas.length || atividades.length);
    const classe = `${ehHoje ? " hoje" : ""}${iso < hoje ? " passou" : ""}${vazio ? " vazio" : ""}${dia?.folga ? " folga" : ""}`;
    const corpo = vazio ? '<p class="coluna-vazia">Nada registrado</p>'
      : !dia ? '<p class="coluna-vazia">Nada marcado</p>'
        : dia.folga ? '<p class="coluna-vazia">Folga</p>'
          : dia.tarefas.length || atividades.length ? `${dia.tarefas.length ? `<ul class="coluna-tarefas">${dia.tarefas.map((t) => `
          <li class="bloco-tarefa ${t.estado} tipo-${t.tipo}"><a href="${esc(t.rota)}" title="${esc(suave(t.titulo))}">
            <span class="bloco-tarefa-tipo">${t.estado === "feito" ? ICONE.marcado : ICONE[t.tipo]}<span>${TIPO[t.tipo]} · ${t.estado === "ficou" ? "não feito" : tempoCurto(t.minutos)}${t.total ? ` · ${certas(t)}` : ""}</span></span>
            <span class="bloco-tarefa-titulo">${titulo(t.titulo)}${feitoLeitor(t)}</span></a></li>`).join("")}</ul>` : ""}
          ${atividades.length ? `<ul class="coluna-atividades">${atividades.map((a) => `
            <li>${a.rota ? `<a href="${esc(a.rota)}">${esc(suave(a.rotulo))}</a>` : esc(a.rotulo)} <span class="meta">${certas(a)}</span></li>`).join("")}</ul>` : ""}`
            : '<p class="coluna-vazia">Nada marcado</p>';
    return `<li class="coluna-dia${classe}"${ehHoje ? ' aria-current="date"' : ""}>
        <p class="coluna-cabeca"><span class="coluna-nome">${ehHoje ? "Hoje" : nome}</span><span class="meta">${dois(data.getDate())}/${dois(data.getMonth() + 1)}</span>
          ${dia && !dia.folga && dia.minutos ? `<span class="meta coluna-tempo">${tempoCurto(dia.minutos)}</span>` : ""}</p>
        ${corpo}
      </li>`;
  });
  return `<ol class="grade-semana">${colunas.join("")}</ol>`;
}

let semanaVista = 0; // a semana aberta na grade do Cronograma, contada desta (0); as que passaram são negativas

async function cronogramaTela() {
  let d = await api("/api/cronograma");
  const semana = new Map(d.ajustes.semana.map((s) => [s.dia, { inicio: s.inicio, minutos: s.minutos }]));
  const ligados = new Set(d.ajustes.concursos);
  const limitarSemana = (n) => Math.max(-d.atual, Math.min(d.semanas.length - 1 - d.atual, n));
  semanaVista = limitarSemana(semanaVista);
  document.title = "Cronograma · Escola";
  pagina.innerHTML = `
    ${aviso()}
    <header class="cabeca">
      <h1>Cronograma</h1>
      <p class="sub largo">Marque os concursos e o tempo que você tem em cada dia. Cada dia sai montado com matéria nova, revisão, simulado e redação, e tudo se refaz na hora.</p>
    </header>
    <section class="ajustes" aria-labelledby="t-ajustes">
      <h2 id="t-ajustes" class="so-leitor">Seus ajustes</h2>
      <fieldset class="ajuste-concursos">
        <legend class="ajuste-nome">Concursos</legend>
        <div class="concursos-opcoes">${d.opcoes.map((c) => `<button type="button" class="chip concurso-chip" data-concurso="${esc(c.id)}" aria-pressed="${ligados.has(c.id)}">${ICONE.marcado}<span data-nome>${esc(c.nome)}</span> <span class="sigla">${esc(c.sigla)}</span></button>`).join("")}</div>
      </fieldset>
      <fieldset class="ajuste-semana">
        <legend class="ajuste-nome">Sua semana <span class="meta" data-total></span></legend>
        <ol class="semana-editor">${DIAS_CURTOS.map((_, i) => editorDia(i, semana.get(i), encaixeDe(d.rotina, i))).join("")}</ol>
      </fieldset>
      <p class="meta ajustes-estado" data-estado role="status"></p>
      <div data-encaixe>${encaixeCronograma(d.rotina)}</div>
    </section>
    <section class="previsoes" aria-label="Previsão" data-previsao></section>
    <section class="semana-vista" aria-labelledby="t-semana" data-semana-vista></section>
    <details class="como">
      <summary><span class="titulo-bloco">Como o cronograma decide</span><span class="seta-abrir">${ICONE.abrir}</span></summary>
      <ol class="regras">${REGRAS.map(([regra, porque, forca, fontes]) => `
        <li><p class="regra">${esc(regra)}</p><p>${esc(porque)} <span class="forca">Evidência: ${esc(forca)}.</span></p>
        ${fontes.length ? `<p class="fontes">${fontes.map(([t, u]) => `<a class="fonte" href="${esc(u)}" target="_blank" rel="noopener">${esc(t)} ${ICONE.fora}</a>`).join("")}</p>` : ""}</li>`).join("")}</ol>
      <p class="meta largo">Ficam de fora reler, grifar e resumir olhando o texto, que rendem pouco, e “estilos de aprendizagem”, que não têm base. <a class="fonte" href="https://doi.org/10.1177/1529100612453266" target="_blank" rel="noopener">Dunlosky et al., 2013 ${ICONE.fora}</a> <a class="fonte" href="https://doi.org/10.1111/j.1539-6053.2009.01038.x" target="_blank" rel="noopener">Pashler et al., 2008 ${ICONE.fora}</a></p>
    </details>`;

  const estado = pagina.querySelector("[data-estado]");
  const total = pagina.querySelector("[data-total]");
  const somarSemana = () => {
    const m = [...semana.values()].reduce((s, x) => s + x.minutos, 0);
    total.textContent = `· ${tempo(m)} por semana em ${semana.size} dia${semana.size > 1 ? "s" : ""}`;
  };

  // A previsão e a grade se redesenham depois de guardar; o editor fica, para o foco não pular.
  const desenharPlano = () => {
    pagina.querySelector("[data-previsao]").innerHTML = previsaoBloco(d.previsao, d.hoje);
    const s = d.semanas[d.atual + semanaVista];
    const fim = new Date(dataDe(s.inicio).getTime() + 6 * 864e5);
    // as semanas que passaram só existem quando têm registro: o nome sai da distância, não da posição
    const distancia = Math.round((dataDe(s.inicio) - dataDe(d.semanas[d.atual].inicio)) / (7 * 864e5));
    const nome = { 0: "Esta semana", 1: "Semana que vem", "-1": "Semana passada" }[distancia] ?? `${dataCurta(s.inicio)} a ${dois(fim.getDate())}/${dois(fim.getMonth() + 1)}`;
    const resumo = semanaVista < 0 ? `${tempo(s.minutos)} concluídos` : tempo(s.minutos);
    pagina.querySelector("[data-semana-vista]").innerHTML = `
      <div class="semana-barra">
        <div class="semana-nav">
          <button type="button" class="icone-botao" data-ir-semana="-1" aria-label="Semana anterior"${semanaVista <= -d.atual ? " disabled" : ""}>${ICONE.anterior}</button>
          <button type="button" class="icone-botao" data-ir-semana="1" aria-label="Próxima semana"${semanaVista >= d.semanas.length - 1 - d.atual ? " disabled" : ""}>${ICONE.proxima}</button>
          <h2 id="t-semana" class="titulo-secao">${nome}</h2>
          ${semanaVista !== 0 ? '<button type="button" class="botao pequeno" data-ir-semana="0">Voltar a esta semana</button>' : ""}
        </div>
        <p class="meta">${dataCurta(s.inicio)} a ${dois(fim.getDate())}/${dois(fim.getMonth() + 1)} · ${resumo}${contagemSemana(s) ? ` · ${contagemSemana(s)}` : ""}${semanaVista >= 0 ? ` · semana ${semanaVista + 1} de ${d.semanas.length - d.atual}` : ""}</p>
      </div>
      ${gradeSemana(s, d.hoje)}`;
    const grade = pagina.querySelector(".grade-semana");
    // a fileira abre em hoje; se ontem tem registro, abre em ontem, para ele ver o que fez
    const hojeCol = grade.querySelector(".hoje");
    const abrirEm = hojeCol?.previousElementSibling?.matches(".passou:not(.vazio)") ? hojeCol.previousElementSibling : hojeCol;
    if (abrirEm && grade.scrollWidth > grade.clientWidth) grade.scrollLeft = abrirEm.offsetLeft - grade.offsetLeft;
    pagina.querySelectorAll("[data-ir-semana]").forEach((b) => b.addEventListener("click", () => {
      const ir = Number(b.dataset.irSemana);
      semanaVista = ir === 0 ? 0 : limitarSemana(semanaVista + ir);
      desenharPlano();
      pagina.querySelector(`[data-ir-semana="${ir === 0 ? 1 : ir}"]:not(:disabled)`)?.focus();
    }));
  };

  // Vai sempre a semana inteira e os concursos: um clique logo depois de outro não perde o primeiro.
  let espera = null;
  const guardar = (texto, depois = 0) => {
    clearTimeout(espera);
    estado.textContent = "Guardando…";
    espera = setTimeout(async () => {
      try {
        await enviar("/api/ajustes", "PUT", {
          semana: [...semana].sort(([a], [b]) => a - b).map(([dia, s]) => ({ dia, ...s })),
          concursos: [...ligados],
        });
        d = await api("/api/cronograma");
        desenharPlano();
        atualizarEncaixe();
        estado.textContent = texto;
        falar(texto);
      } catch {
        estado.textContent = "";
        erro("Não deu para guardar o ajuste. Confira se a Escola está ligada e tente de novo.");
      }
    }, depois);
  };
  const editor = pagina.querySelector(".semana-editor");
  const encaixe = pagina.querySelector("[data-encaixe]");
  // Depois de guardar, cada dia diz onde caiu na Rotina, e o que não coube vira aviso com propostas.
  const atualizarEncaixe = () => {
    editor.querySelectorAll(".dia-ajuste.ligado").forEach((li) => {
      const i = Number(li.dataset.dia);
      li.querySelector(".dia-fim").outerHTML = fimDoDia(semana.get(i), encaixeDe(d.rotina, i));
    });
    encaixe.innerHTML = encaixeCronograma(d.rotina);
  };
  encaixe.addEventListener("click", (e) => {
    const b = e.target.closest("[data-proposta]");
    if (!b) return;
    const p = propostaDe(d.rotina.avisos, b);
    semana.clear();
    p.semana.forEach((x) => semana.set(x.dia, { inicio: x.inicio, minutos: x.minutos }));
    editor.innerHTML = DIAS_CURTOS.map((_, i) => editorDia(i, semana.get(i), encaixeDe(d.rotina, i))).join("");
    somarSemana();
    guardar(`Pronto: ${p.rotulo.charAt(0).toLowerCase()}${p.rotulo.slice(1)}.`);
  });
  const redesenharDia = (i) => {
    const velho = editor.querySelector(`[data-dia="${i}"]`);
    const ativo = document.activeElement;
    const qual = ativo && velho.contains(ativo) ? (ativo.dataset.passo ? `[data-passo="${ativo.dataset.passo}"]` : ativo.matches("input") ? "input" : ".dia-chip") : null;
    velho.outerHTML = editorDia(i, semana.get(i), encaixeDe(d.rotina, i));
    const novo = editor.querySelector(`[data-dia="${i}"]`);
    if (qual) (novo.querySelector(`${qual}:not(:disabled)`) || novo.querySelector(".dia-chip")).focus();
    somarSemana();
  };
  editor.addEventListener("click", (e) => {
    const li = e.target.closest("[data-dia]");
    if (!li) return;
    const i = Number(li.dataset.dia);
    if (e.target.closest(".dia-chip")) {
      if (semana.has(i)) {
        if (semana.size === 1) { erro("Deixe pelo menos um dia de estudo."); return; }
        semana.delete(i);
      } else { // o dia novo começa igual ao dia de estudo mais próximo antes dele
        const antes = [...semana.keys()].filter((k) => k < i).pop() ?? [...semana.keys()][0];
        semana.set(i, antes == null ? { inicio: "", minutos: 60 } : { ...semana.get(antes) });
      }
      redesenharDia(i);
      guardar(`Cronograma refeito: ${semana.has(i) ? `${DIAS[i]} entrou` : `${DIAS[i]} virou folga`}.`);
      return;
    }
    const b = e.target.closest("[data-passo]");
    if (b && semana.has(i)) {
      const s = semana.get(i);
      s.minutos = passoDeTempo(s.minutos, Number(b.dataset.passo));
      redesenharDia(i);
      guardar(`Cronograma refeito: ${tempo(s.minutos)} na ${DIAS[i]}.`, 700);
    }
  });
  editor.addEventListener("change", (e) => {
    const li = e.target.closest("[data-dia]");
    if (!li || !e.target.matches("input[type=time]")) return;
    const i = Number(li.dataset.dia);
    semana.get(i).inicio = e.target.value;
    redesenharDia(i);
    guardar(e.target.value ? `Na ${DIAS[i]}, começa às ${hora(e.target.value)}.` : `Na ${DIAS[i]}, sem hora marcada.`);
  });
  // Tirar um concurso refaz o plano de hoje sem ele: pede um segundo toque, para um toque sem querer (rolando a tela no
  // celular) não trocar o dia. Em 28/10, um toque assim tirou o SMV e o plano virou só CP-T.
  let tirar = null, prazoTirar = null;
  const desarmar = () => {
    clearTimeout(prazoTirar);
    if (!tirar) return;
    tirar.classList.remove("confirmar");
    tirar.querySelector("[data-nome]").textContent = d.opcoes.find((c) => c.id === tirar.dataset.concurso).nome;
    tirar = null;
  };
  pagina.querySelectorAll("[data-concurso]").forEach((b) => b.addEventListener("click", () => {
    const vai = b.getAttribute("aria-pressed") !== "true";
    if (!vai && ligados.size === 1) { erro("Deixe pelo menos um concurso."); return; }
    if (!vai && tirar !== b) {
      desarmar();
      const sigla = d.opcoes.find((c) => c.id === b.dataset.concurso).sigla;
      tirar = b;
      b.classList.add("confirmar");
      b.querySelector("[data-nome]").textContent = "Toque de novo para tirar";
      estado.textContent = `Tirar o ${sigla} refaz o plano de hoje sem ele.`;
      falar(`Toque de novo para tirar o ${sigla} do Cronograma.`);
      prazoTirar = setTimeout(() => { desarmar(); estado.textContent = ""; }, 5000);
      return;
    }
    desarmar();
    if (vai) ligados.add(b.dataset.concurso); else ligados.delete(b.dataset.concurso);
    b.setAttribute("aria-pressed", String(vai));
    const nomes = d.opcoes.filter((c) => ligados.has(c.id)).map((c) => `${c.nome} ${c.sigla}`);
    guardar(`Cronograma refeito com ${new Intl.ListFormat("pt-BR", { type: "conjunction" }).format(nomes)}.`);
  }));
  somarSemana();
  desenharPlano();
}

/* ---------- Situação dos concursos ---------- */

async function situacaoTela() {
  const d = await api("/api/situacao");
  const quando = d.verificado_em
    ? `Verificado em ${dataCompleta(d.verificado_em)} às ${d.verificado_em.slice(11, 16)}. A próxima busca é a partir de ${dataCompleta(d.proxima_busca)}.`
    : "A primeira busca ainda não rodou: ela roda sozinha às 10h, ou quando o PC ligar.";
  // O que pede ação (inscrição aberta) vem primeiro; o que só espera edital, por último.
  const ordem = { inscricoes: 0, andamento: 1, previsto: 2 };
  const concursos = [...d.concursos].sort((a, b) => (ordem[a.situacao?.estado] ?? 3) - (ordem[b.situacao?.estado] ?? 3));
  document.title = "Situação dos concursos · Escola";
  pagina.innerHTML = `
    <header class="cabeca">
      <h1>Situação dos concursos</h1>
      <p class="sub largo">Toda semana eu procuro edital, inscrição e datas. Novidade aparece aqui e no Início${perfilAtual?.dono ? `, e na <a href="${CENTRAL}">central da Thalia</a>` : ""}.</p>
      <p class="meta">${quando}</p>
      ${d.erro ? `<p class="erro" role="alert">A última busca não deu certo (${esc(d.erro)}). Ela tenta de novo amanhã às 10h.</p>` : ""}
    </header>
    <div class="situacao-grade">
      <ul class="situacoes" aria-label="Concursos">${concursos.map((c) => `
        <li class="situacao estado-${esc(c.situacao?.estado || "nenhum")}">
          <div class="situacao-cabeca">
            <a class="situacao-foto" href="#/concurso/${c.id}/sobre" tabindex="-1" aria-hidden="true">${c.foto ? `<img src="${esc(c.foto)}" alt="" loading="lazy">` : ""}</a>
            <div class="situacao-titulos">
              <h2 class="situacao-nome"><a href="#/concurso/${c.id}/sobre">${esc(c.nome)}</a> <span class="sigla">${esc(c.sigla)}</span></h2>
              ${c.situacao ? `<p class="situacao-selo">${selo(c.situacao)} <span class="meta">desde ${dataCurta(c.situacao.desde)}</span></p>` : ""}
            </div>
          </div>
          ${situacaoBloco(c.situacao, null, c.pagina_oficial, { cabeca: false })}
          ${c.pagina_oficial ? `<a class="link-fora" href="${esc(c.pagina_oficial)}" target="_blank" rel="noopener">Página oficial ${ICONE.fora}</a>` : ""}
        </li>`).join("")}</ul>
      <aside class="mudancas" aria-labelledby="t-historico">
        <h2 id="t-historico" class="titulo-secao">O que mudou</h2>
        ${d.historico.length ? `<ol class="historico">${[...d.historico].reverse().map((h) => `<li><span class="data">${dataCompleta(h.em)}</span><p><strong>${esc(h.nome)}</strong> ${esc(h.texto.replace(/^Começou o acompanhamento\.\s*/, ""))}</p>${h.texto.startsWith("Começou o acompanhamento") ? '<span class="meta">Início do acompanhamento</span>' : ""}</li>`).join("")}</ol>`
          : '<p class="sub">Nada ainda. A primeira busca registra o ponto de partida de cada concurso.</p>'}
      </aside>
    </div>`;
}

/* ---------- Aquecimento do dia ---------- */

// "Resumo e 5 cartões do que estudou por último, e 10 perguntas", para o cartão do início.
function conteudoAquecimento(aq) {
  const perguntas = `${aq.perguntas} pergunta${aq.perguntas === 1 ? "" : "s"}`;
  if (!aq.leitura) return `${perguntas} do que você já estudou`;
  const leitura = `Resumo e ${aq.cartoes} cartões do que estudou por último`;
  return aq.perguntas ? `${leitura}, e ${perguntas}` : leitura;
}

function resumoDoDia(l) {
  return `<section class="aq-parte" aria-labelledby="t-resumo">
    <div class="fixacao-cabeca">
      <h2 id="t-resumo" class="titulo-bloco">Resumo da última ${l.item.tipo === "leitura" ? "leitura" : "aula"}</h2>
      <span class="meta">De <a href="${esc(l.item.rota)}">${titulo(l.item.titulo)}</a></span>
    </div>
    <p class="aq-resumo">${rico(l.resumo)}</p>
  </section>`;
}

// Cada cartão é uma carta: a frente tem a pergunta e um toque vira a carta para o verso. As duas faces ocupam o mesmo
// lugar, e a face escondida fica fora do leitor de tela.
function cartoesDoDia(l) {
  const onde = (c) => (c.onde == null ? "" : `<span class="meta">${l.item.video ? `No vídeo, aos ${minSeg(c.onde)}` : `Na página ${c.onde}`}</span>`);
  return `<section class="aq-parte" aria-labelledby="t-cartoes">
    <div class="fixacao-cabeca">
      <h2 id="t-cartoes" class="titulo-bloco">Cartões</h2>
      <span class="meta">Responda de cabeça e só depois vire</span>
    </div>
    <ol class="cartas">${l.cartoes.map((c, n) => `
      <li style="--i: ${n}"><button type="button" class="carta" aria-pressed="false"><span class="carta-miolo">
        <span class="carta-face carta-frente"><span class="numero">${n + 1}</span><span class="carta-texto">${rico(c.frente)}</span><span class="carta-dica">Virar</span></span>
        <span class="carta-face carta-verso" aria-hidden="true"><span class="carta-rotulo">Resposta</span><span class="carta-texto">${rico(c.verso)}</span>${onde(c)}<span class="carta-dica">Voltar</span></span>
      </span></button></li>`).join("")}</ol>
  </section>`;
}

function ligarCartas() {
  pagina.querySelectorAll(".carta").forEach((b) => b.addEventListener("click", () => {
    const virada = b.getAttribute("aria-pressed") !== "true";
    b.setAttribute("aria-pressed", String(virada));
    b.querySelector(".carta-frente").setAttribute("aria-hidden", String(virada));
    b.querySelector(".carta-verso").setAttribute("aria-hidden", String(!virada));
    if (virada) falar(b.querySelector(".carta-verso .carta-texto").textContent);
  }));
}

async function aquecimentoTela() {
  const a = await api("/api/aquecimento");
  const f = a.perguntas;
  const l = a.leitura;
  const partes = l && f ? "O resumo e os cartões do que você estudou por último, e perguntas de tudo o que já estudou."
    : l ? "O resumo e os cartões do que você estudou por último."
      : "Perguntas de tudo o que você já estudou: primeiro as que errou, depois as que ainda não viu.";
  document.title = "Aquecimento do dia · Escola";
  pagina.innerHTML = `
    ${aviso()}
    <div class="trilha-topo">${voltar("#/")}</div>
    <header class="cabeca">
      <h1>Aquecimento do dia</h1>
      <p class="rotulo">Sugestão do dia${a.resumo ? ` · uns ${tempo(a.resumo.minutos)}` : ""}</p>
      <p class="sub largo">${l || f ? `${partes} Tente lembrar antes de ${l ? "virar ou marcar" : "marcar"}.`
        : `Ainda não há o que aquecer: o aquecimento sai das aulas e leituras que você concluiu. Termine uma pelo <a href="#/">Continuar</a> e ele aparece aqui.`}</p>
    </header>
    ${l ? resumoDoDia(l) + cartoesDoDia(l) : ""}
    ${f ? blocoPerguntas(f, { titulo: "Perguntas", sub: "De tudo o que você já estudou · a correção diz de onde veio cada uma", umaPorVez: true }) : ""}`;
  if (l) ligarCartas();
  if (f) ligarPerguntas(f, { umaPorVez: true });
}

/* ---------- Caderno de erros ---------- */

// Toda questão errada, de qualquer lugar da Escola, vem para cá e só sai quando ele acerta em dois dias diferentes
// depois do erro. A rodada de hoje é o centro da tela; ao lado, o placar por matéria e o que está no caderno. A lista
// não mostra a letra certa: na rodada, ele lembraria a letra, não o conteúdo.
function placarMaterias(materias) {
  if (!materias.length) return "";
  return `<section class="caixa" aria-labelledby="t-placar">
    <h2 id="t-placar" class="titulo-bloco">Por matéria</h2>
    <table class="placar-materias">
      <thead><tr><th scope="col">Matéria</th><th scope="col">Respondidas</th><th scope="col">Certas de primeira</th><th scope="col">No caderno</th></tr></thead>
      <tbody>${materias.map((m) => `<tr><th scope="row">${esc(m.materia)}</th><td>${m.respondidas}</td>
        <td>${m.de_primeira} <span class="meta">(${pct(m.de_primeira, m.respondidas)}%)</span></td><td>${m.no_caderno}</td></tr>`).join("")}</tbody>
    </table>
    <p class="meta">"De primeira" é o que você acertou na primeira vez que viu a questão: é o que mais se parece com a prova.</p>
  </section>`;
}

function listaCaderno(d) {
  if (!d.questoes.length) return "";
  return `<section class="caixa" aria-labelledby="t-no-caderno">
    <h2 id="t-no-caderno" class="titulo-bloco">No caderno · ${d.questoes.length}</h2>
    <ol class="erros-lista">${d.questoes.map((x) => `
      <li class="erro-item">
        <span class="erro-texto">
          <span class="erro-enunciado">${x.prova ? `<span class="prova">${esc(x.prova)}</span> ` : ""}${esc(x.enunciado)}</span>
          <span class="meta">${esc(x.materia)} · errou em ${dataCurta(x.errou_em)}${x.para_hoje ? "" : " · já visto hoje"} · <a href="${esc(x.origem.rota)}">${titulo(x.origem.titulo)}</a></span>
        </span>
        <span class="firmar" role="img" aria-label="Acertou em ${x.acertos} de ${d.firmar} dias">${Array.from({ length: d.firmar }, (_, k) => `<span class="${k < x.acertos ? "sim" : ""}"></span>`).join("")}</span>
      </li>`).join("")}</ol>
  </section>`;
}

function rodadaDeHoje(d) {
  const r = d.rodada;
  const aberta = r && !r.tentativas.length;
  const proxima = Math.min(d.para_hoje, d.por_rodada);
  const comecar = d.para_hoje
    ? `<button class="botao primario" type="button" data-rodada>${r ? "Outra rodada" : "Começar a rodada"} · ${proxima} ${proxima === 1 ? "questão" : "questões"} ${ICONE.seta}</button>`
    : "";
  if (aberta) return blocoPerguntas(r, { titulo: "Rodada de hoje", sub: "Sem consultar nada. Errou de novo? Ela fica e volta outro dia.", refazer: false, umaPorVez: true });
  if (r) return `${blocoPerguntas(r, { titulo: "Rodada de hoje", sub: "As que você acertou hoje voltam em outro dia para firmar.", refazer: false, umaPorVez: true })}${comecar ? `<div class="rodada-mais">${comecar}<span class="meta">${d.para_hoje} ainda para hoje</span></div>` : ""}`;
  if (d.para_hoje) {
    return `<section class="rodada-convite" aria-labelledby="t-rodada">
      <h2 id="t-rodada" class="titulo-bloco">${d.para_hoje} ${d.para_hoje === 1 ? "questão" : "questões"} para rever hoje</h2>
      <p class="meta">Uma rodada tem até ${d.por_rodada}, misturando as matérias, das erradas há mais tempo para as mais novas.</p>
      ${comecar}
    </section>`;
  }
  return `<section class="rodada-convite" aria-labelledby="t-rodada">
    <h2 id="t-rodada" class="titulo-bloco">${d.questoes.length ? "Nada para rever hoje" : "Nenhuma questão errada ainda"}</h2>
    <p class="meta">${d.questoes.length ? "O que você errou hoje volta amanhã: rever no dia seguinte fixa mais do que rever na hora." : "Quando errar uma questão, em qualquer lugar da Escola, ela aparece aqui."}</p>
  </section>`;
}

async function cadernoTela() {
  const d = await api("/api/erros");
  document.title = "Caderno de erros · Escola";
  pagina.innerHTML = `
    ${aviso()}
    <div class="trilha-topo">${voltar("#/")}</div>
    <header class="cabeca">
      <h1>Caderno de erros</h1>
      <p class="sub largo">Toda questão que você erra, na aula, na provinha ou no aquecimento, vem para cá. Ela sai quando você acerta em ${d.firmar} dias diferentes depois do erro${d.firmadas ? `: ${d.firmadas} já ${d.firmadas === 1 ? "saiu" : "saíram"}` : ""}.</p>
    </header>
    <div class="caderno-grade">
      <div class="caderno-principal">${rodadaDeHoje(d)}</div>
      <aside class="caderno-lado">${placarMaterias(d.materias)}${listaCaderno(d)}</aside>
    </div>`;
  if (d.rodada) {
    ligarPerguntas(d.rodada, { refazer: false, umaPorVez: true, depois: async () => {
      await cadernoTela();
      pagina.querySelector(".fixacao")?.scrollIntoView({ block: "start" });
    } });
  }
  pagina.querySelector("[data-rodada]")?.addEventListener("click", async (e) => {
    const b = e.currentTarget;
    b.disabled = true;
    try {
      await enviar("/api/erros/rodada", "POST", {});
      await cadernoTela();
      pagina.querySelector(".fixacao")?.scrollIntoView({ block: "start" });
    } catch {
      b.disabled = false;
      erro("Não deu para montar a rodada. Confira se a Escola está ligada e tente de novo.");
    }
  });
}

/* ---------- Rotina ---------- */

const minutosDe = (h) => { const [a, b] = h.split(":").map(Number); return a * 60 + b; };
const hora = (h) => { const [a, b] = h.split(":"); return b === "00" ? (Number(a) ? `${Number(a)}h` : "meia-noite") : `${Number(a)}h${b}`; };
// "das 21h", "da 1h", "da meia-noite"; "às 23h30", "à 1h", "à meia-noite"
const daHora = (h) => (minutosDe(h) < 120 ? "da " : "das ") + hora(h);
const aHora = (h) => (minutosDe(h) < 120 ? "à " : "às ") + hora(h);
// Na legenda, os grupos do método do Augusto, com os mesmos nomes e cores dos Quadradinhos.
const TIPO_ROTINA = { trabalho: "Compromissos", fora: "Compromissos", casa: "Pilares", acordar: "Pilares",
  estudo: "Estudo", aquecimento: "Estudo", coringa: "Coringa", livre: "Livre", sono: "Sono" };
const gradeDe = (r, dia) => r.grades.find((g) => g.dias.includes(dia));

// O dia da rotina vai do acordar ao acordar do dia seguinte: às 3h de terça, ainda vale a noite de segunda.
function blocoDeAgora(r, agora = new Date()) {
  let dia = diaSemana(agora);
  let m = agora.getHours() * 60 + agora.getMinutes();
  let g = gradeDe(r, dia);
  if (g && m < minutosDe(g.blocos[0].inicio)) { dia = (dia + 6) % 7; m += 1440; g = gradeDe(r, dia); }
  if (!g) return {};
  const abre = minutosDe(g.blocos[0].inicio);
  const ini = (h) => minutosDe(h) + (minutosDe(h) < abre ? 1440 : 0);
  const fim = (h) => minutosDe(h) + (minutosDe(h) <= abre ? 1440 : 0);
  return { grade: g, bloco: g.blocos.find((b) => ini(b.inicio) <= m && m < fim(b.fim)) };
}

function cartaoAgora(b) {
  if (!b) return "";
  return `<section class="agora-rotina" aria-label="Agora">
      <span class="agora-texto">
        <span class="rotulo">Agora · até ${hora(b.fim)}</span>
        <span class="agora-titulo">${esc(b.titulo)}</span>
        ${b.nota ? `<span class="meta">${esc(b.nota)}</span>` : ""}
      </span>
      ${b.rota ? `<a class="botao primario" href="${esc(b.rota)}">${esc(b.acao)} ${ICONE.seta}</a>` : ""}
    </section>`;
}

// O dia inteiro numa faixa, do acordar ao acordar seguinte: cada bloco ocupa o tempo que dura. O estudo é o único em
// laranja; o resto vai em tons neutros, do sono (o mais escuro) ao tempo livre (o mais claro).
function faixaDoDia(g, agora) {
  const abre = minutosDe(g.blocos[0].inicio);
  const desde = (m) => (m - abre + 1440) % 1440;
  const dur = (b) => (minutosDe(b.fim) - minutosDe(b.inicio) + 1440) % 1440 || 1440;
  const marcas = [];
  for (let h = Math.ceil(abre / 180) * 180; marcas.length < 8; h += 180) marcas.push(h % 1440);
  const m = agora && new Date().getHours() * 60 + new Date().getMinutes();
  return `<div class="faixa-dia">
      <div class="faixa" role="img" aria-label="O dia, de ${hora(g.blocos[0].inicio)} a ${hora(g.blocos[0].inicio)} do dia seguinte">
        ${g.blocos.map((b) => {
          const largura = (dur(b) / 1440) * 100;
          return `<span class="faixa-bloco tipo-${esc(b.tipo)}${agora?.bloco === b ? " agora" : ""}" style="left:${(desde(minutosDe(b.inicio)) / 1440) * 100}%;width:${largura}%" title="${hora(b.inicio)} – ${hora(b.fim)} · ${esc(b.titulo)}">${largura >= 4 ? `<span>${esc(b.titulo)}</span>` : ""}</span>`;
        }).join("")}
        ${agora ? `<span class="faixa-agora" style="left:${(desde(m) / 1440) * 100}%"></span>` : ""}
      </div>
      <div class="faixa-horas" aria-hidden="true">${marcas.map((h) => `<span style="left:${(desde(h) / 1440) * 100}%">${Math.floor(h / 60)}h</span>`).join("")}</div>
      <ul class="faixa-legenda" aria-hidden="true">${[...new Set(g.blocos.map((b) => TIPO_ROTINA[b.tipo] || b.tipo))].map((t) => {
        const tipo = Object.keys(TIPO_ROTINA).find((k) => TIPO_ROTINA[k] === t) || t;
        return `<li><span class="amostra tipo-${esc(tipo)}"></span>${esc(t)}</li>`;
      }).join("")}</ul>
    </div>`;
}

function gradeRotina(g, agora) {
  return `<ol class="rotina-blocos">${g.blocos.map((b) => `
      <li class="bloco tipo-${esc(b.tipo)}${b === agora.bloco ? " agora" : ""}"${b === agora.bloco ? ' aria-current="time"' : ""}>
        <span class="bloco-hora"><span class="amostra tipo-${esc(b.tipo)}"></span>${hora(b.inicio)} – ${hora(b.fim)}</span>
        <span class="bloco-texto"><span class="bloco-titulo">${esc(b.titulo)}${b === agora.bloco ? ' <span class="foco">agora</span>' : ""}</span>${b.nota ? `<span class="meta">${esc(b.nota)}</span>` : ""}</span>
        ${b.rota ? `<a class="botao pequeno" href="${esc(b.rota)}">${esc(b.acao)}</a>` : ""}
      </li>`).join("")}</ol>`;
}

let gradeVista = null; // a grade aberta na Rotina (o nome); null é a de hoje

// A Rotina em cima, e os Quadradinhos recolhidos embaixo (pedido dele: "tem mais a ver com rotina", num sobe-desce).
// O "agora" redesenha só a parte de cima a cada minuto, para não apagar o que ele está pintando.
async function rotinaTela({ quadros: abrirQuadros = false } = {}) {
  let r = await api("/api/rotina");
  let estadoTexto = "";
  pagina.innerHTML = `
    <div class="rotina-viva"></div>
    <details class="como quadros-caixa" id="quadradinhos"${abrirQuadros ? " open" : ""}>
      <summary><span class="quadros-titulo"><span class="titulo-bloco">Quadradinhos</span><span class="meta">A semana inteira em meias horas, para pintar e testar outra rotina</span></span><span class="seta-abrir">${ICONE.abrir}</span></summary>
      <div class="quadros-corpo"></div>
    </details>`;
  const viva = pagina.querySelector(".rotina-viva");
  const caixa = pagina.querySelector(".quadros-caixa");
  let montado = false;
  const montar = async () => {
    if (montado) return;
    montado = true;
    try {
      await quadros(caixa.querySelector(".quadros-corpo"), r);
    } catch {
      montado = false;
      erro("Não deu para abrir os Quadradinhos. Confira se a Escola está ligada e abra de novo.");
    }
  };
  caixa.addEventListener("toggle", () => { if (caixa.open) montar(); });
  if (abrirQuadros) await montar();
  const desenhar = () => {
    const agora = blocoDeAgora(r);
    const deHoje = agora.grade || gradeDe(r, diaSemana(new Date()));
    const vista = r.grades.find((g) => g.nome === gradeVista) || deHoje || r.grades[0];
    viva.innerHTML = `
      ${aviso()}
      <header class="cabeca">
        <h1>Rotina</h1>
        <p class="sub largo">${esc(r.resumo)}</p>
        <p class="meta">O estudo de cada dia vem do <a href="#/cronograma">Cronograma</a>: mude lá a hora ou o tempo, e a Rotina se ajusta. A semana inteira está nos <a href="#/rotina/quadros">Quadradinhos</a>, no pé da página. Desde ${dataCurta(r.desde)} · próxima revisão no ${dataLonga(r.revisao)}</p>
        <p class="meta" role="status" data-estado-rotina>${esc(estadoTexto)}</p>
      </header>
      <div class="rotina-grade">
        ${cartaoAgora(agora.bloco)}
        <section class="rotina-principal" aria-labelledby="t-dia">
          ${r.avisos.length ? `<section class="encaixe" aria-labelledby="t-encaixe">
            <h2 id="t-encaixe" class="titulo-bloco">Para ajustar</h2>
            ${avisosRotina(r.avisos)}
          </section>` : ""}
          <h2 id="t-dia" class="so-leitor">${esc(vista.nome)}</h2>
          <div class="segmentos" role="group" aria-label="Qual dia ver">${r.grades.map((g) => `
            <button type="button" class="segmento" data-grade="${esc(g.nome)}" aria-pressed="${g === vista}">${esc(g.nome)}${g === deHoje ? ' <span class="segmento-hoje">hoje</span>' : ""}</button>`).join("")}</div>
          ${faixaDoDia(vista, vista === agora.grade ? agora : null)}
          ${gradeRotina(vista, vista === agora.grade ? agora : {})}
        </section>
        <aside class="rotina-lado">
          <section class="caixa" aria-labelledby="t-regras">
            <h2 id="t-regras" class="titulo-bloco">As 3 regras</h2>
            <ol class="regras-lista">${r.regras.map((x) => `<li><p class="regra">${esc(x.titulo)}</p><p>${esc(x.texto)}</p></li>`).join("")}</ol>
          </section>
          <section class="caixa" aria-labelledby="t-ajustar">
            <h2 id="t-ajustar" class="titulo-bloco">Como ajustar</h2>
            <dl class="ajustar">
              <div><dt>Para dormir mais cedo</dt><dd>${esc(r.mais_cedo)}</dd></div>
              <div><dt>Toda semana</dt><dd>${esc(r.acompanhar)}</dd></div>
            </dl>
          </section>
          <details class="como">
            <summary><span class="titulo-bloco">Por que essa rotina</span><span class="seta-abrir">${ICONE.abrir}</span></summary>
            <ol class="regras">${r.porques.map((x) => `<li><p class="regra">${esc(x.titulo)}</p><p>${esc(x.texto)}</p>
              <p class="fontes">${x.fontes.map(([t, u]) => `<a class="fonte" href="${esc(u)}" target="_blank" rel="noopener">${esc(t)} ${ICONE.fora}</a>`).join("")}</p></li>`).join("")}</ol>
          </details>
        </aside>
      </div>`;
    viva.querySelectorAll("[data-proposta]").forEach((b) => b.addEventListener("click", async () => {
      const p = propostaDe(r.avisos, b);
      b.disabled = true;
      try {
        await enviar("/api/ajustes", "PUT", { semana: p.semana });
        r = await api("/api/rotina");
        estadoTexto = `Pronto: ${p.rotulo.charAt(0).toLowerCase()}${p.rotulo.slice(1)}. O Cronograma já mudou.`;
        desenhar();
        falar(estadoTexto);
      } catch {
        b.disabled = false;
        erro("Não deu para mudar o Cronograma. Confira se a Escola está ligada e tente de novo.");
      }
    }));
    viva.querySelectorAll("[data-grade]").forEach((b) => b.addEventListener("click", () => {
      gradeVista = b.dataset.grade;
      const aberto = viva.querySelector(".rotina-lado .como")?.open;
      desenhar();
      if (aberto) viva.querySelector(".rotina-lado .como").open = true;
      viva.querySelector(`[data-grade="${CSS.escape(gradeVista)}"]`)?.focus();
    }));
  };
  document.title = "Rotina · Escola";
  gradeVista = null;
  desenhar();
  relogio = setInterval(() => { // o "agora" anda sozinho
    const y = scrollY;
    const aberto = viva.querySelector(".rotina-lado .como")?.open;
    desenhar();
    if (aberto) viva.querySelector(".rotina-lado .como").open = true;
    scrollTo(0, y);
  }, 60000);
}

/* ---------- Quadradinhos ---------- */

// A semana em quadradinhos de meia hora, como no método do Augusto, no pé da Rotina: cada linha é um dia, do acordar
// ao acordar seguinte. Começa pintada com a Rotina; ele pinta por cima, e o rascunho fica guardado na Escola. A Rotina só muda
// quando ele pede ao Claude para passar o rascunho para ela.
const QUADROS = 48;
const CATEGORIAS = [ // na ordem do método: compromissos, pilares, a prioridade, o coringa, o livre; o sono à parte
  { id: "compromisso", nome: "Compromissos", de: "de compromissos" },
  { id: "pilar", nome: "Pilares", de: "de pilares" },
  { id: "estudo", nome: "Estudo", de: "de estudo" },
  { id: "coringa", nome: "Coringa", de: "de coringa" },
  { id: "livre", nome: "Livre", de: "livres" },
  { id: "sono", nome: "Sono", de: "de sono" },
  { id: "", nome: "Apagar", de: "sem plano" },
];
const NOME_CATEGORIA = Object.fromEntries(CATEGORIAS.map((c) => [c.id, c.id ? c.nome : "Sem plano"]));
const CATEGORIA_DO_TIPO = { trabalho: "compromisso", fora: "compromisso", casa: "pilar", acordar: "pilar",
  estudo: "estudo", aquecimento: "estudo", coringa: "coringa", livre: "livre", sono: "sono" };
const horas = (m) => `${Math.floor(m / 60)}h${m % 60 ? dois(m % 60) : ""}`;
const hhmm = (m) => `${dois(Math.floor(m / 60) % 24)}:${dois(m % 60)}`;
const dentro = (m, a, b) => (a <= b ? a <= m && m < b : m >= a || m < b); // o trecho pode virar a meia-noite
let pincel = "estudo";

// O meio do quadradinho decide a cor: um bloco de 20 min conta como meia hora inteira.
function quadrosDaRotina(r, inicio) {
  return DIAS.map((_, d) => {
    const g = gradeDe(r, d);
    return Array.from({ length: QUADROS }, (_, s) => {
      const m = (inicio + s * 30 + 15) % 1440;
      const b = g?.blocos.find((x) => dentro(m, minutosDe(x.inicio), minutosDe(x.fim)));
      return CATEGORIA_DO_TIPO[b?.tipo] ?? "";
    });
  });
}

const contaDe = (q) => {
  const c = Object.fromEntries(CATEGORIAS.map((x) => [x.id, 0]));
  q.flat().forEach((x) => { c[x] += 30; });
  return c;
};

async function quadros(caixa, r) {
  const { rascunho } = await api("/api/quadros");
  const inicio = rascunho ? minutosDe(rascunho.inicio)
    : Math.floor(Math.min(...r.grades.map((g) => minutosDe(g.blocos[0].inicio))) / 30) * 30;
  const daRotina = quadrosDaRotina(r, inicio);
  let q = (rascunho?.dias || daRotina).map((d) => [...d]);
  const passos = []; // para o Desfazer
  const relogioDe = (s) => (inicio + s * 30) % 1440;
  const agora = new Date();
  const mAgora = agora.getHours() * 60 + agora.getMinutes();
  const diaAgora = mAgora < inicio ? (diaSemana(agora) + 6) % 7 : diaSemana(agora); // de madrugada, ainda é a linha do dia anterior
  const sAgora = Math.floor(((mAgora - inicio + 1440) % 1440) / 30);
  const rotuloDe = (d, s) => `${DIAS[d].charAt(0).toUpperCase()}${DIAS[d].slice(1)}, ${daHora(hhmm(relogioDe(s)))} ${aHora(hhmm(relogioDe(s + 1)))}`;
  const classeDe = (d, s) => `q q-${q[d][s] || "vazio"}${q[d][s] !== daRotina[d][s] ? " mudou" : ""}${d === diaAgora && s === sAgora ? " agora" : ""}`;

  const quadradinhos = DIAS.map((_, d) => q[d].map((_, s) => `<button type="button" class="${classeDe(d, s)}" data-d="${d}" data-s="${s}" style="--l:${d + 2};--c:${s + 2}" tabindex="${d === 0 && s === 0 ? 0 : -1}" aria-label="${esc(rotuloDe(d, s))}: ${esc(NOME_CATEGORIA[q[d][s]])}"></button>`).join("")).join("");
  const rotulosHora = Array.from({ length: QUADROS }, (_, s) => s).filter((s) => relogioDe(s) % 60 === 0)
    .map((s) => `<span class="q-hora" style="--c:${s + 2}">${Math.floor(relogioDe(s) / 60)}h</span>`).join("");
  const rotulosDia = DIAS_CURTOS.map((n, d) => `<span class="q-dia${d === diaAgora ? " hoje" : ""}" style="--l:${d + 2}">${n.charAt(0).toUpperCase()}${n.slice(1)}${d === diaAgora ? '<span class="so-leitor"> (hoje)</span>' : ""}</span>`).join("");

  caixa.innerHTML = `
    <p class="meta quadros-sobre">Meia hora por quadradinho, como no método do Augusto; cada dia vai do acordar ao acordar seguinte. Começa pintada com a Rotina acima. Pinte por cima para testar outra semana: o rascunho fica guardado e não muda a Rotina. Gostou? Peça ao Claude para passar o rascunho para a Rotina.</p>
    <section class="quadros-tela" aria-labelledby="t-pinceis">
      <div class="quadros-ferramentas">
        <h2 id="t-pinceis" class="so-leitor">Pincéis e a conta da semana</h2>
        <div class="pinceis" role="group" aria-label="Pincel">${CATEGORIAS.map((c) => `
          <button type="button" class="pincel" data-pincel="${c.id}" aria-pressed="${c.id === pincel}">
            <span class="amostra q-${c.id || "vazio"}"></span><span class="pincel-nome">${c.nome}</span><span class="pincel-conta" data-conta="${c.id}"></span>
          </button>`).join("")}</div>
        <div class="quadros-acoes">
          <button type="button" class="botao pequeno" data-desfazer disabled>Desfazer</button>
          <button type="button" class="botao pequeno" data-voltar-rotina>Voltar à Rotina</button>
        </div>
      </div>
      <div class="quadros" role="group" aria-label="A semana: uma linha por dia, ${QUADROS} quadradinhos de meia hora, ${daHora(hhmm(inicio))} ${aHora(hhmm(inicio))} do dia seguinte. Setas para andar, Enter para pintar.">
        ${rotulosHora}${rotulosDia}${quadradinhos}
      </div>
      <p class="meta quadros-leitura" data-leitura>Clique e arraste para pintar. Um ponto no quadradinho é o que mudou em relação à Rotina.</p>
      <p class="quadros-resumo" data-resumo></p>
      <p class="meta" role="status" data-estado-quadros></p>
    </section>`;

  const grade = caixa.querySelector(".quadros");
  const leitura = caixa.querySelector("[data-leitura]");
  const estado = caixa.querySelector("[data-estado-quadros]");
  const botaoDesfazer = caixa.querySelector("[data-desfazer]");
  const botaoVoltar = caixa.querySelector("[data-voltar-rotina]");
  const el = (d, s) => grade.querySelector(`[data-d="${d}"][data-s="${s}"]`);
  const igualRotina = () => q.every((dia, d) => dia.every((x, s) => x === daRotina[d][s]));

  const atualizarConta = () => {
    const c = contaDe(q);
    const base = contaDe(daRotina);
    CATEGORIAS.forEach((x) => { caixa.querySelector(`[data-conta="${x.id}"]`).textContent = x.id || c[""] ? horas(c[x.id]) : ""; });
    const acordado = QUADROS * 7 * 30 - c.sono;
    const difs = CATEGORIAS.filter((x) => c[x.id] !== base[x.id])
      .map((x) => `${c[x.id] > base[x.id] ? "+" : "−"}${horas(Math.abs(c[x.id] - base[x.id]))} ${x.de}`);
    caixa.querySelector("[data-resumo]").innerHTML = `Na semana, <strong>${horas(acordado)} acordado</strong> e ${horas(c.sono)} de sono. O Augusto conta 112h acordado, com 8h de sono por noite.${difs.length ? `<span class="quadros-difs">Em relação à Rotina: ${difs.join(", ")}.</span>` : ""}`;
    botaoVoltar.disabled = igualRotina();
    botaoDesfazer.disabled = !passos.length;
  };

  let salvando = null;
  const guardar = () => {
    clearTimeout(salvando);
    salvando = setTimeout(async () => {
      try {
        if (igualRotina()) await api("/api/quadros", { method: "DELETE" });
        else await enviar("/api/quadros", "PUT", { inicio: hhmm(inicio), dias: q });
        estado.textContent = igualRotina() ? "Igual à Rotina: sem rascunho." : "Rascunho guardado.";
      } catch {
        erro("Não deu para guardar o rascunho. Confira se a Escola está ligada e pinte de novo.");
      }
    }, 400);
  };
  const ler = (b) => {
    const d = +b.dataset.d, s = +b.dataset.s;
    leitura.textContent = `${rotuloDe(d, s)}: ${NOME_CATEGORIA[q[d][s]]}${q[d][s] !== daRotina[d][s] ? ` (na Rotina: ${NOME_CATEGORIA[daRotina[d][s]]})` : ""}.`;
  };
  const pintar = (b) => {
    const d = +b.dataset.d, s = +b.dataset.s;
    if (q[d][s] === pincel) return;
    q[d][s] = pincel;
    b.className = classeDe(d, s);
    b.setAttribute("aria-label", `${rotuloDe(d, s)}: ${NOME_CATEGORIA[pincel]}`);
    ler(b);
  };
  const redesenhar = () => {
    grade.querySelectorAll(".q").forEach((b) => {
      const d = +b.dataset.d, s = +b.dataset.s;
      b.className = classeDe(d, s);
      b.setAttribute("aria-label", `${rotuloDe(d, s)}: ${NOME_CATEGORIA[q[d][s]]}`);
    });
    atualizarConta();
  };
  const passo = () => { passos.push(q.map((d) => [...d])); if (passos.length > 100) passos.shift(); };
  // O mouse rápido pula quadradinhos: o traço preenche a linha entre o último pintado e este.
  let ultimo = null;
  const tracar = (b) => {
    const d = +b.dataset.d, s = +b.dataset.s;
    if (ultimo) {
      const n = Math.max(Math.abs(d - ultimo[0]), Math.abs(s - ultimo[1]));
      for (let i = 1; i < n; i++) pintar(el(Math.round(ultimo[0] + ((d - ultimo[0]) * i) / n), Math.round(ultimo[1] + ((s - ultimo[1]) * i) / n)));
    }
    pintar(b);
    ultimo = [d, s];
  };

  // O mouse pinta ao arrastar; no toque, cada toque pinta um (arrastar rola a página); no teclado, Enter ou espaço.
  let ponteiro = "";
  grade.addEventListener("pointerdown", (e) => {
    ponteiro = e.pointerType;
    const b = e.target.closest(".q");
    if (!b || ponteiro === "touch" || e.button !== 0) return;
    passo();
    ultimo = null;
    tracar(b);
    const fim = () => { grade.classList.remove("pintando"); atualizarConta(); guardar(); };
    grade.classList.add("pintando");
    document.addEventListener("pointerup", fim, { once: true });
  });
  grade.addEventListener("pointerover", (e) => {
    const b = e.target.closest(".q");
    if (!b) return;
    if (grade.classList.contains("pintando") && e.buttons & 1) tracar(b);
    else ler(b);
  });
  grade.addEventListener("click", (e) => {
    const b = e.target.closest(".q");
    if (!b || (e.detail && ponteiro !== "touch")) return;
    passo();
    pintar(b);
    atualizarConta();
    guardar();
  });
  grade.addEventListener("focusin", (e) => {
    if (!e.target.matches(".q")) return;
    grade.querySelector('.q[tabindex="0"]')?.setAttribute("tabindex", "-1");
    e.target.tabIndex = 0;
    ler(e.target);
  });
  grade.addEventListener("keydown", (e) => {
    const b = e.target.closest(".q");
    const ir = { ArrowRight: [0, 1], ArrowLeft: [0, -1], ArrowDown: [1, 0], ArrowUp: [-1, 0] }[e.key];
    if (!b || !ir) return;
    e.preventDefault();
    const deitado = el(0, 1).offsetLeft > el(0, 0).offsetLeft; // no celular, os dias viram colunas
    const [dd, ds] = deitado ? ir : [ir[1], ir[0]];
    el(Math.max(0, Math.min(6, +b.dataset.d + dd)), Math.max(0, Math.min(QUADROS - 1, +b.dataset.s + ds))).focus();
  });
  caixa.querySelector(".pinceis").addEventListener("click", (e) => {
    const b = e.target.closest("[data-pincel]");
    if (!b) return;
    pincel = b.dataset.pincel;
    caixa.querySelectorAll("[data-pincel]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
  });
  botaoDesfazer.addEventListener("click", () => {
    if (!passos.length) return;
    q = passos.pop();
    redesenhar();
    guardar();
  });
  botaoVoltar.addEventListener("click", () => {
    passo();
    q = daRotina.map((d) => [...d]);
    redesenhar();
    guardar();
  });
  caixa.querySelector(".quadros-tela").addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z" && passos.length) { e.preventDefault(); botaoDesfazer.click(); }
  });
  atualizarConta();
}

/* ---------- Assistir junto ---------- */

// Uma sala por vídeo, no servidor. Play, pausa e pulo de um vão a todos pelo fluxo da sala; o volume é de cada um.
// O player vira o do YouTube com a API ligada só quando a pessoa entra na sala.
let aoVivo = null; // o fluxo das salas abertas, para o convite
let salasAbertas = [];
let juntos = null; // { sala, fonte, player, conexao, tocandoSala, aplicando, seguindoAte }
let entrarNaSala = null; // o vídeo pedido pelo convite: a aula entra na sala quando abrir
const dispensadas = new Set();
const convite = document.getElementById("convite-juntos");
const ICONE_FECHAR = svg('<path d="M6 6l12 12M18 6L6 18"/>', 18);
const SEGUIR_MS = 15000; // o play que vem logo depois de um comando dos outros é obediência (ou a volta do anúncio)
const TOLERANCIA = 1.5; // segundos de diferença antes de pular para o ponto da sala

function ouvirAoVivo() {
  aoVivo?.close();
  aoVivo = new EventSource("/api/aovivo");
  aoVivo.addEventListener("salas", (e) => { salasAbertas = JSON.parse(e.data).salas; mostrarConvite(); });
}

function mostrarConvite() {
  const eu = perfilAtual?.id;
  [...dispensadas].forEach((k) => { if (!salasAbertas.some((s) => s.sala === k)) dispensadas.delete(k); });
  const s = salasAbertas.find((x) => x.membros.length && !x.membros.some((m) => m.id === eu) && !dispensadas.has(x.sala));
  if (!s || !eu) { convite.hidden = true; return; }
  const quem = s.membros.find((m) => m.id === s.aberta_por.id) || s.membros[0];
  const mais = s.membros.length > 1 ? ` e mais ${s.membros.length - 1}` : "";
  convite.innerHTML = `${avatar(quem, "mini")}
    <p><strong>${esc(quem.nome)}</strong>${mais} ${s.membros.length > 1 ? "estão" : "está"} assistindo <strong>${titulo(s.titulo)}</strong>.</p>
    <button class="botao pequeno primario" type="button" data-entrar-sala>Entrar junto</button>
    <button class="botao-fechar" type="button" data-dispensar title="Dispensar">${ICONE_FECHAR}<span class="so-leitor">Dispensar o convite</span></button>`;
  convite.dataset.sala = s.sala;
  convite.dataset.item = s.item;
  convite.hidden = false;
}

convite.addEventListener("click", (e) => {
  const sala = convite.dataset.sala;
  if (e.target.closest("[data-dispensar]")) { dispensadas.add(sala); mostrarConvite(); return; }
  if (!e.target.closest("[data-entrar-sala]")) return;
  dispensadas.add(sala);
  convite.hidden = true;
  entrarNaSala = convite.dataset.item;
  if (location.hash.split("/")[2] === entrarNaSala) render();
  else location.hash = `#/item/${entrarNaSala}`;
});

function botaoJuntos(i) {
  if (!i.youtube) return "";
  const s = salasAbertas.find((x) => x.item === i.id && x.membros.length);
  return `<button class="link-botao" type="button" data-juntos>${s ? `Entrar na sala (${s.membros.length} assistindo)` : "Assistir junto"}</button>`;
}

function ligarJuntos(i) {
  const b = pagina.querySelector("[data-juntos]");
  if (!b) return;
  b.addEventListener("click", () => juntarSe(i));
  if (entrarNaSala === i.id) { entrarNaSala = null; juntarSe(i); }
}

let ytPronto = null;
function apiDoYouTube() {
  ytPronto ||= new Promise((pronto) => {
    window.onYouTubeIframeAPIReady = pronto;
    document.head.append(Object.assign(document.createElement("script"), { src: "https://www.youtube.com/iframe_api" }));
  });
  return ytPronto;
}

// O iframe precisa da API ligada: troca o src (o vídeo recomeça, e a sala diz onde parar) e embrulha no YT.Player.
async function playerDaSala(iframe, video) {
  await apiDoYouTube();
  iframe.src = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(video)}?rel=0&enablejsapi=1&origin=${encodeURIComponent(location.origin)}`;
  return new Promise((pronto) => {
    const p = new YT.Player(iframe, { events: { onReady: () => pronto(p), onStateChange: (e) => mudouAqui(e.data) } });
  });
}

async function juntarSe(i) {
  const caixa = pagina.querySelector(".video");
  if (!caixa || juntos?.sala === i.id) return;
  const botao = pagina.querySelector("[data-juntos]");
  if (botao) botao.disabled = true;
  try {
    const s = await enviar("/api/juntos", "POST", { item: i.id });
    caixa.insertAdjacentHTML("beforebegin", `
      <div class="juntos-barra" role="status">
        <span class="juntos-ao-vivo">Assistindo junto</span>
        <span class="juntos-membros"></span>
        <button class="link-botao" type="button" data-sair-sala>Sair da sala</button>
      </div>`);
    pagina.querySelector("[data-sair-sala]").addEventListener("click", () => { sairDaSala(); render(); });
    botao?.remove();
    const player = await playerDaSala(caixa.querySelector("iframe"), i.youtube);
    const fonte = new EventSource(`/api/juntos/${encodeURIComponent(s.sala)}/fluxo`);
    juntos = { sala: s.sala, fonte, player, conexao: null, tocandoSala: s.tocando, aplicando: 0, seguindoAte: 0 };
    fonte.addEventListener("entrou", (e) => { const d = JSON.parse(e.data); juntos.conexao = d.conexao; mostrarMembros(d.membros); obedecer(d); });
    fonte.addEventListener("comando", (e) => obedecer(JSON.parse(e.data)));
    fonte.addEventListener("membros", (e) => mostrarMembros(JSON.parse(e.data).membros));
    fonte.addEventListener("fechada", () => { sairDaSala(); falar("A sala fechou."); });
    fonte.addEventListener("error", () => { if (fonte.readyState === EventSource.CLOSED) { sairDaSala(); falar("A sala fechou."); } });
    mostrarConvite();
  } catch {
    if (botao) botao.disabled = false;
    erro("Não deu para abrir a sala. Confira se a Escola está ligada e tente de novo.");
  }
}

function sairDaSala() {
  if (!juntos) return;
  juntos.fonte.close();
  juntos = null;
  pagina.querySelector(".juntos-barra")?.remove();
  mostrarConvite();
}

function mostrarMembros(lista) {
  const el = pagina.querySelector(".juntos-membros");
  if (!el) return;
  el.innerHTML = `<span class="juntos-rostos">${lista.map((m) => avatar(m, "mini")).join("")}</span>
    <span class="meta">${lista.map((m) => esc(m.nome)).join(", ")}</span>`;
}

// Um comando dos outros (ou o estado de quando entrei): pula se a diferença passa da tolerância, depois toca ou pausa.
function obedecer(d) {
  const j = juntos;
  if (!j) return;
  j.tocandoSala = d.tocando;
  j.aplicando = Date.now() + 800; // os avisos do player nesse meio-tempo são efeito do comando, não da pessoa
  if (d.tocando) j.seguindoAte = Date.now() + SEGUIR_MS;
  if (Math.abs(j.player.getCurrentTime() - d.posicao) > TOLERANCIA) j.player.seekTo(d.posicao, true);
  if (d.tocando) j.player.playVideo();
  else j.player.pauseVideo();
  if (d.por) falar(`${d.por} ${d.tocando ? "deu play" : "pausou"}.`);
}

function mudouAqui(estado) {
  const j = juntos;
  if (!j || Date.now() < j.aplicando) return;
  if (estado === YT.PlayerState.PAUSED) mandar("pause");
  else if (estado === YT.PlayerState.PLAYING) {
    // Voltou do anúncio ou do carregamento enquanto a sala toca: segue a sala, sem puxar os outros para trás.
    if (j.tocandoSala && Date.now() < j.seguindoAte) { api(`/api/juntos/${encodeURIComponent(j.sala)}`).then(obedecer).catch(() => {}); return; }
    mandar("play");
  }
}

function mandar(acao) {
  const j = juntos;
  j.tocandoSala = acao === "play";
  j.seguindoAte = 0;
  enviar(`/api/juntos/${encodeURIComponent(j.sala)}/comando`, "POST", { acao, posicao: j.player.getCurrentTime(), conexao: j.conexao })
    .catch(() => erro("A sala não recebeu o comando. Ela pode ter fechado."));
}

/* ---------- Perfis e Turma ---------- */

// Cada aparelho estuda num perfil (o cookie fica com o servidor). Sem perfil, a escolha cobre a tela, como na Netflix,
// e a Escola só monta por trás depois que alguém escolhe. A Turma mostra o estudo de cada um sem entrar no perfil.
const camada = document.getElementById("perfis");
const painel = document.getElementById("painel-perfil");
const botaoPerfil = document.getElementById("perfil-barra");
const reduzido = matchMedia("(prefers-reduced-motion: reduce)");
const NOMES_CORES = ["laranja", "verde", "roxo", "coral", "azul", "amarelo", "oliva", "rosa"]; // na ordem do servidor
const MOVER = "cubic-bezier(.77, 0, .175, 1)"; // o avatar escolhido indo para o centro
const SUMIR = "cubic-bezier(.23, 1, .32, 1)";
let perfilAtual = null;
let perfisDados = { perfis: [], cores: [] };
let gerenciando = false;

const inicial = (nome) => ([...String(nome).trim()][0] || "?").toUpperCase();
const avatar = (p, classe = "") => `<span class="avatar ${classe}" style="--cor: ${esc(p.cor)}" aria-hidden="true">${esc(inicial(p.nome))}</span>`;

function mostrarPerfil(p) {
  perfilAtual = p;
  botaoPerfil.hidden = false;
  botaoPerfil.querySelector(".avatar").outerHTML = avatar(p, "mini");
  botaoPerfil.querySelector(".perfil-barra-nome").textContent = p.nome;
  botaoPerfil.setAttribute("aria-label", `${p.nome}: trocar de perfil`);
  document.querySelector(".volta-thalia").hidden = !p.dono; // a Thalia é de quem instalou
  ouvirAoVivo(); // o fluxo das salas é por perfil: troca junto
}
botaoPerfil.addEventListener("click", () => abrirPerfis());

// "hoje", "ontem", "há 3 dias"; o dia vira às 4h, como no servidor.
function quando(iso) {
  const d = new Date(Date.now() - 4 * 36e5);
  const dias = Math.round((new Date(d.getFullYear(), d.getMonth(), d.getDate()) - dataDe(iso)) / 864e5);
  return dias <= 0 ? "hoje" : dias === 1 ? "ontem" : dias < 7 ? `há ${dias} dias` : `em ${dataCurta(iso)}`;
}

function cartaoTurma(p, eu, n = null) {
  const voce = p.id === eu;
  return `
    <li class="turma-cartao${voce ? " eu" : ""}${n === null ? "" : " perfis-entra"}"${n === null ? "" : ` style="--n: ${n}"`}>
      <div class="turma-topo">${avatar(p, "medio")}
        <div><h2 class="turma-nome">${esc(p.nome)}${voce ? '<span class="selo-voce">você</span>' : ""}${p.coroa ? `<span class="coroa" title="Venceu a semana passada">${ICONE.coroa}<span class="so-leitor">venceu a semana passada</span></span>` : ""}</h2>
          <p class="meta">${p.concursos.map((c) => esc(c.sigla)).join(" · ")}</p></div>
      </div>
      <div class="turma-placar">
        <span class="turma-posicao">${p.posicao}º</span>
        <span class="turma-pontos"><strong>${p.pontos}</strong> pontos na semana</span>
        <span class="foguinho${p.sequencia ? "" : " apagado"}" title="Dias seguidos de estudo">${ICONE.aquecimento}${p.sequencia}<span class="so-leitor"> ${p.sequencia === 1 ? "dia seguido" : "dias seguidos"}</span></span>
      </div>
      <p class="turma-agora">${p.agora ? `Agora: <strong>${titulo(p.agora.titulo)}</strong>, em ${esc(p.agora.materia)}` : "Terminou o caminho dos cursos que escolheu."}</p>
      <dl class="turma-numeros">
        <div><dt>Nesta semana</dt><dd>${tempo(p.minutos_semana)}</dd></div>
        <div><dt>No total</dt><dd>${tempo(p.minutos_total)}</dd></div>
        <div><dt>Aulas concluídas</dt><dd>${p.concluidos}</dd></div>
        <div><dt>Questões</dt><dd>${p.questoes}${p.questoes ? ` <span class="meta">${pct(p.acertos, p.questoes)}% certas</span>` : ""}</dd></div>
      </dl>
      <p class="meta">${p.ultimo ? `Último estudo: ${quando(p.ultimo)}` : "Ainda não estudou aqui."}${p.semanas_vencidas ? ` · ${p.semanas_vencidas} ${p.semanas_vencidas === 1 ? "semana vencida" : "semanas vencidas"}` : ""}</p>
    </li>`;
}

const SOBRE_HORAS = "Horas e pontos são minutos estimados: o tempo da aula concluída e 2 por questão.";
const SOBRE_PONTOS = "Os pontos zeram toda segunda, e neles cada questão conta uma vez. O foguinho conta os dias seguidos com 15 minutos ou mais; a folga não quebra.";

// O placar do Início: a posição na semana e a distância para quem está logo acima (ou logo abaixo, para quem lidera).
function cartaoPlacar(p) {
  const frase = p.acima
    ? (p.acima.pontos === p.pontos ? `Empatado com ${esc(p.acima.nome)}.` : `Você está ${p.acima.pontos - p.pontos} ${p.acima.pontos - p.pontos === 1 ? "ponto" : "pontos"} atrás de ${esc(p.acima.nome)}.`)
    : p.abaixo && p.abaixo.pontos === p.pontos ? `Empatado com ${esc(p.abaixo.nome)}.`
      : p.abaixo ? `Você está ${p.pontos - p.abaixo.pontos} ${p.pontos - p.abaixo.pontos === 1 ? "ponto" : "pontos"} na frente de ${esc(p.abaixo.nome)}.` : "";
  return `<a class="caderno-atalho placar-atalho" href="#/turma">
      <span class="caderno-icone placar-icone">${p.coroa ? ICONE.coroa : ICONE.aquecimento}</span>
      <span class="caderno-texto"><span class="caderno-titulo">${p.posicao}º de ${p.total} na semana · ${p.pontos} pontos</span>
        <span class="meta">${frase}${p.sequencia ? ` ${p.sequencia} ${p.sequencia === 1 ? "dia seguido" : "dias seguidos"}.` : ""}</span></span>
      <span class="link-seta">Turma ${ICONE.seta}</span>
    </a>`;
}

async function turmaTela() {
  const t = await api("/api/turma");
  document.title = "Turma · Escola";
  pagina.innerHTML = `
    <header class="cabeca">
      <h1>Turma</h1>
      <p class="sub largo">O estudo de cada um. ${SOBRE_HORAS} ${SOBRE_PONTOS}</p>
    </header>
    <ul class="turma-grade">${[...t.perfis].sort((a, b) => a.posicao - b.posicao).map((p) => cartaoTurma(p, t.eu)).join("")}</ul>`;
}

async function abrirPerfis(dados = null) {
  if (!camada.hidden) return; // vários pedidos podem dar 401 ao mesmo tempo
  camada.hidden = false;
  app.inert = true; // a Escola por trás não recebe foco nem clique enquanto a escolha cobre a tela
  document.body.classList.add("com-perfis");
  menu(false);
  gerenciando = false;
  try {
    await desenharEscolha({ dados });
  } catch {
    camada.innerHTML = '<p class="erro" role="alert">A Escola não respondeu. Se o PC acabou de ligar, espere um minuto e recarregue a página.</p>';
  }
}

function fecharPerfis() {
  camada.getAnimations({ subtree: true }).forEach((a) => a.cancel());
  camada.hidden = true;
  camada.classList.remove("indo");
  camada.innerHTML = "";
  document.body.classList.remove("com-perfis");
  app.inert = false;
  pagina.focus({ preventScroll: true });
}

async function desenharEscolha({ dados = null, entrar = true } = {}) {
  const d = dados || await api("/api/perfis");
  perfisDados = d;
  const anima = entrar ? "perfis-entra" : "";
  const lapis = `<span class="perfil-lapis">${svg('<path d="M14.5 4.5l5 5L9 20H4v-5z"/><path d="M12.5 6.5l5 5"/>', 30)}</span>`;
  camada.innerHTML = `
    <div class="perfis-centro">
      <h1 class="perfis-titulo ${anima}" tabindex="-1">${gerenciando ? "Gerenciar perfis" : "Quem está estudando?"}</h1>
      ${d.perfis.length ? "" : `<p class="perfis-sub ${anima}">Cada pessoa tem o seu progresso, o seu Cronograma e a sua Rotina. Comece criando o seu.</p>`}
      <ul class="perfis-lista" aria-label="Perfis">${d.perfis.map((p, n) => `
        <li class="${anima}" style="--n: ${n + 1}"><button class="perfil" type="button" data-id="${esc(p.id)}"${gerenciando ? ` aria-label="Editar ${esc(p.nome)}"` : ""}>
          <span class="perfil-rosto">${avatar(p)}${gerenciando ? lapis : ""}</span><span class="perfil-nome">${esc(p.nome)}</span></button></li>`).join("")}
        ${gerenciando ? "" : `<li class="${anima}" style="--n: ${d.perfis.length + 1}"><button class="perfil" type="button" data-novo>
          <span class="perfil-rosto"><span class="avatar vazio" aria-hidden="true">+</span></span><span class="perfil-nome">Novo perfil</span></button></li>`}
      </ul>
      <div class="perfis-acoes ${anima}" style="--n: ${d.perfis.length + 2}">
        ${d.perfis.length ? `<button class="botao" type="button" data-gerenciar>${gerenciando ? "Pronto" : "Gerenciar perfis"}</button>` : ""}
        ${d.perfis.length && !gerenciando ? '<button class="link-botao" type="button" data-turma>Ver a turma</button>' : ""}
      </div>
    </div>`;
  camada.querySelector(".perfis-titulo").focus({ preventScroll: true });
}

async function verTurma() {
  const t = await api("/api/turma");
  camada.innerHTML = `
    <div class="perfis-centro">
      <h1 class="perfis-titulo perfis-entra" tabindex="-1">A turma</h1>
      <p class="perfis-sub perfis-entra">O estudo de cada um, sem entrar no perfil. ${SOBRE_HORAS}</p>
      <ul class="turma-grade">${[...t.perfis].sort((a, b) => a.posicao - b.posicao).map((p, n) => cartaoTurma(p, t.eu, n + 1)).join("")}</ul>
      <div class="perfis-acoes"><button class="botao" type="button" data-voltar>Voltar aos perfis</button></div>
    </div>`;
  camada.querySelector(".perfis-titulo").focus({ preventScroll: true });
}

// A escolha: o avatar vai para o centro e cresce, o resto some, e a camada se desfaz sobre a Escola, que já montou
// por trás. Com movimento reduzido, só a camada some.
function irAoCentro(botao) {
  if (reduzido.matches) return camada.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 200, easing: "ease", fill: "forwards" }).finished;
  const rosto = botao.querySelector(".avatar");
  const r = rosto.getBoundingClientRect();
  const dx = innerWidth / 2 - (r.left + r.width / 2);
  const dy = innerHeight / 2 - (r.top + r.height / 2);
  const agora = getComputedStyle(rosto).transform;
  camada.querySelectorAll(".perfis-titulo, .perfis-sub, .perfis-acoes, .perfis-lista li").forEach((el) => {
    if (!el.contains(botao)) el.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 200, easing: SUMIR, fill: "forwards" });
  });
  botao.querySelector(".perfil-nome").animate([{ opacity: 1 }, { opacity: 0 }], { duration: 160, easing: SUMIR, fill: "forwards" });
  rosto.animate([{ transform: agora === "none" ? "none" : agora }, { transform: `translate(${dx}px, ${dy}px) scale(1.5)` }],
    { duration: 380, easing: MOVER, fill: "forwards" });
  return camada.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 240, delay: 280, easing: SUMIR, fill: "forwards" }).finished;
}

async function escolher(botao, perfil = null) {
  if (camada.classList.contains("indo")) return; // um toque só
  camada.classList.add("indo");
  try {
    const p = perfil || await enviar(`/api/perfis/${encodeURIComponent(botao.dataset.id)}/entrar`, "POST", {});
    mostrarPerfil(p);
    await Promise.all([irAoCentro(botao), render()]);
    fecharPerfis();
  } catch {
    camada.classList.remove("indo");
    camada.getAnimations({ subtree: true }).forEach((a) => a.cancel());
  }
}

function editarPerfil(pid) {
  const d = perfisDados;
  const usadas = new Set(d.perfis.map((x) => x.cor));
  const p = pid ? d.perfis.find((x) => x.id === pid) : { nome: "", cor: d.cores.find((c) => !usadas.has(c)) || d.cores[0] };
  painel.innerHTML = `
    <form class="painel-form" novalidate>
      ${avatar(p)}
      <h2 id="painel-titulo">${pid ? "Editar perfil" : "Novo perfil"}</h2>
      <label class="campo-nome">Nome<input name="nome" maxlength="20" autocomplete="off" spellcheck="false" value="${esc(p.nome)}"></label>
      <fieldset class="cores"><legend>Cor</legend>${d.cores.map((c, n) => `
        <label class="cor"><input type="radio" name="cor" value="${esc(c)}"${c === p.cor ? " checked" : ""}><span class="cor-amostra" style="--cor: ${esc(c)}"></span><span class="so-leitor">${NOMES_CORES[n] || `cor ${n + 1}`}</span></label>`).join("")}
      </fieldset>
      <p class="erro" role="alert" hidden></p>
      <div class="painel-acoes">
        <button class="botao primario" type="submit">${pid ? "Salvar" : "Criar e entrar"}</button>
        <button class="link-botao" type="button" data-cancelar>Cancelar</button>
      </div>
    </form>`;
  const form = painel.querySelector("form");
  const previa = form.querySelector(".avatar");
  form.addEventListener("input", () => {
    previa.textContent = inicial(form.nome.value);
    previa.style.setProperty("--cor", form.cor.value);
  });
  form.querySelector("[data-cancelar]").addEventListener("click", () => painel.close());
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const salvar = form.querySelector("[type=submit]");
    const msg = form.querySelector(".erro");
    salvar.disabled = true;
    let r;
    try {
      r = await fetch(pid ? `/api/perfis/${encodeURIComponent(pid)}` : "/api/perfis", {
        method: pid ? "PUT" : "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nome: form.nome.value, cor: form.cor.value }) });
    } catch { r = null; }
    salvar.disabled = false;
    if (!r?.ok) {
      const detalhe = r?.status === 422 ? (await r.json()).detail : null;
      msg.textContent = typeof detalhe === "string" ? detalhe : r?.status === 422 ? "O nome precisa ter de 1 a 20 letras." : "Não deu para salvar. Tente de novo.";
      msg.hidden = false;
      form.nome.focus();
      return;
    }
    const salvo = await r.json();
    painel.close();
    if (pid) {
      if (perfilAtual?.id === pid) mostrarPerfil(salvo);
      await desenharEscolha({ entrar: false });
      camada.querySelector(`[data-id="${CSS.escape(pid)}"]`)?.focus();
      return;
    }
    gerenciando = false; // o perfil novo já entrou (o servidor pôs o cookie): ele vai para o centro como numa escolha
    await desenharEscolha({ entrar: false });
    escolher(camada.querySelector(`[data-id="${CSS.escape(salvo.id)}"]`), salvo);
  });
  painel.showModal();
  form.nome.focus();
}

camada.addEventListener("click", (e) => {
  const b = e.target.closest("button");
  if (!b || camada.classList.contains("indo")) return;
  if ("novo" in b.dataset) editarPerfil(null);
  else if ("gerenciar" in b.dataset) { gerenciando = !gerenciando; desenharEscolha({ entrar: false }); }
  else if ("turma" in b.dataset) verTurma();
  else if ("voltar" in b.dataset) desenharEscolha({ entrar: false });
  else if (b.dataset.id) { if (gerenciando) editarPerfil(b.dataset.id); else escolher(b); }
});

// Setas andam entre os perfis, como num controle de TV; Enter escolhe (é um botão).
camada.addEventListener("keydown", (e) => {
  if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(e.key)) return;
  const botoes = [...camada.querySelectorAll(".perfil")];
  if (!botoes.length) return;
  e.preventDefault();
  const i = botoes.indexOf(document.activeElement);
  const passo = e.key === "ArrowLeft" || e.key === "ArrowUp" ? -1 : 1;
  botoes[i < 0 ? 0 : (i + passo + botoes.length) % botoes.length].focus();
});

async function iniciar() {
  try {
    const d = await api("/api/perfis");
    if (!d.atual) { abrirPerfis(d); return; }
    mostrarPerfil(d.atual);
  } catch { /* o render mostra o erro */ }
  render();
}

/* ---------- Rotas ---------- */

async function render() {
  if (relogio) { clearInterval(relogio); relogio = null; }
  sairDaSala(); // mudar de tela é sair da sala do vídeo
  menu(false);
  const [, rota, a, b] = location.hash.split("/");
  const cid = rota === "concurso" ? a : rota === "item" ? b : null;
  atualizarBarra(rota === "quadros" ? "rotina" : ["cronograma", "rotina", "erros", "situacao", "turma"].includes(rota) ? rota : rota ? "" : "inicio", cid);
  try {
    if (rota === "item" && a) await item(a, b);
    else if (rota === "concurso" && a) await concurso(a, b);
    else if (rota === "revisao" && a && b) await revisao(a, b);
    else if (rota === "redacao" && a && b) await redacao(a, b);
    else if (rota === "provinha" && a) await provinhaTela(a);
    else if (rota === "cronograma") await cronogramaTela();
    else if (rota === "rotina" || rota === "quadros") await rotinaTela({ quadros: rota === "quadros" || a === "quadros" });
    else if (rota === "erros") await cadernoTela();
    else if (rota === "aquecimento") await aquecimentoTela();
    else if (rota === "situacao") await situacaoTela();
    else if (rota === "turma") await turmaTela();
    else await inicio();
  } catch (e) {
    if (e.message === "401") return; // a escolha de perfil já cobriu a tela
    document.title = "Escola";
    pagina.innerHTML = `<p class="erro" role="alert">${e.message === "404"
      ? "Isso não existe mais no catálogo."
      : "A Escola não respondeu. Se o PC acabou de ligar, espere um minuto e recarregue a página."}</p>
      <a class="link" href="#/">Voltar ao início</a>`;
  }
  window.scrollTo(0, 0);
  pagina.focus({ preventScroll: true });
}

addEventListener("hashchange", render);
iniciar();
