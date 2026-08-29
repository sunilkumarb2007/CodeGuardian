import * as vscode from 'vscode'
import { CodeGuardianApiClient } from '../api/client'

export class ImmunizationTreeProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
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

    const guards = await this.client.getImmunizationGuards()
    return guards.map((g) => {
      const item = new vscode.TreeItem(g.test_name, vscode.TreeItemCollapsibleState.None)
      item.description = `[${g.fingerprint}] · ${g.validation_status}`
      item.tooltip = `Guard Path: ${g.test_path}\nActive: ${g.is_active}\nFingerprint: ${g.fingerprint}`
      item.iconPath = new vscode.ThemeIcon('shield', new vscode.ThemeColor('charts.green'))
      return item
    })
  }
}
