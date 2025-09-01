import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  BarChart3, 
  TrendingUp, 
  Target, 
  Clock, 
  Star,
  Award,
  Zap,
  Brain,
  Users,
  Code,
  Settings as SettingsIcon
} from 'lucide-react';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

// Mock analytics data
const mockAnalytics = {
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
  recentAchievements: [
    { title: 'System Design Master', description: 'Completed 5 advanced system design sessions', icon: '🏗️', date: '2024-01-15' },
    { title: 'Consistent Learner', description: '7-day practice streak', icon: '🔥', date: '2024-01-14' },
    { title: 'Score Improver', description: 'Improved average score by 20%', icon: '📈', date: '2024-01-12' },
    { title: 'Question Master', description: 'Asked 50+ clarifying questions', icon: '❓', date: '2024-01-10' }
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

export const Analytics: React.FC = () => {
  const [selectedTimeframe, setSelectedTimeframe] = useState<'week' | 'month' | 'quarter'>('month');

  const getSkillColor = (level: number) => {
    if (level >= 85) return 'from-green-500 to-emerald-600';
    if (level >= 70) return 'from-cyber-500 to-blue-600';
    if (level >= 60) return 'from-yellow-500 to-orange-600';
    return 'from-red-500 to-pink-600';
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'System Design':
        return <SettingsIcon size={20} className="text-cyber-400" />;
      case 'Behavioral':
        return <Users size={20} className="text-electric-400" />;
      case 'Coding':
        return <Code size={20} className="text-neon-400" />;
      default:
        return <Target size={20} className="text-orange-400" />;
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Analytics Dashboard</h1>
            <p className="text-white/70">
              Track your interview preparation progress and identify areas for improvement
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            {(['week', 'month', 'quarter'] as const).map((timeframe) => (
              <Button
                key={timeframe}
                variant={selectedTimeframe === timeframe ? 'cyber' : 'ghost'}
                size="sm"
                onClick={() => setSelectedTimeframe(timeframe)}
              >
                {timeframe.charAt(0).toUpperCase() + timeframe.slice(1)}
              </Button>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Key Metrics */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8"
      >
        <Card variant="glass">
          <CardContent className="p-6 text-center">
            <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-gradient-to-r from-cyber-500 to-electric-500 mx-auto mb-3">
              <BarChart3 size={24} className="text-white" />
            </div>
            <div className="text-2xl font-bold text-white mb-1">{mockAnalytics.overview.totalSessions}</div>
            <div className="text-white/60 text-sm">Total Sessions</div>
          </CardContent>
        </Card>

        <Card variant="glass">
          <CardContent className="p-6 text-center">
            <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-gradient-to-r from-electric-500 to-purple-600 mx-auto mb-3">
              <Clock size={24} className="text-white" />
            </div>
            <div className="text-2xl font-bold text-white mb-1">{mockAnalytics.overview.totalHours}h</div>
            <div className="text-white/60 text-sm">Practice Time</div>
          </CardContent>
        </Card>

        <Card variant="glass">
          <CardContent className="p-6 text-center">
            <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-gradient-to-r from-neon-500 to-green-600 mx-auto mb-3">
              <Star size={24} className="text-white" />
            </div>
            <div className="text-2xl font-bold text-white mb-1">{mockAnalytics.overview.averageScore}</div>
            <div className="text-white/60 text-sm">Average Score</div>
          </CardContent>
        </Card>

        <Card variant="glass">
          <CardContent className="p-6 text-center">
            <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-gradient-to-r from-orange-500 to-red-600 mx-auto mb-3">
              <Zap size={24} className="text-white" />
            </div>
            <div className="text-2xl font-bold text-white mb-1">{mockAnalytics.overview.currentStreak}</div>
            <div className="text-white/60 text-sm">Day Streak</div>
          </CardContent>
        </Card>

        <Card variant="glass">
          <CardContent className="p-6 text-center">
            <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-gradient-to-r from-green-500 to-emerald-600 mx-auto mb-3">
              <TrendingUp size={24} className="text-white" />
            </div>
            <div className="text-2xl font-bold text-green-400 mb-1">+{mockAnalytics.overview.improvement}%</div>
            <div className="text-white/60 text-sm">Improvement</div>
          </CardContent>
        </Card>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
        {/* Session Distribution */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card variant="glass">
            <CardHeader>
              <h3 className="text-lg font-semibold text-white flex items-center">
                <BarChart3 size={18} className="mr-2 text-cyber-400" />
                Session Distribution
              </h3>
            </CardHeader>
            <CardContent className="space-y-4">
              {mockAnalytics.sessionsByType.map((item, index) => (
                <motion.div
                  key={item.type}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + index * 0.1 }}
                  className="space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {getTypeIcon(item.type)}
                      <span className="text-white font-medium">{item.type}</span>
                    </div>
                    <div className="text-right">
                      <div className="text-white font-medium">{item.count}</div>
                      <div className="text-xs text-white/60">{item.percentage}%</div>
                    </div>
                  </div>
                  <div className="w-full bg-space-700 rounded-full h-2">
                    <motion.div
                      className="bg-gradient-to-r from-cyber-500 to-electric-500 h-2 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${item.percentage}%` }}
                      transition={{ duration: 0.8, delay: 0.5 + index * 0.1 }}
                    />
                  </div>
                  <div className="text-xs text-white/60 text-right">
                    Avg Score: {item.avgScore}/10
                  </div>
                </motion.div>
              ))}
            </CardContent>
          </Card>
        </motion.div>

        {/* Weekly Progress */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card variant="glass">
            <CardHeader>
              <h3 className="text-lg font-semibold text-white flex items-center">
                <TrendingUp size={18} className="mr-2 text-electric-400" />
                Weekly Progress
              </h3>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {mockAnalytics.weeklyProgress.map((week, index) => (
                  <motion.div
                    key={week.week}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 + index * 0.1 }}
                    className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/10"
                  >
                    <div>
                      <div className="text-white font-medium">{week.week}</div>
                      <div className="text-xs text-white/60">
                        {week.sessions} sessions • {week.hours}h
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold text-cyber-400">{week.avgScore}</div>
                      <div className="text-xs text-white/60">avg score</div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Recent Achievements */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card variant="glass">
            <CardHeader>
              <h3 className="text-lg font-semibold text-white flex items-center">
                <Award size={18} className="mr-2 text-neon-400" />
                Recent Achievements
              </h3>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {mockAnalytics.recentAchievements.map((achievement, index) => (
                  <motion.div
                    key={achievement.title}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.5 + index * 0.1 }}
                    className="flex items-start space-x-3 p-3 rounded-lg bg-white/5 border border-white/10"
                  >
                    <div className="text-2xl">{achievement.icon}</div>
                    <div className="flex-1">
                      <div className="text-white font-medium text-sm">{achievement.title}</div>
                      <div className="text-xs text-white/60 mb-1">{achievement.description}</div>
                      <div className="text-xs text-cyber-400">
                        {new Date(achievement.date).toLocaleDateString()}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Skill Breakdown */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Card variant="glass">
            <CardHeader>
              <h3 className="text-lg font-semibold text-white flex items-center">
                <Brain size={18} className="mr-2 text-electric-400" />
                Skill Breakdown
              </h3>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {mockAnalytics.skillBreakdown.map((skill, index) => (
                  <motion.div
                    key={skill.skill}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.6 + index * 0.1 }}
                    className="space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-white font-medium">{skill.skill}</span>
                      <div className="flex items-center space-x-2">
                        <span className="text-green-400 text-sm font-medium">{skill.improvement}</span>
                        <span className="text-white">{skill.level}%</span>
                      </div>
                    </div>
                    <div className="w-full bg-space-700 rounded-full h-2">
                      <motion.div
                        className={`bg-gradient-to-r ${getSkillColor(skill.level)} h-2 rounded-full`}
                        initial={{ width: 0 }}
                        animate={{ width: `${skill.level}%` }}
                        transition={{ duration: 0.8, delay: 0.7 + index * 0.1 }}
                      />
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Strengths & Improvements */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.6 }}
          className="space-y-4"
        >
          {/* Strengths */}
          <Card variant="glass">
            <CardHeader>
              <h3 className="text-lg font-semibold text-white flex items-center">
                <Star size={18} className="mr-2 text-green-400" />
                Top Strengths
              </h3>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {mockAnalytics.strengths.slice(0, 3).map((strength, index) => (
                  <motion.div
                    key={strength}
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.7 + index * 0.1 }}
                    className="flex items-center space-x-2 text-sm text-white/80"
                  >
                    <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                    <span>{strength}</span>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Improvements */}
          <Card variant="glass">
            <CardHeader>
              <h3 className="text-lg font-semibold text-white flex items-center">
                <Target size={18} className="mr-2 text-yellow-400" />
                Focus Areas
              </h3>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {mockAnalytics.improvements.slice(0, 3).map((improvement, index) => (
                  <motion.div
                    key={improvement}
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.8 + index * 0.1 }}
                    className="flex items-center space-x-2 text-sm text-white/80"
                  >
                    <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                    <span>{improvement}</span>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Action Items */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
      >
        <Card variant="glass" glow>
          <CardHeader>
            <h3 className="text-lg font-semibold text-white flex items-center">
              <Zap size={18} className="mr-2 text-electric-400" />
              Recommended Next Steps
            </h3>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-lg bg-cyber-500/10 border border-cyber-500/30">
                <h4 className="font-medium text-cyber-400 mb-2">Practice System Design</h4>
                <p className="text-sm text-white/70 mb-3">
                  Focus on database sharding and caching strategies to improve your weak areas.
                </p>
                <Button variant="cyber" size="sm">Start Session</Button>
              </div>
              
              <div className="p-4 rounded-lg bg-electric-500/10 border border-electric-500/30">
                <h4 className="font-medium text-electric-400 mb-2">Behavioral Practice</h4>
                <p className="text-sm text-white/70 mb-3">
                  Work on leadership scenarios with more quantified results.
                </p>
                <Button variant="ghost" size="sm" className="border-electric-500 text-electric-400">
                  Schedule
                </Button>
              </div>
              
              <div className="p-4 rounded-lg bg-neon-500/10 border border-neon-500/30">
                <h4 className="font-medium text-neon-400 mb-2">Review Sessions</h4>
                <p className="text-sm text-white/70 mb-3">
                  Analyze your past responses to identify improvement patterns.
                </p>
                <Button variant="ghost" size="sm" className="border-neon-500 text-neon-400">
                  Review
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};
