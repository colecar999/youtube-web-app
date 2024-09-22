import React from 'react';
import { Alert, AlertIcon, Box } from '@chakra-ui/react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ errorInfo });
    // Optionally, send error details to an external logging service
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box p={4}>
          <Alert status="error">
            <AlertIcon />
            <Box>
              <strong>Something went wrong.</strong>
              <Box as="span" display="block">
                {this.state.error && this.state.error.toString()}
              </Box>
              <Box as="span" display="block">
                {this.state.errorInfo && this.state.errorInfo.componentStack}
              </Box>
            </Box>
          </Alert>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;