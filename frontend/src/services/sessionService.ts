import type {
  Session,
  CreateSessionRequest,
  UpdateSessionRequest,
  SessionFeedback,
  SessionMessage,
  PaginatedResponse
} from './types';

// Mock data for development - remove when backend is integrated
const mockSessions: Session[] = [
  {
    id: '1',
    title: 'Design a URL Shortener',
    type: 'system-design',
    status: 'completed',
    difficulty: 'intermediate',
    duration: 45,
    startTime: '2024-01-15T10:00:00Z',
    endTime: '2024-01-15T10:45:00Z',
    score: 8.5,
    feedback: {
      overallScore: 8.5,
      strengths: ['Clear problem understanding', 'Good scalability discussion'],
      improvements: ['Consider caching strategies', 'Database sharding'],
      detailed: {
        communication: 9,
        technicalKnowledge: 8,
        problemSolving: 8,
        systemThinking: 8
      },
      summary: 'Great overall performance with room for improvement in advanced topics.',
      nextSteps: ['Study database sharding patterns', 'Practice cache invalidation strategies']
    },
    tags: ['url-shortener', 'system-design', 'scalability'],
    createdAt: '2024-01-15T09:00:00Z',
    updatedAt: '2024-01-15T10:45:00Z'
  },
  {
    id: '2',
    title: 'Leadership Experience Discussion',
    type: 'behavioral',
    status: 'completed',
    difficulty: 'advanced',
    duration: 30,
    startTime: '2024-01-14T14:00:00Z',
    endTime: '2024-01-14T14:30:00Z',
    score: 7.8,
    feedback: {
      overallScore: 7.8,
      strengths: ['Concrete examples', 'STAR method usage'],
      improvements: ['Quantify results better', 'Show more impact'],
      detailed: {
        communication: 8,
        technicalKnowledge: 7,
        problemSolving: 8,
        systemThinking: 8
      },
      summary: 'Good behavioral responses with solid examples.',
      nextSteps: ['Practice with metrics', 'Prepare impact stories']
    },
    tags: ['behavioral', 'leadership', 'management'],
    createdAt: '2024-01-14T13:00:00Z',
    updatedAt: '2024-01-14T14:30:00Z'
  }
];

class SessionService {
  // Get all sessions with optional filtering
  async getSessions(
    page = 1,
    limit = 10,
    filters?: {
      type?: Session['type'];
      status?: Session['status'];
      difficulty?: Session['difficulty'];
      search?: string;
    }
  ): Promise<PaginatedResponse<Session>> {
    try {
      // Mock implementation - replace with real API call
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate API delay
      
      let filteredSessions = [...mockSessions];
      
      if (filters) {
        if (filters.type) {
          filteredSessions = filteredSessions.filter(s => s.type === filters.type);
        }
        if (filters.status) {
          filteredSessions = filteredSessions.filter(s => s.status === filters.status);
        }
        if (filters.difficulty) {
          filteredSessions = filteredSessions.filter(s => s.difficulty === filters.difficulty);
        }
        if (filters.search) {
          const search = filters.search.toLowerCase();
          filteredSessions = filteredSessions.filter(s => 
            s.title.toLowerCase().includes(search) ||
            s.tags.some(tag => tag.toLowerCase().includes(search))
          );
        }
      }
      
      const startIndex = (page - 1) * limit;
      const endIndex = startIndex + limit;
      const paginatedSessions = filteredSessions.slice(startIndex, endIndex);
      
      return {
        data: paginatedSessions,
        pagination: {
          page,
          limit,
          total: filteredSessions.length,
          totalPages: Math.ceil(filteredSessions.length / limit)
        }
      };
      
      // Real implementation:
      // const params = new URLSearchParams({
      //   page: page.toString(),
      //   limit: limit.toString(),
      //   ...filters
      // });
      // return httpClient.get<PaginatedResponse<Session>>(`${API_ENDPOINTS.sessions.list}?${params}`);
    } catch (error) {
      console.error('Error fetching sessions:', error);
      throw error;
    }
  }

  // Get a specific session by ID
  async getSession(sessionId: string): Promise<Session> {
    try {
      // Mock implementation
      await new Promise(resolve => setTimeout(resolve, 300));
      const session = mockSessions.find(s => s.id === sessionId);
      if (!session) {
        throw new Error('Session not found');
      }
      return session;
      
      // Real implementation:
      // return httpClient.get<Session>(API_ENDPOINTS.sessions.get(sessionId));
    } catch (error) {
      console.error('Error fetching session:', error);
      throw error;
    }
  }

  // Create a new session
  async createSession(sessionData: CreateSessionRequest): Promise<Session> {
    try {
      // Mock implementation
      await new Promise(resolve => setTimeout(resolve, 500));
      const newSession: Session = {
        id: Date.now().toString(),
        ...sessionData,
        tags: sessionData.tags || [],
        status: 'scheduled',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      mockSessions.unshift(newSession);
      return newSession;
      
      // Real implementation:
      // return httpClient.post<Session>(API_ENDPOINTS.sessions.create, sessionData);
    } catch (error) {
      console.error('Error creating session:', error);
      throw error;
    }
  }

  // Update a session
  async updateSession(sessionId: string, updates: UpdateSessionRequest): Promise<Session> {
    try {
      // Mock implementation
      await new Promise(resolve => setTimeout(resolve, 300));
      const sessionIndex = mockSessions.findIndex(s => s.id === sessionId);
      if (sessionIndex === -1) {
        throw new Error('Session not found');
      }
      
      mockSessions[sessionIndex] = {
        ...mockSessions[sessionIndex],
        ...updates,
        updatedAt: new Date().toISOString()
      };
      
      return mockSessions[sessionIndex];
      
      // Real implementation:
      // return httpClient.put<Session>(API_ENDPOINTS.sessions.update(sessionId), updates);
    } catch (error) {
      console.error('Error updating session:', error);
      throw error;
    }
  }

  // Delete a session
  async deleteSession(sessionId: string): Promise<void> {
    try {
      // Mock implementation
      await new Promise(resolve => setTimeout(resolve, 300));
      const sessionIndex = mockSessions.findIndex(s => s.id === sessionId);
      if (sessionIndex === -1) {
        throw new Error('Session not found');
      }
      mockSessions.splice(sessionIndex, 1);
      
      // Real implementation:
      // return httpClient.delete<void>(API_ENDPOINTS.sessions.delete(sessionId));
    } catch (error) {
      console.error('Error deleting session:', error);
      throw error;
    }
  }

  // Get session messages/transcript
  async getSessionMessages(sessionId: string): Promise<SessionMessage[]> {
    try {
      // Mock implementation
      await new Promise(resolve => setTimeout(resolve, 300));
      return [
        {
          id: '1',
          sessionId,
          type: 'system',
          content: 'Welcome to your interview session. I\'ll be your interviewer today.',
          timestamp: new Date(Date.now() - 10 * 60 * 1000).toISOString()
        },
        {
          id: '2',
          sessionId,
          type: 'ai',
          content: 'Let\'s start with designing a URL shortener like bit.ly. Can you walk me through your approach?',
          timestamp: new Date(Date.now() - 9 * 60 * 1000).toISOString()
        },
        {
          id: '3',
          sessionId,
          type: 'user',
          content: 'Sure! I\'d start by understanding the requirements. We need to shorten long URLs and redirect users when they click the short URL.',
          timestamp: new Date(Date.now() - 8 * 60 * 1000).toISOString()
        }
      ];
      
      // Real implementation:
      // return httpClient.get<SessionMessage[]>(API_ENDPOINTS.sessions.transcript(sessionId));
    } catch (error) {
      console.error('Error fetching session messages:', error);
      throw error;
    }
  }

  // Submit session feedback
  async submitFeedback(sessionId: string, feedback: SessionFeedback): Promise<void> {
    try {
      // Mock implementation
      await new Promise(resolve => setTimeout(resolve, 300));
      const sessionIndex = mockSessions.findIndex(s => s.id === sessionId);
      if (sessionIndex !== -1) {
        mockSessions[sessionIndex].feedback = feedback;
        mockSessions[sessionIndex].score = feedback.overallScore;
      }
      
      // Real implementation:
      // return httpClient.post<void>(API_ENDPOINTS.sessions.feedback(sessionId), feedback);
    } catch (error) {
      console.error('Error submitting feedback:', error);
      throw error;
    }
  }
}

export const sessionService = new SessionService();
