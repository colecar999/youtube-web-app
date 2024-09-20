// frontend/components/RealtimeUpdates.js

import React from 'react';
import {
  Box,
  Heading,
  VStack,
  Badge,
  Text,
  useColorModeValue,
} from '@chakra-ui/react';

const RealtimeUpdates = ({ updates }) => {
  const bg = useColorModeValue('gray.50', 'gray.800');

  return (
    <Box mt={8} p={4} bg={bg} borderRadius="md" boxShadow="md">
      <Heading size="md" mb={4}>
        Real-time Updates
      </Heading>
      <VStack align="start" spacing={2}>
        {updates.map((update, index) => {
          const isError = update.toLowerCase().includes('error');
          return (
            <Box key={index} display="flex" alignItems="center">
              <Badge colorScheme={isError ? 'red' : 'blue'} mr={2}>
                {isError ? 'Error' : 'Info'}
              </Badge>
              <Text fontSize="sm">
                {new Date().toLocaleTimeString()}: {update}
              </Text>
            </Box>
          );
        })}
      </VStack>
    </Box>
  );
};

export default RealtimeUpdates;
