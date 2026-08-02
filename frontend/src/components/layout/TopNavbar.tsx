'use client';

import React from 'react';
import { Sun, Moon, User as UserIcon, LogOut } from 'lucide-react';
import { useTheme } from '@/providers/ThemeProvider';
import { useAuth } from '@/context/auth-context';
import { Button } from '@/components/ui/Button';
import Link from 'next/link';

export function TopNavbar() {
  const { resolvedTheme, toggleTheme } = useTheme();
  const { user, isAuthenticated, logout } = useAuth();

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <header className="h-16 sticky top-0 z-20 w-full border-b border-slate-200/80 bg-white/80 dark:border-slate-800/80 dark:bg-slate-900/80 backdrop-blur-md px-6 flex items-center justify-end">

      {/* Right Controls: Theme Toggle & User Auth Status */}
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

        {isAuthenticated && user ? (
          <div className="flex items-center gap-3 pl-2 border-l border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 text-slate-950 font-bold text-xs flex items-center justify-center shadow-md">
                {getInitials(user.full_name)}
              </div>
              <div className="hidden md:flex flex-col text-left">
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 leading-tight">
                  {user.full_name}
                </span>
                <span className="text-[10px] text-slate-500 dark:text-slate-400 leading-none">
                  {user.email}
                </span>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={logout}
              className="rounded-xl text-xs gap-1.5 text-slate-600 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-400 border-slate-200 dark:border-slate-800"
              title="Log out of GraphGuard AI"
            >
              <LogOut className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Logout</span>
            </Button>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Link href="/login">
              <Button variant="outline" size="sm" className="rounded-xl text-xs">
                Login
              </Button>
            </Link>
            <Link href="/signup">
              <Button size="sm" className="rounded-xl text-xs bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold">
                Sign Up
              </Button>
            </Link>
          </div>
        )}
      </div>
    </header>
  );
}
