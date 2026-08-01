'use client';

import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import {
  Send,
  Bot,
  User,
  ShieldCheck,
  Sparkles,
  BookOpen,
  Network,
  HelpCircle,
  Loader2,
  FileText,
  AlertCircle,
} from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { queryService } from '@/services/query.service';
import { useToast } from '@/hooks/useToast';
import { Citation, QueryResponse } from '@/types/query';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  response?: QueryResponse;
  timestamp: string;
}

export default function ChatPage() {
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-welcome',
      sender: 'assistant',
      text: 'Hello! I am your Compliance Knowledge Graph Assistant. Ask me anything about your uploaded regulatory policies, data assets, or system governance rules.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [activeResponse, setActiveResponse] = useState<QueryResponse | null>(null);
  const { toast } = useToast();

  const suggestedQueries = [
    'What technical measures does GDPR Article 32 require for customer data storage?',
    'Which applications store PII data and who owns them?',
    'Are there any SOC 2 compliance risks identified in our storage buckets?',
  ];

  // TanStack Mutation connecting POST /query
  const queryMutation = useMutation({
    mutationFn: (qText: string) => queryService.executeQuery({ question: qText, top_k: 5 }),
    onSuccess: (res, qText) => {
      const qData = res.data;

      const newMsg: ChatMessage = {
        id: Math.random().toString(36).substring(2, 9),
        sender: 'assistant',
        text: qData.answer,
        response: qData,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, newMsg]);
      setActiveResponse(qData);
      setQuestion('');
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Query Failed',
        description: err.message || 'Error occurred while querying the Knowledge Graph.',
      });
    },
  });

  const handleSendQuestion = (textToSend?: string) => {
    const q = textToSend || question;
    if (!q.trim() || queryMutation.isPending) return;

    // Push user message
    const userMsg: ChatMessage = {
      id: Math.random().toString(36).substring(2, 9),
      sender: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    queryMutation.mutate(q);
  };

  return (
    <div className="space-y-6 h-[calc(100vh-7rem)] flex flex-col">
      <PageHeader
        title="Compliance RAG Assistant"
        description="Query the Neo4j Knowledge Graph using natural language. Answers are strictly grounded with verbatim document citations."
        badge="GraphRAG Active"
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
        {/* Left Column: Chat Conversation Window */}
        <Card className="lg:col-span-2 flex flex-col min-h-0">
          <CardHeader className="py-4 border-b border-slate-100 dark:border-slate-800/60 flex flex-row items-center justify-between space-y-0">
            <div className="flex items-center gap-2.5">
              <Bot className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              <CardTitle className="text-base">GraphGuard AI Assistant</CardTitle>
            </div>
            <Badge variant="success">Grounded Answers</Badge>
          </CardHeader>

          {/* Chat Messages */}
          <CardContent className="flex-1 overflow-y-auto p-6 space-y-6">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex items-start gap-3 ${
                  msg.sender === 'user' ? 'flex-row-reverse' : ''
                }`}
              >
                <div
                  className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl font-bold shadow-xs ${
                    msg.sender === 'user'
                      ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900'
                      : 'bg-blue-600 text-white'
                  }`}
                >
                  {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-5 h-5" />}
                </div>

                <div
                  className={`flex flex-col gap-1.5 max-w-xl ${
                    msg.sender === 'user' ? 'items-end' : ''
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                      {msg.sender === 'user' ? 'You' : 'GraphGuard Assistant'}
                    </span>
                    <span className="text-[10px] text-slate-400">{msg.timestamp}</span>
                  </div>

                  <div
                    className={`p-4 rounded-2xl text-sm leading-relaxed ${
                      msg.sender === 'user'
                        ? 'bg-blue-600 text-white rounded-tr-none'
                        : 'bg-slate-100 dark:bg-slate-800/80 text-slate-900 dark:text-slate-100 rounded-tl-none border border-slate-200/60 dark:border-slate-700/60'
                    }`}
                  >
                    {msg.text}

                    {/* Grounded Response Metadata Badge */}
                    {msg.response && (
                      <div className="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700/60 flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <span className="text-slate-500 dark:text-slate-400">Confidence:</span>
                          <span className="font-bold text-emerald-600 dark:text-emerald-400">
                            {Math.round(msg.response.confidence * 100)}%
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5 text-slate-500">
                          <BookOpen className="w-3.5 h-3.5" />
                          <span>{msg.response.citations.length} Citations</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {/* Query Processing Spinner */}
            {queryMutation.isPending && (
              <div className="flex items-start gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white shadow-xs">
                  <Bot className="w-5 h-5" />
                </div>
                <div className="p-4 rounded-2xl bg-slate-100 dark:bg-slate-800/80 text-sm text-slate-600 dark:text-slate-300 flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                  <span>Retrieving vector + graph context from Neo4j...</span>
                </div>
              </div>
            )}

            {/* Prompt Suggestions */}
            {messages.length < 3 && (
              <div className="p-4 rounded-2xl border border-blue-100 dark:border-blue-900/40 bg-blue-50/50 dark:bg-blue-950/20 space-y-3">
                <div className="flex items-center gap-2 text-xs font-semibold text-blue-700 dark:text-blue-300">
                  <Sparkles className="w-4 h-4" />
                  <span>Suggested Compliance Queries</span>
                </div>
                <div className="space-y-2">
                  {suggestedQueries.map((sQuery, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSendQuestion(sQuery)}
                      disabled={queryMutation.isPending}
                      className="w-full text-left p-2.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 text-xs font-medium text-slate-700 dark:text-slate-300 hover:border-blue-500/50 hover:text-blue-600 dark:hover:text-blue-400 transition-all flex items-center justify-between group"
                    >
                      <span>{sQuery}</span>
                      <HelpCircle className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-500 shrink-0 ml-2" />
                    </button>
                  ))}
                </div>
              </div>
            )}
          </CardContent>

          {/* Chat Input Form */}
          <div className="p-4 border-t border-slate-100 dark:border-slate-800/60 bg-white dark:bg-slate-900">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendQuestion();
              }}
              className="flex items-center gap-3"
            >
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a compliance question..."
                disabled={queryMutation.isPending}
                className="flex-1 h-11 px-4 text-sm rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <Button
                variant="primary"
                size="md"
                type="submit"
                isLoading={queryMutation.isPending}
              >
                <Send className="w-4 h-4 mr-1.5" />
                Ask
              </Button>
            </form>
          </div>
        </Card>

        {/* Right Column: Citation & Subgraph Provenance */}
        <div className="space-y-6 flex flex-col min-h-0">
          <Card className="flex-1 flex flex-col min-h-0">
            <CardHeader className="py-4 border-b border-slate-100 dark:border-slate-800/60">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  <CardTitle className="text-sm">Retrieved Citations</CardTitle>
                </div>
                {activeResponse && (
                  <Badge variant="success">
                    {Math.round(activeResponse.confidence * 100)}% Match
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="p-4 flex-1 overflow-y-auto space-y-3">
              {!activeResponse || activeResponse.citations.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-400">
                  Execute a query to inspect verbatim document evidence citations.
                </div>
              ) : (
                activeResponse.citations.map((c, i) => (
                  <div
                    key={i}
                    className="p-3.5 rounded-xl border border-slate-200/80 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/40 space-y-2"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-blue-600 dark:text-blue-400 truncate max-w-[180px]">
                        {c.document_name}
                      </span>
                      {c.page_number && (
                        <Badge variant="primary">Page {c.page_number}</Badge>
                      )}
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-300 italic leading-relaxed">
                      "{c.snippet}"
                    </p>
                    <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-200/40 dark:border-slate-800/40">
                      <span>ID: {c.chunk_id}</span>
                      <span>Confidence: {Math.round(c.confidence_score * 100)}%</span>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          {/* Subgraph Triple Path View */}
          <Card>
            <CardHeader className="py-3 border-b border-slate-100 dark:border-slate-800/60">
              <div className="flex items-center gap-2">
                <Network className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                <CardTitle className="text-sm">Retrieved Graph Triples</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="p-4 text-xs text-slate-500 dark:text-slate-400">
              {!activeResponse || activeResponse.subgraph.edges.length === 0 ? (
                <div className="text-center py-3 text-[11px]">
                  Graph paths will display here after querying.
                </div>
              ) : (
                <div className="p-3 rounded-xl bg-slate-900 text-slate-100 font-mono text-[11px] space-y-2 max-h-48 overflow-y-auto">
                  {activeResponse.subgraph.edges.map((edge, idx) => (
                    <div key={idx} className="space-y-0.5">
                      <span className="text-blue-400 font-bold">{edge.source}</span>
                      <span className="text-slate-400">
                        {' '}──[{edge.type || edge.relationship_type || 'RELATED_TO'}]──►{' '}
                      </span>
                      <span className="text-emerald-400 font-bold">{edge.target}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
