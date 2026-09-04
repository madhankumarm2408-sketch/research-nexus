import dagre from "dagre";

const nodeWidth = 172;
const nodeHeight = 50;

export function getLayoutedElements(nodes,edges){
    const dagreGraph = new dagre.graphlib.Graph();
    dagreGraph.setDefaultEdgeLabel(()=> ({}));
    dagreGraph.setGraph({rankdir:"TB"});

    nodes.forEach((node) => {
        dagreGraph.setNode(node.id, {width:nodeWidth, height:nodeHeight});
    });
    edges.forEach((edge) => {
        dagreGraph.setEdge(edge.source, edge.target);
    });

    dagre.layout(dagreGraph);
    const layoutedNodes = nodes.map((node) => {
    const pos = dagreGraph.node(node.id);
    return {
      ...node,
      position: { x: pos.x - nodeWidth / 2, y: pos.y - nodeHeight / 2 },
    };
  });

  return { nodes: layoutedNodes, edges };

}