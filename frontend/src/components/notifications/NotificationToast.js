import { memo } from 'react';
import { CheckCircle, AlertTriangle, Info, X, XCircle } from 'lucide-react';

export const NotificationToast = memo(function NotificationToast({ message, type = 'success', onClose }) {
  const styles = {
    success: {
      bg: '#10B981',
      text: '#FFFFFF',
      icon: CheckCircle,
    },
    error: {
      bg: '#EF4444',
      text: '#FFFFFF',
      icon: XCircle,
    },
    warning: {
      bg: '#F59E0B',
      text: '#FFFFFF',
      icon: AlertTriangle,
    },
    info: {
      bg: '#3B82F6',
      text: '#FFFFFF',
      icon: Info,
    },
  };

  const config = styles[type] || styles.info;
  const Icon = config.icon;

  return (
    <div
      className="animate-slide-in"
      style={{
        maxWidth: '400px',
        animation: 'slideInRight 0.3s ease-out',
      }}
    >
      <div
        className="p-4 rounded-lg shadow-lg flex items-center justify-between gap-3"
        style={{
          backgroundColor: config.bg,
          color: config.text,
        }}
      >
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <Icon className="w-5 h-5 flex-shrink-0" />
          <span className="font-medium text-sm break-words">{message}</span>
        </div>
        <button
          onClick={onClose}
          className="flex-shrink-0 p-1 rounded hover:bg-white hover:bg-opacity-20 transition-colors"
          aria-label="Close notification"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
      
      <style>{`
        @keyframes slideInRight {
          from {
            opacity: 0;
            transform: translateX(100px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
      `}</style>
    </div>
  );
});