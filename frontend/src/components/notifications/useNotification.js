import { useState, useRef, useCallback, useEffect } from 'react';
import { NotificationToast } from './NotificationToast';

export function useNotification() {
  const [notifications, setNotifications] = useState([]);
  const notificationIdRef = useRef(0);
  const recentNotificationsRef = useRef(new Map());
  const timeoutsRef = useRef(new Map());

  const showNotification = useCallback((message, type = 'success', duration = 5000) => {
    // Create a unique key for this notification
    const notificationKey = `${type}:${message}`;
    const now = Date.now();
    
    // Check if this exact notification was shown recently (within 2 seconds)
    const lastShown = recentNotificationsRef.current.get(notificationKey);
    if (lastShown && (now - lastShown) < 2000) {
      console.log('🚫 Duplicate notification blocked:', { 
        message, 
        type, 
        timeSinceLast: `${now - lastShown}ms` 
      });
      return;
    }
    
    // Generate unique ID
    const id = ++notificationIdRef.current;
    
    console.log('🔔 Showing notification:', { id, message, type });
    
    // Record when this notification was shown
    recentNotificationsRef.current.set(notificationKey, now);
    
    // Add notification to state
    setNotifications((prev) => {
      // Extra safety: check if this notification is already in the list
      const alreadyExists = prev.some(n => n.message === message && n.type === type);
      if (alreadyExists) {
        console.log('🚫 Notification already in list, blocked');
        return prev;
      }
      return [...prev, { id, message, type }];
    });

    // Auto-dismiss after duration
    const timeoutId = setTimeout(() => {
      console.log('⏰ Auto-dismissing notification:', id);
      dismissNotification(id);
      
      // Clean up the recent notification record 2 seconds after dismissal
      setTimeout(() => {
        recentNotificationsRef.current.delete(notificationKey);
        console.log('🧹 Cleaned up notification record:', notificationKey);
      }, 2000);
    }, duration);

    // Store timeout ID
    timeoutsRef.current.set(id, { timeoutId, notificationKey });
  }, []);

  const dismissNotification = useCallback((id) => {
    console.log('❌ Dismissing notification:', id);
    
    // Clear the timeout if it exists
    const timeoutData = timeoutsRef.current.get(id);
    if (timeoutData) {
      clearTimeout(timeoutData.timeoutId);
      timeoutsRef.current.delete(id);
    }
    
    // Remove from state
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Clear all timeouts on unmount
      timeoutsRef.current.forEach(({ timeoutId }) => {
        clearTimeout(timeoutId);
      });
      timeoutsRef.current.clear();
      recentNotificationsRef.current.clear();
    };
  }, []);

  const NotificationContainer = () => (
    <div className="fixed top-4 right-4 z-50 space-y-2" style={{ pointerEvents: 'none' }}>
      {notifications.map((notification) => (
        <div key={notification.id} style={{ pointerEvents: 'auto' }}>
          <NotificationToast
            message={notification.message}
            type={notification.type}
            onClose={() => dismissNotification(notification.id)}
          />
        </div>
      ))}
    </div>
  );

  return { showNotification, NotificationContainer };
}