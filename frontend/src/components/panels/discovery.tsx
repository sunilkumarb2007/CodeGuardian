import type { Repository, Run } from '../../api/types'
import { Card, EmptyState, KeyValue, Metric, PanelHeading, StatusBadge } from '../primitives'

export function RepositoryPanel({ repository }: { repository?: Repository }) {
  return (
    <Card>
      <PanelHeading
        index="01"
        title="Repository &amp; inspection"
        caption="What CodeGuardian was pointed at, and what it found when it looked inside."
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
              <Metric label="Files scanned" value={repository.fileCount} />
            </div>
            <div className="mt-7">
              <KeyValue label="URL" value={repository.url} />
              <KeyValue label="Provider" value={repository.provider} />
              <KeyValue label="Application" value={repository.application} />
              <KeyValue label="Environment" value={repository.environment} />
            </div>
            {repository.files.length > 0 ? (
              <ul className="mt-7 max-h-[240px] space-y-1 overflow-y-auto">
                {repository.files.map((file) => (
                  <li key={file.path} className="flex items-center justify-between gap-4 font-mono text-xs">
                    <span className="break-all text-ink-300">{file.path}</span>
                    {file.language ? <span className="shrink-0 text-ink-500">{file.language}</span> : null}
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
          <div className="bg-ink-800 p-7">
            <p className="eyebrow">Architecture</p>
            <div className="mt-4 space-y-1">
              <KeyValue label="Language" value={repository.language} />
              <KeyValue label="Framework" value={repository.framework} />
              <KeyValue label="Build tool" value={repository.buildTool} />
            </div>
            <p className="eyebrow mt-8">Services</p>
            {repository.services.length === 0 ? (
              <p className="mt-3 font-mono text-xs text-ink-500">not reported</p>
            ) : (
              <div className="mt-3 flex flex-wrap gap-2">
                {repository.services.map((service) => (
                  <span key={service} className="pill border-ink-600 text-ink-300">
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
