import { useState, useEffect } from 'react';
import { DollarSign, RefreshCw, Info, AlertTriangle } from 'lucide-react';
import { useCurrency } from '../../contexts/CurrencyContext';
import { useCurrencyFormatter } from '../../utils/currencyFormatter';

const PREVIEW_AMOUNTS = [10, 50, 100, 500];

export default function CurrencyConversionTab({ companyProfile }) {
  const { conversionRate, updateConversionRate } = useCurrency();
  const { fmtMoney } = useCurrencyFormatter();

  const [tempRate, setTempRate]       = useState(conversionRate);
  const [rateChanged, setRateChanged] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Keep tempRate in sync if the context rate changes externally
  useEffect(() => {
    setTempRate(conversionRate);
  }, [conversionRate]);

  // Track whether the draft differs from the live rate
  useEffect(() => {
    setRateChanged(parseFloat(tempRate) !== parseFloat(conversionRate));
    setSaveSuccess(false);
  }, [tempRate, conversionRate]);

  const handleSave = () => {
    const ok = updateConversionRate(tempRate);
    if (ok) {
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    }
  };

  const handleReset = () => setTempRate(conversionRate);

  const primaryColor   = companyProfile?.primary_color   || '#FF6B4A';
  const secondaryColor = companyProfile?.secondary_color || '#2C3E50';
  const parsedTemp     = parseFloat(tempRate) || 0;

  return (
    <div className="max-w-2xl">

      {/* ── Header ── */}
      <div className="mb-6">
        <h4 className="text-base font-bold mb-1" style={{ color: secondaryColor }}>
          Currency Conversion Rate
        </h4>
        <p className="text-sm" style={{ color: '#7F8C8D' }}>
          Set the exchange rate used throughout the system for USD → ZWG conversions.
        </p>
      </div>

      {/* ── Active Rate Banner ── */}
      <div
        className="rounded-xl p-5 mb-6 flex items-center justify-between"
        style={{ backgroundColor: '#EFF6FF', border: '1px solid #DBEAFE' }}
      >
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider mb-1" style={{ color: '#3B82F6' }}>
            Active Rate
          </p>
          <p className="text-2xl font-bold" style={{ color: secondaryColor }}>
            {fmtMoney(1, 'USD')} = ZWG {conversionRate.toFixed(2)}
          </p>
        </div>
        <div
          className="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: '#DBEAFE' }}
        >
          <DollarSign className="w-6 h-6" style={{ color: '#3B82F6' }} />
        </div>
      </div>

      {/* ── Rate Input Card ── */}
      <div
        className="rounded-xl border-2 p-6 mb-4"
        style={{ borderColor: '#E5E7EB', backgroundColor: '#FFFFFF' }}
      >
        <label
          className="block text-sm font-semibold mb-3"
          htmlFor="rate-input"
          style={{ color: secondaryColor }}
        >
          New Conversion Rate
        </label>

        {/* Input */}
        <div className="relative mb-5">
          <span
            className="absolute left-4 top-1/2 -translate-y-1/2 text-sm font-semibold select-none"
            style={{ color: '#9CA3AF' }}
          >
            1 USD =
          </span>
          <input
            id="rate-input"
            type="number"
            step="0.01"
            min="0.01"
            value={tempRate}
            onChange={(e) => setTempRate(e.target.value)}
            className="w-full pl-20 pr-20 py-3 rounded-lg border-2 text-lg font-bold focus:outline-none transition-colors"
            style={{
              borderColor: rateChanged ? primaryColor : '#E5E7EB',
              color: secondaryColor,
            }}
            placeholder="25.00"
          />
          <span
            className="absolute right-4 top-1/2 -translate-y-1/2 text-sm font-semibold select-none"
            style={{ color: '#9CA3AF' }}
          >
            ZWG
          </span>
        </div>

        {/* Preview grid — uses fmtMoney so formatting stays consistent */}
        <div className="grid grid-cols-4 gap-2 mb-5">
          {PREVIEW_AMOUNTS.map((usd) => (
            <div
              key={usd}
              className="rounded-lg p-3 text-center"
              style={{ backgroundColor: '#F9FAFB', border: '1px solid #E5E7EB' }}
            >
              <p className="text-xs mb-0.5" style={{ color: '#9CA3AF' }}>
                {fmtMoney(usd, 'USD')}
              </p>
              <p className="text-sm font-bold" style={{ color: secondaryColor }}>
                ZWG {(usd * parsedTemp).toFixed(2)}
              </p>
            </div>
          ))}
        </div>

        {/* Unsaved changes warning */}
        {rateChanged && (
          <div
            className="flex items-start gap-2 text-sm rounded-lg p-3 mb-4"
            style={{ backgroundColor: '#FEF3C7', color: '#92400E' }}
          >
            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>
              Unsaved changes — click <strong>Save Rate</strong> to apply.
            </span>
          </div>
        )}

        {/* Success notice */}
        {saveSuccess && (
          <div
            className="flex items-start gap-2 text-sm rounded-lg p-3 mb-4"
            style={{ backgroundColor: '#D1FAE5', color: '#065F46' }}
          >
            <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>Rate updated successfully. Changes are now live across the system.</span>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={handleSave}
            disabled={!rateChanged || parsedTemp <= 0}
            className="flex-1 py-2.5 rounded-lg text-white text-sm font-semibold transition-opacity disabled:opacity-40 disabled:cursor-not-allowed"
            style={{ backgroundColor: primaryColor }}
          >
            Save Rate
          </button>
          <button
            onClick={handleReset}
            disabled={!rateChanged}
            className="flex items-center gap-1.5 px-5 py-2.5 rounded-lg text-sm font-semibold transition-opacity disabled:opacity-40 disabled:cursor-not-allowed"
            style={{ backgroundColor: '#F3F4F6', color: '#6B7280' }}
          >
            <RefreshCw className="w-4 h-4" />
            Reset
          </button>
        </div>
      </div>

    </div>
  );
}