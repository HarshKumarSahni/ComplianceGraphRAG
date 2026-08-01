'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  FileText,
  Filter,
  Trash2,
  ExternalLink,
  RefreshCw,
  Sparkles,
  ArrowUpDown,
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
  const queryClient = useQueryClient();
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

  const extractMutation = useMutation({
    mutationFn: (documentId: string) => documentsService.extractKnowledge(documentId),
    onSuccess: (data) => {
      toast({
        type: 'success',
        title: 'Knowledge Extraction Complete',
        description: `Extracted ${data?.data?.entity_count || 0} entities & ${data?.data?.relationship_count || 0} relationships.`,
      });
      queryClient.invalidateQueries({ queryKey: ['documents-list'] });
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Extraction Failed',
        description: err.message || 'Could not extract entities from document.',
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
      <PageHeader
        title="Uploaded Compliance Documents"
        description="Catalog of all ingested PDF policy documents, CSV asset inventories, and MP3 audit recordings."
        badge={`${rawDocuments.length} Registered Files`}
        action={
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
            Refresh Catalog
          </Button>
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
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-8 text-xs"
                        isLoading={extractMutation.isPending}
                        onClick={() => extractMutation.mutate(doc.document_id)}
                        title="Run AI knowledge extraction"
                      >
                        <Sparkles className="w-3 h-3 mr-1 text-purple-500" />
                        Extract
                      </Button>

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
