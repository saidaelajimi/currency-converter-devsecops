import React, { useState, useEffect, useCallback } from 'react';
import './converter.css';

const CurrencyConverter = () => {
  const [rates, setRates] = useState({});
  const [amount, setAmount] = useState(1);
  const [fromCurrency, setFromCurrency] = useState('USD');
  const [toCurrency, setToCurrency] = useState('EUR');
  const [convertedAmount, setConvertedAmount] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Use environment variable or fallback to localhost for development
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

  // Fonction de conversion avec useCallback pour éviter les re-créations
  const convertCurrency = useCallback(() => {
    if (!rates[fromCurrency] || !rates[toCurrency]) return;
    const result = (amount / rates[fromCurrency]) * rates[toCurrency];
    setConvertedAmount(result);
  }, [amount, fromCurrency, toCurrency, rates]);

  useEffect(() => {
    fetch(`${API_URL}/rates`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch rates');
        return res.json();
      })
      .then(data => {
        setRates(data.conversion_rates);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching rates:", err);
        setError(err.message);
        setLoading(false);
      });
  }, [API_URL]); // Ajouter API_URL comme dépendance

  useEffect(() => {
    if (Object.keys(rates).length > 0 && amount > 0) {
      convertCurrency();
    }
  }, [amount, fromCurrency, toCurrency, rates, convertCurrency]);

  const handleSwitch = () => {
    setFromCurrency(toCurrency);
    setToCurrency(fromCurrency);
  };

  const handleAmountChange = (e) => {
    const value = e.target.value;
    
    // Allow empty string while typing
    if (value === '') {
      setAmount('');
      return;
    }
    
    // Parse the value and ensure it's a valid number
    const parsedValue = parseFloat(value);
    if (!isNaN(parsedValue) && parsedValue >= 0) {
      setAmount(parsedValue);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading exchange rates...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Error Loading Exchange Rates</h2>
        <p>{error}</p>
        <small>API URL: {API_URL}</small>
        <button 
          className="retry-button"
          onClick={() => window.location.reload()}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="converter-container">
      <header className="converter-header">
        <h1>Currency Converter</h1>
        <p className="subtitle">Real-time exchange rates</p>
      </header>

      <div className="input-section">
        <label htmlFor="amount-input" className="input-label">
          Amount
        </label>
        <input
          id="amount-input"
          type="number"
          value={amount}
          onChange={handleAmountChange}
          placeholder="Enter amount"
          className="converter-input"
          min="0"
          step="any"
          aria-label="Amount to convert"
        />
      </div>

      <div className="currency-row">
        <div className="currency-select-group">
          <label htmlFor="from-currency" className="select-label">
            From
          </label>
          <select
            id="from-currency"
            value={fromCurrency}
            onChange={(e) => setFromCurrency(e.target.value)}
            className="currency-select"
            aria-label="Select source currency"
          >
            {Object.keys(rates).map(curr => (
              <option key={curr} value={curr}>{curr}</option>
            ))}
          </select>
        </div>

        <button 
          className="switch-button" 
          onClick={handleSwitch}
          aria-label="Switch currencies"
          title="Switch currencies"
        >
          ⇄
        </button>

        <div className="currency-select-group">
          <label htmlFor="to-currency" className="select-label">
            To
          </label>
          <select
            id="to-currency"
            value={toCurrency}
            onChange={(e) => setToCurrency(e.target.value)}
            className="currency-select"
            aria-label="Select target currency"
          >
            {Object.keys(rates).map(curr => (
              <option key={curr} value={curr}>{curr}</option>
            ))}
          </select>
        </div>
      </div>

      {convertedAmount !== null && amount > 0 && (
        <div className="converted-result">
          <div className="result-card">
            <h2 className="result-amount">
              {amount} {fromCurrency} = {convertedAmount.toFixed(4)} {toCurrency}
            </h2>
            <p className="converted-rate">
              1 {fromCurrency} = {((1 / rates[fromCurrency]) * rates[toCurrency]).toFixed(6)} {toCurrency}
            </p>
          </div>
        </div>
      )}

      <footer className="converter-footer">
        <div className="timestamp">
          Exchange rates updated: {new Date().toLocaleString()}
        </div>
        <div className="disclaimer">
          Rates provided by ExchangeRate-API. For informational purposes only.
        </div>
      </footer>
    </div>
  );
};

export default CurrencyConverter;