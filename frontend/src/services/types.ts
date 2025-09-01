// Type definitions for API responses
export interface User {
  id: string;
  name: string;
  email: string;
  phone?: string;
  location?: string;
  role?: string;
  company?: string;
  avatar?: string;
  goals: string[];
  joinedDate: string;
  preferences: UserPreferences;
  stats: UserStats;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  language: string;
  timezone: string;
  notifications: NotificationPreferences;
}

export interface NotificationPreferences {
  email: boolean;
  push: boolean;
  reminders: boolean;
  weeklyReport: boolean;
}

export interface UserStats {
  totalSessions: number;
  averageScore: number;
  hoursSpent: number;
  streak: number;
}

export interface Session {
  id: string;
  title: string;
  type: 'system-design' | 'behavioral' | 'coding' | 'product-design';
  status: 'scheduled' | 'in-progress' | 'completed' | 'cancelled';
  difficulty: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  duration: number; // minutes
  scheduledTime?: string;
  startTime?: string;
  endTime?: string;
  score?: number;
  feedback?: SessionFeedback;
  transcript?: SessionMessage[];
  tags: string[];
  createdAt: string;
  updatedAt: string;
}

export interface SessionFeedback {
  overallScore: number;
  strengths: string[];
  improvements: string[];
  detailed: {
    communication: number;
    technicalKnowledge: number;
    problemSolving: number;
    systemThinking: number;
  };
  summary: string;
  nextSteps: string[];
}

export interface SessionMessage {
  id: string;
  sessionId: string;
  type: 'user' | 'ai' | 'system';
  content: string;
  timestamp: string;
  metadata?: {
    attachments?: FileAttachment[];
    audioRecording?: AudioRecording;
  };
}

export interface FileAttachment {
  id: string;
  name: string;
  type: string;
  size: number;
  url: string;
  uploadedAt: string;
}

export interface AudioRecording {
  id: string;
  duration: number;
  url: string;
  transcript?: string;
  recordedAt: string;
}

export interface Analytics {
  overview: AnalyticsOverview;
  sessionsByType: SessionTypeAnalytics[];
  weeklyProgress: WeeklyProgress[];
  skillBreakdown: SkillAnalytics[];
  achievements: Achievement[];
  strengths: string[];
  improvements: string[];
}

export interface AnalyticsOverview {
  totalSessions: number;
  totalHours: number;
  averageScore: number;
  currentStreak: number;
  improvement: number;
}

export interface SessionTypeAnalytics {
  type: string;
  count: number;
  percentage: number;
  avgScore: number;
}

export interface WeeklyProgress {
  week: string;
  sessions: number;
  avgScore: number;
  hours: number;
}

export interface SkillAnalytics {
  skill: string;
  level: number;
  improvement: string;
}

export interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  date: string;
  category: 'learning' | 'performance' | 'consistency' | 'milestone';
}

export interface CreateSessionRequest {
  title: string;
  type: Session['type'];
  difficulty: Session['difficulty'];
  duration: number;
  scheduledTime?: string;
  tags?: string[];
  customPrompt?: string;
}

export interface UpdateSessionRequest {
  title?: string;
  status?: Session['status'];
  feedback?: SessionFeedback;
  tags?: string[];
}

export interface WebSocketMessage {
  type: 'message' | 'status' | 'error' | 'feedback' | 'typing';
  data: any;
  timestamp: string;
}

// API Response wrappers
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

export interface ApiError {
  message: string;
  code?: string;
  status?: number;
  details?: any;
}
