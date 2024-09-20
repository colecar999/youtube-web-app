import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, errorInfo: error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by ErrorBoundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      // Display detailed error information in development
      if (process.env.NODE_ENV === 'development') {
        return (
          <div>
            <h2>Something went wrong.</h2>
            <details style={{ whiteSpace: 'pre-wrap' }}>
              {this.state.errorInfo && this.state.errorInfo.toString()}
            </details>
          </div>
        );
      }
      // Fallback for production
      return this.props.fallback || <div>Something went wrong</div>;
    }
    return this.props.children;
  }
}

export default ErrorBoundary;