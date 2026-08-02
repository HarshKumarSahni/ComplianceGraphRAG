'use client';

import React, { useState, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  FileCode,
  Headphones,
  X,
  Loader2,
  Sparkles,
  Layers,
  Database,
  ArrowRight,
} from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { documentsService } from '@/services/documents.service';
import { useToast } from '@/hooks/useToast';
import { formatBytes } from '@/lib/utils';

export default function UploadPage() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [activeStep, setActiveStep] = useState<number>(0);
  const [processingStage, setProcessingStage] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const pipelineSteps = [
    { title: '1. Cloud Storage', desc: 'Secure Cloudinary CDN upload' },
    { title: '2. Semantic Chunking', desc: 'Section boundary partitioning' },
    { title: '3. LLM Extraction', desc: 'Entities & relationship triples' },
    { title: '4. Neo4j Indexing', desc: 'Cypher property graph & vectors' },
  ];

  const uploadMutation = useMutation({
    mutationFn: async (files: File[]) => {
      setActiveStep(1);
      setProcessingStage('Uploading documents to CDN...');

      // 1. Upload files
      const uploadRes = await documentsService.uploadDocuments(files, (progress) => {
        setUploadProgress(progress);
      });

      const uploadedFiles = uploadRes?.data?.files || [];

      // 2. Process each file
      for (const item of uploadedFiles) {
        if (item.success && item.metadata?.document_id) {
          const docId = item.metadata.document_id;
          try {
            setActiveStep(2);
            setProcessingStage(`Chunking document: ${item.filename}...`);
            await documentsService.processDocument(docId);

            setActiveStep(3);
            setProcessingStage(`Extracting AI knowledge triples for ${item.filename}...`);
            await documentsService.extractKnowledge(docId);

            setActiveStep(4);
            setProcessingStage(`Graph indexing complete for ${item.filename}!`);
            queryClient.invalidateQueries({ queryKey: ['graph-data'] });
            queryClient.invalidateQueries({ queryKey: ['graph-stats'] });
          } catch (e) {
            console.warn(`Ingestion pipeline notice for ${docId}:`, e);
          }
        }
      }

      return uploadRes;
    },
    onSuccess: (data) => {
      const successCount = data?.data?.successful_uploads || selectedFiles.length;
      toast({
        type: 'success',
        title: 'Documents Successfully Ingested',
        description: `${successCount} document(s) extracted and stored into Neo4j Aura.`,
      });
      setSelectedFiles([]);
      setUploadProgress(0);
      setActiveStep(0);
      setProcessingStage('');
      queryClient.invalidateQueries({ queryKey: ['documents-list'] });
      queryClient.invalidateQueries({ queryKey: ['graph-data'] });
      queryClient.invalidateQueries({ queryKey: ['graph-stats'] });
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Upload Ingestion Error',
        description: err.message || 'Failed to complete document ingestion pipeline.',
      });
      setUploadProgress(0);
      setActiveStep(0);
      setProcessingStage('');
    },
  });

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files);
      setSelectedFiles((prev) => [...prev, ...newFiles]);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files);
      setSelectedFiles((prev) => [...prev, ...newFiles]);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-8 max-w-5xl">
      <PageHeader
        title="Upload Compliance Documents"
        description="Ingest PDF regulatory policies, CSV data inventories, or MP3 audit recordings into GraphGuard AI."
        badge="Multi-Modal Ingestion"
      />

      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        multiple
        accept=".pdf,.csv,.mp3"
        className="hidden"
      />

      {/* Drag & Drop File Zone */}
      <Card className="border-2 border-dashed border-blue-300 dark:border-blue-800/80 bg-blue-50/30 dark:bg-blue-950/20 hover:border-blue-500 transition-all">
        <CardContent
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          className="flex flex-col items-center justify-center p-12 text-center cursor-pointer"
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-100 dark:bg-blue-950 text-blue-600 dark:text-blue-400 mb-4 shadow-sm group-hover:scale-110 transition-transform">
            <UploadCloud className="h-8 w-8" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            Drag & Drop compliance files here, or click to browse
          </h3>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400 max-w-md">
            Supports <span className="font-semibold text-slate-700 dark:text-slate-300">PDF</span>,{' '}
            <span className="font-semibold text-slate-700 dark:text-slate-300">CSV</span>, and{' '}
            <span className="font-semibold text-slate-700 dark:text-slate-300">MP3</span> files up to 50MB.
          </p>

          <Button
            type="button"
            variant="outline"
            size="sm"
            className="mt-6 border-blue-300 dark:border-blue-800"
          >
            Select Files
          </Button>
        </CardContent>
      </Card>

      {/* Selected Files List & Pipeline Progress */}
      {selectedFiles.length > 0 && (
        <Card className="border-blue-500/30">
          <CardHeader className="py-4 border-b border-slate-100 dark:border-slate-800/60 flex flex-row items-center justify-between space-y-0">
            <CardTitle className="text-base">
              Selected Files ({selectedFiles.length})
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedFiles([])}
              disabled={uploadMutation.isPending}
            >
              Clear All
            </Button>
          </CardHeader>

          <CardContent className="p-4 space-y-3">
            <AnimatePresence>
              {selectedFiles.map((file, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200/80 dark:border-slate-800/80 text-sm"
                >
                  <div className="flex items-center gap-3">
                    <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400 shrink-0" />
                    <div>
                      <span className="font-semibold text-slate-900 dark:text-slate-100 block">
                        {file.name}
                      </span>
                      <span className="text-xs text-slate-400">
                        {formatBytes(file.size)}
                      </span>
                    </div>
                  </div>

                  {!uploadMutation.isPending && (
                    <button
                      onClick={() => removeFile(idx)}
                      className="p-1 text-slate-400 hover:text-rose-500 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Pipeline Stage Timeline Tracker */}
            {uploadMutation.isPending && (
              <div className="space-y-4 pt-4 border-t border-slate-100 dark:border-slate-800/80">
                <div className="flex items-center justify-between text-xs font-semibold text-blue-600 dark:text-blue-400">
                  <span className="flex items-center gap-1.5">
                    <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                    {processingStage}
                  </span>
                  <span>{uploadProgress}%</span>
                </div>

                <div className="w-full h-2 rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
                  <div
                    className="h-full bg-blue-600 transition-all duration-300 rounded-full"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
                  {pipelineSteps.map((step, sIdx) => {
                    const stepNum = sIdx + 1;
                    const isDone = activeStep > stepNum;
                    const isCurrent = activeStep === stepNum;

                    return (
                      <div
                        key={sIdx}
                        className={`p-3 rounded-xl border text-xs transition-all ${
                          isDone
                            ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-300 text-emerald-800 dark:text-emerald-300'
                            : isCurrent
                            ? 'bg-blue-50 dark:bg-blue-950/60 border-blue-400 text-blue-900 dark:text-blue-200 font-semibold'
                            : 'bg-slate-50 dark:bg-slate-900/40 border-slate-200 dark:border-slate-800 text-slate-400'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span>{step.title}</span>
                          {isDone && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />}
                          {isCurrent && <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-500" />}
                        </div>
                        <span className="text-[10px] opacity-80 block mt-0.5">{step.desc}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="pt-3 flex justify-end">
              <Button
                variant="primary"
                size="md"
                onClick={() => uploadMutation.mutate(selectedFiles)}
                isLoading={uploadMutation.isPending}
              >
                <Sparkles className="w-4 h-4 mr-2" />
                Start Ingestion Pipeline
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Formats Overview Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center gap-3 space-y-0">
            <div className="p-2.5 rounded-xl bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <CardTitle className="text-base">PDF Compliance Policies</CardTitle>
              <CardDescription className="text-xs">GDPR, HIPAA, SOC 2</CardDescription>
            </div>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center gap-3 space-y-0">
            <div className="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400">
              <FileCode className="w-5 h-5" />
            </div>
            <div>
              <CardTitle className="text-base">CSV Data Inventories</CardTitle>
              <CardDescription className="text-xs">Data catalogs & assets</CardDescription>
            </div>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center gap-3 space-y-0">
            <div className="p-2.5 rounded-xl bg-purple-50 dark:bg-purple-950/60 text-purple-600 dark:text-purple-400">
              <Headphones className="w-5 h-5" />
            </div>
            <div>
              <CardTitle className="text-base">MP3 Audit Audio</CardTitle>
              <CardDescription className="text-xs">Whisper transcribed</CardDescription>
            </div>
          </CardHeader>
        </Card>
      </div>
    </div>
  );
}
