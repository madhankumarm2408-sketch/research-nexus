import {
  forceSimulation,
  forceLink,
  forceManyBody,
  forceCenter,
  forceCollide,
} from "d3-force";

export function getLayoutedElements(nodes, edges) {
  const simNodes = nodes.map((n) => ({ id: n.id }));
  const simLinks = edges.map((e) => ({ source: e.source, target: e.target }));

  const simulation = forceSimulation(simNodes)
    .force("link", forceLink(simLinks).id((d) => d.id).distance(150).strength(0.7))
    .force("charge", forceManyBody().strength(-700))
    .force("center", forceCenter(0, 0))
    .force("collide", forceCollide(90))
    .stop();

  for (let i = 0; i < 300; i++) simulation.tick();

  const positions = new Map(simNodes.map((n) => [n.id, n]));

  const layoutedNodes = nodes.map((node) => {
    const p = positions.get(node.id);
    return { ...node, position: { x: p.x, y: p.y } };
  });

  return { nodes: layoutedNodes, edges };
}