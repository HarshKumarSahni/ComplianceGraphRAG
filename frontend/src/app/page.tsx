'use client';

import React from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
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
  Cpu,
  Zap,
  Activity,
  CheckCircle2,
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
import { useAuth } from '@/context/auth-context';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function DashboardPage() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  // Health & Document queries
  const { data: healthData, isLoading: healthLoading } = useHealth();

  const {
    data: docsData,
    isLoading: docsLoading,
    refetch: refetchDocs,
  } = useQuery({
    queryKey: ['documents-list'],
    queryFn: () => documentsService.listDocuments(),
    refetchInterval: 10000,
  });

  const { data: graphStatsData, isLoading: graphStatsLoading } = useQuery({
    queryKey: ['graph-stats'],
    queryFn: () => graphService.getGraphStats(),
  });

  const documents = docsData?.data?.documents || [];
  const totalDocs = docsData?.data?.total || documents.length;
  const graphStats = graphStatsData?.data || { entity_count: 0, relationship_count: 0, chunk_count: 0 };
  const systemStatus = healthData?.data?.status === 'online' || healthData?.data ? 'online' : 'degraded';

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.08 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 15 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.3 } },
  };

  const metricStats = [
    {
      title: 'Total Documents',
      value: docsLoading ? '...' : totalDocs.toString(),
      change: `${documents.filter((d) => d.status === 'READY' || d.status === 'GRAPH_BUILT').length} parsed`,
      icon: FileText,
      color: 'text-blue-600 dark:text-blue-400',
      bg: 'bg-blue-50 dark:bg-blue-950/60 border-blue-200/60 dark:border-blue-900/50',
    },
    {
      title: 'Total Nodes',
      value: graphStatsLoading ? '...' : (graphStats.entity_count ?? 0).toString(),
      change: 'Extracted Entities',
      icon: Network,
      color: 'text-indigo-600 dark:text-indigo-400',
      bg: 'bg-indigo-50 dark:bg-indigo-950/60 border-indigo-200/60 dark:border-indigo-900/50',
    },
    {
      title: 'Total Relationships',
      value: graphStatsLoading ? '...' : (graphStats.relationship_count ?? 0).toString(),
      change: 'Neo4j Cypher Edges',
      icon: Activity,
      color: 'text-emerald-600 dark:text-emerald-400',
      bg: 'bg-emerald-50 dark:bg-emerald-950/60 border-emerald-200/60 dark:border-emerald-900/50',
    },
    {
      title: 'Graph Index Health',
      value: healthLoading ? '...' : systemStatus === 'online' ? '100%' : 'Degraded',
      change: 'Neo4j Active',
      icon: Database,
      color: 'text-amber-600 dark:text-amber-400',
      bg: 'bg-amber-50 dark:bg-amber-950/60 border-amber-200/60 dark:border-amber-900/50',
    },
  ];

  const quickActions = [
    {
      title: 'Upload Documents',
      description: 'Ingest PDF policies, CSV datasets, or audio transcripts into the graph.',
      href: '/upload',
      icon: UploadCloud,
      buttonText: 'Start Upload',
      gradient: 'from-blue-600/10 to-indigo-600/10',
    },
    {
      title: 'Ask Compliance Assistant',
      description: 'Query the knowledge graph with natural language for grounded answers.',
      href: '/chat',
      icon: MessageSquare,
      buttonText: 'Open Chat',
      gradient: 'from-indigo-600/10 to-purple-600/10',
    },
    {
      title: 'Explore Knowledge Graph',
      description: 'Visualize policy connections, entity relationships, and risk nodes.',
      href: '/graph',
      icon: Network,
      buttonText: 'View Graph',
      gradient: 'from-purple-600/10 to-emerald-600/10',
    },
  ];

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-8"
    >
      {/* Page Header */}
      <motion.div variants={itemVariants}>
        <PageHeader
          title="Compliance Knowledge Dashboard"
          description="GraphGuard AI synthesizes multi-modal compliance documents into a unified, queryable Neo4j Knowledge Graph."
          badge="Enterprise Active"
          action={
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => refetchDocs()}>
                <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
                Refresh Data
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
      </motion.div>

      {/* Metrics Grid */}
      <motion.div
        variants={itemVariants}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5"
      >
        {metricStats.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <Card key={i} className="hover:border-blue-500/50 transition-all hover:shadow-md">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className={`p-3 rounded-xl border ${stat.bg} ${stat.color}`}>
                    <Icon className="w-5 h-5" />
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
      </motion.div>

      {/* AI Processing Statistics Card */}
      <motion.div variants={itemVariants}>
        <Card className="bg-gradient-to-r from-blue-900/90 via-slate-900 to-indigo-950 text-white overflow-hidden shadow-xl border-blue-500/30">
          <CardContent className="p-6 md:p-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
              <div className="space-y-2 md:col-span-2">
                <div className="flex items-center gap-2 text-blue-400 text-xs font-bold uppercase tracking-wider">
                  <Zap className="w-4 h-4 text-amber-400" />
                  <span>GraphGuard Engine Status</span>
                </div>
                <h3 className="text-xl md:text-2xl font-bold text-white">
                  Multi-Modal Grounded AI Engine Active
                </h3>
                <p className="text-xs md:text-sm text-slate-300 max-w-xl leading-relaxed">
                  FastAPI backend is processing document chunks into vector embeddings (`BAAI/bge-small-en-v1.5`) and extracting Cypher entity relationships via OpenRouter (`anthropic/claude-sonnet-5`).
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 p-4 rounded-2xl bg-white/10 backdrop-blur-md border border-white/10 text-xs">
                <div>
                  <span className="text-slate-400 block">Vector Model</span>
                  <span className="font-semibold text-white">BGE-Small-EN</span>
                </div>
                <div>
                  <span className="text-slate-400 block">LLM Extractor</span>
                  <span className="font-semibold text-white">anthropic/claude-sonnet-5</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Graph Engine</span>
                  <span className="font-semibold text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> Neo4j Aura
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block">Retrieval Latency</span>
                  <span className="font-semibold text-white">&lt; 350ms</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Quick Action Cards */}
      <motion.div variants={itemVariants} className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
          Platform Shortcuts
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {quickActions.map((action, idx) => {
            const Icon = action.icon;
            return (
              <Card
                key={idx}
                className="flex flex-col justify-between hover:shadow-lg transition-all group border-slate-200/80 dark:border-slate-800"
              >
                <CardHeader>
                  <div className="h-11 w-11 rounded-xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center mb-2 group-hover:scale-105 transition-transform">
                    <Icon className="w-5 h-5" />
                  </div>
                  <CardTitle>{action.title}</CardTitle>
                  <CardDescription>{action.description}</CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <Link href={action.href}>
                    <Button variant="outline" size="sm" className="w-full justify-between group-hover:border-blue-500/50">
                      <span>{action.buttonText}</span>
                      <ArrowRight className="w-4 h-4 text-slate-400 group-hover:translate-x-1 transition-transform" />
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </motion.div>

      {/* Recent Uploads Table */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader className="border-b border-slate-100 dark:border-slate-800/60 flex flex-row items-center justify-between space-y-0">
            <div>
              <CardTitle>Recent Ingested Documents</CardTitle>
              <CardDescription>
                Live overview of uploaded compliance policies, datasets, and recordings.
              </CardDescription>
            </div>
            <Link href="/documents">
              <Button variant="ghost" size="sm">
                View All Catalog
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
                  Upload your first file
                </Link>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Filename</TableHead>
                    <TableHead>Format</TableHead>
                    <TableHead>Size</TableHead>
                    <TableHead>Pipeline Status</TableHead>
                    <TableHead>Upload Date</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {documents.slice(0, 5).map((doc) => (
                    <TableRow key={doc.document_id}>
                      <TableCell className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
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
      </motion.div>
    </motion.div>
  );
}
