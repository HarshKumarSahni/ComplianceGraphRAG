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
    </motion.div>
  );
}
