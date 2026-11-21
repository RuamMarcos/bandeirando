// Painel de estatísticas: gráficos com Chart.js.
(() => {
  const fonte = document.getElementById('dados-grafico');
  if (!fonte || typeof Chart === 'undefined') return;
  const dados = JSON.parse(fonte.textContent);
  let graficos = [];

  function cores() {
    const css = getComputedStyle(document.documentElement);
    return {
      texto: getComputedStyle(document.body).color,
      grade: css.getPropertyValue('--borda').trim(),
      azul: css.getPropertyValue('--azul').trim(),
    };
  }

  function desenhar() {
    graficos.forEach((g) => g.destroy());
    const c = cores();
    Chart.defaults.color = c.texto;
    Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;

    graficos = [new Chart(document.getElementById('grafico-pontos'), {
      type: 'bar',
      data: {
        labels: dados.rotulos,
        datasets: [{ label: 'Pontos', data: dados.pontos, backgroundColor: c.azul, borderRadius: 6, maxBarThickness: 28 }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 7 } },
          y: { beginAtZero: true, grid: { color: c.grade }, ticks: { precision: 0 } },
        },
      },
    })];
  }

  desenhar();
  document.addEventListener('tema-alterado', () => setTimeout(desenhar, 50));
})();
