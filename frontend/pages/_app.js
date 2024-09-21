import React from 'react';
import { ChakraProvider } from '@chakra-ui/react';
import ErrorBoundary from '../components/ErrorBoundary';

function MyApp({ Component, pageProps }) {
  console.log('MyApp rendering');
  return (
    <ChakraProvider>
      <ErrorBoundary fallback={<div>Something went wrong</div>}>
        <Component {...pageProps} />
      </ErrorBoundary>
    </ChakraProvider>
  );
}

export default MyApp;