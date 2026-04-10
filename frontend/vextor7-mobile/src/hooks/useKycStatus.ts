import { useState, useEffect } from 'react';
import { securityApi } from '@/services/securityApi';
import { useAuth } from '@/hooks/useAuth';

export const useKycStatus = () => {
  const { user } = useAuth();
  const [status, setStatus] = useState<'NONE' | 'PENDING' | 'VERIFIED' | 'REJECTED'>('NONE');
  const [loading, setLoading] = useState(true);
  const [level, setLevel] = useState(0);

  const fetchStatus = async () => {
    if (!user) return;
    try {
      setLoading(true);
      const data = await securityApi.getKycStatus();
      setStatus(data.status);
      setLevel(data.current_level);
    } catch (error) {
      console.error('Failed to fetch KYC status', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, [user]);

  return { status, level, loading, refresh: fetchStatus };
};