// A caneta da Escola (pedido dele em 29/10): rabiscar por cima de qualquer tela, como no próprio caderno. Os rabiscos
// ficam só neste navegador, um conjunto por tela e, nas questões uma por vez, um por questão. Eles moram nas
// coordenadas da página e rolam junto com ela, mas não acompanham um texto que rola por dentro (o minimizado). Cada
// traço guarda a largura da página em que foi feito e só aparece nela: com a janela de outro tamanho, o texto quebra
// em outro lugar e o círculo cairia na alternativa errada.
const pagina = document.getElementById("pagina");
const conteudo = document.querySelector(".conteudo");
const tela = document.getElementById("caneta-tela");
const barra = document.getElementById("caneta-barra");
const ctx = tela.getContext("2d");
const raiz = document.documentElement;

const LARGURA = { caneta: 3, marca: 18 };
const BORRACHA = 12; // o raio, em px
let tintas = null; // lidas do CSS na primeira vez que precisa: --tinta-caneta e --marca-texto
const tinta = (f) => (tintas ??= {
  caneta: getComputedStyle(raiz).getPropertyValue("--tinta-caneta").trim(),
  marca: getComputedStyle(raiz).getPropertyValue("--marca-texto").trim(),
})[f];

let ferramenta = "caneta";
let rabiscos = []; // [{ f: "caneta" | "marca", l: largura, p: [[x, y], …] }], em px a partir do canto de cima da página
let historico = []; // como estava antes de cada mudança, para o Desfazer
let chave = "";
let antes = null; // como estava quando o traço começou; null fora de um traço
let mudou = false;
let ultimo = null;

const ligada = () => raiz.dataset.caneta === "ligada";
const largura = () => Math.round(pagina.clientWidth);
const visivel = (r, l) => Math.abs(r.l - l) <= 1;

function guardar() {
  try {
    if (rabiscos.length) localStorage.setItem(chave, JSON.stringify(rabiscos));
    else localStorage.removeItem(chave);
  } catch { /* sem armazenamento, ou cheio: o rabisco vale até sair da tela */ }
}

function atualizarBotoes() {
  barra.querySelectorAll("[data-ponta]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.ponta === ferramenta)));
  barra.querySelector("[data-desfazer]").disabled = !historico.length;
  barra.querySelector("[data-limpar]").disabled = !rabiscos.length;
}

// A tela é a da rota; nas questões uma por vez, também a da questão aberta (o data-atual da folha).
function trocarDeTela() {
  const n = pagina.querySelector("[data-atual]")?.dataset.atual;
  const nova = `escola:rabiscos:${location.hash || "#/"}${n == null ? "" : `:${n}`}`;
  if (nova === chave) return;
  soltar();
  chave = nova;
  historico = [];
  try { rabiscos = JSON.parse(localStorage.getItem(chave)) || []; } catch { rabiscos = []; }
  atualizarBotoes();
  pedirDesenho();
}

/* ---------- Desenho ---------- */

let pedido = 0;
const pedirDesenho = () => { pedido ||= requestAnimationFrame(desenhar); };

// A tela de desenho é do tamanho da janela, sobre a coluna do conteúdo; a cada rolagem os traços são redesenhados
// a partir de onde a página está agora.
function desenhar() {
  pedido = 0;
  const c = conteudo.getBoundingClientRect();
  const dpr = devicePixelRatio || 1;
  tela.style.left = `${c.left}px`;
  tela.style.width = `${c.width}px`;
  tela.style.height = `${innerHeight}px`;
  barra.style.left = `${c.left + c.width / 2}px`;
  const w = Math.round(c.width * dpr), h = Math.round(innerHeight * dpr);
  if (tela.width !== w || tela.height !== h) { tela.width = w; tela.height = h; }
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.clearRect(0, 0, w, h);
  if (!rabiscos.length) return;
  const p = pagina.getBoundingClientRect();
  ctx.setTransform(dpr, 0, 0, dpr, (p.left - c.left) * dpr, p.top * dpr);
  ctx.lineCap = ctx.lineJoin = "round";
  const l = largura();
  rabiscos.filter((r) => visivel(r, l)).forEach(traco);
}

// O traço passa pelo meio de cada par de pontos, em curva: fica liso mesmo com o mouse rápido.
function traco({ f, p }) {
  ctx.strokeStyle = tinta(f);
  ctx.lineWidth = LARGURA[f];
  ctx.beginPath();
  ctx.moveTo(...p[0]);
  if (p.length === 1) ctx.lineTo(p[0][0] + 0.01, p[0][1]); // um toque vira um ponto
  for (let k = 1; k < p.length - 1; k++) ctx.quadraticCurveTo(...p[k], (p[k][0] + p[k + 1][0]) / 2, (p[k][1] + p[k + 1][1]) / 2);
  if (p.length > 1) ctx.lineTo(...p.at(-1));
  ctx.stroke();
}

/* ---------- Mão ---------- */

const ponto = (e) => {
  const p = pagina.getBoundingClientRect();
  return [Math.round((e.clientX - p.left) * 10) / 10, Math.round((e.clientY - p.top) * 10) / 10];
};

// A distância de s ao segmento ab
function distancia(s, a, b) {
  const dx = b[0] - a[0], dy = b[1] - a[1];
  const t = dx || dy ? Math.max(0, Math.min(1, ((s[0] - a[0]) * dx + (s[1] - a[1]) * dy) / (dx * dx + dy * dy))) : 0;
  return Math.hypot(s[0] - a[0] - t * dx, s[1] - a[1] - t * dy);
}

// A borracha tira o traço inteiro que ela encostar no caminho de "de" até "ate", como a de apagar risco do tablet.
function apagar(de, ate) {
  const passos = Math.max(1, Math.ceil(Math.hypot(ate[0] - de[0], ate[1] - de[1]) / 4));
  const l = largura();
  const resta = rabiscos.filter((r) => {
    if (!visivel(r, l)) return true; // o que não aparece agora não se apaga sem ver
    const { f, p } = r;
    const folga = BORRACHA + LARGURA[f] / 2;
    for (let i = 0; i <= passos; i++) {
      const s = [de[0] + ((ate[0] - de[0]) * i) / passos, de[1] + ((ate[1] - de[1]) * i) / passos];
      for (let k = 0; k < p.length; k++) if (distancia(s, p[k], p[k + 1] ?? p[k]) < folga) return false;
    }
    return true;
  });
  if (resta.length !== rabiscos.length) { rabiscos = resta; mudou = true; }
}

tela.addEventListener("pointerdown", (e) => {
  if (!e.isPrimary || e.button !== 0) return;
  e.preventDefault();
  tela.setPointerCapture(e.pointerId);
  antes = JSON.stringify(rabiscos);
  mudou = false;
  ultimo = ponto(e);
  if (ferramenta === "borracha") apagar(ultimo, ultimo);
  else { rabiscos.push({ f: ferramenta, l: largura(), p: [ultimo] }); mudou = true; }
  pedirDesenho();
});
tela.addEventListener("pointermove", (e) => {
  if (!antes) return;
  const atual = ferramenta === "borracha" ? null : rabiscos.at(-1);
  const juntos = e.getCoalescedEvents?.() ?? [];
  for (const c of juntos.length ? juntos : [e]) {
    const pt = ponto(c);
    if (Math.hypot(pt[0] - ultimo[0], pt[1] - ultimo[1]) < 2) continue;
    if (atual) atual.p.push(pt);
    else apagar(ultimo, pt);
    ultimo = pt;
  }
  pedirDesenho();
});
function soltar() {
  if (!antes) return;
  if (mudou) {
    historico.push(antes);
    if (historico.length > 50) historico.shift();
    guardar();
  }
  antes = null;
  atualizarBotoes();
}
tela.addEventListener("pointerup", soltar);
tela.addEventListener("pointercancel", soltar);

/* ---------- Barra ---------- */

function desfazer() {
  if (!historico.length) return;
  rabiscos = JSON.parse(historico.pop());
  guardar();
  atualizarBotoes();
  pedirDesenho();
}

function limpar() { // não pede confirmação: o Desfazer traz de volta
  if (!rabiscos.length) return;
  historico.push(JSON.stringify(rabiscos));
  rabiscos = [];
  guardar();
  atualizarBotoes();
  pedirDesenho();
}

function ligar(sim) {
  soltar();
  if (sim) raiz.dataset.caneta = "ligada";
  else delete raiz.dataset.caneta;
  barra.hidden = !sim;
  document.querySelectorAll("[data-ligar-caneta]").forEach((b) => b.setAttribute("aria-pressed", String(sim)));
  pedirDesenho();
}

document.addEventListener("click", (e) => {
  if (e.target.closest("[data-ligar-caneta]")) ligar(!ligada());
});
barra.addEventListener("click", (e) => {
  const b = e.target.closest("button");
  if (!b) return;
  if (b.dataset.ponta) { ferramenta = b.dataset.ponta; atualizarBotoes(); }
  else if (b.hasAttribute("data-desfazer")) desfazer();
  else if (b.hasAttribute("data-limpar")) limpar();
  else if (b.hasAttribute("data-pronto")) ligar(false);
});
addEventListener("keydown", (e) => {
  if (!ligada() || e.target.closest?.("input, textarea, [contenteditable]")) return;
  if (e.key === "Escape") ligar(false);
  else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") { e.preventDefault(); desfazer(); }
});

addEventListener("scroll", pedirDesenho, { passive: true });
addEventListener("resize", pedirDesenho);
new ResizeObserver(pedirDesenho).observe(conteudo); // a página cresceu, ou a barra lateral recolheu
addEventListener("hashchange", trocarDeTela);
new MutationObserver(trocarDeTela).observe(pagina, { childList: true, subtree: true, attributes: true, attributeFilter: ["data-atual"] });
trocarDeTela();
