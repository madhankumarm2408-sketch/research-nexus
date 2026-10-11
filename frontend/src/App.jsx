import { useState } from 'react'
import ReactFlow, { Background, Controls } from 'reactflow'
import 'reactflow/dist/style.css'
import { getLayoutedElements } from './layout.js'
import './App.css'

const API = "http://localhost:8000";

const COLORS = {
  paper: "#cce5ff",
  domain: "#fff3cd",
  concept: "#d4edda",
};

function App() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [results, setResults] = useState([]);
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [concepts, setConcepts] = useState([]);
  const [analysisType, setAnalysisType] = useState("");
  const [graphNodes, setGraphNodes] = useState([]);
  const [graphEdges, setGraphEdges] = useState([]);
  const [graphKey, setGraphKey] = useState(0);

  async function runSearch(q) {
    const res = await fetch(`${API}/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    setResults(data.results);
    setSelectedPaper(null);
    setConcepts([]);
  }

  async function loadGraph(q) {
    const res = await fetch(`${API}/graph?q=${encodeURIComponent(q)}`);
    const data = await res.json();

    const rfNodes = data.nodes.map((n) => ({
      id: n.id,
      data: { label: n.label },
      position: { x: 0, y: 0 },
      style: {
        background:
          n.node_type === "paper"
            ? COLORS.paper
            : n.concept_type === "Domain"
            ? COLORS.domain
            : COLORS.concept,
      },
    }));
    const rfEdges = data.edges.map((e, i) => ({
      id: `e${i}`,
      source: e.source,
      target: e.target,
    }));

    const layouted = getLayoutedElements(rfNodes, rfEdges);
    setGraphNodes(layouted.nodes);
    setGraphEdges(layouted.edges);
    setGraphKey((k) => k + 1);
  }

  async function showTopic(q) {
    await runSearch(q);
    await loadGraph(q);
  }

  async function handleSearch() {
    setStatus("");
    try {
      await showTopic(query.trim());
    } catch {
      setStatus("Could not reach the backend. Is uvicorn running?");
    }
  }

  async function handleFetch() {
    const topic = query.trim();
    if (!topic) {
      setStatus("Type a topic first.");
      return;
    }

    try {
      setStatus("Fetching papers from arXiv...");
      const res = await fetch(
        `${API}/import?q=${encodeURIComponent(topic)}&max_results=10`,
        { method: "POST" }
      );

      if (res.ok) {
        const info = await res.json();
        setStatus(`arXiv returned ${info.fetched} papers, ${info.added} new.`);
      } else {
        let reason = "request failed";
        try {
          const err = await res.json();
          if (typeof err.detail === "string") reason = err.detail;
        } catch {
          // response body was not JSON
        }
        setStatus(`Import problem: ${reason}. Showing papers already stored.`);
      }

      await showTopic(topic);
    } catch {
      setStatus("Could not reach the backend. Is uvicorn running?");
    }
  }

  async function handleSelectPaper(paper) {
    setSelectedPaper(paper);
    const res = await fetch(`${API}/analyze/${encodeURIComponent(paper.paper_id)}`);
    const data = await res.json();
    setConcepts(data.concepts);
    setAnalysisType(data.analysis_type);
  }

  const grouped = {};
  concepts.forEach((c) => {
    if (!grouped[c.concept_type]) grouped[c.concept_type] = [];
    grouped[c.concept_type].push(c.concept_name);
  });

  return (
    <>
      <header className="topbar">
        <div className="brand">
          <h1>Research Nexus</h1>
          <span>papers → concepts → meaning</span>
        </div>
        <div className="search">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="Enter a research topic..."
          />
          <button className="btn" onClick={handleSearch}>Search stored</button>
          <button className="btn primary" onClick={handleFetch}>Fetch from arXiv</button>
          <button className="btn ghost" onClick={() => loadGraph("")}>Full graph</button>
        </div>
      </header>

      {status && <div className="status">{status}</div>}

      <main className="workspace">
        <aside className={"sidebar" + (selectedPaper ? " has-detail" : "")}>
          <div className="results-pane">
            <div className="section-label">
              {results.length} {results.length === 1 ? "paper" : "papers"}
            </div>
            {results.length === 0 ? (
              <p className="empty">
                No papers yet. Search the stored papers, or fetch a topic from arXiv.
              </p>
            ) : (
              <ul className="results">
                {results.map((paper) => (
                  <li
                    key={paper.paper_id}
                    className={
                      "result" +
                      (selectedPaper && selectedPaper.paper_id === paper.paper_id ? " active" : "")
                    }
                    onClick={() => handleSelectPaper(paper)}
                  >
                    <div className="result-title">{paper.title}</div>
                    <div className="result-meta">
                      {paper.publication_year} · {paper.source}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {selectedPaper && (
            <div className="detail" key={selectedPaper.paper_id}>
              <h2>{selectedPaper.title}</h2>
              <div className="meta">
                {selectedPaper.authors} · {selectedPaper.publication_year}
              </div>
              <p className="abstract">{selectedPaper.abstract}</p>
              {selectedPaper.paper_id.startsWith("arxiv:") && (
                <a
                  href={`https://arxiv.org/abs/${selectedPaper.paper_id.slice(6)}`}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open on arXiv
                </a>
              )}

              <div className="section-label" style={{ marginTop: "20px" }}>
                Extracted concepts
                {analysisType && <span className="badge">{analysisType.replace("_", " ")}</span>}
              </div>
              {Object.entries(grouped).map(([type, names]) => (
                <div className="concept-group" key={type}>
                  <div className="label">{type}</div>
                  <div className="chips">
                    {names.map((name) => (
                      <span key={name} className={`chip chip-${type.toLowerCase()}`}>
                        {name}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </aside>

        <section className="graph-pane">
          <div className="legend">
            <span><i style={{ background: COLORS.paper }} />Paper</span>
            <span><i style={{ background: COLORS.domain }} />Domain</span>
            <span><i style={{ background: COLORS.concept }} />Concept</span>
          </div>
          {graphNodes.length === 0 && (
            <div className="graph-empty">
              Search or fetch a topic to see its knowledge graph.
            </div>
          )}
          <div className="graph-canvas">
            <ReactFlow key={graphKey} nodes={graphNodes} edges={graphEdges} fitView>
              <Background color="#2a3040" gap={22} />
              <Controls />
            </ReactFlow>
          </div>
        </section>
      </main>
    </>
  )
}

export default App