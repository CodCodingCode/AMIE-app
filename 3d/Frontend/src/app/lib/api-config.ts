/**
 * API Configuration
 * Handles different environments and API endpoints
 */

// Get the backend API URL from environment variables
const getApiUrl = (): string => {
  // Check if we have an environment variable set
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  // Always use Railway URL for now (since we don't have local backend)  
  return 'https://web-production-f5ba7.up.railway.app';
};

// Define the API configuration type
interface ApiConfig {
  BASE_URL: string;
  ENDPOINTS: {
    PROCESS_FILE: string;
  };
  getEndpoint: (endpoint: keyof ApiConfig['ENDPOINTS']) => string;
  fetchWithConfig: (endpoint: string, options?: RequestInit) => Promise<Response>;
}

export const API_CONFIG: ApiConfig = {
  BASE_URL: getApiUrl(),
  ENDPOINTS: {
    PROCESS_FILE: '/api/process-file',
  },
  
  // Helper method to get full endpoint URL
  getEndpoint: function(endpoint: keyof ApiConfig['ENDPOINTS']): string {
    return `${this.BASE_URL}${this.ENDPOINTS[endpoint]}`;
  },
  
  // Helper method for making API calls with proper error handling
  async fetchWithConfig(endpoint: string, options: RequestInit = {}): Promise<Response> {
    const url = endpoint.startsWith('http') ? endpoint : `${API_CONFIG.BASE_URL}${endpoint}`;
    
    // Don't set Content-Type for FormData - let the browser handle it
    const headers: Record<string, string> = {};
    
    // Only set Content-Type for JSON requests
    if (options.body && typeof options.body === 'string') {
      headers['Content-Type'] = 'application/json';
    }
    
    const response = await fetch(url, {
      ...options,
      headers: {
        ...headers,
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      let errorMessage = `HTTP error! status: ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.error || errorData.message || errorMessage;
      } catch {
        // If we can't parse the error response, use the default message
      }
      throw new Error(errorMessage);
    }
    
    return response;
  }
};

export default API_CONFIG; 