import { createContext, useContext, useState, useEffect } from 'react';

const CurrencyContext = createContext();

export function CurrencyProvider({ children }) {
  // Default to 25 if nothing in localStorage
  const [conversionRate, setConversionRate] = useState(() => {
    const stored = localStorage.getItem('usd_to_zwg_rate');
    return stored ? parseFloat(stored) : 25;
  });

  // Persist to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('usd_to_zwg_rate', conversionRate.toString());
  }, [conversionRate]);

  const updateConversionRate = (newRate) => {
    const rate = parseFloat(newRate);
    if (!isNaN(rate) && rate > 0) {
      setConversionRate(rate);
      return true;
    }
    return false;
  };

  const value = {
    conversionRate,
    updateConversionRate,
  };

  return (
    <CurrencyContext.Provider value={value}>
      {children}
    </CurrencyContext.Provider>
  );
}

export function useCurrency() {
  const context = useContext(CurrencyContext);
  if (!context) {
    throw new Error('useCurrency must be used within a CurrencyProvider');
  }
  return context;
}