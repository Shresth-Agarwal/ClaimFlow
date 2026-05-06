import { useState, useEffect } from 'react';
import { useAuthContext } from '../context/AuthContext';
import { getUserProfile, getAgentProfile, getUserOrders } from '../services/api';

/**
 * Fetches the correct profile on mount based on user.role.
 * Also fetches orders for "user" role.
 */
export function useProfile() {
  const { token, user } = useAuthContext();
  const [profile, setProfile] = useState(null);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!token || !user) {
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        if (user.role === 'agent') {
          const profileData = await getAgentProfile(token);
          setProfile(profileData);
        } else {
          const [profileData, ordersData] = await Promise.all([
            getUserProfile(token),
            getUserOrders(token),
          ]);
          setProfile(profileData);
          setOrders(ordersData || []);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token, user]);

  return { profile, orders, loading, error };
}
