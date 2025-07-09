// API client for WatchTower AI backend
const API_BASE_URL = 'http://localhost:5050';

export interface ChatResponse {
  user_query: string;
  promql_query: string;
  explanation: string;
  raw_data: any;
  error?: string;
}

export interface HealthResponse {
  status: string;
  service: string;
}

export class WatchTowerAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async chat(query: string): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/chat?query=${encodeURIComponent(query)}`);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to get response');
      }
      
      return data;
    } catch (error) {
      console.error('Chat API error:', error);
      throw error;
    }
  }

  async checkHealth(): Promise<HealthResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/health`);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error('Health check failed');
      }
      
      return data;
    } catch (error) {
      console.error('Health check error:', error);
      throw error;
    }
  }

  async checkBackendConnection(): Promise<boolean> {
    try {
      await this.checkHealth();
      return true;
    } catch (error) {
      return false;
    }
  }
}

// Export singleton instance
export const api = new WatchTowerAPI();