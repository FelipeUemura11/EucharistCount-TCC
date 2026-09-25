import { useEffect, useState } from 'react';

export function useSystemStatus() {
  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    let mounted = true;
    
    async function checkStatus() {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/status');
        if (response.ok) {
          const data = await response.json();
          if (mounted) setIsActive(data.isCountingActive);
        }
      } catch (error) {
        if (mounted) setIsActive(false);
      }
    }

    checkStatus();
    const interval = setInterval(checkStatus, 5000);
    
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return isActive;
}
