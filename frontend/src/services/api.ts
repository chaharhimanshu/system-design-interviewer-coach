// API configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';

// API endpoints
export const API_ENDPOINTS = {
  // Authentication
  auth: {
    login: '/auth/login',
    logout: '/auth/logout',
    refresh: '/auth/refresh',
    profile: '/auth/profile'
  },
  
  // Sessions
  sessions: {
    list: '/sessions',
    create: '/sessions',
    get: (id: string) => `/sessions/${id}`,
    update: (id: string) => `/sessions/${id}`,
    delete: (id: string) => `/sessions/${id}`,
    feedback: (id: string) => `/sessions/${id}/feedback`,
    transcript: (id: string) => `/sessions/${id}/transcript`
  },
  
  // Analytics
  analytics: {
    overview: '/analytics/overview',
    progress: '/analytics/progress',
    skills: '/analytics/skills',
    recommendations: '/analytics/recommendations'
  },
  
  // User
  user: {
    profile: '/user/profile',
    preferences: '/user/preferences',
    goals: '/user/goals',
    achievements: '/user/achievements'
  },
  
  // WebSocket
  websocket: {
    session: (sessionId: string) => `/ws/session/${sessionId}`
  }
} as const;

// HTTP client configuration
export const httpClient = {
  get: async <T>(endpoint: string): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        // Add auth headers here when implemented
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  },
  
  post: async <T>(endpoint: string, data?: any): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Add auth headers here when implemented
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  },
  
  put: async <T>(endpoint: string, data?: any): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        // Add auth headers here when implemented
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  },
  
  delete: async <T>(endpoint: string): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        // Add auth headers here when implemented
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  },
};
