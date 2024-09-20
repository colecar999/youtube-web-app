// frontend/pages/index.js

import { useState, useEffect } from 'react';
import axios from 'axios';
import RealtimeUpdates from '../components/RealtimeUpdates';

export default function Home() {
  // State variables for form inputs
  const [videoIds, setVideoIds] = useState('');
  const [numVideos, setNumVideos] = useState(10);
  const [numComments, setNumComments] = useState(50);
  const [numTags, setNumTags] = useState(5);
  const [clusteringStrength, setClusteringStrength] = useState(0.3);

  // State variables for handling the WebSocket connection
  const [socket, setSocket] = useState(null);
  const [updates, setUpdates] = useState([]);

  useEffect(() => {
    // Cleanup WebSocket on component unmount
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, [socket]);

  // Handler for form submission
  const handleSubmit = async (e) => {
    e.preventDefault();

    // Clear previous updates
    setUpdates([]);

    try {
      // Send POST request to backend to start processing
      const response = await axios.post(`${process.env.NEXT_PUBLIC_BACKEND_URL}/process`, {
        video_ids: videoIds.split('\\n').map(id => id.trim()).filter(id => id),
        num_videos: parseInt(numVideos),
        num_comments: parseInt(numComments),
        num_tags: parseInt(numTags),
        clustering_strength: parseFloat(clusteringStrength)
      });

      const { session_id } = response.data;

      // Establish WebSocket connection for real-time updates
      const ws = new WebSocket(`wss://${process.env.NEXT_PUBLIC_BACKEND_URL.replace(/^https?:\/\//, '')}/ws/${session_id}`);

      ws.onopen = () => {
        console.log('WebSocket connection established.');
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setUpdates(prev => [...prev, data.message]);
      };

      ws.onclose = () => {
        console.log('WebSocket connection closed.');
      };

      setSocket(ws);
    } catch (error) {
      console.error('Error initiating processing:', error);
      setUpdates(prev => [...prev, 'Error initiating processing. Please check your inputs and try again.']);
    }
  };

  return (
    <div style={styles.container}>
      <h1>YouTube Video Processor</h1>
      <form onSubmit={handleSubmit} style={styles.form}>
        <label style={styles.label}>
          List of YouTube Video IDs (one per line):
          <textarea
            value={videoIds}
            onChange={(e) => setVideoIds(e.target.value)}
            rows="5"
            style={styles.textarea}
            required
          />
        </label>
        <label style={styles.label}>
          Number of Top Videos per Channel (NUM_VIDEOS):
          <input
            type="number"
            value={numVideos}
            onChange={(e) => setNumVideos(e.target.value)}
            min="1"
            style={styles.input}
            required
          />
        </label>
        <label style={styles.label}>
          Number of Comments per Video to Retrieve (NUM_COMMENTS_RETRIEVED):
          <input
            type="number"
            value={numComments}
            onChange={(e) => setNumComments(e.target.value)}
            min="1"
            style={styles.input}
            required
          />
        </label>
        <label style={styles.label}>
          Number of Tags per Video:
          <input
            type="number"
            value={numTags}
            onChange={(e) => setNumTags(e.target.value)}
            min="1"
            style={styles.input}
            required
          />
        </label>
        <label style={styles.label}>
          Strength of Tag Clustering (0.0 - 1.0):
          <input
            type="number"
            step="0.1"
            value={clusteringStrength}
            onChange={(e) => setClusteringStrength(e.target.value)}
            min="0.0"
            max="1.0"
            style={styles.input}
            required
          />
        </label>
        <button type="submit" style={styles.button}>Start Processing</button>
      </form>

      <RealtimeUpdates updates={updates} />
    </div>
  );
}

// Inline styles for simplicity; consider using CSS modules or styled-components for larger projects
const styles = {
  container: {
    padding: '20px',
    fontFamily: 'Arial, sans-serif'
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    maxWidth: '600px'
  },
  label: {
    marginBottom: '15px'
  },
  textarea: {
    width: '100%',
    padding: '10px',
    fontSize: '16px'
  },
  input: {
    width: '100%',
    padding: '8px',
    fontSize: '16px'
  },
  button: {
    padding: '10px',
    fontSize: '16px',
    backgroundColor: '#0070f3',
    color: '#fff',
    border: 'none',
    cursor: 'pointer'
  }
};
