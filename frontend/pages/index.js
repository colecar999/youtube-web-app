// frontend/pages/index.js

import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Box,
  Button,
  Container,
  Heading,
  VStack,
  Text,
  useToast,
  Textarea,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  FormControl,
  FormLabel,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  useColorModeValue,
  Icon,
  Fade,
  Alert,
  AlertIcon,
  Spinner,
} from '@chakra-ui/react';
import { motion } from 'framer-motion';
import { FaYoutube, FaNetworkWired } from 'react-icons/fa';
import RealtimeUpdates from '../components/RealtimeUpdates';
import { supabase } from '../lib/supabaseClient';

const MotionBox = motion(Box);

export default function Home() {
  console.log('Home component rendering');

  const [videoIds, setVideoIds] = useState('');
  const [numVideos, setNumVideos] = useState(10);
  const [numComments, setNumComments] = useState(50);
  const [numTags, setNumTags] = useState(5);
  const [clusteringStrength, setClusteringStrength] = useState(0.3);
  const [sessionId, setSessionId] = useState(null);
  const [updates, setUpdates] = useState([]);
  const [isSupabaseInitialized, setIsSupabaseInitialized] = useState(false);
  const [error, setError] = useState(null);

  const toast = useToast();
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBgColor = useColorModeValue('white', 'gray.800');

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
      toast({
        title: "Error",
        description: "Failed to start processing. Please try again.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

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
    <Box bg={bgColor} minHeight="100vh" py={10}>
      <Container maxW="container.md">
        <MotionBox
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Heading as="h1" size="xl" textAlign="center" mb={6}>
            Podcast Topic & Sentiment Analyzer
          </Heading>
        </MotionBox>
        <VStack
          as="form"
          onSubmit={handleSubmit}
          spacing={6}
          align="stretch"
          bg={cardBgColor}
          p={8}
          borderRadius="lg"
          boxShadow="xl"
        >
          <FormControl>
            <FormLabel>Enter video IDs for the YouTube channels you want analyzed (one per line):</FormLabel>
            <Textarea
              value={videoIds}
              onChange={(e) => setVideoIds(e.target.value)}
              placeholder="Enter video IDs here..."
              size="sm"
              rows={5}
            />
          </FormControl>

          <FormControl>
            <FormLabel>Number of videos to analyze per channel:</FormLabel>
            <NumberInput min={1} max={50} value={numVideos} onChange={(value) => setNumVideos(Number(value))}>
              <NumberInputField />
              <NumberInputStepper>
                <NumberIncrementStepper />
                <NumberDecrementStepper />
              </NumberInputStepper>
            </NumberInput>
          </FormControl>

          <FormControl>
            <FormLabel>Number of comments to analyze per video:</FormLabel>
            <NumberInput min={1} max={100} value={numComments} onChange={(value) => setNumComments(Number(value))}>
              <NumberInputField />
              <NumberInputStepper>
                <NumberIncrementStepper />
                <NumberDecrementStepper />
              </NumberInputStepper>
            </NumberInput>
          </FormControl>

          <FormControl>
            <FormLabel>Number of content tags to generate per video:</FormLabel>
            <NumberInput min={1} max={20} value={numTags} onChange={(value) => setNumTags(Number(value))}>
              <NumberInputField />
              <NumberInputStepper>
                <NumberIncrementStepper />
                <NumberDecrementStepper />
              </NumberInputStepper>
            </NumberInput>
          </FormControl>

          <FormControl>
            <FormLabel>Strength of tag clustering:</FormLabel>
            <Slider
              min={0}
              max={1}
              step={0.1}
              value={clusteringStrength}
              onChange={(value) => setClusteringStrength(value)}
            >
              <SliderTrack>
                <SliderFilledTrack />
              </SliderTrack>
              <SliderThumb boxSize={6}>
                <Box color="blue.500" as={FaNetworkWired} />
              </SliderThumb>
            </Slider>
            <Text textAlign="center" mt={2}>
              {clusteringStrength.toFixed(1)}
            </Text>
          </FormControl>

          <Button
            type="submit"
            colorScheme="blue"
            size="lg"
            leftIcon={<Icon as={FaYoutube} />}
            _hover={{
              transform: 'translateY(-2px)',
              boxShadow: 'lg',
            }}
            transition="all 0.2s"
          >
            Start Analysis
          </Button>
        </VStack>

        <Fade in={updates.length > 0}>
          <Box mt={8}>
            <RealtimeUpdates updates={updates} />
          </Box>
        </Fade>
      </Container>
    </Box>
  );
}