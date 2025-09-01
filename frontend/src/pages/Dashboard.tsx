import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Plus, 
  Clock, 
  Target, 
  TrendingUp, 
  Star,
  Calendar,
  BookOpen,
  Zap,
  Award,
  ChevronRight,
  Play,
  BarChart3
} from 'lucide-react';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

// Mock data for demonstration
const mockStats = {
  totalSessions: 12,
  averageScore: 8.5,
  improvementRate: 23,
  streakDays: 7
};

const mockRecentSessions = [
  {
    id: '1',
    type: 'System Design',
    topic: 'Design Twitter',
    status: 'completed',
    score: 9.2,
    date: '2024-01-15T10:30:00Z',
    duration: 45
  },
  {
    id: '2',
    type: 'Behavioral',
    topic: 'Leadership Experience',
    status: 'completed',
    score: 8.8,
    date: '2024-01-14T14:15:00Z',
    duration: 30
  },
  {
    id: '3',
    type: 'System Design',
    topic: 'Design Netflix',
    status: 'in_progress',
    score: null,
    date: '2024-01-16T09:00:00Z',
    duration: 60
  }
];

const mockRecommendations = [
  {
    title: 'System Design Fundamentals',
    description: 'Master the basics of distributed systems',
    difficulty: 'Beginner',
    estimatedTime: 30,
    category: 'System Design'
  },
  {
    title: 'Leadership Questions',
    description: 'Practice common behavioral interview scenarios',
    difficulty: 'Intermediate',
    estimatedTime: 25,
    category: 'Behavioral'
  },
  {
    title: 'Database Scaling',
    description: 'Deep dive into database sharding and replication',
    difficulty: 'Advanced',
    estimatedTime: 45,
    category: 'System Design'
  }
];

export const Dashboard: React.FC = () => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-400';
      case 'in_progress': return 'text-yellow-400';
      case 'scheduled': return 'text-blue-400';
      default: return 'text-white/70';
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Beginner': return 'text-green-400 border-green-400/30 bg-green-400/5';
      case 'Intermediate': return 'text-yellow-400 border-yellow-400/30 bg-yellow-400/5';
      case 'Advanced': return 'text-red-400 border-red-400/30 bg-red-400/5';
      default: return 'text-white/70 border-white/20 bg-white/5';
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Welcome Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-white mb-2">
          Welcome back! 👋
        </h1>
        <p className="text-white/70">
          Ready to ace your next interview? Let's continue your preparation journey.
        </p>
      </motion.div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-8"
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link to="/new-session">
            <Card variant="glass" hover glow className="h-full">
              <CardContent className="p-6 text-center">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-gradient-to-r from-cyber-500 to-electric-500 mb-4">
                  <Plus size={24} className="text-white" />
                </div>
                <h3 className="text-white font-medium mb-2">New Session</h3>
                <p className="text-white/60 text-sm">Start a new interview practice</p>
              </CardContent>
            </Card>
          </Link>

          <Link to="/history">
            <Card variant="glass" hover className="h-full">
              <CardContent className="p-6 text-center">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-space-700 mb-4">
                  <Clock size={24} className="text-cyber-400" />
                </div>
                <h3 className="text-white font-medium mb-2">History</h3>
                <p className="text-white/60 text-sm">Review past sessions</p>
              </CardContent>
            </Card>
          </Link>

          <Link to="/analytics">
            <Card variant="glass" hover className="h-full">
              <CardContent className="p-6 text-center">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-space-700 mb-4">
                  <TrendingUp size={24} className="text-electric-400" />
                </div>
                <h3 className="text-white font-medium mb-2">Analytics</h3>
                <p className="text-white/60 text-sm">Track your progress</p>
              </CardContent>
            </Card>
          </Link>

          <Link to="/profile">
            <Card variant="glass" hover className="h-full">
              <CardContent className="p-6 text-center">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-space-700 mb-4">
                  <Target size={24} className="text-neon-400" />
                </div>
                <h3 className="text-white font-medium mb-2">Goals</h3>
                <p className="text-white/60 text-sm">Set learning targets</p>
              </CardContent>
            </Card>
          </Link>
        </div>
      </motion.div>

      {/* Stats Overview */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-8"
      >
        <h2 className="text-xl font-semibold text-white mb-4 flex items-center">
          <BarChart3 size={20} className="mr-2 text-cyber-400" />
          Your Progress
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card variant="glass">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white/60 text-sm">Total Sessions</p>
                  <p className="text-2xl font-bold text-white">{mockStats.totalSessions}</p>
                </div>
                <BookOpen size={24} className="text-cyber-400" />
              </div>
            </CardContent>
          </Card>

          <Card variant="glass">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white/60 text-sm">Average Score</p>
                  <p className="text-2xl font-bold text-white">{mockStats.averageScore}/10</p>
                </div>
                <Star size={24} className="text-yellow-400" />
              </div>
            </CardContent>
          </Card>

          <Card variant="glass">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white/60 text-sm">Improvement</p>
                  <p className="text-2xl font-bold text-green-400">+{mockStats.improvementRate}%</p>
                </div>
                <TrendingUp size={24} className="text-green-400" />
              </div>
            </CardContent>
          </Card>

          <Card variant="glass">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white/60 text-sm">Current Streak</p>
                  <p className="text-2xl font-bold text-white">{mockStats.streakDays} days</p>
                </div>
                <Award size={24} className="text-electric-400" />
              </div>
            </CardContent>
          </Card>
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Sessions */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="lg:col-span-2"
        >
          <Card variant="glass">
            <CardHeader>
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-white flex items-center">
                  <Clock size={18} className="mr-2 text-cyber-400" />
                  Recent Sessions
                </h3>
                <Link 
                  to="/history"
                  className="text-cyber-400 hover:text-cyber-300 text-sm flex items-center transition-colors"
                >
                  View all
                  <ChevronRight size={16} className="ml-1" />
                </Link>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="space-y-4 p-6">
                {mockRecentSessions.map((session, index) => (
                  <motion.div
                    key={session.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4 + index * 0.1 }}
                    className="flex items-center justify-between p-4 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h4 className="font-medium text-white">{session.topic}</h4>
                        <span className={`text-xs px-2 py-1 rounded-full border ${getStatusColor(session.status)}`}>
                          {session.status.replace('_', ' ')}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-white/60">
                        <span>{session.type}</span>
                        <span>{formatDate(session.date)}</span>
                        <span>{session.duration}min</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {session.score && (
                        <div className="text-right">
                          <div className="text-lg font-bold text-white">{session.score}</div>
                          <div className="text-xs text-white/60">score</div>
                        </div>
                      )}
                      {session.status === 'in_progress' ? (
                        <Button variant="cyber" size="sm">
                          <Play size={14} className="mr-1" />
                          Resume
                        </Button>
                      ) : (
                        <Button variant="ghost" size="sm">
                          <ChevronRight size={16} />
                        </Button>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Recommendations */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card variant="glass">
            <CardHeader>
              <h3 className="text-lg font-semibold text-white flex items-center">
                <Zap size={18} className="mr-2 text-electric-400" />
                Recommended for You
              </h3>
            </CardHeader>
            <CardContent className="p-0">
              <div className="space-y-4 p-6">
                {mockRecommendations.map((rec, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 + index * 0.1 }}
                    className="p-4 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors cursor-pointer group"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium text-white group-hover:text-cyber-400 transition-colors">
                        {rec.title}
                      </h4>
                      <span className={`text-xs px-2 py-1 rounded-full border ${getDifficultyColor(rec.difficulty)}`}>
                        {rec.difficulty}
                      </span>
                    </div>
                    <p className="text-sm text-white/60 mb-3">{rec.description}</p>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-xs text-white/50">
                        <Calendar size={12} />
                        <span>{rec.estimatedTime} min</span>
                      </div>
                      <Button variant="ghost" size="sm" className="text-xs">
                        Start
                      </Button>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
};
