import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Clock, 
  Calendar, 
  Search, 
  Star, 
  TrendingUp, 
  Play, 
  MoreVertical,
  Eye,
  Download,
  BarChart3,
  Target,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

// Mock data for session history
const mockSessions = [
  {
    id: 'session_001',
    topic: 'Design Twitter/X',
    type: 'System Design',
    status: 'completed',
    score: 9.2,
    duration: 45,
    date: '2024-01-15T10:30:00Z',
    difficulty: 'Advanced',
    questions: 12,
    feedback: {
      strengths: ['Clear architecture thinking', 'Good scalability considerations', 'Asked clarifying questions'],
      improvements: ['Database sharding details', 'Caching strategy depth', 'Load balancer specifics']
    },
    tags: ['microservices', 'scalability', 'social_media']
  },
  {
    id: 'session_002',
    topic: 'Leadership Challenge',
    type: 'Behavioral',
    status: 'completed',
    score: 8.8,
    duration: 30,
    date: '2024-01-14T14:15:00Z',
    difficulty: 'Intermediate',
    questions: 8,
    feedback: {
      strengths: ['Concrete examples', 'STAR method usage', 'Clear communication'],
      improvements: ['More quantified results', 'Conflict resolution details']
    },
    tags: ['leadership', 'team_management', 'conflict_resolution']
  },
  {
    id: 'session_003',
    topic: 'Design Netflix',
    type: 'System Design',
    status: 'in_progress',
    score: null,
    duration: 25,
    date: '2024-01-16T09:00:00Z',
    difficulty: 'Advanced',
    questions: 6,
    feedback: null,
    tags: ['streaming', 'cdn', 'video_processing']
  },
  {
    id: 'session_004',
    topic: 'Binary Tree Algorithms',
    type: 'Coding',
    status: 'completed',
    score: 7.5,
    duration: 50,
    date: '2024-01-12T16:20:00Z',
    difficulty: 'Intermediate',
    questions: 3,
    feedback: {
      strengths: ['Correct algorithm', 'Good time complexity analysis'],
      improvements: ['Edge case handling', 'Code optimization', 'Memory usage']
    },
    tags: ['algorithms', 'data_structures', 'trees']
  },
  {
    id: 'session_005',
    topic: 'Design Uber',
    type: 'System Design',
    status: 'completed',
    score: 8.1,
    duration: 55,
    date: '2024-01-10T11:45:00Z',
    difficulty: 'Advanced',
    questions: 15,
    feedback: {
      strengths: ['Location services understanding', 'Real-time updates', 'Database design'],
      improvements: ['Payment system details', 'Surge pricing algorithm']
    },
    tags: ['location_services', 'real_time', 'geospatial']
  }
];

const sessionTypes = ['All', 'System Design', 'Behavioral', 'Coding', 'Product Design'];
const statusTypes = ['All', 'Completed', 'In Progress', 'Scheduled'];
const difficultyTypes = ['All', 'Beginner', 'Intermediate', 'Advanced', 'Expert'];

export const History: React.FC = () => {
  const [sessions] = useState(mockSessions);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('All');
  const [selectedStatus, setSelectedStatus] = useState('All');
  const [selectedDifficulty, setSelectedDifficulty] = useState('All');
  const [sortBy, setSortBy] = useState<'date' | 'score' | 'duration'>('date');

  const filteredSessions = sessions
    .filter(session => {
      const matchesSearch = session.topic.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           session.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
      const matchesType = selectedType === 'All' || session.type === selectedType;
      const matchesStatus = selectedStatus === 'All' || 
                           session.status === selectedStatus.toLowerCase().replace(' ', '_');
      const matchesDifficulty = selectedDifficulty === 'All' || session.difficulty === selectedDifficulty;
      
      return matchesSearch && matchesType && matchesStatus && matchesDifficulty;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'score':
          return (b.score || 0) - (a.score || 0);
        case 'duration':
          return b.duration - a.duration;
        default:
          return new Date(b.date).getTime() - new Date(a.date).getTime();
      }
    });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle size={16} className="text-green-400" />;
      case 'in_progress':
        return <AlertCircle size={16} className="text-yellow-400" />;
      default:
        return <XCircle size={16} className="text-red-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-400 border-green-400/30 bg-green-400/5';
      case 'in_progress':
        return 'text-yellow-400 border-yellow-400/30 bg-yellow-400/5';
      default:
        return 'text-red-400 border-red-400/30 bg-red-400/5';
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Beginner':
        return 'text-green-400';
      case 'Intermediate':
        return 'text-yellow-400';
      case 'Advanced':
        return 'text-orange-400';
      case 'Expert':
        return 'text-red-400';
      default:
        return 'text-white/70';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getAverageScore = () => {
    const completedSessions = sessions.filter(s => s.score !== null);
    const total = completedSessions.reduce((sum, s) => sum + (s.score || 0), 0);
    return completedSessions.length > 0 ? (total / completedSessions.length).toFixed(1) : '0.0';
  };

  const getTotalHours = () => {
    return (sessions.reduce((sum, s) => sum + s.duration, 0) / 60).toFixed(1);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-white mb-2">Session History</h1>
        <p className="text-white/70">
          Track your interview preparation progress and review past sessions
        </p>
      </motion.div>

      {/* Stats Overview */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8"
      >
        <Card variant="glass">
          <CardContent className="p-6 text-center">
            <div className="text-2xl font-bold text-white mb-1">{sessions.length}</div>
            <div className="text-white/60 text-sm flex items-center justify-center">
              <BarChart3 size={14} className="mr-1" />
              Total Sessions
            </div>
          </CardContent>
        </Card>

        <Card variant="glass">
          <CardContent className="p-6 text-center">
            <div className="text-2xl font-bold text-cyber-400 mb-1">{getAverageScore()}</div>
            <div className="text-white/60 text-sm flex items-center justify-center">
              <Star size={14} className="mr-1" />
              Average Score
            </div>
          </CardContent>
        </Card>

        <Card variant="glass">
          <CardContent className="p-6 text-center">
            <div className="text-2xl font-bold text-electric-400 mb-1">{getTotalHours()}h</div>
            <div className="text-white/60 text-sm flex items-center justify-center">
              <Clock size={14} className="mr-1" />
              Total Practice
            </div>
          </CardContent>
        </Card>

        <Card variant="glass">
          <CardContent className="p-6 text-center">
            <div className="text-2xl font-bold text-green-400 mb-1">
              {sessions.filter(s => s.status === 'completed').length}
            </div>
            <div className="text-white/60 text-sm flex items-center justify-center">
              <Target size={14} className="mr-1" />
              Completed
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Filters and Search */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mb-6"
      >
        <Card variant="glass">
          <CardContent className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
              {/* Search */}
              <div className="md:col-span-2">
                <div className="relative">
                  <Search size={18} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-white/40" />
                  <Input
                    placeholder="Search sessions..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              {/* Type Filter */}
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="bg-space-800 border border-space-600 text-white rounded-lg px-3 py-2 text-sm focus:border-cyber-500 focus:outline-none"
              >
                {sessionTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>

              {/* Status Filter */}
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="bg-space-800 border border-space-600 text-white rounded-lg px-3 py-2 text-sm focus:border-cyber-500 focus:outline-none"
              >
                {statusTypes.map(status => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </select>

              {/* Difficulty Filter */}
              <select
                value={selectedDifficulty}
                onChange={(e) => setSelectedDifficulty(e.target.value)}
                className="bg-space-800 border border-space-600 text-white rounded-lg px-3 py-2 text-sm focus:border-cyber-500 focus:outline-none"
              >
                {difficultyTypes.map(difficulty => (
                  <option key={difficulty} value={difficulty}>{difficulty}</option>
                ))}
              </select>

              {/* Sort By */}
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as 'date' | 'score' | 'duration')}
                className="bg-space-800 border border-space-600 text-white rounded-lg px-3 py-2 text-sm focus:border-cyber-500 focus:outline-none"
              >
                <option value="date">Latest First</option>
                <option value="score">Highest Score</option>
                <option value="duration">Longest First</option>
              </select>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Session List */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="space-y-4"
      >
        {filteredSessions.map((session, index) => (
          <motion.div
            key={session.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card variant="glass" hover>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="text-xl font-semibold text-white mb-2 flex items-center">
                          {session.topic}
                          <span className={`ml-3 text-xs px-2 py-1 rounded-full border ${getStatusColor(session.status)}`}>
                            {getStatusIcon(session.status)}
                            <span className="ml-1 capitalize">{session.status.replace('_', ' ')}</span>
                          </span>
                        </h3>
                        <div className="flex items-center space-x-4 text-sm text-white/60">
                          <span className="flex items-center">
                            <Calendar size={14} className="mr-1" />
                            {formatDate(session.date)}
                          </span>
                          <span className="flex items-center">
                            <Clock size={14} className="mr-1" />
                            {session.duration}min
                          </span>
                          <span className={`flex items-center ${getDifficultyColor(session.difficulty)}`}>
                            <Target size={14} className="mr-1" />
                            {session.difficulty}
                          </span>
                          <span className="px-2 py-1 rounded bg-space-700 text-cyber-400 text-xs">
                            {session.type}
                          </span>
                        </div>
                      </div>

                      {session.score && (
                        <div className="text-right">
                          <div className="text-2xl font-bold text-white mb-1">
                            {session.score}
                            <span className="text-sm text-white/60 ml-1">/10</span>
                          </div>
                          <div className="flex items-center text-xs text-white/60">
                            <Star size={12} className="mr-1 text-yellow-400" />
                            Final Score
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Tags */}
                    <div className="flex flex-wrap gap-2 mb-4">
                      {session.tags.map((tag) => (
                        <span 
                          key={tag}
                          className="px-2 py-1 text-xs bg-white/5 border border-white/10 rounded text-white/70"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>

                    {/* Feedback Preview */}
                    {session.feedback && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div>
                          <h4 className="text-sm font-medium text-green-400 mb-2 flex items-center">
                            <CheckCircle size={14} className="mr-1" />
                            Strengths
                          </h4>
                          <ul className="space-y-1">
                            {session.feedback.strengths.slice(0, 2).map((strength, idx) => (
                              <li key={idx} className="text-xs text-white/70 flex items-start">
                                <span className="w-1 h-1 bg-green-400 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                                {strength}
                              </li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <h4 className="text-sm font-medium text-yellow-400 mb-2 flex items-center">
                            <TrendingUp size={14} className="mr-1" />
                            Areas to Improve
                          </h4>
                          <ul className="space-y-1">
                            {session.feedback.improvements.slice(0, 2).map((improvement, idx) => (
                              <li key={idx} className="text-xs text-white/70 flex items-start">
                                <span className="w-1 h-1 bg-yellow-400 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                                {improvement}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex items-center justify-between pt-4 border-t border-white/10">
                      <div className="text-xs text-white/50">
                        {session.questions} questions • Session #{session.id.split('_')[1]}
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        {session.status === 'in_progress' ? (
                          <Button variant="cyber" size="sm">
                            <Play size={14} className="mr-1" />
                            Resume
                          </Button>
                        ) : (
                          <>
                            <Button variant="ghost" size="sm">
                              <Eye size={14} className="mr-1" />
                              Review
                            </Button>
                            <Button variant="ghost" size="sm">
                              <Download size={14} />
                            </Button>
                            <Button variant="ghost" size="sm">
                              <MoreVertical size={14} />
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.div>

      {filteredSessions.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <div className="text-6xl mb-4">📋</div>
          <h3 className="text-xl font-medium text-white mb-2">No sessions found</h3>
          <p className="text-white/60 mb-6">
            Try adjusting your filters or search terms
          </p>
          <Button variant="cyber">
            Start New Session
          </Button>
        </motion.div>
      )}
    </div>
  );
};
