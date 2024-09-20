import { useEffect, useState } from 'react';
import axios from 'axios';
import RealtimeUpdates from '../components/RealtimeUpdates';
import { supabase } from '../lib/supabaseClient';
import { Button, Input, Textarea, Label, Container, Heading, Form, FormField } from '@shadcn/ui';

export default function Home() {
  const [isSupabaseInitialized, setIsSupabaseInitialized] = useState(false);
  const [error, setError] = useState(null);
  const [updates, setUpdates] = useState([]);

  useEffect(() => {
    try {
      if (supabase) {
        setIsSupabaseInitialized(true);
      }
    } catch (err) {
      console.error('Error initializing Supabase:', err);
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    let channel;

    if (supabase && isSupabaseInitialized) {
      channel = supabase.channel('custom-all-channel');

      channel
        .on('broadcast', { event: 'update' }, (payload) => {
          console.log('Received update:', payload);
          setUpdates(prev => [...prev, payload.message]);
        })
        .subscribe((status) => {
          console.log('Subscription status:', status);
          if (status === 'SUBSCRIBED') {
            console.log('Successfully subscribed to channel');
          }
        });
    }

    return () => {
      if (channel) {
        supabase.removeChannel(channel);
      }
    };
  }, [supabase, isSupabaseInitialized]);

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

      // Use Supabase for real-time updates
      const newChannel = supabase.channel(session_id);

      newChannel
        .on('broadcast', { event: 'update' }, (payload) => {
          console.log('Received update:', payload);
          setUpdates(prev => [...prev, payload.message]);
        })
        .subscribe((status) => {
          console.log('Subscription status:', status);
          if (status === 'SUBSCRIBED') {
            console.log('Successfully subscribed to channel');
          }
        });

    } catch (error) {
      console.error('Error initiating processing:', error);
      setUpdates(prev => [...prev, 'Error initiating processing. Please check your inputs and try again.']);
    }
  };

  // State variables for form inputs
  const [videoIds, setVideoIds] = useState('');
  const [numVideos, setNumVideos] = useState(10);
  const [numComments, setNumComments] = useState(50);
  const [numTags, setNumTags] = useState(5);
  const [clusteringStrength, setClusteringStrength] = useState(0.3);

  if (error) {
    return <div>Error: {error}</div>;
  }

  if (!isSupabaseInitialized) {
    return <div>Loading...</div>;
  }

  return (
    <Container className="p-8">
      <Heading className="mb-6">YouTube Video Processor</Heading>
      <Form onSubmit={handleSubmit}>
        <FormField>
          <Label htmlFor="videoIds">List of YouTube Video IDs (one per line):</Label>
          <Textarea
            id="videoIds"
            value={videoIds}
            onChange={(e) => setVideoIds(e.target.value)}
            rows="5"
            className="mt-1 mb-4"
            placeholder="Enter video IDs here..."
          />
        </FormField>
        <FormField>
          <Label htmlFor="numVideos">Number of Top Videos per Channel (NUM_VIDEOS):</Label>
          <Input
            type="number"
            id="numVideos"
            value={numVideos}
            onChange={(e) => setNumVideos(e.target.value)}
            className="mt-1 mb-4"
            min="1"
          />
        </FormField>
        <FormField>
          <Label htmlFor="numComments">Number of Comments per Video to Retrieve (NUM_COMMENTS_RETRIEVED):</Label>
          <Input
            type="number"
            id="numComments"
            value={numComments}
            onChange={(e) => setNumComments(e.target.value)}
            className="mt-1 mb-4"
            min="1"
          />
        </FormField>
        <FormField>
          <Label htmlFor="numTags">Number of Tags per Video:</Label>
          <Input
            type="number"
            id="numTags"
            value={numTags}
            onChange={(e) => setNumTags(e.target.value)}
            className="mt-1 mb-4"
            min="1"
          />
        </FormField>
        <FormField>
          <Label htmlFor="clusteringStrength">Strength of Tag Clustering (0.0 - 1.0):</Label>
          <Input
            type="number"
            id="clusteringStrength"
            value={clusteringStrength}
            onChange={(e) => setClusteringStrength(e.target.value)}
            step="0.1"
            min="0"
            max="1"
            className="mt-1 mb-4"
          />
        </FormField>
        <Button type="submit" className="mt-4">Start Processing</Button>
      </Form>
      <RealtimeUpdates updates={updates} />
    </Container>
  );
}
