// Core entity types matching the backend
export interface User {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  company?: string;
  jobTitle?: string;
  yearsOfExperience?: number;
  bio?: string;
  avatarUrl?: string;
  createdAt: string;
  subscription: {
    tier: 'free' | 'pro' | 'enterprise';
    isActive: boolean;
    expiresAt?: string;
  };
  preferences: {
    preferredTopics: string[];
    difficultyLevel: 'beginner' | 'intermediate' | 'advanced' | 'expert';
    sessionDurationPreference: number;
    emailNotifications: boolean;
    pushNotifications: boolean;
  };
}

export interface InterviewSession {
  id: string;
  userId: string;
  topic: string;
  difficultyLevel: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  status: 'active' | 'completed' | 'abandoned' | 'paused';
  startedAt: string;
  endedAt?: string;
  totalDuration?: number; // in seconds
  maxDurationMinutes: number;
  enableHints: boolean;
  enableRealTimeFeedback: boolean;
  customRequirements?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Message {
  id: string;
  sessionId: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  messageType: 'text' | 'code' | 'diagram' | 'feedback' | 'question' | 'evaluation';
  timestamp: string;
  tokensUsed: number;
  metadata: Record<string, any>;
}

export interface SessionMetrics {
  sessionId: string;
  status: string;
  topic: string;
  difficulty: string;
  durationSeconds: number;
  totalMessages: number;
  userMessages: number;
  assistantMessages: number;
  totalTokensUsed: number;
  startedAt: string;
  endedAt?: string;
}

export interface UserSessionStats {
  totalSessions: number;
  completedSessions: number;
  averageDuration: number;
  totalTimeSpent: number;
  favoriteTopics: string[];
  difficultyBreakdown: Record<string, number>;
  monthlyProgress: Array<{
    month: string;
    sessions: number;
    completedSessions: number;
  }>;
}

// Task and AI related types
export interface Task {
  id: string;
  sessionId: string;
  taskType: 'ai_process_message' | 'ai_hint' | 'ai_feedback' | 'ai_insights' | 'ai_summary';
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress?: {
    percentage: number;
    currentStep: string;
    totalSteps: number;
    message: string;
  };
  result?: any;
  error?: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  totalCount: number;
  hasMore: boolean;
  page: number;
  limit: number;
}

// Session creation types
export interface CreateSessionRequest {
  topic: string;
  difficultyLevel: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  maxDurationMinutes: number;
  enableHints: boolean;
  enableRealTimeFeedback: boolean;
  customRequirements?: string;
}

// WebSocket message types
export interface WebSocketMessage {
  type: 'task_update' | 'session_update' | 'message_update' | 'error';
  data: any;
  timestamp: string;
}
