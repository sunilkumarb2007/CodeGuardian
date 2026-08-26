const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function startDemo(repositoryUrl) {
  const response = await fetch(`${API_BASE_URL}/api/demo/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ repository_url: repositoryUrl })
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail?.message || `Failed to start demo: ${response.statusText}`);
  }
  
  return response.json();
}

export async function getDemoRun(runId) {
  const response = await fetch(`${API_BASE_URL}/api/demo/runs/${runId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch run status: ${response.statusText}`);
  }
  return response.json();
}

export async function getDemoResult(runId) {
  const response = await fetch(`${API_BASE_URL}/api/demo/runs/${runId}/result`);
  if (!response.ok) {
    throw new Error(`Failed to fetch run result: ${response.statusText}`);
  }
  return response.json();
}

export async function approveDemo(runId) {
  const response = await fetch(`${API_BASE_URL}/api/demo/runs/${runId}/approve`, {
    method: 'POST'
  });
  if (!response.ok) {
    throw new Error(`Failed to approve run: ${response.statusText}`);
  }
  return response.json();
}

export async function rejectDemo(runId) {
  const response = await fetch(`${API_BASE_URL}/api/demo/runs/${runId}/reject`, {
    method: 'POST'
  });
  if (!response.ok) {
    throw new Error(`Failed to reject run: ${response.statusText}`);
  }
  return response.json();
}
