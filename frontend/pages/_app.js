import React from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import { ShadcnProvider } from '@shadcn/ui'; // Assuming ShadcnProvider exists for theming

function MyApp({ Component, pageProps }) {
  return (
    <ShadcnProvider>
      <ErrorBoundary fallback={<div>Something went wrong</div>}>
        <Component {...pageProps} />
      </ErrorBoundary>
    </ShadcnProvider>
  );
}

export default MyApp;