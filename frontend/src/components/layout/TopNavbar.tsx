'use client';

import React from 'react';
import { Sun, Moon, Database, Cloud, Cpu, Activity } from 'lucide-react';
import { useTheme } from '@/providers/ThemeProvider';
import { useHealth } from '@/hooks/useHealth';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Button } from '@/components/ui/Button';

export function TopNavbar() {
  const { resolvedTheme, toggleTheme } = useTheme();
  const { data: healthData, isLoading, isError } = useHealth();

  const apiStatus = isError ? 'offline' : healthData?.data?.status || (isLoading ? 'processing' : 'online');
  const services = healthData?.data?.services || {
    neo4j: 'connected',
    cloudinary: 'configured',
    openrouter: 'configured',
  };

  return (
    <header className="h-16 sticky top-0 z-20 w-full border-b border-slate-200/80 bg-white/80 dark:border-slate-800/80 dark:bg-slate-900/80 backdrop-blur-md px-6 flex items-center justify-between">
      {/* Left Title / System Connection Badges */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          <span className="text-sm font-semibold text-slate-700 dark:text-slate-300 hidden sm:inline">
            API Status:
          </span>
          <StatusBadge status={apiStatus} />
        </div>

        <div className="h-4 w-px bg-slate-200 dark:bg-slate-800 hidden lg:block" />

        {/* Individual Service Badges */}
        <div className="hidden lg:flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
          <div className="flex items-center gap-1.5" title="Neo4j Aura Database">
            <Database className="h-3.5 w-3.5 text-blue-500" />
            <span>Neo4j:</span>
            <span className="font-semibold text-slate-700 dark:text-slate-200 capitalize">
              {services.neo4j || 'connected'}
            </span>
          </div>

          <div className="flex items-center gap-1.5" title="Cloudinary CDN Storage">
            <Cloud className="h-3.5 w-3.5 text-indigo-500" />
            <span>Cloudinary:</span>
            <span className="font-semibold text-slate-700 dark:text-slate-200 capitalize">
              {services.cloudinary || 'configured'}
            </span>
          </div>

          <div className="flex items-center gap-1.5" title="OpenRouter LLM API">
            <Cpu className="h-3.5 w-3.5 text-purple-500" />
            <span>OpenRouter:</span>
            <span className="font-semibold text-slate-700 dark:text-slate-200 capitalize">
              {services.openrouter || 'configured'}
            </span>
          </div>
        </div>
      </div>

      {/* Right Controls: Theme Toggle */}
      <div className="flex items-center gap-3">
        <Button
          variant="outline"
          size="icon"
          onClick={toggleTheme}
          aria-label="Toggle theme"
          className="rounded-xl border-slate-200 dark:border-slate-800"
        >
          {resolvedTheme === 'dark' ? (
            <Sun className="h-4 w-4 text-amber-400" />
          ) : (
            <Moon className="h-4 w-4 text-slate-600" />
          )}
        </Button>
      </div>
    </header>
  );
}
