// Path A: logical model -> ELK layered (x-layering, no-overlap) -> deterministic lane bands (y) -> draw.io XML
import ELK from 'elkjs/lib/elk.bundled.js';
import { readFileSync, writeFileSync } from 'node:fs';

const model = JSON.parse(readFileSync(new URL('./model.json', import.meta.url)));

const DIM = { start: [40, 40], end: [40, 40], gateway: [50, 50], task: [150, 60] };
const LANE_H = 180, LANE_LABEL_W = 30, POOL_X = 40, POOL_Y = 40, INNER_PAD = 40;

const elk = new ELK();
const elkGraph = {
  id: 'root',
  layoutOptions: {
    'elk.algorithm': 'layered',
    'elk.direction': 'RIGHT',
    'elk.layered.spacing.nodeNodeBetweenLayers': '70',
    'elk.spacing.nodeNode': '50',
    'elk.edgeRouting': 'ORTHOGONAL',
  },
  children: model.nodes.map(n => ({ id: n.id, width: DIM[n.type][0], height: DIM[n.type][1] })),
  edges: model.edges.map(e => ({ id: e.id, sources: [e.source], targets: [e.target] })),
};

const laid = await elk.layout(elkGraph);
const elkPos = Object.fromEntries(laid.children.map(c => [c.id, c]));

// ELK gives X (layer ordering). Y comes from the node's lane band (deterministic, no cross-lane drift).
const laneIndex = Object.fromEntries(model.lanes.map((l, i) => [l, i]));
const nodeById = Object.fromEntries(model.nodes.map(n => [n, n].map(()=>n)[0] && [n.id, n]).map(x=>x));
const byId = Object.fromEntries(model.nodes.map(n => [n.id, n]));

const maxX = Math.max(...laid.children.map(c => c.x + c.width));
const poolW = LANE_LABEL_W + INNER_PAD + maxX + INNER_PAD + 60;
const poolH = model.lanes.length * LANE_H;

const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
const style = {
  start: 'ellipse;html=1;fillColor=#d5e8d4;strokeColor=#82b366;',
  end:   'ellipse;html=1;fillColor=#f8cecc;strokeColor=#b85450;strokeWidth=3;',
  gateway:'rhombus;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;',
  task:  'rounded=1;whiteSpace=wrap;html=1;arcSize=20;fillColor=#dae8fc;strokeColor=#6c8ebf;',
};

let cells = '';
// pool
cells += `<mxCell id="pool" value="${esc(model.pool)}" style="swimlane;html=1;horizontal=0;startSize=30;fillColor=none;strokeColor=#333333;fontStyle=1;" vertex="1" parent="1"><mxGeometry x="${POOL_X}" y="${POOL_Y}" width="${poolW}" height="${poolH}" as="geometry"/></mxCell>\n`;
// lanes (children of pool)
model.lanes.forEach((lane, i) => {
  cells += `<mxCell id="lane_${i}" value="${esc(lane)}" style="swimlane;html=1;horizontal=0;startSize=${LANE_LABEL_W};fillColor=none;strokeColor=#999999;" vertex="1" parent="pool"><mxGeometry x="0" y="${i*LANE_H}" width="${poolW}" height="${LANE_H}" as="geometry"/></mxCell>\n`;
});
// nodes (children of their lane), x from ELK, y centered in lane band
for (const n of model.nodes) {
  const [w, h] = DIM[n.type];
  const li = laneIndex[n.lane];
  const x = LANE_LABEL_W + INNER_PAD + elkPos[n.id].x;
  const y = (LANE_H - h) / 2;            // centered within its lane
  cells += `<mxCell id="${n.id}" value="${esc(n.label)}${n.req_ids?'&#10;('+n.req_ids.join(',')+')':''}" style="${style[n.type]}" vertex="1" parent="lane_${li}"><mxGeometry x="${x}" y="${y}" width="${w}" height="${h}" as="geometry"/></mxCell>\n`;
}
// edges (parent pool; draw.io orthogonal routing between cross-lane cells)
for (const e of model.edges) {
  cells += `<mxCell id="${e.id}" value="${e.label?esc(e.label):''}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;" edge="1" parent="pool" source="${e.source}" target="${e.target}"><mxGeometry relative="1" as="geometry"/></mxCell>\n`;
}

const xml = `<mxfile host="spike"><diagram id="A" name="Path A ELK">
<mxGraphModel dx="1200" dy="800" grid="0" page="1" pageWidth="${poolW+120}" pageHeight="${poolH+120}" math="0" shadow="0">
<root><mxCell id="0"/><mxCell id="1" parent="0"/>
${cells}</root></mxGraphModel></diagram></mxfile>`;

writeFileSync(new URL('./pathA.drawio', import.meta.url), xml);
console.log('pathA.drawio written; pool', poolW+'x'+poolH, 'maxX', maxX);
console.log('ELK node X:', model.nodes.map(n=>`${n.id}:${Math.round(elkPos[n.id].x)}`).join(' '));
