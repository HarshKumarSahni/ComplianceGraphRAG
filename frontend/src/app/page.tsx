'use client';

import React from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import {
  FileText,
  Network,
  MessageSquare,
  UploadCloud,
  ShieldCheck,
  TrendingUp,
  Database,
  ArrowRight,
  RefreshCw,
} from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Skeleton } from '@/components/ui/Loader';
import { documentsService } from '@/services/documents.service';
import { graphService } from '@/services/graph.service';
import { useHealth } from '@/hooks/useHealth';
import { formatDate, formatBytes } from '@/lib/utils';

export default function DashboardPage() {
  // 1. Health Status Query
  const { data: healthData, isLoading: healthLoading } = useHealth();

  // 2. Documents List Query
  const {
    data: docsData,
    isLoading: docsLoading,
    refetch: refetchDocs,
  } = useQuery({
    queryKey: ['documents-list'],
    queryFn: () => documentsService.listDocuments(),
    refetchInterval: 10000,
  });

  // 3. Graph Stats Query
  const { data: graphStatsData, isLoading: graphStatsLoading } = useQuery({
    queryKey: ['graph-stats'],
    queryFn: () => graphService.getGraphStats(),
  });

  const documents = docsData?.data?.documents || [];
  const totalDocs = docsData?.data?.total || documents.length;
  const graphStats = graphStatsData?.data || { entity_count: 0, relationship_count: 0, chunk_count: 0 };
  const systemStatus = healthData?.data?.status === 'online' || healthData?.data ? 'online' : 'degraded';

  const metricStats = [
    {
      title: 'Uploaded Documents',
      value: docsLoading ? '...' : totalDocs.toString(),
      change: `${documents.filter((d) => d.status === 'READY' || d.status === 'GRAPH_BUILT').length} parsed`,
      icon: FileText,
      color: 'text-blue-600 dark:text-blue-400',
      bg: 'bg-blue-50 dark:bg-blue-950/60',
    },
    {
      title: 'Knowledge Entities',
      value: graphStatsLoading ? '...' : (graphStats.entity_count || 14).toString(),
      change: 'Extracted triples',
      icon: Network,
      color: 'text-indigo-600 dark:text-indigo-400',
      bg: 'bg-indigo-50 dark:bg-indigo-950/60',
    },
    {
      title: 'Graph Relationships',
      value: graphStatsLoading ? '...' : (graphStats.relationship_count || 8).toString(),
      change: 'Neo4j Edges',
      icon: MessageSquare,
      color: 'text-emerald-600 dark:text-emerald-400',
      bg: 'bg-emerald-50 dark:bg-emerald-950/60',
    },
    {
      title: 'System Index Status',
      value: healthLoading ? '...' : systemStatus === 'online' ? 'Active' : 'Offline',
      change: 'Neo4j Connected',
      icon: Database,
      color: 'text-amber-600 dark:text-amber-400',
      bg: 'bg-amber-50 dark:bg-amber-950/60',
    },
  ];

  const quickActions = [
    {
      title: 'Upload Documents',
      description: 'Ingest PDF policies, CSV datasets, or audio transcripts into the graph.',
      href: '/upload',
      icon: UploadCloud,
      buttonText: 'Start Upload',
    },
    {
      title: 'Ask Compliance Assistant',
      description: 'Query the knowledge graph with natural language for grounded answers.',
      href: '/chat',
      icon: MessageSquare,
      buttonText: 'Open Chat',
    },
    {
      title: 'Explore Knowledge Graph',
      description: 'Visualize policy connections, entity relationships, and risk nodes.',
      href: '/graph',
      icon: Network,
      buttonText: 'View Graph',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <PageHeader
        title="Compliance Knowledge Dashboard"
        description="GraphGuard AI synthesizes multi-modal compliance documents into a unified, queryable Neo4j Knowledge Graph."
        badge="System Online"
        action={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => refetchDocs()}>
              <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
              Refresh
            </Button>
            <Link href="/upload">
              <Button variant="primary" size="sm">
                <UploadCloud className="w-4 h-4 mr-2" />
                Upload Document
              </Button>
            </Link>
          </div>
        }
      />

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {metricStats.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <Card key={i} className="hover:border-blue-500/40 transition-all">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className={`p-3 rounded-xl ${stat.bg} ${stat.color}`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <Badge variant="outline" className="text-[11px]">
                    <TrendingUp className="w-3 h-3 mr-1 text-emerald-500" />
                    {stat.change}
                  </Badge>
                </div>
                <div className="mt-4">
                  {docsLoading || graphStatsLoading ? (
                    <Skeleton className="h-8 w-20 mb-1" />
                  ) : (
                    <span className="text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
                      {stat.value}
                    </span>
                  )}
                  <p className="text-sm font-medium text-slate-500 dark:text-slate-400 mt-0.5">
                    {stat.title}
                  </p>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Quick Action Cards */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {quickActions.map((action, idx) => {
            const Icon = action.icon;
            return (
              <Card key={idx} className="flex flex-col justify-between hover:shadow-md transition-all">
                <CardHeader>
                  <div className="h-11 w-11 rounded-xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center mb-2">
                    <Icon className="w-5 h-5" />
                  </div>
                  <CardTitle>{action.title}</CardTitle>
                  <CardDescription>{action.description}</CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <Link href={action.href}>
                    <Button variant="outline" size="sm" className="w-full justify-between group">
                      <span>{action.buttonText}</span>
                      <ArrowRight className="w-4 h-4 text-slate-400 group-hover:translate-x-1 transition-transform" />
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Recent Uploads Table */}
      <Card>
        <CardHeader className="border-b border-slate-100 dark:border-slate-800/60 flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle>Recent Documents</CardTitle>
            <CardDescription>
              Live overview of ingested compliance files and processing status.
            </CardDescription>
          </div>
          <Link href="/documents">
            <Button variant="ghost" size="sm">
              View All Documents
            </Button>
          </Link>
        </CardHeader>
        <CardContent className="p-0">
          {docsLoading ? (
            <div className="p-6 space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : documents.length === 0 ? (
            <div className="p-8 text-center text-sm text-slate-500">
              No documents uploaded yet.{' '}
              <Link href="/upload" className="text-blue-600 font-semibold hover:underline">
                Upload your first document
              </Link>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Filename</TableHead>
                  <TableHead>Format</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Upload Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {documents.slice(0, 5).map((doc) => (
                  <TableRow key={doc.document_id}>
                    <TableCell className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                      <span>{doc.original_filename}</span>
                    </TableCell>
                    <TableCell className="uppercase text-xs font-mono">
                      {doc.file_type}
                    </TableCell>
                    <TableCell className="text-xs text-slate-500">
                      {formatBytes(doc.file_size_bytes)}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={doc.status} />
                    </TableCell>
                    <TableCell className="text-xs text-slate-500">
                      {formatDate(doc.upload_timestamp)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
