// frontend/pages/index.js

import { useEffect, useState } from 'react';
import axios from 'axios';
import RealtimeUpdates from '../components/RealtimeUpdates';
import { supabase } from '../lib/supabaseClient';
import {
  Button,
  Input,
  Textarea,
  FormControl,
  FormLabel,
  Container,
  Heading,
  VStack,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Box,
  Spinner,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';

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
          setUpdates((prev) => [...prev, payload.message]);
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
        video_ids: videoIds.split('\n').map((id) => id.trim()).filter((id) => id),
        num_videos: parseInt(numVideos),
        num_comments: parseInt(numComments),
        num_tags: parseInt(numTags),
        clustering_strength: parseFloat(clusteringStrength),
      });

      const { session_id } = response.data;

      // Use Supabase for real-time updates
      const newChannel = supabase.channel(session_id);

      newChannel
        .on('broadcast', { event: 'update' }, (payload) => {
          console.log('Received update:', payload);
          setUpdates((prev) => [...prev, payload.message]);
        })
        .subscribe((status) => {
          console.log('Subscription status:', status);
          if (status === 'SUBSCRIBED') {
            console.log('Successfully subscribed to channel');
          }
        });
    } catch (error) {
      console.error('Error initiating processing:', error);
      setUpdates((prev) => [...prev, 'Error initiating processing. Please check your inputs and try again.']);
    }
  };

  // State variables for form inputs
  const [videoIds, setVideoIds] = useState('');
  const [numVideos, setNumVideos] = useState(10);
  const [numComments, setNumComments] = useState(50);
  const [numTags, setNumTags] = useState(5);
  const [clusteringStrength, setClusteringStrength] = useState(0.3);

  if (error) {
    return (
      <Container centerContent>
        <Alert status="error">
          <AlertIcon />
          {error}
        </Alert>
      </Container>
    );
  }

  if (!isSupabaseInitialized) {
    return (
      <Container centerContent>
        <Spinner size="xl" />
      </Container>
    );
  }

  return (
    <Container maxW="container.md" p={8}>
      <Heading mb={6}>YouTube Video Processor</Heading>
      <Box as="form" onSubmit={handleSubmit}>
        <VStack spacing={4} align="stretch">
          <FormControl id="videoIds" isRequired>
            <FormLabel>List of YouTube Video IDs (one per line):</FormLabel>
            <Textarea
              value={videoIds}
              onChange={(e) => setVideoIds(e.target.value)}
              placeholder="Enter video IDs here..."
            />
          </FormControl>

          <FormControl id="numVideos" isRequired>
            <FormLabel>Number of Top Videos per Channel (NUM_VIDEOS):</FormLabel>
            <NumberInput min={1} value={numVideos} onChange={(valueString) => setNumVideos(valueString)}>
              <NumberInputField />
              <NumberInputStepper>
                <NumberIncrementStepper />
                <NumberDecrementStepper />
              </NumberInputStepper>
            </NumberInput>
          </FormControl>

          <FormControl id="numComments" isRequired>
            <FormLabel>Number of Comments per Video to Retrieve (NUM_COMMENTS_RETRIEVED):</FormLabel>
            <NumberInput min={1} value={numComments} onChange={(valueString) => setNumComments(valueString)}>
              <NumberInputField />
              <NumberInputStepper>
                <NumberIncrementStepper />
                <NumberDecrementStepper />
              </NumberInputStepper>
            </NumberInput>
          </FormControl>

          <FormControl id="numTags" isRequired>
            <FormLabel>Number of Tags per Video:</FormLabel>
            <NumberInput min={1} value={numTags} onChange={(valueString) => setNumTags(valueString)}>
              <NumberInputField />
              <NumberInputStepper>
                <NumberIncrementStepper />
                <NumberDecrementStepper />
              </NumberInputStepper>
            </NumberInput>
          </FormControl>

          <FormControl id="clusteringStrength" isRequired>
            <FormLabel>Strength of Tag Clustering (0.0 - 1.0):</FormLabel>
            <NumberInput
              min={0}
              max={1}
              step={0.1}
              value={clusteringStrength}
              onChange={(valueString) => setClusteringStrength(valueString)}
            >
              <NumberInputField />
              <NumberInputStepper>
                <NumberIncrementStepper />
                <NumberDecrementStepper />
              </NumberInputStepper>
            </NumberInput>
          </FormControl>

          <Button type="submit" colorScheme="teal">
            Start Processing
          </Button>
        </VStack>
      </Box>
      <RealtimeUpdates updates={updates} />
    </Container>
  );
}
