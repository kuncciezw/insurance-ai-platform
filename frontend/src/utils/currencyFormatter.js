import { useCurrency } from '../contexts/CurrencyContext';

/**
 * Custom hook for currency formatting and conversion
 * @returns {Object} Currency utilities
 */
export function useCurrencyFormatter() {
  const { conversionRate } = useCurrency();

  /**
   * Format money with proper currency symbol
   * @param {number|string} usdAmount - Amount in USD
   * @param {string} curr - Currency code ('USD' or 'ZWG')
   * @returns {string} Formatted currency string
   */
  const fmtMoney = (usdAmount, curr = 'USD') => {
    if (usdAmount == null || usdAmount === '') {
      return curr === 'USD' ? '$—' : 'ZWG —';
    }
    const n = parseFloat(usdAmount);
    if (isNaN(n)) return '—';
    
    const value = curr === 'ZWG' ? n * conversionRate : n;
    const formatted = value.toLocaleString('en-US', { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    });
    
    return curr === 'USD' ? `$${formatted}` : `ZWG ${formatted}`;
  };

  /**
   * Convert USD to ZWG
   * @param {number} usdAmount - Amount in USD
   * @returns {number} Amount in ZWG
   */
  const usdToZwg = (usdAmount) => {
    return parseFloat(usdAmount || 0) * conversionRate;
  };

  /**
   * Convert ZWG to USD
   * @param {number} zwgAmount - Amount in ZWG
   * @returns {number} Amount in USD
   */
  const zwgToUsd = (zwgAmount) => {
    return parseFloat(zwgAmount || 0) / conversionRate;
  };

  return {
    fmtMoney,
    usdToZwg,
    zwgToUsd,
    conversionRate,
  };
}