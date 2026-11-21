// Mapas dos países: recorte (ou globo) com o país destacado. Usa d3-geo + topojson-client e
// os contornos de static/core/data/mundo.json (gerado por tools/gerar_mapa.mjs).
window.Mapa = (() => {
  const L = 400;
  const A = 300;
  let dados = null;
  let promessa = null;

  function carregar(url) {
    if (dados) return Promise.resolve(dados);
    if (!window.d3 || !window.topojson) return Promise.reject(new Error('Não foi possível carregar a biblioteca de mapas. Verifique sua conexão.'));
    if (!promessa) {
      promessa = fetch(url)
        .then((r) => { if (!r.ok) throw new Error('Não foi possível carregar os mapas.'); return r.json(); })
        .then((topo) => {
          const geo = window.topojson.feature(topo, topo.objects.paises);
          const porCodigo = {};
          geo.features.forEach((f) => { if (f.properties && f.properties.c) porCodigo[f.properties.c] = f; });
          dados = { terra: geo.features, porCodigo, vistas: topo.vistas, grade: window.d3.geoGraticule10() };
          return dados;
        })
        .catch((e) => { promessa = null; throw e; });
    }
    return promessa;
  }

  function moldura() {
    let ticks = '';
    for (let x = 25; x < L; x += 25) ticks += `M${x} 3v5M${x} ${A - 3}v-5`;
    for (let y = 25; y < A; y += 25) ticks += `M3 ${y}h5M${L - 3} ${y}h-5`;
    return `<rect class="mapa-moldura" x="3" y="3" width="${L - 6}" height="${A - 6}"/><path class="mapa-ticks" d="${ticks}"/>
      <g class="mapa-rosa" transform="translate(${L - 38} ${A - 40})"><path d="M0-17L4-4 17 0 4 4 0 17-4 4-17 0-4-4Z"/><path class="norte" d="M0-17L4-4H-4Z"/><text y="-21" text-anchor="middle">N</text></g>`;
  }

  // Desenha o país `codigo` (ISO2 minúsculo) dentro do <svg>. Os dados precisam ter sido carregados.
  function desenhar(svg, codigo) {
    const d3 = window.d3;
    const v = dados && dados.vistas[codigo];
    if (!v) { svg.innerHTML = ''; return; }
    const [lon, lat, raio] = v;
    const globo = raio >= 55;
    const proj = d3.geoOrthographic().rotate([-lon, -lat]).translate([L / 2, A / 2]).precision(0.4);
    if (globo) {
      proj.scale(A / 2 - 10);
    } else {
      proj.scale((L / 2) / Math.sin((raio * Math.PI) / 180)).clipExtent([[0, 0], [L, A]]);
    }
    const caminho = d3.geoPath(proj);
    const alvo = dados.porCodigo[codigo];

    let terra = '';
    dados.terra.forEach((f) => { if (f !== alvo) terra += caminho(f) || ''; });

    let marca = '';
    let tamanho = 0;
    let area = 0;
    if (alvo) {
      const b = caminho.bounds(alvo);
      tamanho = Math.max(b[1][0] - b[0][0], b[1][1] - b[0][1]);
      area = caminho.area(alvo);
    }
    if (!alvo || tamanho < 24 || area < 450) { // país minúsculo ou arquipélago de pontinhos: mira
      const p = proj([lon, lat]);
      if (p) {
        marca = `<g transform="translate(${p[0].toFixed(1)} ${p[1].toFixed(1)})"><circle class="mapa-anel pulso" r="14"/><circle class="mapa-anel" r="14"/>
          <path class="mapa-mira" d="M-24 0H-10M10 0H24M0-24V-10M0 10V24"/></g>`;
      }
    }

    svg.setAttribute('viewBox', `0 0 ${L} ${A}`);
    svg.innerHTML = `<rect class="mapa-fundo${globo ? ' globo' : ''}" width="${L}" height="${A}"/>`
      + (globo ? `<path class="mapa-esfera" d="${caminho({ type: 'Sphere' })}"/>` : '')
      + `<path class="mapa-grade" d="${caminho(dados.grade)}"/>`
      + `<path class="mapa-terra" d="${terra}"/>`
      + (alvo ? `<path class="mapa-alvo" d="${caminho(alvo) || ''}"/>` : '')
      + marca + moldura();
  }

  return { carregar, desenhar };
})();
