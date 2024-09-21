import React from 'react';
import { ChakraProvider } from '@chakra-ui/react';
import ErrorBoundary from '../components/ErrorBoundary';

function MyApp({ Component, pageProps }) {
  console.log('MyApp rendering');
  console.log('Environment variables:', {
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ? 'Set' : 'Not set',
    NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL,
  });

  return (
    <ChakraProvider>
      <ErrorBoundary fallback={<div>Something went wrong</div>}>
        <Component {...pageProps} />
      </ErrorBoundary>
    </ChakraProvider>
  );
}

export default MyApp;