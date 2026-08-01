'use client';

import React, { useEffect } from 'react';
import { ErrorState } from '@/components/ui/ErrorState';

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Unhandled UI error:', error);
  }, [error]);

  return (
    <div className="min-h-[70vh] flex items-center justify-center p-6">
      <ErrorState
        title="Application Exception Captured"
        message={error.message || 'An unexpected error occurred in the GraphGuard UI layout.'}
        onRetry={() => reset()}
      />
    </div>
  );
}
