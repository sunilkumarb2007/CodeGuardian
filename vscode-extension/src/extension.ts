import * as vscode from 'vscode'
import { CodeGuardianApiClient } from './api/client'
import { IncidentTreeProvider } from './views/incidentTree'
import { RepairLabTreeProvider } from './views/repairLabTree'
import { ImmunizationTreeProvider } from './views/immunizationTree'
import { investigateSelectionCommand } from './commands/investigateCommand'
import { loadCapsuleCommand } from './commands/capsuleCommand'

export function activate(context: vscode.ExtensionContext): void {
  const config = vscode.workspace.getConfiguration('codeguardian')
  const client = new CodeGuardianApiClient()

  // Register Tree Views in CodeGuardian Activity Bar
  const incidentTree = new IncidentTreeProvider(client)
  const repairLabTree = new RepairLabTreeProvider(client)
  const immunizationTree = new ImmunizationTreeProvider(client)

  vscode.window.registerTreeDataProvider('codeguardian.incidentsView', incidentTree)
  vscode.window.registerTreeDataProvider('codeguardian.repairLabView', repairLabTree)
  vscode.window.registerTreeDataProvider('codeguardian.immunizationView', immunizationTree)

  // Register Commands
  context.subscriptions.push(
    vscode.commands.registerCommand('codeguardian.investigateSelection', () =>
      investigateSelectionCommand()
    ),
    vscode.commands.registerCommand('codeguardian.loadCapsule', () =>
      loadCapsuleCommand(client)
    ),
    vscode.commands.registerCommand('codeguardian.refreshIncidents', () => {
      incidentTree.refresh()
      repairLabTree.refresh()
      immunizationTree.refresh()
      vscode.window.showInformationMessage('CodeGuardian: Telemetry refreshed.')
    }),
    vscode.commands.registerCommand('codeguardian.openDashboard', (runOrIncidentId?: string) => {
      const dashboardUrl = config.get<string>('dashboardUrl') || 'http://localhost:5173'
      const targetUrl = runOrIncidentId ? `${dashboardUrl}/runs/${runOrIncidentId}` : dashboardUrl
      vscode.env.openExternal(vscode.Uri.parse(targetUrl))
    })
  )
}

export function deactivate(): void {}
