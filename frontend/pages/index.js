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
  useToast
} from '@chakra-ui/react';

console.log('Index.js loaded');

export default function Home() {
  console.log('Home component rendering');

  const [isSupabaseInitialized, setIsSupabaseInitialized] = useState(false);
  const [error, setError] = useState(null);
  const [updates, setUpdates] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const toast = useToast();

  useEffect(() => {
    console.log('Home component mounted');
    try {
      console.log('Supabase object:', supabase);
      if (supabase) {
        console.log('Supabase initialized successfully');
        setIsSupabaseInitialized(true);
      } else {
        console.error('Supabase object is undefined');
        setError('Supabase initialization failed');
      }
    } catch (err) {
      console.error('Error initializing Supabase:', err);
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    if (isSupabaseInitialized && sessionId) {
      console.log(`Setting up Supabase subscription for session ${sessionId}`);
      const channel = supabase
        .channel(`updates:${sessionId}`)
        .on(
          'postgres_changes',
          { event: '*', schema: 'public', table: 'updates' },
          (payload) => {
            console.log("Supabase update received:", payload);
            if (payload.new && payload.new.session_id === sessionId) {
              console.log('Updating state with new message:', payload.new.message);
              setUpdates((prev) => [...prev, payload.new.message]);
            } else {
              console.log('Received update for different session, ignoring');
            }
          }
        )
        .subscribe((status) => {
          console.log('Supabase subscription status:', status);
          if (status === 'CHANNEL_ERROR') {
            console.error("Supabase channel error. Attempting to reconnect...");
            channel.unsubscribe();
            // Attempt to resubscribe after a short delay
            setTimeout(() => channel.subscribe(), 5000);
          }
        });

      return () => {
        console.log(`Removing Supabase channel for session ${sessionId}`);
        supabase.removeChannel(channel);
      };
    }
  }, [isSupabaseInitialized, sessionId, toast]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setUpdates([]);
    try {
      console.log('Submitting form with data:', {
        video_ids: videoIds,
        num_videos: numVideos,
        num_comments: numComments,
        num_tags: numTags,
        clustering_strength: clusteringStrength,
      });
      const response = await axios.post(`${process.env.NEXT_PUBLIC_BACKEND_URL}/process`, {
        video_ids: videoIds.split('\n').map((id) => id.trim()).filter((id) => id),
        num_videos: parseInt(numVideos),
        num_comments: parseInt(numComments),
        num_tags: parseInt(numTags),
        clustering_strength: parseFloat(clusteringStrength),
      });
      const { session_id } = response.data;
      console.log('Received session_id:', session_id);
      setSessionId(session_id);
      toast({
        title: "Processing Started",
        description: `Session ID: ${session_id}`,
        status: "success",
        duration: 5000,
        isClosable: true,
      });
    } catch (error) {
      console.error('Error initiating processing:', error);
      setUpdates((prev) => [...prev, 'Error initiating processing. Please check your inputs and try again.']);
      toast({
        title: "Error",
        description: "Failed to start processing. Please try again.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

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
        <Box mt={4}>Initializing Supabase...</Box>
      </Container>
    );
  }

  console.log('Rendering Home component', { isSupabaseInitialized, error });

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
