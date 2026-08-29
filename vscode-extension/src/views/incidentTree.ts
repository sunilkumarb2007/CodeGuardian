import * as vscode from 'vscode'
import { CodeGuardianApiClient } from '../api/client'
import { IncidentItem } from '../models/types'

export class IncidentTreeProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
  private _onDidChangeTreeData: vscode.EventEmitter<vscode.TreeItem | undefined | null | void> = new vscode.EventEmitter<vscode.TreeItem | undefined | null | void>()
  readonly onDidChangeTreeData: vscode.Event<vscode.TreeItem | undefined | null | void> = this._onDidChangeTreeData.event

  constructor(private client: CodeGuardianApiClient) {}

  refresh(): void {
    this._onDidChangeTreeData.fire()
  }

  getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
    return element
  }

  async getChildren(element?: vscode.TreeItem): Promise<vscode.TreeItem[]> {
    if (element) {
      return []
    }

    try {
      const incidents = await this.client.getIncidents()
      if (incidents.length === 0) {
        const item = new vscode.TreeItem('No active engineering incidents detected')
        item.iconPath = new vscode.ThemeIcon('check')
        return [item]
      }

      return incidents.map((inc) => {
        const item = new vscode.TreeItem(
          `#${inc.incident_number}: ${inc.title}`,
          vscode.TreeItemCollapsibleState.None
        )
        item.description = `${inc.http_method || 'POST'} ${inc.endpoint || ''} [${inc.fingerprint || 'NULL_OBJECT_ACCESS'}]`
        item.tooltip = `Failure DNA: ${inc.fingerprint}\nStatus: ${inc.status}\nObserved HTTP: ${inc.observed_status_code}`
        item.iconPath = new vscode.ThemeIcon('error', new vscode.ThemeColor('errorForeground'))
        item.command = {
          command: 'codeguardian.openDashboard',
          title: 'Open in CodeGuardian Dashboard',
          arguments: [inc.id],
        }
        return item
      })
    } catch {
      const item = new vscode.TreeItem('Error fetching incidents from CodeGuardian backend')
      item.iconPath = new vscode.ThemeIcon('warning')
      return [item]
    }
  }
}
