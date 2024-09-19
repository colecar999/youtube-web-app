// frontend/components/RealtimeUpdates.js

import React from 'react';

const RealtimeUpdates = ({ updates }) => {
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
