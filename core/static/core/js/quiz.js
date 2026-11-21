// Quiz de bandeiras (clássico e sobrevivência). A pontuação é calculada no servidor.
(() => {
  const raiz = document.getElementById('quiz-app');
  if (!raiz) return;

  const csrf = document.querySelector('meta[name="csrf-token"]').content;
  const $ = (id) => document.getElementById(id);
  const telas = { config: $('tela-config'), jogo: $('tela-jogo'), fim: $('tela-fim') };
  const TEMPO_CLASSICO = 10; // segundos só para o bônus de rapidez (visual)

  let bloqueado = false;
  let ultimaConfig = null;
  let resumo = null;
  let modo = 'classico';
  let tipo = 'bandeira';
  let progresso = { indice: 1, total: 10 };
  let autoAvanco = null;
  let fimTempo = null;
  let relogio = null;

  // ================= som (sintetizado no navegador, sem arquivos) =================
  const som = { ctx: null, mudo: localStorage.getItem('som') === '0' };
  function audio() {
    if (!som.ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (AC) som.ctx = new AC();
    }
    if (som.ctx && som.ctx.state === 'suspended') som.ctx.resume();
    return som.ctx;
  }
  function tom(freq, atraso, duracao, tipo = 'sine', volume = 0.16) {
    const c = audio();
    if (!c || som.mudo) return;
    const t = c.currentTime + atraso;
    const osc = c.createOscillator();
    const ganho = c.createGain();
    osc.type = tipo;
    osc.frequency.setValueAtTime(freq, t);
    ganho.gain.setValueAtTime(0.0001, t);
    ganho.gain.exponentialRampToValueAtTime(volume, t + 0.012);
    ganho.gain.exponentialRampToValueAtTime(0.0001, t + duracao);
    osc.connect(ganho).connect(c.destination);
    osc.start(t);
    osc.stop(t + duracao + 0.03);
  }
  // Escala pentatônica: cada acerto seguido sobe uma nota (efeito de combo).
  const ESCALA = [523.25, 587.33, 659.25, 783.99, 880, 1046.5, 1174.66, 1318.5, 1567.98, 1760];
  const somAcerto = (combo) => {
    const f = ESCALA[Math.min(Math.max(combo, 1) - 1, ESCALA.length - 1)];
    tom(f, 0, 0.16, 'triangle', 0.2);
    tom(f * 2, 0.05, 0.14, 'sine', 0.07);
  };
  const somErro = () => { tom(180, 0, 0.22, 'sawtooth', 0.1); tom(130, 0.12, 0.3, 'sawtooth', 0.1); };
  const somTique = () => tom(900, 0, 0.05, 'square', 0.05);
  const somFim = (bom) => (bom ? [523, 659, 784, 1047] : [392, 330, 262]).forEach((f, i) => tom(f, i * 0.13, 0.3, 'triangle', 0.18));
  const somAprendido = () => [784, 988, 1175].forEach((f, i) => tom(f, i * 0.07, 0.18, 'sine', 0.15));

  const btnSom = $('btn-som');
  function iconeSom() { btnSom.innerHTML = som.mudo ? '<i class="bi bi-volume-mute-fill"></i>' : '<i class="bi bi-volume-up-fill"></i>'; }
  iconeSom();
  btnSom.addEventListener('click', () => {
    som.mudo = !som.mudo;
    localStorage.setItem('som', som.mudo ? '0' : '1');
    iconeSom();
    if (!som.mudo) somAcerto(1);
  });

  // ================= utilidades =================
  function mostrar(nome) {
    Object.entries(telas).forEach(([chave, el]) => el.classList.toggle('d-none', chave !== nome));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function aviso(texto) {
    $('alerta-quiz').innerHTML = `<div class="alert alert-danger alert-dismissible fade show" role="alert">${texto}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button></div>`;
  }

  async function api(url, corpo) {
    const opcoes = corpo === undefined
      ? { headers: { Accept: 'application/json' } }
      : { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf }, body: JSON.stringify(corpo) };
    const resp = await fetch(url, opcoes);
    const dados = await resp.json().catch(() => ({}));
    if (!resp.ok) throw new Error(dados.erro || 'Algo deu errado. Tente novamente.');
    return dados;
  }

  function reiniciarAnimacao(el, classe) {
    el.classList.remove(classe);
    void el.offsetWidth;
    el.classList.add(classe);
  }

  function flutuar(texto, pequeno) {
    const el = document.createElement('div');
    el.className = `ganho${pequeno ? ' pequeno' : ''}`;
    el.textContent = texto;
    $('moldura').appendChild(el);
    setTimeout(() => el.remove(), 900);
  }

  // ================= mascote (Bandi) =================
  const mascote = telas.jogo.querySelector('.mascote');
  const FRASES = {
    acerto: ['Isso aí!', 'Boa!', 'Mandou bem!', 'Perfeito!', 'Show!'],
    erro: ['Quase!', 'Anota essa!', 'Essa é difícil!', 'Vai com calma!'],
    inicio: { bandeira: 'Que bandeira é essa?', mapa: 'Onde estamos?', 'mapa-bandeira': 'Qual é a bandeira?', capital: 'Qual é a capital?' },
  };
  const sorteia = (lista) => lista[Math.floor(Math.random() * lista.length)];
  function humor(estado, fala) {
    mascote.dataset.humor = estado;
    $('fala').textContent = fala;
    if (estado === 'feliz') reiniciarAnimacao(mascote, 'salta');
  }
  const rotuloAprendido = () => (tipo === 'capital' ? 'Capital aprendida!' : tipo === 'bandeira' ? 'País aprendido!' : 'Mapa aprendido!');

  // ================= HUD =================
  let vidasAntes = 3;
  function desenharVidas(vidas) {
    const perdeu = vidas < vidasAntes;
    vidasAntes = vidas;
    $('hud-vidas').innerHTML = [0, 1, 2].map((i) => {
      if (i < vidas) return '<i class="bi bi-heart-fill"></i>';
      return `<i class="bi bi-heart-fill perdida${perdeu && i === vidas ? ' nova' : ''}"></i>`;
    }).join('');
    $('hud-vidas').setAttribute('aria-label', `${vidas} vidas restantes`);
  }

  function mostrarCombo(n) {
    const el = $('combo');
    if (n < 2) { el.classList.add('d-none'); return; }
    el.classList.remove('d-none', 'c5', 'c10');
    if (n >= 10) el.classList.add('c10'); else if (n >= 5) el.classList.add('c5');
    el.textContent = `Combo x${n}`;
    reiniciarAnimacao(el, 'pop');
  }

  function atualizarHud(r) {
    $('hud-pontos').textContent = r.pontos;
    mostrarCombo(r.sequencia);
    if (modo === 'sobrevivencia') desenharVidas(r.vidas);
  }

  // ================= cronômetro =================
  const barra = $('barra-tempo');
  function pararTempo() {
    clearTimeout(fimTempo); clearInterval(relogio);
    fimTempo = relogio = null;
    const largura = getComputedStyle(barra).width;
    barra.style.transition = 'none';
    barra.style.width = largura;
  }

  function iniciarTempo(segundos) {
    pararTempo();
    const trilho = $('trilho-tempo');
    const num = $('tempo-num');
    trilho.classList.remove('urgente');
    barra.style.transition = 'none';
    barra.style.width = '100%';
    void barra.offsetWidth;
    barra.style.transition = `width ${segundos}s linear`;
    barra.style.width = '0%';
    if (modo !== 'sobrevivencia') return; // no clássico a barra é só visual
    const fim = performance.now() + segundos * 1000;
    let ultimo = Math.ceil(segundos);
    num.textContent = ultimo;
    relogio = setInterval(() => {
      const resta = Math.max(0, Math.ceil((fim - performance.now()) / 1000));
      if (resta !== ultimo) {
        ultimo = resta;
        num.textContent = resta;
        if (resta <= 3 && resta > 0) { trilho.classList.add('urgente'); somTique(); }
      }
    }, 100);
    fimTempo = setTimeout(() => responder(null), segundos * 1000);
  }

  // ================= perguntas =================
  function precarregar(url) { if (url) { const img = new Image(); img.src = url; } }

  async function proximaPergunta() {
    try {
      const p = await api(raiz.dataset.urlPergunta);
      bloqueado = false;
      modo = p.modo;
      tipo = p.tipo;
      const sobrev = modo === 'sobrevivencia';
      const ehMapa = tipo === 'mapa' || tipo === 'mapa-bandeira';
      progresso = { indice: p.indice, total: p.total };
      $('rotulo-progresso').textContent = sobrev ? `Sobrevivência · carta ${p.indice}` : `Pergunta ${p.indice} de ${p.total}`;
      $('wrap-progresso').classList.toggle('d-none', sobrev);
      $('hud-vidas').classList.toggle('d-none', !sobrev);
      $('tempo-num').classList.toggle('d-none', !sobrev);
      if (sobrev) desenharVidas(p.vidas);
      $('barra-progresso').style.width = `${((p.indice - 1) / Math.max(p.total, 1)) * 100}%`;
      $('hud-pontos').textContent = p.pontos;
      mostrarCombo(p.sequencia);
      $('feedback').classList.add('d-none');
      $('feedback').innerHTML = '';
      $('moldura').classList.remove('acerto', 'erro');
      $('bandeira').classList.toggle('d-none', ehMapa);
      $('mapa-svg').classList.toggle('d-none', !ehMapa);
      $('pergunta-nome').classList.toggle('d-none', tipo !== 'capital');
      $('pergunta-nome').textContent = p.nome || '';
      $('pergunta-texto').textContent = {
        bandeira: 'De qual país é esta bandeira?', mapa: 'De qual país é este mapa?',
        'mapa-bandeira': 'Qual é a bandeira deste país?', capital: 'Qual é a capital deste país?',
      }[tipo];
      humor('neutro', p.sequencia >= 2 ? `Combo x${p.sequencia}!` : FRASES.inicio[tipo]);

      const lista = $('opcoes');
      lista.innerHTML = '';
      p.opcoes.forEach((o, i) => {
        const col = document.createElement('div');
        col.className = 'col-12 col-sm-6';
        const botao = document.createElement('button');
        botao.type = 'button';
        botao.className = tipo === 'mapa-bandeira' ? 'opcao opcao-img' : 'opcao';
        botao.dataset.id = o.id;
        const tecla = document.createElement('span');
        tecla.className = 'tecla';
        tecla.textContent = i + 1;
        if (tipo === 'mapa-bandeira') {
          const img = document.createElement('img');
          img.src = o.bandeira;
          img.alt = `Opção ${i + 1}`;
          botao.append(tecla, img);
        } else {
          botao.append(tecla, document.createTextNode(tipo === 'capital' ? o.capital : o.nome));
        }
        botao.addEventListener('click', () => responder(o.id));
        col.appendChild(botao);
        lista.appendChild(col);
      });

      const tempo = sobrev ? p.tempo : TEMPO_CLASSICO;
      let iniciado = false;
      const largar = () => { if (!iniciado) { iniciado = true; iniciarTempo(tempo); } };
      if (ehMapa) {
        await window.Mapa.carregar(raiz.dataset.urlMapa);
        window.Mapa.desenhar($('mapa-svg'), p.codigo);
        mostrar('jogo');
        largar();
        return;
      }
      const img = $('bandeira');
      img.onload = largar;
      img.onerror = largar;
      img.src = p.bandeira;
      if (img.complete && img.naturalWidth) largar(); // imagem já em cache (pré-carregada)
      setTimeout(largar, 700); // garantia: o relógio começa mesmo se a imagem demorar
      mostrar('jogo');
    } catch (e) {
      mostrar('config');
      aviso(e.message);
    }
  }

  async function responder(id) {
    if (bloqueado) return;
    bloqueado = true;
    pararTempo();
    const botoes = [...document.querySelectorAll('.opcao')];
    botoes.forEach((b) => { b.disabled = true; });
    try {
      const r = await api(raiz.dataset.urlResponder, { opcao: id });
      botoes.forEach((b) => {
        const bid = Number(b.dataset.id);
        if (bid === r.correta_id) b.classList.add('correta');
        else if (bid === id) b.classList.add('errada');
        else b.classList.add('apagada');
      });
      $('barra-progresso').style.width = `${(progresso.indice / Math.max(progresso.total, 1)) * 100}%`;
      atualizarHud(r);
      resumo = r.finalizado ? r.resumo : null;
      precarregar(r.proxima_bandeira);

      if (r.correto) {
        somAcerto(r.sequencia);
        reiniciarAnimacao($('moldura'), 'acerto');
        flutuar(`+${r.ganhos}`, false);
        humor('feliz', r.sequencia >= 5 ? 'Combo imbatível!' : r.sequencia >= 3 ? `Combo x${r.sequencia}!` : sorteia(FRASES.acerto));
        if (r.novo_aprendido) { setTimeout(somAprendido, 140); flutuar(rotuloAprendido(), true); }
        // Acertou: segue sozinho, bem rápido, para manter o combo.
        autoAvanco = setTimeout(avancar, r.sequencia >= 5 ? 330 : 430);
      } else {
        somErro();
        reiniciarAnimacao($('moldura'), 'erro');
        humor('triste', r.timeout ? 'O tempo voou!' : sorteia(FRASES.erro));
        mostrarErro(r);
      }
    } catch (e) {
      aviso(e.message);
      mostrar('config');
    }
  }

  function mostrarErro(r) {
    const el = $('feedback');
    const certa = tipo === 'capital' ? `A capital de ${r.nome} é ${r.capital}` : `Era ${r.nome}`;
    const titulo = r.timeout ? `Tempo esgotado! ${certa}` : certa;
    const vidas = modo === 'sobrevivencia' && !r.finalizado
      ? `<div class="small mt-1">Vidas restantes: <strong>${r.vidas}</strong></div>` : '';
    const selo = r.novo_aprendido ? '<div class="mt-1"><span class="badge text-bg-success">${rotuloAprendido()}</span></div>' : '';
    el.className = 'feedback erro';
    el.innerHTML = `<div class="fw-bold fs-5 text-danger"><i class="bi bi-x-circle-fill me-1"></i>${titulo}</div>${vidas}${selo}
      <div class="mt-2 small"><strong>${r.nome}</strong>: capital ${r.capital}, ${r.continente}.</div>
      <button type="button" class="btn btn-primary mt-3 w-100" id="btn-proxima">${r.finalizado ? 'Ver resultado' : 'Próxima bandeira'}</button>`;
    $('btn-proxima').addEventListener('click', avancar);
    $('btn-proxima').focus({ preventScroll: true });
  }

  function avancar() {
    if (autoAvanco) { clearTimeout(autoAvanco); autoAvanco = null; }
    if (resumo) return mostrarResultado(resumo);
    proximaPergunta();
  }

  // ================= resultado =================
  function mostrarResultado(r) {
    const sobrev = r.modo === 'sobrevivencia';
    $('fim-classico').classList.toggle('d-none', sobrev);
    $('fim-sobrev').classList.toggle('d-none', !sobrev);
    $('fim-pontos').textContent = r.pontos;
    $('fim-sequencia').textContent = r.melhor_sequencia;
    let titulo, texto, festa;
    if (sobrev) {
      $('fim-grande').textContent = r.acertos;
      $('fim-acertos').textContent = r.acertos;
      $('fim-rotulo-acertos').textContent = r.acertos === 1 ? 'acerto' : 'acertos';
      titulo = r.novo_recorde ? 'Novo recorde!' : 'Fim da sobrevivência';
      texto = `${r.motivo === 'tempo' ? 'O tempo da bandeira acabou.' : 'Você usou as 3 vidas.'} Seu recorde: ${r.recorde} acerto${r.recorde === 1 ? '' : 's'}.`;
      festa = r.novo_recorde;
    } else {
      $('fim-anel').style.setProperty('--p', r.percentual);
      $('fim-percentual').textContent = `${r.percentual}%`;
      $('fim-acertos').textContent = `${r.acertos}/${r.total}`;
      $('fim-rotulo-acertos').textContent = 'acertos';
      titulo = 'Bom começo!'; texto = 'Cada partida deixa as bandeiras mais familiares. Jogue de novo para fixar.';
      if (r.percentual === 100) { titulo = 'Perfeito!'; texto = 'Nenhum erro. Você domina essa região.'; }
      else if (r.percentual >= 80) { titulo = 'Excelente!'; texto = 'Você está muito bem. Falta pouco para a perfeição.'; }
      else if (r.percentual >= 50) { titulo = 'Muito bem!'; texto = 'Mais da metade certa. Treine os erros no próximo quiz.'; }
      festa = r.percentual >= 80;
    }
    $('fim-titulo').textContent = titulo;
    $('fim-texto').textContent = texto;
    const mf = $('fim-mascote').querySelector('.mascote');
    if (mf) mf.dataset.humor = festa ? 'feliz' : 'neutro';
    mostrar('fim');
    somFim(festa);
    if (festa) confete();
  }

  function confete() {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const canvas = document.createElement('canvas');
    canvas.className = 'confete';
    canvas.width = innerWidth; canvas.height = innerHeight;
    document.body.appendChild(canvas);
    const ctx = canvas.getContext('2d');
    if (!ctx) { canvas.remove(); return; }
    const cores = ['#e9bb4e', '#3b7ea6', '#3f9b76', '#cf5b6d', '#f4f8f7'];
    const pecas = Array.from({ length: 110 }, () => ({
      x: Math.random() * canvas.width, y: -20 - Math.random() * canvas.height * 0.5,
      w: 6 + Math.random() * 6, h: 8 + Math.random() * 8, v: 2 + Math.random() * 3.5,
      dx: (Math.random() - 0.5) * 2, r: Math.random() * 6, dr: (Math.random() - 0.5) * 0.3,
      cor: cores[Math.floor(Math.random() * cores.length)],
    }));
    const fim = performance.now() + 3200;
    (function quadro(agora) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      pecas.forEach((p) => {
        p.y += p.v; p.x += p.dx; p.r += p.dr;
        ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.r);
        ctx.fillStyle = p.cor; ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h); ctx.restore();
      });
      if (agora < fim) requestAnimationFrame(quadro); else canvas.remove();
    })(performance.now());
  }

  // ================= início =================
  const radios = (nome) => document.querySelector(`input[name="${nome}"]:checked`).value;

  function lerConfig() {
    return {
      tipo: radios('tipo'),
      modo: radios('modo'),
      continente: radios('continente'),
      quantidade: Number(radios('quantidade')),
      foco: $('foco').checked,
    };
  }

  document.querySelectorAll('input[name="modo"]').forEach((r) => r.addEventListener('change', () => {
    $('bloco-quantidade').classList.toggle('d-none', radios('modo') === 'sobrevivencia');
  }));

  async function comecar(config) {
    audio(); // libera o som (precisa de um clique do usuário)
    const botao = $('btn-comecar');
    botao.disabled = true;
    try {
      ultimaConfig = config;
      if (config.tipo === 'mapa' || config.tipo === 'mapa-bandeira') await window.Mapa.carregar(raiz.dataset.urlMapa);
      await api(raiz.dataset.urlIniciar, config);
      resumo = null;
      await proximaPergunta();
    } catch (e) {
      aviso(e.message);
    } finally {
      botao.disabled = false;
    }
  }

  $('btn-comecar').addEventListener('click', () => comecar(lerConfig()));
  $('btn-jogar-de-novo').addEventListener('click', () => comecar(ultimaConfig || lerConfig()));
  const continuar = $('btn-continuar');
  if (continuar) continuar.addEventListener('click', () => { audio(); resumo = null; proximaPergunta(); });

  // Atalhos: 1 a 4 escolhem a resposta; Enter avança.
  document.addEventListener('keydown', (e) => {
    if (telas.jogo.classList.contains('d-none') || e.ctrlKey || e.metaKey || e.altKey) return;
    if (/^[1-4]$/.test(e.key) && !bloqueado) {
      const botao = document.querySelectorAll('.opcao')[Number(e.key) - 1];
      if (botao) botao.click();
    } else if (e.key === 'Enter' && bloqueado) {
      const proxima = $('btn-proxima');
      if (proxima) { if (document.activeElement !== proxima) proxima.click(); }
      else if (autoAvanco) avancar();
    }
  });
})();
