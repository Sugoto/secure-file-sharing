const API_URL = 'http://localhost:8000';

export const httpClient = {
  getHeaders(): HeadersInit {
    const token = localStorage.getItem('token');
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  },

  async get(endpoint: string) {
    const response = await fetch(`${API_URL}${endpoint}`, {
      headers: this.getHeaders(),
    });
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  },

  async post(endpoint: string, data: unknown) {
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  }
};
