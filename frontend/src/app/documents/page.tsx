'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  FileText,
  ExternalLink,
  RefreshCw,
  ArrowUpDown,
  AlertTriangle,
  RotateCcw,
} from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card, CardContent } from '@/components/ui/Card';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '@/components/ui/Table';
import { Button } from '@/components/ui/Button';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { SearchBar } from '@/components/ui/SearchBar';
import { Skeleton } from '@/components/ui/Loader';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { documentsService } from '@/services/documents.service';
import { useToast } from '@/hooks/useToast';
import { formatDate, formatBytes } from '@/lib/utils';
import { DocumentMetadata } from '@/types/document';

export default function DocumentsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFormat, setSelectedFormat] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<'date' | 'name' | 'size'>('date');
  const [showConfirm, setShowConfirm] = useState(false);
  const queryClient = useQueryClient();
  const router = useRouter();
  const { toast } = useToast();

  const {
    data: docsResponse,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['documents-list'],
    queryFn: () => documentsService.listDocuments(),
  });

  const resetMutation = useMutation({
    mutationFn: () => documentsService.resetInstance(),
    onSuccess: () => {
      // Clear all cached data so graph/chat/documents all reflect empty state
      queryClient.clear();
      toast({
        type: 'success',
        title: 'New instance created.',
        description: 'Upload files to begin.',
      });
      router.push('/upload');
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Reset Failed',
        description: err?.response?.data?.message || err?.message || 'Could not reset instance.',
      });
    },
  });

  const rawDocuments: DocumentMetadata[] = docsResponse?.data?.documents || [];

  // Filter & Sort Documents
  const filteredDocuments = rawDocuments
    .filter((doc) => {
      const matchesSearch =
        doc.original_filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
        doc.document_id.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesFormat =
        selectedFormat === 'ALL' || doc.file_type.toUpperCase() === selectedFormat;

      return matchesSearch && matchesFormat;
    })
    .sort((a, b) => {
      if (sortBy === 'name') {
        return a.original_filename.localeCompare(b.original_filename);
      }
      if (sortBy === 'size') {
        return b.file_size_bytes - a.file_size_bytes;
      }
      return new Date(b.upload_timestamp).getTime() - new Date(a.upload_timestamp).getTime();
    });

  return (
    <div className="space-y-6">
      {/* ── Confirmation Dialog ── */}
      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-red-500/30 bg-slate-900 p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-red-500" />
              </div>
              <h2 className="text-base font-bold text-white">Start a new instance?</h2>
            </div>
            <p className="text-sm text-slate-400 mb-6 leading-relaxed">
              This will <span className="text-red-400 font-semibold">permanently delete</span> your current
              documents and knowledge graph data. Your login account will remain unchanged.
            </p>
            <div className="flex gap-3 justify-end">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowConfirm(false)}
                disabled={resetMutation.isPending}
                className="rounded-xl"
              >
                Cancel
              </Button>
              <Button
                variant="outline"
                size="sm"
                isLoading={resetMutation.isPending}
                onClick={() => { setShowConfirm(false); resetMutation.mutate(); }}
                className="rounded-xl border-red-500/50 text-red-400 hover:bg-red-950/40"
              >
                Yes, Reset Everything
              </Button>
            </div>
          </div>
        </div>
      )}

      <PageHeader
        title="Uploaded Compliance Documents"
        description="Catalog of all ingested PDF policy documents, CSV asset inventories, and MP3 audit recordings."
        badge={`${rawDocuments.length} Registered Files`}
        action={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
              Refresh Catalog
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowConfirm(true)}
              className="border-red-500/30 text-red-500 hover:bg-red-950/30"
            >
              <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
              New Instance
            </Button>
          </div>
        }
      />

      {/* Filter, Search & Sorting Bar */}
      <Card>
        <CardContent className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <SearchBar
            value={searchTerm}
            onChange={setSearchTerm}
            placeholder="Search filename or ID..."
            className="max-w-md"
          />

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1 text-xs">
              <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
              <span className="text-slate-500 font-medium">Sort:</span>
              <select
                value={sortBy}
                onChange={(e: any) => setSortBy(e.target.value)}
                className="bg-transparent text-xs font-semibold text-slate-700 dark:text-slate-200 focus:outline-none cursor-pointer"
              >
                <option value="date">Date</option>
                <option value="name">Name</option>
                <option value="size">Size</option>
              </select>
            </div>

            <div className="flex items-center gap-1">
              {['ALL', 'PDF', 'CSV', 'AUDIO'].map((fmt) => (
                <Button
                  key={fmt}
                  variant={selectedFormat === fmt ? 'primary' : 'outline'}
                  size="sm"
                  onClick={() => setSelectedFormat(fmt)}
                  className="text-xs h-8"
                >
                  {fmt}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Documents Content Table */}
      {isLoading ? (
        <Card>
          <div className="p-6 space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        </Card>
      ) : isError ? (
        <ErrorState
          title="Failed to Load Documents"
          message={(error as any)?.message || 'Could not connect to backend API server.'}
          onRetry={() => refetch()}
        />
      ) : filteredDocuments.length === 0 ? (
        <EmptyState
          title="No Documents Found"
          description={
            searchTerm
              ? `No files match "${searchTerm}".`
              : 'No documents have been uploaded to GraphGuard AI yet.'
          }
          actionLabel="Upload New File"
          onAction={() => (window.location.href = '/upload')}
        />
      ) : (
        <Card>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Document Name</TableHead>
                <TableHead>Format</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Uploaded At</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredDocuments.map((doc) => (
                <TableRow key={doc.document_id}>
                  <TableCell className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
                    <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                    <div>
                      <span>{doc.original_filename}</span>
                      <span className="block text-[11px] font-mono text-slate-400">
                        ID: {doc.document_id.substring(0, 8)}...
                      </span>
                    </div>
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
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      {doc.cloudinary_url && (
                        <a
                          href={doc.cloudinary_url}
                          target="_blank"
                          rel="noreferrer"
                        >
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-slate-400 hover:text-slate-600"
                            title="View remote document"
                          >
                            <ExternalLink className="h-4 w-4" />
                          </Button>
                        </a>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </div>
  );
}
