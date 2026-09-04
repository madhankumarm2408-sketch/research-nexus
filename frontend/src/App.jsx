import { useState } from 'react'
import ReactFlow, { Background, Controls } from 'reactflow'
import 'reactflow/dist/style.css'
import { getLayoutedElements } from './layout.js'
import './App.css'

function App() {
  const [count, setCount] = useState(0)
  const [ query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [concepts, setConcepts] = useState([]);
  const [graphNodes, setGraphNodes] = useState([]);
  const [graphEdges, setGraphEdges] = useState([]);

  async function loadGraph(){
    const res = await fetch("http://localhost:8000/graph");
    const data = await res.json();

    const rfNodes = data.nodes.map((n) =>({
      id: n.id,
      data: { label: n.label },
      position: { x: 0, y: 0 },
      style: n.node_type === "paper" ? { background: "#cce5ff" } : { background: "#d4edda"},
    }));
    const rfEdges = data.edges.map((e, i) => ({
    id: `e${i}`,
    source: e.source,
    target: e.target,
  }));

  const layouted = getLayoutedElements(rfNodes, rfEdges);
  setGraphNodes(layouted.nodes);
  setGraphEdges(layouted.edges);

  }
  async function handleSearch(){
    const res = await fetch(`http://localhost:8000/search?q=${query}`);
    const data = await res.json();
    setResults(data.results);
  }
  async function handleSelectedPaper(paper){
    setSelectedPaper(paper);
    const res = await fetch(`http://localhost:8000/analyze/${paper.paper_id}`);
    const data = await res.json();
    setConcepts(data.concepts);
    
  }
  return (
    <>
      <section id="center">
        <h1> Research Nexus</h1>

        <input type="text" value={query}
               onChange={(e) => setQuery(e.target.value)}
               placeholder="Search papers..."
        />
        <button onClick={handleSearch}>Search</button>
        
        <ul>
          {results.map((paper) =>(
            <li key={paper.paper_id} onClick={() => handleSelectedPaper(paper)} style={{cursor:"pointer"}}>
              <strong>{paper.title}</strong> ({paper.publication_year})
            </li>
          ))}
        </ul>
       {selectedPaper && (
          <div>
            <h2>{selectedPaper.title}</h2>
            <p>{selectedPaper.abstract}</p>
            <h3>Extracted Concepts ({selectedPaper.full_text_available ? "full text" : "abstract only"})</h3>
            <ul>
              {concepts.map((c, i) => (
                <li key={i}>
                  <strong>{c.concept_type}:</strong> {c.concept_name}
                </li>
              ))}
            </ul>
          </div>
        )} 
      </section>

      <div style = {{marginTop:"2rem"}}>
        <button onClick={loadGraph}>Load Knowledge Graph</button>
      </div>
      <div style = {{height:"500px", border:"1px solid #444"}}>
        <ReactFlow nodes={graphNodes} edges={graphEdges} fitView>
          <Background />
          <Controls />
        </ReactFlow>
      </div>
    </>
  )
}

export default App
