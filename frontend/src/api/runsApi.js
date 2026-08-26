const API_BASE = '/api/runs';

export const runsApi = {
    async getWorkspace(runId) {
        const response = await fetch(`${API_BASE}/${runId}/workspace`);
        if (!response.ok) throw new Error('Failed to fetch workspace');
        return response.json();
    },

    async getAgentEvents(runId) {
        const response = await fetch(`${API_BASE}/${runId}/agent-events`);
        if (!response.ok) throw new Error('Failed to fetch events');
        return response.json();
    },

    async approveDelivery(runId) {
        const response = await fetch(`${API_BASE}/${runId}/approve`, { method: 'POST' });
        if (!response.ok) throw new Error('Failed to approve delivery');
        return response.json();
    },

    async rejectDelivery(runId) {
        const response = await fetch(`${API_BASE}/${runId}/reject`, { method: 'POST' });
        if (!response.ok) throw new Error('Failed to reject delivery');
        return response.json();
    },
    
    async startDemo() {
        const response = await fetch(`/api/demo/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                repository_url: "https://github.com/sunilkumarb2007/JavaAPICheck"
            })
        });
        if (!response.ok) throw new Error('Failed to start demo');
        return response.json();
    }
};
