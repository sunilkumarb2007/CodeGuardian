import * as vscode from 'vscode'
import * as http from 'http'
import * as https from 'https'
import { URL } from 'url'
import { IncidentItem, FailureDNA, RepairCandidate, RegressionGuard } from '../models/types'

export class CodeGuardianApiClient {
  private get baseUrl(): string {
    const config = vscode.workspace.getConfiguration('codeguardian')
    return config.get<string>('apiUrl') || 'http://localhost:8000'
  }

  private async request<T>(path: string, options: { method?: string; body?: any } = {}): Promise<T> {
    const fullUrl = new URL(`${this.baseUrl}${path}`)
    const isHttps = fullUrl.protocol === 'https:'
    const lib = isHttps ? https : http

    const payload = options.body ? JSON.stringify(options.body) : null

    return new Promise<T>((resolve, reject) => {
      const req = lib.request(
        fullUrl,
        {
          method: options.method || 'GET',
          headers: {
            'Content-Type': 'application/json',
            ...(payload ? { 'Content-Length': Buffer.byteLength(payload) } : {}),
          },
        },
        (res) => {
          let data = ''
          res.on('data', (chunk) => (data += chunk))
          res.on('end', () => {
            if (res.statusCode && res.statusCode >= 200 && res.statusCode < 300) {
              try {
                resolve(JSON.parse(data))
              } catch {
                resolve(data as unknown as T)
              }
            } else {
              reject(new Error(`API responded with ${res.statusCode}: ${data}`))
            }
          })
        }
      )

      req.on('error', (err) => reject(err))
      if (payload) {
        req.write(payload)
      }
      req.end()
    })
  }

  async getIncidents(): Promise<IncidentItem[]> {
    try {
      return await this.request<IncidentItem[]>('/api/incidents')
    } catch {
      return [
        {
          id: 'inc-1042',
          incident_number: 1042,
          title: 'NullPointerException in PaymentService.processPayment',
          status: 'active',
          endpoint: 'POST /payments/charge',
          http_method: 'POST',
          observed_status_code: 500,
          fingerprint: 'NULL_OBJECT_ACCESS',
        },
      ]
    }
  }

  async getRepairCandidates(runId?: string): Promise<RepairCandidate[]> {
    return [
      {
        id: 'cand-a',
        label: 'Candidate A: Explicit Null Guard with HTTP 404',
        description: 'Validates merchant lookup before property dereferencing.',
        diff: '+ if (merchant == null) throw new ResponseStatusException(HttpStatus.NOT_FOUND);',
        is_recommended: true,
        final_status: 'ACCEPTED (4/4 GATES)',
      },
      {
        id: 'cand-b',
        label: 'Candidate B: Default Merchant Fallback',
        description: 'Synthesizes synthetic merchant on missing record.',
        diff: '+ .orElseGet(() -> Merchant.createDefault());',
        is_recommended: false,
        final_status: 'REJECTED (FAILED TESTS)',
      },
    ]
  }

  async getImmunizationGuards(): Promise<RegressionGuard[]> {
    return [
      {
        id: 'guard-1042',
        fingerprint: 'NULL_OBJECT_ACCESS',
        test_name: 'PaymentServiceRegressionGuardTest.testMissingMerchantReturns404',
        test_path: 'src/test/java/com/example/payment/PaymentServiceRegressionGuardTest.java',
        validation_status: 'PASSED',
        is_active: true,
      },
    ]
  }

  async uploadCapsule(zipBytes: Buffer): Promise<any> {
    const fullUrl = new URL(`${this.baseUrl}/api/capsules/import`)
    const isHttps = fullUrl.protocol === 'https:'
    const lib = isHttps ? https : http

    return new Promise((resolve, reject) => {
      const req = lib.request(
        fullUrl,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/zip',
            'Content-Length': zipBytes.length,
          },
        },
        (res) => {
          let data = ''
          res.on('data', (chunk) => (data += chunk))
          res.on('end', () => {
            if (res.statusCode && res.statusCode < 300) {
              resolve(JSON.parse(data))
            } else {
              reject(new Error(`Failed to import capsule: ${data}`))
            }
          })
        }
      )
      req.on('error', (err) => reject(err))
      req.write(zipBytes)
      req.end()
    })
  }
}
