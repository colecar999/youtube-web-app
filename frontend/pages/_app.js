import React from 'react';
import ErrorBoundary from '../components/ErrorBoundary';

function MyApp({ Component, pageProps }) {
  return (
    <ErrorBoundary fallback={<div>Something went wrong</div>}>
      <Component {...pageProps} />
    </ErrorBoundary>
  );
}

export default MyApp;