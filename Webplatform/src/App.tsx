import { useState } from 'react';
import CalculatorForm from './components/CalculatorForm';
import ResultsDisplay from './components/ResultsDisplay';

// This is a placeholder for the actual response type, 
// which should be imported or defined more accurately based on your API.
type CalculationResults = any; 

function App() {
  const [results, setResults] = useState<CalculationResults | null>(null);

  return (
    <div className="App" style={{ padding: '20px' }}>
      <header className="App-header">
        <h1>Калькулятор</h1>
      </header>
      <main>
        <CalculatorForm onCalculateSuccess={(data) => setResults(data)} />
        {results && <ResultsDisplay results={results} />}
      </main>
    </div>
  )
}

export default App;
