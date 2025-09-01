import type { Analytics } from './types';

// Mock analytics data
const mockAnalytics: Analytics = {
  overview: {
    totalSessions: 12,
    totalHours: 8.5,
    averageScore: 8.5,
    currentStreak: 7,
    improvement: 23
  },
  sessionsByType: [
    { type: 'System Design', count: 6, percentage: 50, avgScore: 8.8 },
    { type: 'Behavioral', count: 3, percentage: 25, avgScore: 8.2 },
    { type: 'Coding', count: 2, percentage: 17, avgScore: 7.8 },
    { type: 'Product Design', count: 1, percentage: 8, avgScore: 9.0 }
  ],
  weeklyProgress: [
    { week: 'Week 1', sessions: 2, avgScore: 7.5, hours: 1.8 },
    { week: 'Week 2', sessions: 3, avgScore: 8.0, hours: 2.2 },
    { week: 'Week 3', sessions: 4, avgScore: 8.3, hours: 2.8 },
    { week: 'Week 4', sessions: 3, avgScore: 8.8, hours: 1.7 }
  ],
  skillBreakdown: [
    { skill: 'System Architecture', level: 85, improvement: '+12%' },
    { skill: 'Scalability Design', level: 78, improvement: '+8%' },
    { skill: 'Database Design', level: 82, improvement: '+15%' },
    { skill: 'Communication', level: 88, improvement: '+5%' },
    { skill: 'Problem Solving', level: 80, improvement: '+10%' }
  ],
  achievements: [
    {
      id: '1',
      title: 'System Design Master',
      description: 'Completed 5 advanced system design sessions',
      icon: '🏗️',
      date: '2024-01-15',
      category: 'learning'
    },
    {
      id: '2',
      title: 'Consistent Learner',
      description: '7-day practice streak',
      icon: '🔥',
      date: '2024-01-14',
      category: 'consistency'
    },
    {
      id: '3',
      title: 'Score Improver',
      description: 'Improved average score by 20%',
      icon: '📈',
      date: '2024-01-12',
      category: 'performance'
    },
    {
      id: '4',
      title: 'Question Master',
      description: 'Asked 50+ clarifying questions',
      icon: '❓',
      date: '2024-01-10',
      category: 'learning'
    }
  ],
  strengths: [
    'Clear architectural thinking',
    'Good scalability considerations', 
    'Effective communication',
    'Asks clarifying questions',
    'Considers trade-offs'
  ],
  improvements: [
    'Database sharding strategies',
    'Caching layer implementation',
    'Load balancer configurations',
    'Monitoring and alerting',
    'Security considerations'
  ]
};

class AnalyticsService {
  // Get complete analytics data
  async getAnalytics(timeframe: 'week' | 'month' | 'quarter' = 'month'): Promise<Analytics> {
    try {
      // Mock implementation - simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // In a real implementation, timeframe would affect the data returned
      return mockAnalytics;
      
      // Real implementation:
      // return httpClient.get<Analytics>(`${API_ENDPOINTS.analytics.overview}?timeframe=${timeframe}`);
    } catch (error) {
      console.error('Error fetching analytics:', error);
      throw error;
    }
  }

  // Get overview metrics only
  async getOverview(timeframe: 'week' | 'month' | 'quarter' = 'month') {
    try {
      await new Promise(resolve => setTimeout(resolve, 300));
      return mockAnalytics.overview;
      
      // Real implementation:
      // return httpClient.get(`${API_ENDPOINTS.analytics.overview}?timeframe=${timeframe}`);
    } catch (error) {
      console.error('Error fetching overview:', error);
      throw error;
    }
  }

  // Get progress data
  async getProgress(timeframe: 'week' | 'month' | 'quarter' = 'month') {
    try {
      await new Promise(resolve => setTimeout(resolve, 300));
      return {
        weeklyProgress: mockAnalytics.weeklyProgress,
        sessionsByType: mockAnalytics.sessionsByType
      };
      
      // Real implementation:
      // return httpClient.get(`${API_ENDPOINTS.analytics.progress}?timeframe=${timeframe}`);
    } catch (error) {
      console.error('Error fetching progress:', error);
      throw error;
    }
  }

  // Get skill breakdown
  async getSkills() {
    try {
      await new Promise(resolve => setTimeout(resolve, 300));
      return {
        skillBreakdown: mockAnalytics.skillBreakdown,
        strengths: mockAnalytics.strengths,
        improvements: mockAnalytics.improvements
      };
      
      // Real implementation:
      // return httpClient.get(API_ENDPOINTS.analytics.skills);
    } catch (error) {
      console.error('Error fetching skills:', error);
      throw error;
    }
  }

  // Get achievements
  async getAchievements() {
    try {
      await new Promise(resolve => setTimeout(resolve, 300));
      return mockAnalytics.achievements;
      
      // Real implementation:
      // return httpClient.get(API_ENDPOINTS.user.achievements);
    } catch (error) {
      console.error('Error fetching achievements:', error);
      throw error;
    }
  }

  // Get recommendations
  async getRecommendations() {
    try {
      await new Promise(resolve => setTimeout(resolve, 400));
      
      // Generate dynamic recommendations based on analytics
      const recommendations = [
        {
          type: 'practice',
          title: 'Practice System Design',
          description: 'Focus on database sharding and caching strategies to improve your weak areas.',
          priority: 'high',
          estimatedTime: '30-45 minutes',
          category: 'technical'
        },
        {
          type: 'review',
          title: 'Review Past Sessions',
          description: 'Analyze your behavioral interview responses to identify improvement patterns.',
          priority: 'medium',
          estimatedTime: '15-20 minutes',
          category: 'behavioral'
        },
        {
          type: 'skill',
          title: 'Strengthen Communication',
          description: 'Practice explaining complex concepts in simpler terms.',
          priority: 'medium',
          estimatedTime: '20-30 minutes',
          category: 'soft-skills'
        }
      ];

      return recommendations;
      
      // Real implementation:
      // return httpClient.get(API_ENDPOINTS.analytics.recommendations);
    } catch (error) {
      console.error('Error fetching recommendations:', error);
      throw error;
    }
  }

  // Calculate improvement trend
  calculateImprovement(currentScore: number, previousScore: number): number {
    if (previousScore === 0) return 0;
    return Math.round(((currentScore - previousScore) / previousScore) * 100);
  }

  // Get performance trend
  getPerformanceTrend(sessions: { score?: number; endTime?: string }[]) {
    const scoredSessions = sessions
      .filter(s => s.score && s.endTime)
      .sort((a, b) => new Date(a.endTime!).getTime() - new Date(b.endTime!).getTime())
      .slice(-10); // Last 10 sessions

    if (scoredSessions.length < 2) return 'stable';

    const recentAvg = scoredSessions.slice(-3).reduce((sum, s) => sum + (s.score || 0), 0) / 3;
    const earlierAvg = scoredSessions.slice(0, 3).reduce((sum, s) => sum + (s.score || 0), 0) / 3;
    
    const improvement = ((recentAvg - earlierAvg) / earlierAvg) * 100;
    
    if (improvement > 10) return 'improving';
    if (improvement < -10) return 'declining';
    return 'stable';
  }

  // Generate insights based on analytics data
  generateInsights(analytics: Analytics) {
    const insights = [];
    
    // Check streak
    if (analytics.overview.currentStreak >= 7) {
      insights.push({
        type: 'positive',
        title: 'Great Consistency!',
        message: `You've maintained a ${analytics.overview.currentStreak}-day practice streak. Keep it up!`
      });
    }
    
    // Check improvement
    if (analytics.overview.improvement > 15) {
      insights.push({
        type: 'positive',
        title: 'Excellent Progress!',
        message: `Your performance has improved by ${analytics.overview.improvement}% recently.`
      });
    }
    
    // Check for focus areas
    const weakestSkill = analytics.skillBreakdown.reduce((min, skill) => 
      skill.level < min.level ? skill : min
    );
    
    if (weakestSkill.level < 70) {
      insights.push({
        type: 'suggestion',
        title: 'Focus Area Identified',
        message: `Consider practicing ${weakestSkill.skill} - it's your biggest improvement opportunity.`
      });
    }
    
    return insights;
  }
}

export const analyticsService = new AnalyticsService();
