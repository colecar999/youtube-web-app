// frontend/components/RealtimeUpdates.js

import React, { useEffect, useState } from 'react';
import { supabase } from '../lib/supabaseClient';

const RealtimeUpdates = () => {
  const [updates, setUpdates] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!supabase) {
      setError('Supabase client is not initialized');
      return;
    }

    const channel = supabase.channel('custom-all-channel');

    channel
      .on('broadcast', { event: 'test' }, (payload) => {
        console.log('Received broadcast:', payload);
        setUpdates(prevUpdates => [...prevUpdates, JSON.stringify(payload)]);
      })
      .subscribe((status) => {
        console.log('Subscription status:', status);
        if (status === 'SUBSCRIBED') {
          console.log('Successfully subscribed to channel');
        }
      });

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h2>Real-time Updates</h2>
      <div>
        {updates.map((update, index) => (
          <p key={index}>{update}</p>
        ))}
      </div>
    </div>
  );
};

export default RealtimeUpdates;
