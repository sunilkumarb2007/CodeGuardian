import * as vscode from 'vscode'
import * as fs from 'fs'
import { CodeGuardianApiClient } from '../api/client'

export async function loadCapsuleCommand(client: CodeGuardianApiClient): Promise<void> {
  const uris = await vscode.window.showOpenDialog({
    canSelectFiles: true,
    canSelectMany: false,
    filters: {
      'Failure Capsules (*.zip)': ['zip'],
    },
    openLabel: 'Import Failure Capsule',
  })

  if (!uris || uris.length === 0) return

  const fileUri = uris[0]
  try {
    const fileBytes = fs.readFileSync(fileUri.fsPath)
    
    vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: 'CodeGuardian: Validating sealed Failure Capsule...',
      },
      async (progress) => {
        progress.report({ increment: 40, message: 'Verifying path traversal safety and secret redactions...' })
        const res = await client.uploadCapsule(fileBytes)
        progress.report({ increment: 100, message: 'Verified!' })

        vscode.window.showInformationMessage(
          `Failure Capsule Verified: ${res.title || 'Imported Incident'} (${res.files_count} files, Fingerprint: ${res.fingerprint}).`,
          'Open in IDE'
        )
      }
    )
  } catch (err: any) {
    vscode.window.showErrorMessage(`Failed to import Failure Capsule: ${err?.message || err}`)
  }
}
