// frontend/components/RealtimeUpdates.js

import React, { useEffect } from 'react';
import { supabase } from '../lib/supabaseClient';

const RealtimeUpdates = () => {
  useEffect(() => {
    console.log('RealtimeUpdates component mounted');
    const channel = supabase.channel('custom-all-channel');

    channel
      .on('broadcast', { event: 'test' }, (payload) => {
        console.log('Received broadcast:', payload);
        // Handle the payload
      })
      .subscribe((status) => {
        console.log('Subscription status:', status);
        if (status === 'SUBSCRIBED') {
          console.log('Successfully subscribed to channel');
        }
      });

    return () => {
      console.log('RealtimeUpdates component unmounting');
      supabase.removeChannel(channel);
    };
  }, []);

  return (
    <div style={styles.container}>
      <h2>Real-time Updates</h2>
      <div style={styles.updates}>
        {updates.map((update, index) => (
          <p key={index} style={styles.update}>
            {update}
          </p>
        ))}
      </div>
    </div>
  );
};

const styles = {
  container: {
    marginTop: '30px'
  },
  updates: {
    maxHeight: '400px',
    overflowY: 'scroll',
    border: '1px solid #ccc',
    padding: '10px',
    backgroundColor: '#f9f9f9'
  },
  update: {
    margin: '5px 0'
  }
};

export default RealtimeUpdates;
