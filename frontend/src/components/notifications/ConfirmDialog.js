import { memo, useEffect } from 'react';
import { AlertTriangle, X } from 'lucide-react';

export const ConfirmDialog = memo(function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  onCancel,
  type = 'danger',
}) {
  // Handle escape key
  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onCancel();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  const typeStyles = {
    danger: {
      iconColor: '#DC2626',
      iconBg: '#FEE2E2',
      confirmBg: '#DC2626',
      confirmHover: '#B91C1C',
    },
    warning: {
      iconColor: '#D97706',
      iconBg: '#FEF3C7',
      confirmBg: '#D97706',
      confirmHover: '#B45309',
    },
    info: {
      iconColor: '#2563EB',
      iconBg: '#DBEAFE',
      confirmBg: '#2563EB',
      confirmHover: '#1D4ED8',
    },
  };

  const style = typeStyles[type] || typeStyles.danger;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onCancel}
        style={{ animation: 'fadeIn 0.2s ease-out' }}
      />

      {/* Dialog */}
      <div
        className="relative bg-white rounded-xl shadow-2xl max-w-md w-full"
        style={{ animation: 'scaleIn 0.2s ease-out' }}
        role="dialog"
        aria-modal="true"
        aria-labelledby="dialog-title"
        aria-describedby="dialog-description"
      >
        {/* Header */}
        <div className="p-6 border-b" style={{ borderColor: '#E5E7EB' }}>
          <div className="flex items-start justify-between">
            <div className="flex items-center">
              <div
                className="p-3 rounded-full mr-4"
                style={{ backgroundColor: style.iconBg }}
              >
                <AlertTriangle
                  className="w-6 h-6"
                  style={{ color: style.iconColor }}
                />
              </div>
              <h3 
                id="dialog-title"
                className="text-xl font-bold" 
                style={{ color: '#2C3E50' }}
              >
                {title}
              </h3>
            </div>
            <button
              onClick={onCancel}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              aria-label="Close dialog"
            >
              <X className="w-5 h-5" style={{ color: '#7F8C8D' }} />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="p-6">
          <p 
            id="dialog-description"
            className="text-base" 
            style={{ color: '#7F8C8D' }}
          >
            {message}
          </p>
        </div>

        {/* Footer */}
        <div className="p-6 border-t flex justify-end gap-3" style={{ borderColor: '#E5E7EB' }}>
          <button
            onClick={onCancel}
            className="px-6 py-2.5 rounded-lg font-medium transition-all hover:bg-gray-100"
            style={{
              backgroundColor: '#F8F9FA',
              color: '#7F8C8D',
            }}
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            className="px-6 py-2.5 rounded-lg font-medium text-white transition-all shadow-md hover:shadow-lg"
            style={{
              backgroundColor: style.confirmBg,
            }}
            onMouseEnter={(e) => {
              e.target.style.backgroundColor = style.confirmHover;
            }}
            onMouseLeave={(e) => {
              e.target.style.backgroundColor = style.confirmBg;
            }}
          >
            {confirmText}
          </button>
        </div>
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        
        @keyframes scaleIn {
          from {
            opacity: 0;
            transform: scale(0.95);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }
      `}</style>
    </div>
  );
});