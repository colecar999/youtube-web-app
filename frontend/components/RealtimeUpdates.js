// frontend/components/RealtimeUpdates.js

import React, { useRef, useEffect } from 'react';
import {
  Box,
  Heading,
  VStack,
  Badge,
  Text,
  useColorModeValue,
  ScrollArea,
} from '@chakra-ui/react';

const RealtimeUpdates = ({ updates }) => {
  const bg = useColorModeValue('gray.50', 'gray.800');
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [updates]);

  return (
    <Box mt={8} p={4} bg={bg} borderRadius="md" boxShadow="md">
      <Heading size="md" mb={4}>
        Real-time Updates
      </Heading>
      <Box maxHeight="300px" overflowY="auto" ref={scrollRef}>
        <VStack align="start" spacing={2}>
          {updates.map((update, index) => {
            const isError = update.toLowerCase().includes('error');
            return (
              <Box key={index} display="flex" alignItems="center" width="100%">
                <Badge colorScheme={isError ? 'red' : 'blue'} mr={2}>
                  {isError ? 'Error' : 'Info'}
                </Badge>
                <Text fontSize="sm" flex={1}>
                  {new Date().toLocaleTimeString()}: {update}
                </Text>
              </Box>
            );
          })}
        </VStack>
      </Box>
    </Box>
  );
};

export default RealtimeUpdates;
