import { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

const PricingSettingsContext = createContext();

export function PricingSettingsProvider({ children }) {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        setLoading(true);
        const data = await api.getGlobalPricingSettings();  // ← Use the api method
        setSettings(data);
        setError(null);
      } catch (err) {
        console.error("Failed to load global pricing settings:", err);
        setError(err.message);
        setSettings({
          addon_roadside_assistance: 50,
          addon_rental_coverage: 75,
          addon_glass_coverage: 30,
          base_premium_percentage: 0.05,
          minimum_premium: 300,
        });
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, []);

  const refreshSettings = async () => {
    setLoading(true);
    try {
      const data = await api.getGlobalPricingSettings(); 
      setSettings(data);
      setError(null);
    } catch (err) {
      console.error("Failed to refresh settings:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <PricingSettingsContext.Provider value={{ settings, loading, error, refreshSettings }}>
      {children}
    </PricingSettingsContext.Provider>
  );
}

export function usePricingSettings() {
  const context = useContext(PricingSettingsContext);
  if (!context) {
    throw new Error('usePricingSettings must be used within PricingSettingsProvider');
  }
  return context;
}