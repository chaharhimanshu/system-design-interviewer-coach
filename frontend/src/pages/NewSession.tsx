import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { 
  Settings, 
  Clock, 
  Target, 
  Brain, 
  Users, 
  Code,
  ChevronRight,
  Play,
  Sparkles
} from 'lucide-react';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input, Textarea } from '../components/ui/Input';

const sessionTypes = [
  {
    id: 'system_design',
    name: 'System Design',
    description: 'Design scalable distributed systems',
    icon: Settings,
    color: 'from-cyber-500 to-blue-600',
    duration: '45-60 min',
    difficulty: 'Advanced',
    topics: ['Twitter/X', 'Netflix', 'Uber', 'Instagram', 'WhatsApp', 'YouTube', 'Custom Topic']
  },
  {
    id: 'behavioral',
    name: 'Behavioral Interview',
    description: 'Practice leadership and behavioral questions',
    icon: Users,
    color: 'from-electric-500 to-purple-600',
    duration: '30-45 min',
    difficulty: 'Intermediate',
    topics: ['Leadership', 'Conflict Resolution', 'Project Management', 'Team Collaboration', 'Problem Solving', 'Custom Question']
  },
  {
    id: 'coding',
    name: 'Coding Interview',
    description: 'Algorithm and data structure problems',
    icon: Code,
    color: 'from-neon-500 to-green-600',
    duration: '45-60 min',
    difficulty: 'Advanced',
    topics: ['Arrays & Strings', 'Trees & Graphs', 'Dynamic Programming', 'System Design Coding', 'Custom Problem']
  },
  {
    id: 'product',
    name: 'Product Design',
    description: 'Design user experiences and products',
    icon: Target,
    color: 'from-orange-500 to-pink-600',
    duration: '45 min',
    difficulty: 'Intermediate',
    topics: ['Mobile App', 'Web Platform', 'Feature Design', 'User Research', 'Custom Product']
  }
];

const difficultyLevels = [
  { id: 'beginner', name: 'Beginner', description: 'New to interviews' },
  { id: 'intermediate', name: 'Intermediate', description: '2-5 years experience' },
  { id: 'advanced', name: 'Advanced', description: '5+ years experience' },
  { id: 'expert', name: 'Expert', description: 'Senior/Staff level' }
];

export const NewSession: React.FC = () => {
  const navigate = useNavigate();
  const [selectedType, setSelectedType] = useState<string>('');
  const [selectedTopic, setSelectedTopic] = useState<string>('');
  const [customTopic, setCustomTopic] = useState<string>('');
  const [difficulty, setDifficulty] = useState<string>('intermediate');
  const [duration, setDuration] = useState<number>(45);
  const [additionalContext, setAdditionalContext] = useState<string>('');

  const selectedSessionType = sessionTypes.find(type => type.id === selectedType);

  const handleStartSession = () => {
    const sessionData = {
      type: selectedType,
      topic: selectedTopic === 'Custom Topic' || selectedTopic === 'Custom Question' || selectedTopic === 'Custom Problem' || selectedTopic === 'Custom Product' 
        ? customTopic 
        : selectedTopic,
      difficulty,
      duration,
      additionalContext
    };
    
    console.log('Starting session with:', sessionData);
    
    // Generate a session ID and navigate to the active session
    const sessionId = `session_${Date.now()}`;
    navigate(`/session/${sessionId}`);
  };

  const isReadyToStart = selectedType && selectedTopic && (
    !['Custom Topic', 'Custom Question', 'Custom Problem', 'Custom Product'].includes(selectedTopic) || customTopic.trim()
  );

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 text-center"
      >
        <h1 className="text-3xl font-bold text-white mb-2 flex items-center justify-center">
          <Brain size={32} className="mr-3 text-cyber-400" />
          Start New Interview Session
        </h1>
        <p className="text-white/70 max-w-2xl mx-auto">
          Choose your interview type and customize your practice session. Our AI interviewer will adapt to your experience level and provide personalized feedback.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Session Configuration */}
        <div className="lg:col-span-2 space-y-6">
          {/* Session Types */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card variant="glass">
              <CardHeader>
                <h2 className="text-xl font-semibold text-white mb-2">Choose Interview Type</h2>
                <p className="text-white/60">Select the type of interview you want to practice</p>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {sessionTypes.map((type, index) => {
                    const Icon = type.icon;
                    const isSelected = selectedType === type.id;
                    
                    return (
                      <motion.div
                        key={type.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 + index * 0.1 }}
                        className={`p-4 rounded-lg border cursor-pointer transition-all duration-200 ${
                          isSelected 
                            ? 'border-cyber-500 bg-cyber-500/10 shadow-cyber' 
                            : 'border-white/20 hover:border-white/40 hover:bg-white/5'
                        }`}
                        onClick={() => setSelectedType(type.id)}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`p-2 rounded-lg bg-gradient-to-r ${type.color}`}>
                            <Icon size={20} className="text-white" />
                          </div>
                          <div className="flex-1">
                            <h3 className="font-medium text-white mb-1">{type.name}</h3>
                            <p className="text-sm text-white/60 mb-2">{type.description}</p>
                            <div className="flex items-center gap-4 text-xs text-white/50">
                              <span className="flex items-center gap-1">
                                <Clock size={12} />
                                {type.duration}
                              </span>
                              <span>{type.difficulty}</span>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Topic Selection */}
          {selectedSessionType && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              <Card variant="glass">
                <CardHeader>
                  <h2 className="text-xl font-semibold text-white mb-2">Select Topic</h2>
                  <p className="text-white/60">Choose a specific topic or provide your own</p>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
                    {selectedSessionType.topics.map((topic) => {
                      const isSelected = selectedTopic === topic;
                      
                      return (
                        <button
                          key={topic}
                          onClick={() => setSelectedTopic(topic)}
                          className={`p-3 rounded-lg text-sm transition-all duration-200 ${
                            isSelected 
                              ? 'bg-cyber-500/20 border border-cyber-500 text-cyber-400' 
                              : 'bg-white/5 border border-white/20 text-white hover:bg-white/10'
                          }`}
                        >
                          {topic}
                        </button>
                      );
                    })}
                  </div>

                  {['Custom Topic', 'Custom Question', 'Custom Problem', 'Custom Product'].includes(selectedTopic) && (
                    <div className="mt-4">
                      <Input
                        label="Custom Topic"
                        placeholder="Enter your custom topic or question..."
                        value={customTopic}
                        onChange={(e) => setCustomTopic(e.target.value)}
                      />
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Settings */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card variant="glass">
              <CardHeader>
                <h2 className="text-xl font-semibold text-white mb-2">Session Settings</h2>
                <p className="text-white/60">Customize your interview experience</p>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Difficulty */}
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-3">
                    Experience Level
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {difficultyLevels.map((level) => {
                      const isSelected = difficulty === level.id;
                      
                      return (
                        <button
                          key={level.id}
                          onClick={() => setDifficulty(level.id)}
                          className={`p-3 rounded-lg text-sm transition-all duration-200 text-left ${
                            isSelected 
                              ? 'bg-electric-500/20 border border-electric-500 text-electric-400' 
                              : 'bg-white/5 border border-white/20 text-white hover:bg-white/10'
                          }`}
                        >
                          <div className="font-medium">{level.name}</div>
                          <div className="text-xs text-white/60 mt-1">{level.description}</div>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Duration */}
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-3">
                    Duration (minutes)
                  </label>
                  <div className="flex items-center gap-4">
                    <input
                      type="range"
                      min="15"
                      max="90"
                      step="15"
                      value={duration}
                      onChange={(e) => setDuration(Number(e.target.value))}
                      className="flex-1 h-2 bg-space-700 rounded-lg appearance-none cursor-pointer slider"
                    />
                    <div className="min-w-[60px] text-center">
                      <span className="text-white font-medium">{duration}</span>
                      <span className="text-white/60 text-sm ml-1">min</span>
                    </div>
                  </div>
                </div>

                {/* Additional Context */}
                <div>
                  <Textarea
                    label="Additional Context (Optional)"
                    placeholder="Any specific areas you want to focus on or additional information for the AI interviewer..."
                    value={additionalContext}
                    onChange={(e) => setAdditionalContext(e.target.value)}
                    rows={3}
                  />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Session Summary & Start */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
          className="space-y-6"
        >
          {/* Summary */}
          <Card variant="glass" glow>
            <CardHeader>
              <h2 className="text-xl font-semibold text-white flex items-center">
                <Sparkles size={20} className="mr-2 text-electric-400" />
                Session Summary
              </h2>
            </CardHeader>
            <CardContent>
              {selectedSessionType ? (
                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-white/60">Type</label>
                    <p className="text-white font-medium">{selectedSessionType.name}</p>
                  </div>
                  
                  {selectedTopic && (
                    <div>
                      <label className="text-sm text-white/60">Topic</label>
                      <p className="text-white font-medium">
                        {['Custom Topic', 'Custom Question', 'Custom Problem', 'Custom Product'].includes(selectedTopic) 
                          ? customTopic || 'Custom topic...' 
                          : selectedTopic}
                      </p>
                    </div>
                  )}
                  
                  <div>
                    <label className="text-sm text-white/60">Level</label>
                    <p className="text-white font-medium capitalize">{difficulty}</p>
                  </div>
                  
                  <div>
                    <label className="text-sm text-white/60">Duration</label>
                    <p className="text-white font-medium">{duration} minutes</p>
                  </div>

                  <div className="pt-4 border-t border-white/10">
                    <Button
                      variant="cyber"
                      size="lg"
                      className="w-full"
                      disabled={!isReadyToStart}
                      onClick={handleStartSession}
                    >
                      <Play size={20} className="mr-2" />
                      Start Interview
                      <ChevronRight size={16} className="ml-2" />
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <Brain size={48} className="mx-auto text-white/30 mb-4" />
                  <p className="text-white/60">Select an interview type to get started</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Tips */}
          <Card variant="outline">
            <CardHeader>
              <h3 className="text-lg font-medium text-white">💡 Pro Tips</h3>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-white/70">
                <li>• Find a quiet environment</li>
                <li>• Have pen and paper ready</li>
                <li>• Think out loud during the session</li>
                <li>• Don't rush - take your time</li>
                <li>• Ask clarifying questions</li>
              </ul>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
};
