import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface LoaderProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
  className?: string;
  fullPage?: boolean;
}

export function Loader({ size = 'md', text, className, fullPage = false }: LoaderProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-10 h-10',
  };

  const content = (
    <div className={cn('flex flex-col items-center justify-center gap-3 p-6 text-slate-500 dark:text-slate-400', className)}>
      <Loader2 className={cn('animate-spin text-blue-600 dark:text-blue-400', sizeClasses[size])} />
      {text && <p className="text-sm font-medium">{text}</p>}
    </div>
  );

  if (fullPage) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/80 dark:bg-slate-950/80 backdrop-blur-xs">
        {content}
      </div>
    );
  }

  return content;
}

export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('animate-pulse rounded-xl bg-slate-200/80 dark:bg-slate-800/80', className)}
      {...props}
    />
  );
}
