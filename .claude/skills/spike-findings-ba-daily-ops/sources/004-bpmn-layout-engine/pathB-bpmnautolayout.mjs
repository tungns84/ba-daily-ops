// Path B: logical model -> standard BPMN 2.0 XML (semantic, no DI, with lanes) -> bpmn-auto-layout (adds DI) -> .bpmn
import { layoutProcess } from 'bpmn-auto-layout';
import { readFileSync, writeFileSync } from 'node:fs';

const model = JSON.parse(readFileSync(new URL('./model.json', import.meta.url)));
const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');

const tag = { start: 'startEvent', end: 'endEvent', gateway: 'exclusiveGateway', task: 'task' };
const incoming = id => model.edges.filter(e => e.target === id).map(e => `<bpmn:incoming>${e.id}</bpmn:incoming>`).join('');
const outgoing = id => model.edges.filter(e => e.source === id).map(e => `<bpmn:outgoing>${e.id}</bpmn:outgoing>`).join('');

const flowNodes = model.nodes.map(n =>
  `<bpmn:${tag[n.type]} id="${n.id}" name="${esc(n.label)}">${incoming(n.id)}${outgoing(n.id)}</bpmn:${tag[n.type]}>`
).join('\n');

const flows = model.edges.map(e =>
  `<bpmn:sequenceFlow id="${e.id}" sourceRef="${e.source}" targetRef="${e.target}"${e.label?` name="${esc(e.label)}"`:''}/>`
).join('\n');

const lanes = model.lanes.map((lane, i) => {
  const refs = model.nodes.filter(n => n.lane === lane).map(n => `<bpmn:flowNodeRef>${n.id}</bpmn:flowNodeRef>`).join('');
  return `<bpmn:lane id="lane_${i}" name="${esc(lane)}">${refs}</bpmn:lane>`;
}).join('\n');

const bpmn = `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="defs_1" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_1" isExecutable="false">
    <bpmn:laneSet id="ls_1">
${lanes}
    </bpmn:laneSet>
${flowNodes}
${flows}
  </bpmn:process>
</bpmn:definitions>`;

writeFileSync(new URL('./pathB-input.bpmn', import.meta.url), bpmn);

try {
  const laidOut = await layoutProcess(bpmn);
  writeFileSync(new URL('./pathB.bpmn', import.meta.url), laidOut);
  const hasDI = laidOut.includes('BPMNDiagram') && laidOut.includes('BPMNShape');
  const hasLaneShape = laidOut.includes('lane_0') && /BPMNShape[^>]*lane_0/.test(laidOut);
  console.log('layoutProcess OK. DI present:', hasDI, '| lane shapes:', hasLaneShape);
  console.log('bytes:', laidOut.length);
} catch (err) {
  console.error('layoutProcess FAILED:', err.message);
  process.exit(3);
}
