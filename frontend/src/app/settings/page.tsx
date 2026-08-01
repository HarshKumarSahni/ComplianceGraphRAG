'use client';

import React from 'react';
import { Settings, Database, Key, Sliders, Cpu, Save } from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

export default function SettingsPage() {
  return (
    <div className="space-y-8 max-w-4xl">
      <PageHeader
        title="Project Settings"
        description="Configure API parameters, Neo4j connection string, LLM extraction models, and indexing properties."
        badge="Configuration"
      />

      {/* Backend API Configuration */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2.5">
            <Sliders className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <CardTitle>API Endpoint Settings</CardTitle>
          </div>
          <CardDescription>
            Configure the base backend URL for FastAPI requests.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
              Backend API Base URL
            </label>
            <input
              type="text"
              defaultValue="http://localhost:8000/api/v1"
              className="w-full h-10 px-3.5 text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 font-mono text-slate-900 dark:text-slate-100"
            />
          </div>
        </CardContent>
      </Card>

      {/* Neo4j Database Settings */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2.5">
            <Database className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            <CardTitle>Neo4j Aura Connection</CardTitle>
          </div>
          <CardDescription>
            Configuration for the Neo4j Graph database driver.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
                Neo4j URI
              </label>
              <input
                type="text"
                defaultValue="neo4j+s://your-instance.databases.neo4j.io"
                className="w-full h-10 px-3.5 text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 font-mono text-slate-900 dark:text-slate-100"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
                Database Name
              </label>
              <input
                type="text"
                defaultValue="neo4j"
                className="w-full h-10 px-3.5 text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 font-mono text-slate-900 dark:text-slate-100"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Models Configuration */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2.5">
            <Cpu className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            <CardTitle>AI Models & Embedding Configuration</CardTitle>
          </div>
          <CardDescription>
            Specify model identifiers for extraction and vector embeddings.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
                LLM Extraction Model
              </label>
              <input
                type="text"
                defaultValue="openai/gpt-4o-mini"
                className="w-full h-10 px-3.5 text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 font-mono text-slate-900 dark:text-slate-100"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">
                Embedding Model
              </label>
              <input
                type="text"
                defaultValue="BAAI/bge-small-en-v1.5"
                className="w-full h-10 px-3.5 text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 font-mono text-slate-900 dark:text-slate-100"
              />
            </div>
          </div>

          <div className="pt-4 flex items-center justify-end">
            <Button variant="primary" size="md">
              <Save className="w-4 h-4 mr-2" />
              Save Configuration
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
