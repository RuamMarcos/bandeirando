// Página "Aprender": grade, slides, busca, várias regiões, modo estudo e detalhes.
(() => {
  const grade = document.getElementById('grade-paises');
  if (!grade) return;

  const $ = (id) => document.getElementById(id);
  const colunas = [...grade.querySelectorAll('.pais-col')];
  const busca = $('busca');
  const chips = [...document.querySelectorAll('[data-filtro-continente]')];
  const chipTodos = chips.find((c) => c.dataset.filtroContinente === '');
  const contador = $('contador');
  const vazio = $('sem-resultados');
  const modoEstudo = $('modo-estudo');
  const modoSlides = $('modo-slides');
  const btnEmbaralhar = $('btn-embaralhar');
  const btnOrdenar = $('btn-ordenar');
  const secaoSlide = $('modo-slide');
  const modal = new bootstrap.Modal($('modal-pais'));
  function desenharMapa(id, codigo) {
    const svg = $(id);
    if (!window.Mapa) { svg.classList.add('d-none'); return; }
    window.Mapa.carregar(grade.dataset.urlMapa)
      .then(() => { svg.classList.remove('d-none'); window.Mapa.desenhar(svg, codigo.toLowerCase()); })
      .catch(() => svg.classList.add('d-none'));
  }
  const norm = (s) => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const embaralhar = (lista) => {
    for (let i = lista.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [lista[i], lista[j]] = [lista[j], lista[i]];
    }
    return lista;
  };

  colunas.forEach((c) => { c.dataset.texto = norm(`${c.dataset.nome} ${c.dataset.capital}`); });
  const regioes = new Set(); // regiões escolhidas (vazio = todas)

  function treinoHtml(d) {
    const a = Number(d.acertos), er = Number(d.erros);
    if (a + er === 0) return '<span class="text-body-secondary">Ainda não treinado</span>';
    const selo = d.status === 'aprendido' ? ' <span class="badge text-bg-success">aprendido</span>' : '';
    return `<span class="text-success fw-bold"><i class="bi bi-check-lg"></i> ${a}</span> <span class="text-danger fw-bold ms-2"><i class="bi bi-x-lg"></i> ${er}</span>${selo}`;
  }

  // ---------- filtros ----------
  const visiveis = () => colunas.filter((c) => !c.classList.contains('d-none'));

  function filtrar() {
    const termo = norm(busca.value.trim());
    colunas.forEach((c) => {
      const ok = (!regioes.size || regioes.has(c.dataset.continente)) && (!termo || c.dataset.texto.includes(termo));
      c.classList.toggle('d-none', !ok);
    });
    const n = visiveis().length;
    contador.textContent = n;
    vazio.classList.toggle('d-none', n > 0);
    if (modoSlides.checked) montarFila();
  }

  function marcarChips() {
    chips.forEach((chip) => {
      const chave = chip.dataset.filtroContinente;
      const ativo = chave === '' ? regioes.size === 0 : regioes.has(chave);
      chip.classList.toggle('active', ativo);
      chip.setAttribute('aria-pressed', ativo);
    });
  }

  busca.addEventListener('input', filtrar);
  chips.forEach((chip) => chip.addEventListener('click', () => {
    const chave = chip.dataset.filtroContinente;
    if (chave === '') regioes.clear();                       // "Todos" limpa a seleção
    else if (regioes.has(chave)) regioes.delete(chave);      // clicar de novo desmarca
    else regioes.add(chave);
    marcarChips();
    filtrar();
  }));

  modoEstudo.addEventListener('change', () => {
    grade.classList.toggle('modo-estudo', modoEstudo.checked);
    grade.querySelectorAll('.card-pais.revelado').forEach((c) => c.classList.remove('revelado'));
    if (modoSlides.checked) ocultarSlide();
  });

  // ---------- grade ----------
  const reordenar = (lista) => lista.forEach((c) => grade.appendChild(c));
  btnEmbaralhar.addEventListener('click', () => {
    reordenar(embaralhar([...colunas]));
    btnOrdenar.classList.remove('d-none');
  });
  btnOrdenar.addEventListener('click', () => {
    reordenar([...colunas].sort((a, b) => a.dataset.ordem - b.dataset.ordem));
    btnOrdenar.classList.add('d-none');
  });

  grade.addEventListener('click', (e) => {
    const botao = e.target.closest('.card-pais');
    if (!botao) return;
    // No modo estudo o clique revela o nome; fora dele, abre os detalhes.
    if (grade.classList.contains('modo-estudo') && !botao.classList.contains('revelado')) {
      botao.classList.add('revelado');
      return;
    }
    const d = botao.closest('.pais-col').dataset;
    $('modal-nome').textContent = d.nome;
    const img = $('modal-bandeira');
    img.src = d.flag;
    img.alt = `Bandeira de ${d.nome}`;
    $('modal-capital').textContent = d.capital;
    $('modal-regiao').textContent = d.regiao;
    $('modal-codigo').textContent = d.codigo;
    if ($('modal-treino')) $('modal-treino').innerHTML = treinoHtml(d);
    desenharMapa('modal-mapa', d.codigo);
    modal.show();
  });

  // ---------- slides ----------
  const info = $('slide-info');
  const aleatorio = $('slide-aleatorio');
  let fila = [];
  let pos = 0;

  function montarFila() {
    const lista = visiveis().sort((a, b) => a.dataset.ordem - b.dataset.ordem);
    fila = aleatorio.checked ? embaralhar(lista) : lista;
    pos = 0;
    mostrarSlide();
  }

  function ocultarSlide() {
    const ocultar = modoEstudo.checked && fila.length > 0;
    info.classList.toggle('oculto', ocultar);
    $('slide-revelar').classList.toggle('d-none', !ocultar);
  }

  function mostrarSlide() {
    if (!fila.length) {
      $('slide-bandeira').removeAttribute('src');
      $('slide-nome').textContent = 'Nenhum país encontrado';
      ['capital', 'regiao', 'codigo', 'treino'].forEach((k) => { if ($(`slide-${k}`)) $(`slide-${k}`).textContent = ''; });
      $('slide-contador').textContent = '';
      $('slide-mapa').innerHTML = '';
      ocultarSlide();
      return;
    }
    const d = fila[pos].dataset;
    const img = $('slide-bandeira');
    img.src = d.flag;
    img.alt = modoEstudo.checked ? 'Bandeira a ser identificada' : `Bandeira de ${d.nome}`;
    $('slide-nome').textContent = d.nome;
    $('slide-capital').textContent = d.capital;
    $('slide-regiao').textContent = d.regiao;
    $('slide-codigo').textContent = d.codigo;
    if ($('slide-treino')) $('slide-treino').innerHTML = treinoHtml(d);
    $('slide-contador').textContent = `${pos + 1} de ${fila.length}`;
    desenharMapa('slide-mapa', d.codigo);
    ocultarSlide();
  }

  function mover(passo) {
    if (!fila.length) return;
    const novo = pos + passo;
    if (novo >= fila.length) {
      if (aleatorio.checked) embaralhar(fila); // nova rodada aleatória
      pos = 0;
    } else {
      pos = novo < 0 ? fila.length - 1 : novo;
    }
    mostrarSlide();
  }

  modoSlides.addEventListener('change', () => {
    const slide = modoSlides.checked;
    secaoSlide.classList.toggle('d-none', !slide);
    grade.classList.toggle('d-none', slide);
    $('acoes-grade').classList.toggle('d-none', slide);
    if (slide) montarFila();
  });
  $('slide-proximo').addEventListener('click', () => mover(1));
  $('slide-anterior').addEventListener('click', () => mover(-1));
  $('slide-revelar').addEventListener('click', () => {
    info.classList.remove('oculto');
    $('slide-revelar').classList.add('d-none');
  });
  aleatorio.addEventListener('change', montarFila);

  document.addEventListener('keydown', (e) => {
    if (!modoSlides.checked || e.ctrlKey || e.metaKey || e.altKey) return;
    const alvo = document.activeElement;
    if (alvo && alvo.tagName === 'INPUT' && alvo.type === 'search') return;
    if (e.key === 'ArrowRight') { e.preventDefault(); mover(1); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); mover(-1); }
  });
})();
