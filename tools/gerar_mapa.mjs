// Gera core/static/core/data/mundo.json: contornos dos países (Natural Earth 1:50m, domínio público)
// + para cada país da lista uma "vista" [longitude, latitude, raio em graus, sem_geometria].
// Uso: cd tools && npm install && node gerar_mapa.mjs
import fs from 'node:fs';
import { createRequire } from 'node:module';
import { feature } from 'topojson-client';
import { geoArea, geoCentroid, geoDistance } from 'd3-geo';

const require = createRequire(import.meta.url);
const topo = JSON.parse(fs.readFileSync(require.resolve('world-atlas/countries-50m.json'), 'utf8'));
const mundo = require('world-countries');

const py = fs.readFileSync(new URL('../core/dados_paises.py', import.meta.url), 'utf8');
const codigos = [...py.matchAll(/^([a-z]{2})\|/gm)].map((m) => m[1]);

const infoPorCodigo = Object.fromEntries(mundo.map((c) => [c.cca2.toLowerCase(), c]));
const codigoPorNumero = Object.fromEntries(
  mundo.filter((c) => codigos.includes(c.cca2.toLowerCase())).map((c) => [String(Number(c.ccn3)), c.cca2.toLowerCase()]),
);

const geoms = topo.objects.countries.geometries;
const achados = {};
geoms.forEach((g) => {
  const cod = g.id !== undefined ? codigoPorNumero[String(Number(g.id))] : undefined;
  g.properties = cod ? { c: cod } : {};
  if (cod) achados[cod] = g;
  delete g.id;
});

const rad = (g) => (g * Math.PI) / 180;
const grau = (r) => (r * 180) / Math.PI;
const vistas = {};
const semGeometria = [];
for (const cod of codigos) {
  const [lat, lon] = infoPorCodigo[cod].latlng;
  const centro = [lon, lat];
  const g = achados[cod];
  let ext = 0;
  if (g) {
    const f = feature(topo, g);
    const partes = f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates;
    for (const coords of partes) {
      const p = { type: 'Feature', geometry: { type: 'Polygon', coordinates: coords } };
      const d = geoDistance(centro, geoCentroid(p));
      const r = Math.sqrt(geoArea(p) / Math.PI);
      if (d < 0.7) ext = Math.max(ext, d + r);
    }
  } else {
    semGeometria.push(cod);
  }
  const raio = Math.min(90, Math.max(6, grau(ext) * 1.8));
  vistas[cod] = [Math.round(lon * 10) / 10, Math.round(lat * 10) / 10, Math.round(raio * 10) / 10, g ? 0 : 1];
}

const saida = { type: 'Topology', arcs: topo.arcs, transform: topo.transform, objects: { paises: topo.objects.countries }, vistas };
fs.writeFileSync(new URL('../core/static/core/data/mundo.json', import.meta.url), JSON.stringify(saida));
console.log('países:', codigos.length, '| com geometria:', codigos.length - semGeometria.length, '| sem geometria:', semGeometria.join(', ') || '-');
