import { useState } from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import './App.css';

function App() {
  const [count, setCount] = useState(0);

  return (
    <div className="App">
      <nav>
        <ul>
          <li>
            <Link to="/">Home</Link>
          </li>
          <li>
            <Link to="/dashboard">Dashboard</Link>
          </li>
          <li>
            <Link to="/ingestion">Ingestion</Link>
          </li>
        </ul>
      </nav>

      <header className="App-header">
        <h1>Material Ingestion Frontend</h1>
        <p>Welcome to the Material Ingestion Pipeline UI.</p>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<div>Home Page Content</div>} />
          <Route path="/dashboard" element={<div>Dashboard View</div>} />
          <Route path="/ingestion" element={<div>Ingestion Workflow</div>} />
          <Route path="*" element={<div>404 Not Found</div>} />
        </Routes>

        <div className="card">
          <button onClick={() => setCount((count) => count + 1)}>
            count is {count}
          </button>
          <p>
            Edit <code>src/App.tsx</code> and save to test HMR
          </p>
        </div>
      </main>

      <footer>
        <p>&copy; 2024 Material Ingestion Pipeline</p>
      </footer>
    </div>
  );
}

export default App;
