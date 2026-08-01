'use client';

import React, { useState, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
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
  Filter,
  RotateCcw,
  Layers,
  X,
  Maximize2,
  Minimize2,
  Info,
  Database,
  Search,
} from 'lucide-react';
import { PageHeader } from '@/components/ui/PageHeader';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { SearchBar } from '@/components/ui/SearchBar';
import { Skeleton } from '@/components/ui/Loader';
import { graphService } from '@/services/graph.service';
import { GraphNode, GraphEdge } from '@/types/graph';

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
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Fetch Graph Data
  const { data: graphResponse, isLoading, refetch } = useQuery({
    queryKey: ['graph-data'],
    queryFn: () => graphService.getGraph(),
  });

  const rawNodes: GraphNode[] = graphResponse?.data?.nodes || [];
  const rawEdges: GraphEdge[] = graphResponse?.data?.edges || [];

  // Filter nodes by search term
  const filteredNodes = useMemo(() => {
    if (!searchTerm) return rawNodes;
    return rawNodes.filter(
      (n) =>
        n.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        n.type.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [rawNodes, searchTerm]);

  // Convert raw nodes to React Flow nodes
  const reactFlowNodes: Node[] = useMemo(() => {
    const center = { x: 400, y: 250 };
    const radius = 220;

    return filteredNodes.map((node, index) => {
      const angle = (index / (filteredNodes.length || 1)) * 2 * Math.PI;
      const x = center.x + radius * Math.cos(angle);
      const y = center.y + radius * Math.sin(angle);

      const colorScheme =
        nodeColorMap[node.type] || {
          bg: '#f8fafc',
          border: '#64748b',
          text: '#334155',
        };

      return {
        id: node.id || `node-${index}`,
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
          background: colorScheme.bg,
          border: `2px solid ${colorScheme.border}`,
          color: colorScheme.text,
          borderRadius: '16px',
          padding: '8px 12px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.05)',
          cursor: 'pointer',
          width: 160,
        },
      };
    });
  }, [filteredNodes]);

  // Convert raw edges to React Flow edges
  const reactFlowEdges: Edge[] = useMemo(() => {
    const validNodeIds = new Set(filteredNodes.map((n) => n.id));

    return rawEdges
      .filter((e) => validNodeIds.has(e.source) && validNodeIds.has(e.target))
      .map((edge, idx) => ({
        id: edge.id || `edge-${idx}`,
        source: edge.source,
        target: edge.target,
        label: edge.type || edge.relationship_type || 'RELATED_TO',
        animated: true,
        style: { stroke: '#94a3b8', strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#64748b',
        },
        labelStyle: { fill: '#64748b', fontSize: 10, fontWeight: 600 },
        labelBgStyle: { fill: '#ffffff', fillOpacity: 0.8 },
      }));
  }, [rawEdges, filteredNodes]);

  const [nodes, setNodes, onNodesChange] = useNodesState(reactFlowNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(reactFlowEdges);

  React.useEffect(() => {
    setNodes(reactFlowNodes);
    setEdges(reactFlowEdges);
  }, [reactFlowNodes, reactFlowEdges, setNodes, setEdges]);

  const onNodeClick = useCallback((_: any, node: Node) => {
    const raw = (node.data as any).rawNode as GraphNode;
    setSelectedNode(raw);
  }, []);

  return (
    <div className={`space-y-6 flex flex-col ${isFullscreen ? 'fixed inset-0 z-50 p-6 bg-slate-900' : 'h-[calc(100vh-7rem)]'}`}>
      {!isFullscreen && (
        <PageHeader
          title="Neo4j Compliance Knowledge Graph"
          description="Interactive visualization of extracted policies, applications, storage buckets, and compliance governance relationships."
          badge={`${rawNodes.length} Nodes | ${rawEdges.length} Edges`}
          action={
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => refetch()}>
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
        {/* Left Sidebar Filter & Legend */}
        {!isFullscreen && (
          <Card className="lg:col-span-1 flex flex-col min-h-0">
            <CardHeader className="py-4 border-b border-slate-100 dark:border-slate-800/60">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <CardTitle className="text-sm">Filter & Entity Legend</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="p-4 space-y-4 flex-1 overflow-y-auto">
              <SearchBar
                value={searchTerm}
                onChange={setSearchTerm}
                placeholder="Search node name..."
                className="max-w-full"
              />

              <div className="space-y-2 text-xs">
                <div className="p-2.5 rounded-xl bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900/50 flex items-center justify-between">
                  <span className="font-semibold text-blue-700 dark:text-blue-300">
                    Regulation / Policy
                  </span>
                  <Badge variant="primary">Blue</Badge>
                </div>
                <div className="p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-900/50 flex items-center justify-between">
                  <span className="font-semibold text-indigo-700 dark:text-indigo-300">
                    Application
                  </span>
                  <Badge variant="default">Indigo</Badge>
                </div>
                <div className="p-2.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900/50 flex items-center justify-between">
                  <span className="font-semibold text-emerald-700 dark:text-emerald-300">
                    Storage / Asset
                  </span>
                  <Badge variant="success">Emerald</Badge>
                </div>
                <div className="p-2.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900/50 flex items-center justify-between">
                  <span className="font-semibold text-amber-700 dark:text-amber-300">
                    Compliance Risk
                  </span>
                  <Badge variant="warning">Amber</Badge>
                </div>
              </div>
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
                <Background color="#cbd5e1" gap={16} size={1} />
                <Controls />
              </ReactFlow>

              {/* Node Inspector Card */}
              {selectedNode && (
                <div className="absolute top-4 right-4 z-20 w-80 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-slate-900/95 p-5 shadow-2xl backdrop-blur-md animate-in slide-in-from-right duration-200">
                  <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800/80 pb-3">
                    <span className="text-xs font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                      {selectedNode.type} Entity
                    </span>
                    <button
                      onClick={() => setSelectedNode(null)}
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

                    <div className="pt-2 border-t border-slate-100 dark:border-slate-800/80 text-xs space-y-1 text-slate-500">
                      <div>Node ID: <span className="font-mono text-slate-700 dark:text-slate-300">{selectedNode.id}</span></div>
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
