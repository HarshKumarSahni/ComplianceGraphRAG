import React from 'react';
import { cn } from '@/lib/utils';

export type StatusVariant =
  | 'online'
  | 'offline'
  | 'degraded'
  | 'ready'
  | 'processing'
  | 'failed'
  | 'uploaded';

export interface StatusBadgeProps {
  status: StatusVariant | string;
  label?: string;
  className?: string;
}

export function StatusBadge({ status, label, className }: StatusBadgeProps) {
  const normalized = (status || '').toLowerCase();

  let colorClasses = 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
  let dotColor = 'bg-slate-400';

  if (['online', 'ready', 'connected', 'healthy', 'configured'].includes(normalized)) {
    colorClasses = 'bg-emerald-100/80 text-emerald-800 dark:bg-emerald-950/80 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900/50';
    dotColor = 'bg-emerald-500 animate-pulse';
  } else if (['degraded', 'mock_mode', 'processing', 'parsing', 'normalizing', 'chunking', 'entity_extraction'].includes(normalized)) {
    colorClasses = 'bg-amber-100/80 text-amber-800 dark:bg-amber-950/80 dark:text-amber-300 border border-amber-200 dark:border-amber-900/50';
    dotColor = 'bg-amber-500 animate-ping';
  } else if (['offline', 'failed', 'unhealthy', 'disconnected'].includes(normalized)) {
    colorClasses = 'bg-rose-100/80 text-rose-800 dark:bg-rose-950/80 dark:text-rose-300 border border-rose-200 dark:border-rose-900/50';
    dotColor = 'bg-rose-500';
  }

  const displayLabel = label || status;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider',
        colorClasses,
        className
      )}
    >
      <span className={cn('h-1.5 w-1.5 rounded-full shrink-0', dotColor)} />
      {displayLabel}
    </span>
  );
}
