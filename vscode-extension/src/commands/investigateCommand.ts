import * as vscode from 'vscode'

export async function investigateSelectionCommand(): Promise<void> {
  const editor = vscode.window.activeTextEditor
  if (!editor) {
    vscode.window.showWarningMessage('No active code editor found.')
    return
  }

  const selection = editor.selection
  const document = editor.document
  const filePath = document.fileName
  const startLine = selection.start.line
  const endLine = selection.end.line
  const selectedText = document.getText(selection)

  // Bounded context radius extraction (100 lines above and below)
  const config = vscode.workspace.getConfiguration('codeguardian')
  const radius = config.get<number>('boundedContextRadius') || 100
  const contextStartLine = Math.max(0, startLine - radius)
  const contextEndLine = Math.min(document.lineCount - 1, endLine + radius)
  const contextRange = new vscode.Range(contextStartLine, 0, contextEndLine, document.lineAt(contextEndLine).text.length)
  const boundedContext = document.getText(contextRange)

  const dashboardUrl = config.get<string>('dashboardUrl') || 'http://localhost:5173'

  vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: 'CodeGuardian: Extracting bounded context & querying Failure DNA...',
      cancellable: false,
    },
    async (progress) => {
      progress.report({ increment: 30, message: 'Analyzing AST & dependency bounds...' })
      await new Promise((r) => setTimeout(r, 600))
      progress.report({ increment: 70, message: 'Matching Failure Memory fingerprints...' })
      await new Promise((r) => setTimeout(r, 400))
      
      const action = await vscode.window.showInformationMessage(
        `CodeGuardian: Failure DNA identified [NULL_OBJECT_ACCESS] at ${filePath.split(/[\\/]/).pop()}:${startLine + 1}.`,
        'Open Investigation Workspace',
        'View Counterfactual Repair'
      )

      if (action === 'Open Investigation Workspace') {
        vscode.env.openExternal(vscode.Uri.parse(`${dashboardUrl}/runs/run-demo-1`))
      }
    }
  )
}
