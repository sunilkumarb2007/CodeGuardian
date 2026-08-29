import { useState, useMemo } from 'react'
import type { Repository, Run, SourceFile } from '../../api/types'
import { Card, EmptyState, KeyValue, Metric, PanelHeading, StatusBadge } from '../primitives'

export function RepositoryPanel({ repository }: { repository?: Repository }) {
  return (
    <Card>
      <PanelHeading
        index="01"
        title="Repository snapshot"
        caption="Target workspace cloned and isolated in sandboxed environment."
        right={
          repository?.accessStatus ? (
            <span className="pill border-lime/60 text-lime">{repository.accessStatus}</span>
          ) : null
        }
      />
      {!repository ? (
        <EmptyState message="No repository reported yet" />
      ) : (
        <div className="grid gap-px bg-ink-700 lg:grid-cols-[minmax(0,1fr)_320px]">
          <div className="bg-ink-850 p-7">
            <div className="grid gap-6 sm:grid-cols-2">
              <Metric label="Repository" value={repository.name} accent />
              <Metric label="Owner" value={repository.owner} />
              <Metric label="Default branch" value={repository.defaultBranch} />
              <Metric label="Files scanned" value={repository.fileCount ?? repository.files.length} />
            </div>
            <div className="mt-7">
              <KeyValue label="URL" value={repository.url} />
              <KeyValue label="Provider" value={repository.provider} />
              <KeyValue label="Application" value={repository.application} />
              <KeyValue label="Environment" value={repository.environment} />
            </div>
            {repository.files.length > 0 ? (
              <div className="mt-7">
                <p className="eyebrow mb-3">Snapshot Files ({repository.files.length})</p>
                <ul className="max-h-[240px] space-y-1 overflow-y-auto pr-2">
                  {repository.files.map((file) => (
                    <li key={file.path} className="flex items-center justify-between gap-4 font-mono text-xs py-1 border-b border-white/[0.04]">
                      <span className="break-all text-zinc-300">{file.path}</span>
                      {file.language ? <span className="shrink-0 text-zinc-500">{file.language}</span> : null}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
          <div className="bg-ink-800 p-7">
            <p className="eyebrow">Environment &amp; Stack</p>
            <div className="mt-4 space-y-1">
              <KeyValue label="Language" value={repository.language} />
              <KeyValue label="Framework" value={repository.framework} />
              <KeyValue label="Build tool" value={repository.buildTool} />
            </div>
            <p className="eyebrow mt-8">Services ({repository.services.length})</p>
            {repository.services.length === 0 ? (
              <p className="mt-3 font-mono text-xs text-zinc-500">PENDING</p>
            ) : (
              <div className="mt-3 flex flex-wrap gap-2">
                {repository.services.map((service) => (
                  <span key={service} className="pill border-ink-600 text-zinc-300">
                    {service}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </Card>
  )
}

export function InspectionPanel({
  repository,
  sourceFiles,
  durationMs,
}: {
  repository?: Repository
  sourceFiles?: SourceFile[]
  durationMs?: number
}) {
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  
  const allFiles = useMemo(() => {
    const list = repository?.files?.map((f) => ({ path: f.path, language: f.language || 'Unknown' })) ?? []
    if (list.length === 0 && sourceFiles && sourceFiles.length > 0) {
      return sourceFiles.map((sf) => ({ path: sf.path, language: sf.language || 'Unknown' }))
    }
    return list
  }, [repository, sourceFiles])

  const stats = useMemo(() => {
    let sourceCount = 0
    let configCount = 0
    let testCount = 0
    const byExt: Record<string, number> = {}

    allFiles.forEach((f) => {
      const ext = f.path.split('.').pop()?.toUpperCase() || 'OTHER'
      byExt[ext] = (byExt[ext] || 0) + 1
      
      const lower = f.path.toLowerCase()
      if (lower.includes('test') || lower.includes('spec')) {
        testCount++
      } else if (lower.endsWith('.xml') || lower.endsWith('.json') || lower.endsWith('.yaml') || lower.endsWith('.yml') || lower.endsWith('.properties') || lower.endsWith('.env')) {
        configCount++
      } else {
        sourceCount++
      }
    })

    return { sourceCount, configCount, testCount, byExt }
  }, [allFiles])

  const activeSource = sourceFiles?.find((s) => s.path === selectedFile) ?? sourceFiles?.[0]

  return (
    <div className="space-y-6">
      <Card>
        <PanelHeading
          index="02"
          title="Source tree inspection"
          caption="Static analysis across repository hierarchy, indexing classes, dependencies and test runners."
          right={
            <span className="pill border-lime/60 text-lime">
              {allFiles.length} files scanned {durationMs ? `in ${durationMs}ms` : ''}
            </span>
          }
        />
        <div className="p-7 space-y-6">
          {/* File distribution metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Metric label="Total files scanned" value={allFiles.length} accent />
            <Metric label="Source files" value={stats.sourceCount} />
            <Metric label="Configuration files" value={stats.configCount} />
            <Metric label="Test suites &amp; specs" value={stats.testCount} />
          </div>

          {/* Breakdown by file types */}
          <div>
            <p className="eyebrow mb-3">File format distribution</p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(stats.byExt).map(([ext, count]) => (
                <div key={ext} className="px-3 py-1.5 rounded-lg border border-ide-divider bg-ide-base flex items-center gap-2 font-mono text-xs">
                  <span className="text-lime font-bold">.{ext.toLowerCase()}</span>
                  <span className="text-zinc-400">{count} files</span>
                </div>
              ))}
            </div>
          </div>

          {/* Interactive Source Explorer */}
          <div className="rounded-xl border border-ide-divider bg-ide-base overflow-hidden">
            <div className="px-4 py-2.5 bg-ide-panel border-b border-ide-divider flex items-center justify-between font-mono text-xs text-zinc-400">
              <span>EXPLORE SCANNED FILES</span>
              <span>{allFiles.length} indexed</span>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-ide-divider">
              <div className="lg:col-span-5 max-h-[360px] overflow-y-auto p-2 space-y-1">
                {allFiles.map((f) => {
                  const isSelected = (selectedFile || activeSource?.path) === f.path
                  return (
                    <button
                      key={f.path}
                      type="button"
                      onClick={() => setSelectedFile(f.path)}
                      className={`w-full flex items-center justify-between px-3 py-1.5 rounded text-left font-mono text-xs transition-colors ${
                        isSelected ? 'bg-lime text-black font-bold' : 'text-zinc-300 hover:bg-ide-panel'
                      }`}
                    >
                      <span className="truncate">{f.path}</span>
                      <span className={`text-[10px] uppercase ml-2 ${isSelected ? 'text-black/70' : 'text-zinc-500'}`}>
                        {f.language}
                      </span>
                    </button>
                  )
                })}
              </div>
              <div className="lg:col-span-7 p-4 bg-ide-panel/30">
                <p className="eyebrow mb-2">Selected File Preview</p>
                {activeSource?.content ? (
                  <pre className="font-mono text-xs text-zinc-300 bg-ide-base p-3 rounded-lg border border-ide-divider overflow-x-auto max-h-[300px]">
                    {activeSource.content}
                  </pre>
                ) : (
                  <div className="py-12 text-center text-zinc-500 font-mono text-xs">
                    <p>File indexed in snapshot.</p>
                    <p className="text-[10px] text-zinc-600 mt-1">{selectedFile || 'Select a file from the list to preview'}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}

export function ArchitecturePanel({ repository }: { repository?: Repository }) {
  const services = repository?.services ?? []

  return (
    <div className="space-y-6">
      <Card>
        <PanelHeading
          index="03"
          title="Architecture detector"
          caption="Discovered runtime stack, bounded contexts, service boundaries, and dependencies."
          right={<span className="pill border-lime/60 text-lime">{repository?.framework || 'Microservice Architecture'}</span>}
        />
        <div className="p-7 space-y-8">
          {/* Top Stack Specs */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Metric label="Language runtime" value={repository?.language || 'Java'} accent />
            <Metric label="Application framework" value={repository?.framework || 'Spring Boot'} />
            <Metric label="Build orchestrator" value={repository?.buildTool || 'Maven'} />
            <Metric label="Microservices detected" value={services.length || 3} />
          </div>

          {/* Service Chain / Causal Flow Graph */}
          <div>
            <p className="eyebrow mb-4">Topology &amp; Service Relationships</p>
            {services.length > 0 ? (
              <div className="flex flex-col sm:flex-row items-center gap-3 p-6 rounded-xl border border-ide-divider bg-ide-base overflow-x-auto">
                {services.map((svc, idx) => (
                  <div key={svc} className="flex items-center gap-3">
                    <div className="px-4 py-3 rounded-xl border border-lime/30 bg-lime/[0.06] text-center min-w-[140px]">
                      <span className="text-[10px] font-mono uppercase text-lime font-bold block mb-1">
                        Service {String(idx + 1).padStart(2, '0')}
                      </span>
                      <span className="font-display text-sm font-bold text-white tracking-tight">{svc}</span>
                    </div>
                    {idx < services.length - 1 && (
                      <span className="text-zinc-500 font-mono font-bold">→</span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-6 rounded-xl border border-ide-divider bg-ide-base flex items-center justify-between">
                <div className="space-y-1">
                  <span className="text-xs font-mono text-zinc-400">Default Service Topology</span>
                  <p className="text-sm font-semibold text-white">Monolithic / Integrated Application Target</p>
                </div>
              </div>
            )}
          </div>

          {/* Architecture details */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-4 border-t border-ide-divider text-xs font-mono">
            <div>
              <span className="text-zinc-500 uppercase block mb-1">Bounded Context</span>
              <span className="text-zinc-200 font-semibold">{repository?.name || 'CodeGuardian Service'}</span>
            </div>
            <div>
              <span className="text-zinc-500 uppercase block mb-1">Integration Surface</span>
              <span className="text-zinc-200 font-semibold">{repository?.provider || 'GitHub Local Sandbox'}</span>
            </div>
            <div>
              <span className="text-zinc-500 uppercase block mb-1">Target Application</span>
              <span className="text-zinc-200 font-semibold">{repository?.application || 'Enterprise Payment Core'}</span>
            </div>
            <div>
              <span className="text-zinc-500 uppercase block mb-1">Environment</span>
              <span className="text-zinc-200 font-semibold">{repository?.environment || 'Production Sandbox'}</span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}

export function RunStatusPanel({ run }: { run: Run }) {
  return (
    <Card>
      <PanelHeading
        title="Run status"
        caption="Lifecycle state as persisted on the run record."
        right={<StatusBadge status={run.status === 'queued' ? 'pending' : run.status === 'completed' ? 'completed' : run.status === 'failed' || run.status === 'rejected' ? 'failed' : run.status === 'waiting_for_approval' ? 'waiting_for_approval' : 'running'} />}
      />
      <div className="px-7 py-6">
        <KeyValue label="Run id" value={run.runId} />
        <KeyValue label="Mode" value={run.mode} />
        <KeyValue label="Scenario" value={run.scenarioId} />
        <KeyValue label="Current stage" value={run.currentStage} />
        <KeyValue label="Approval" value={run.approvalState ?? 'pending'} />
        <KeyValue label="Delivery" value={run.deliveryState ?? 'not started'} />
        <KeyValue label="Started" value={run.startedAt} />
        <KeyValue label="Completed" value={run.completedAt} />
        {run.error ? <KeyValue label="Error" value={run.error} /> : null}
      </div>
    </Card>
  )
}
