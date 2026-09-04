import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import heroImg from './assets/hero.png'
import './App.css'

function App() {
  const [count, setCount] = useState(0)
  const [ query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [concepts, setConcepts] = useState([]);

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

      <div className="ticks"></div>

      <section id="next-steps">
        <div id="docs">
          <svg className="icon" role="presentation" aria-hidden="true">
            <use href="/icons.svg#documentation-icon"></use>
          </svg>
          <h2>Documentation</h2>
          <p>Your questions, answered</p>
          <ul>
            <li>
              <a href="https://vite.dev/" target="_blank">
                <img className="logo" src={viteLogo} alt="" />
                Explore Vite
              </a>
            </li>
            <li>
              <a href="https://react.dev/" target="_blank">
                <img className="button-icon" src={reactLogo} alt="" />
                Learn more
              </a>
            </li>
          </ul>
        </div>
        <div id="social">
          <svg className="icon" role="presentation" aria-hidden="true">
            <use href="/icons.svg#social-icon"></use>
          </svg>
          <h2>Connect with us</h2>
          <p>Join the Vite community</p>
          <ul>
            <li>
              <a href="https://github.com/vitejs/vite" target="_blank">
                <svg
                  className="button-icon"
                  role="presentation"
                  aria-hidden="true"
                >
                  <use href="/icons.svg#github-icon"></use>
                </svg>
                GitHub
              </a>
            </li>
            <li>
              <a href="https://chat.vite.dev/" target="_blank">
                <svg
                  className="button-icon"
                  role="presentation"
                  aria-hidden="true"
                >
                  <use href="/icons.svg#discord-icon"></use>
                </svg>
                Discord
              </a>
            </li>
            <li>
              <a href="https://x.com/vite_js" target="_blank">
                <svg
                  className="button-icon"
                  role="presentation"
                  aria-hidden="true"
                >
                  <use href="/icons.svg#x-icon"></use>
                </svg>
                X.com
              </a>
            </li>
            <li>
              <a href="https://bsky.app/profile/vite.dev" target="_blank">
                <svg
                  className="button-icon"
                  role="presentation"
                  aria-hidden="true"
                >
                  <use href="/icons.svg#bluesky-icon"></use>
                </svg>
                Bluesky
              </a>
            </li>
          </ul>
        </div>
      </section>

      <div className="ticks"></div>
      <section id="spacer"></section>
    </>
  )
}

export default App
