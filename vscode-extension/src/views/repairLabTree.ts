import * as vscode from 'vscode'
import { CodeGuardianApiClient } from '../api/client'

export class RepairLabTreeProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
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
    if (element) return []

    const candidates = await this.client.getRepairCandidates()
    return candidates.map((cand) => {
      const item = new vscode.TreeItem(cand.label, vscode.TreeItemCollapsibleState.None)
      item.description = cand.final_status
      item.tooltip = `${cand.description}\n\nDiff:\n${cand.diff}`
      item.iconPath = cand.is_recommended
        ? new vscode.ThemeIcon('pass', new vscode.ThemeColor('testing.iconPassed'))
        : new vscode.ThemeIcon('error', new vscode.ThemeColor('testing.iconFailed'))
      return item
    })
  }
}
