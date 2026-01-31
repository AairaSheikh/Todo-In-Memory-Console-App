/**Error boundary component for catching and displaying errors.*/

'use client';

import React, { ReactNode, useState, useEffect } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export default function ErrorBoundary({ children }: ErrorBoundaryProps) {
  const [state, setState] = useState<ErrorBoundaryState>({
    hasError: false,
    error: null,
  });

  useEffect(() => {
    const handleError = (event: ErrorEvent) => {
      setState({
        hasError: true,
        error: event.error,
      });
    };

    window.addEventListener('error', handleError);
    return () => window.removeEventListener('error', handleError);
  }, []);

  if (state.hasError) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <h1>Something went wrong</h1>
        <p>{state.error?.message || 'An unexpected error occurred'}</p>
        <button
          onClick={() => setState({ hasError: false, error: null })}
          className="btn btn-primary"
        >
          Try again
        </button>
      </div>
    );
  }

  return <>{children}</>;
}
