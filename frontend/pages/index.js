// frontend/pages/index.js

import React, { useState, useEffect } from 'react';
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
    console.log('Home component mounted');
    return () => console.log('Home component unmounting');
  }, []);

  // Handler for form submission
  const handleSubmit = async (e) => {
    e.preventDefault();

    // Clear previous updates
    setUpdates([]);

    try {
      // Send POST request to backend to start processing
      const response = await axios.post(`${process.env.NEXT_PUBLIC_BACKEND_URL}/process`, {
        video_ids: videoIds.split('\n').map(id => id.trim()).filter(id => id),
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
    <div>
      <h1>Welcome to the YouTube Web App</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="videoIds">List of YouTube Video IDs (one per line):</label>
          <textarea
            id="videoIds"
            value={videoIds}
            onChange={(e) => setVideoIds(e.target.value)}
            rows="5"
          />
        </div>
        <div>
          <label htmlFor="numVideos">Number of Top Videos per Channel (NUM_VIDEOS):</label>
          <input
            type="number"
            id="numVideos"
            value={numVideos}
            onChange={(e) => setNumVideos(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="numComments">Number of Comments per Video to Retrieve (NUM_COMMENTS_RETRIEVED):</label>
          <input
            type="number"
            id="numComments"
            value={numComments}
            onChange={(e) => setNumComments(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="numTags">Number of Tags per Video:</label>
          <input
            type="number"
            id="numTags"
            value={numTags}
            onChange={(e) => setNumTags(e.target.value)}
          />
        </div>
        <div>
          <label htmlFor="clusteringStrength">Strength of Tag Clustering (0.0 - 1.0):</label>
          <input
            type="number"
            id="clusteringStrength"
            value={clusteringStrength}
            onChange={(e) => setClusteringStrength(e.target.value)}
            step="0.1"
            min="0"
            max="1"
          />
        </div>
        <button type="submit">Start Processing</button>
      </form>
      <RealtimeUpdates updates={updates} />
    </div>
  );
}
