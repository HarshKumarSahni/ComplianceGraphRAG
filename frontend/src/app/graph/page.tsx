'use client';

import React, { useState, useMemo, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ReactFlow,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
  Node,
  Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import {
  Network,
  RotateCcw,
  Layers,
  X,
  Maximize2,
  Minimize2,
  Trash2,
  ChevronDown,
  Info,
} from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Skeleton } from '@/components/ui/Loader';
import { graphService } from '@/services/graph.service';
import { GraphNode, GraphEdge } from '@/types/graph';
import { useToast } from '@/hooks/useToast';

// Colors mapped by node entity type
const nodeColorMap: Record<string, { bg: string; border: string; text: string }> = {
  Regulation: { bg: '#eff6ff', border: '#3b82f6', text: '#1d4ed8' },
  Policy: { bg: '#eff6ff', border: '#3b82f6', text: '#1d4ed8' },
  Application: { bg: '#eef2ff', border: '#6366f1', text: '#4338ca' },
  Storage: { bg: '#ecfdf5', border: '#10b981', text: '#047857' },
  'Cloud Service': { bg: '#ecfdf5', border: '#10b981', text: '#047857' },
  'Data Asset': { bg: '#ecfdf5', border: '#10b981', text: '#047857' },
  'Compliance Rule': { bg: '#fef3c7', border: '#f59e0b', text: '#b45309' },
  Risk: { bg: '#fff1f2', border: '#f43f5e', text: '#be123c' },
};

export default function GraphPage() {
  const [selectedNodeId, setSelectedNodeId] = useState<string>('');
  const [selectedRelType, setSelectedRelType] = useState<string>('');
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // Fetch Graph Data — always re-fetch on mount
  const { data: graphResponse, isLoading, refetch } = useQuery({
    queryKey: ['graph-data'],
    queryFn: () => graphService.getGraph(),
    refetchOnMount: 'always',
    staleTime: 0,
  });

  const clearGraphMutation = useMutation({
    mutationFn: () => graphService.resetGraph(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['graph-data'] });
      queryClient.invalidateQueries({ queryKey: ['graph-stats'] });
      setSelectedNode(null);
      setSelectedNodeId('');
      setSelectedRelType('');
      toast({
        type: 'success',
        title: 'Knowledge Graph Cleared',
        description: 'All nodes and relationships have been reset.',
      });
    },
    onError: (err: any) => {
      toast({
        type: 'error',
        title: 'Failed to Clear Graph',
        description: err.message || 'Could not reset Knowledge Graph.',
      });
    },
  });

  // Strict empty arrays — never use sample/fallback data
  const rawNodes: GraphNode[] = useMemo(() => graphResponse?.data?.nodes ?? [], [graphResponse]);
  const rawEdges: GraphEdge[] = useMemo(() => graphResponse?.data?.edges ?? [], [graphResponse]);

  // Unique relationship types list for dropdown
  const uniqueRelTypes = useMemo(() => {
    const typesSet = new Set<string>();
    rawEdges.forEach((e) => {
      const rel = e.relationship_type || e.type;
      if (rel) typesSet.add(rel);
    });
    return Array.from(typesSet).sort();
  }, [rawEdges]);

  // Filter nodes based on selected dropdown options
  const filteredNodes = useMemo(() => {
    let nodesList = rawNodes;

    // Filter by selected relationship type
    if (selectedRelType) {
      const matchingEdges = rawEdges.filter(
        (e) => (e.relationship_type || e.type) === selectedRelType
      );
      const connectedNodeIds = new Set<string>();
      matchingEdges.forEach((e) => {
        connectedNodeIds.add(e.source);
        connectedNodeIds.add(e.target);
      });
      nodesList = nodesList.filter((n) => connectedNodeIds.has(n.id || n.name));
    }

    return nodesList;
  }, [rawNodes, rawEdges, selectedRelType]);

  // Filter edges based on selected relationship type
  const filteredEdges = useMemo(() => {
    if (!selectedRelType) return rawEdges;
    return rawEdges.filter((e) => (e.relationship_type || e.type) === selectedRelType);
  }, [rawEdges, selectedRelType]);

  // Convert raw nodes to React Flow nodes with generous grid spacing (prevents clustering)
  const reactFlowNodes: Node[] = useMemo(() => {
    const total = filteredNodes.length || 1;
    const cols = Math.max(3, Math.ceil(Math.sqrt(total * 1.5)));
    const spacingX = 280; // Spacious 280px horizontal gap
    const spacingY = 170; // Spacious 170px vertical gap

    return filteredNodes.map((node, index) => {
      const row = Math.floor(index / cols);
      const col = index % cols;
      const offsetX = row % 2 === 1 ? 140 : 0; // Stagger alternating rows
      const x = col * spacingX + offsetX;
      const y = row * spacingY;

      const isSelected = selectedNodeId === (node.id || node.name);

      const colorScheme =
        nodeColorMap[node.type] || {
          bg: '#f8fafc',
          border: '#64748b',
          text: '#334155',
        };

      return {
        id: node.id || node.name || `node-${index}`,
        position: { x, y },
        data: {
          label: (
            <div className="flex flex-col items-center text-center p-2">
              <span className="text-[10px] uppercase font-bold tracking-wider opacity-75">
                {node.type}
              </span>
              <span className="text-xs font-bold mt-0.5">{node.name}</span>
            </div>
          ),
          rawNode: node,
        },
        style: {
          background: isSelected ? '#3b82f6' : colorScheme.bg,
          border: isSelected ? '3px solid #1d4ed8' : `2px solid ${colorScheme.border}`,
          color: isSelected ? '#ffffff' : colorScheme.text,
          borderRadius: '16px',
          padding: '8px 12px',
          boxShadow: isSelected
            ? '0 0 20px rgba(59, 130, 246, 0.5)'
            : '0 4px 12px rgba(0, 0, 0, 0.05)',
          cursor: 'pointer',
          width: 160,
          transition: 'all 0.2s ease',
        },
      };
    });
  }, [filteredNodes, selectedNodeId]);

  // Convert raw edges to React Flow edges
  const reactFlowEdges: Edge[] = useMemo(() => {
    const validNodeIds = new Set(filteredNodes.map((n) => n.id || n.name));

    return filteredEdges
      .filter((e) => validNodeIds.has(e.source) && validNodeIds.has(e.target))
      .map((edge, idx) => ({
        id: edge.id || `edge-${idx}`,
        source: edge.source,
        target: edge.target,
        label: edge.relationship_type || edge.type || 'RELATED_TO',
        animated: true,
        style: { stroke: '#94a3b8', strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#64748b',
        },
        labelStyle: { fill: '#64748b', fontSize: 10, fontWeight: 600 },
        labelBgStyle: { fill: '#ffffff', fillOpacity: 0.85 },
      }));
  }, [filteredEdges, filteredNodes]);

  const [nodes, setNodes, onNodesChange] = useNodesState(reactFlowNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(reactFlowEdges);

  React.useEffect(() => {
    setNodes(reactFlowNodes);
    setEdges(reactFlowEdges);
  }, [reactFlowNodes, reactFlowEdges, setNodes, setEdges]);

  const onNodeClick = useCallback((_: any, node: Node) => {
    const raw = (node.data as any).rawNode as GraphNode;
    setSelectedNode(raw);
    setSelectedNodeId(raw.id || raw.name);
  }, []);

  const handleNodeSelect = (nodeId: string) => {
    setSelectedNodeId(nodeId);
    if (!nodeId) {
      setSelectedNode(null);
      return;
    }
    const found = rawNodes.find((n) => (n.id || n.name) === nodeId);
    if (found) {
      setSelectedNode(found);
    }
  };

  return (
    <div className={`space-y-6 flex flex-col ${isFullscreen ? 'fixed inset-0 z-50 p-6 bg-slate-900' : 'h-[calc(100vh-7rem)]'}`}>
      {!isFullscreen && (
        <PageHeader
          title="Neo4j Compliance Knowledge Graph"
          description="Interactive visualization of extracted policies, applications, storage buckets, and compliance governance relationships."
          badge={`${rawNodes.length} Nodes | ${rawEdges.length} Edges`}
          action={
            <div className="flex items-center gap-2">
              {rawNodes.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  className="border-red-500/30 text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30"
                  onClick={() => clearGraphMutation.mutate()}
                  disabled={clearGraphMutation.isPending}
                >
                  <Trash2 className="w-4 h-4 mr-1.5" />
                  Clear Graph Data
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSelectedNodeId('');
                  setSelectedRelType('');
                  setSelectedNode(null);
                  refetch();
                }}
              >
                <RotateCcw className="w-4 h-4 mr-1.5" />
                Reset View
              </Button>
              <Button variant="primary" size="sm" onClick={() => setIsFullscreen(true)}>
                <Maximize2 className="w-4 h-4 mr-1.5" />
                Fullscreen
              </Button>
            </div>
          }
        />
      )}

      {/* Main Canvas Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 flex-1 min-h-0">
        {/* Left Sidebar Node & Relationship Selection Dropdowns */}
        {!isFullscreen && (
          <Card className="lg:col-span-1 flex flex-col min-h-0 border-slate-200 dark:border-slate-800">
            <CardHeader className="py-4 border-b border-slate-100 dark:border-slate-800/60">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <CardTitle className="text-sm font-semibold">Graph Filters & Navigator</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="p-4 space-y-5 flex-1 overflow-y-auto">

              {/* 1. NODE DROPDOWN */}
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 block">
                  Select Node ({rawNodes.length})
                </label>
                <div className="relative">
                  <select
                    value={selectedNodeId}
                    onChange={(e) => handleNodeSelect(e.target.value)}
                    className="w-full appearance-none rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 px-3.5 py-2.5 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all cursor-pointer pr-8"
                  >
                    <option value="">-- All Nodes ({rawNodes.length}) --</option>
                    {rawNodes.map((n) => (
                      <option key={n.id || n.name} value={n.id || n.name}>
                        [{n.type}] {n.name}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-3 pointer-events-none" />
                </div>
              </div>

              {/* 2. RELATIONSHIP DROPDOWN */}
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 block">
                  Select Relationship ({uniqueRelTypes.length})
                </label>
                <div className="relative">
                  <select
                    value={selectedRelType}
                    onChange={(e) => setSelectedRelType(e.target.value)}
                    className="w-full appearance-none rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 px-3.5 py-2.5 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all cursor-pointer pr-8"
                  >
                    <option value="">-- All Relationships ({rawEdges.length}) --</option>
                    {uniqueRelTypes.map((relType) => (
                      <option key={relType} value={relType}>
                        {relType}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="w-4 h-4 text-slate-400 absolute right-3 top-3 pointer-events-none" />
                </div>
              </div>

              {/* Selected Node Details Box */}
              {selectedNode && (
                <div className="mt-4 p-3.5 rounded-xl border border-blue-200/80 bg-blue-50/60 dark:border-blue-900/50 dark:bg-blue-950/30 text-xs space-y-2 animate-in fade-in duration-200">
                  <div className="flex items-center justify-between">
                    <span className="font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400 text-[10px]">
                      {selectedNode.type}
                    </span>
                    <button
                      onClick={() => {
                        setSelectedNode(null);
                        setSelectedNodeId('');
                      }}
                      className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  <h4 className="font-bold text-slate-900 dark:text-slate-100">{selectedNode.name}</h4>
                  {selectedNode.description && (
                    <p className="text-[11px] text-slate-600 dark:text-slate-300 leading-relaxed italic">
                      "{selectedNode.description}"
                    </p>
                  )}
                </div>
              )}

            </CardContent>
          </Card>
        )}

        {/* Center React Flow Canvas Viewport */}
        <Card className={`${isFullscreen ? 'lg:col-span-4' : 'lg:col-span-3'} flex flex-col relative overflow-hidden`}>
          {isFullscreen && (
            <button
              onClick={() => setIsFullscreen(false)}
              className="absolute top-4 left-4 z-30 p-2 rounded-xl bg-white/90 dark:bg-slate-900/90 text-slate-700 dark:text-slate-200 shadow-lg border border-slate-200 dark:border-slate-800"
            >
              <Minimize2 className="w-5 h-5" />
            </button>
          )}

          {isLoading ? (
            <div className="flex-1 flex items-center justify-center p-12">
              <Skeleton className="h-full w-full rounded-2xl" />
            </div>
          ) : rawNodes.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center p-12 text-center bg-slate-900/40 rounded-2xl">
              <div className="w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center mb-4 shadow-lg shadow-cyan-500/10">
                <Network className="w-8 h-8 text-cyan-400" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">No Knowledge Graph Data Found</h3>
              <p className="text-sm text-slate-400 max-w-md mb-6">
                Upload compliance documents (PDFs, CSVs, Audio) to extract entities, construct governance relationships, and view your custom interactive knowledge graph.
              </p>
              <a href="/upload">
                <Button className="bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold rounded-xl px-6 py-2.5 shadow-lg shadow-cyan-500/20 cursor-pointer">
                  Upload Documents to Build Graph
                </Button>
              </a>
            </div>
          ) : (
            <div className="flex-1 w-full h-full relative">
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={onNodeClick}
                fitView
                className="bg-slate-50/50 dark:bg-slate-950"
              >
                <Background color="#cbd5e1" gap={20} size={1} />
                <Controls />
              </ReactFlow>

              {/* Node Inspector Floating Overlay */}
              {selectedNode && (
                <div className="absolute top-4 right-4 z-20 w-80 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-slate-900/95 p-5 shadow-2xl backdrop-blur-md animate-in slide-in-from-right duration-200">
                  <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800/80 pb-3">
                    <span className="text-xs font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                      {selectedNode.type} Entity
                    </span>
                    <button
                      onClick={() => {
                        setSelectedNode(null);
                        setSelectedNodeId('');
                      }}
                      className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="mt-3 space-y-3">
                    <div>
                      <h4 className="text-base font-bold text-slate-900 dark:text-slate-100">
                        {selectedNode.name}
                      </h4>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                        {selectedNode.description || 'No description provided.'}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
