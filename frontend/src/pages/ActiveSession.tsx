import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Send, 
  Pause,
  Square,
  Clock,
  Target,
  Brain,
  MessageSquare,
  FileText,
  Volume2,
  Settings,
  Lightbulb,
  CheckCircle
} from 'lucide-react';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Textarea } from '../components/ui/Input';

// Mock session data
const mockSession = {
  id: 'session_123',
  type: 'System Design',
  topic: 'Design Twitter/X',
  difficulty: 'Advanced',
  duration: 60,
  currentQuestion: {
    content: "Let's design a social media platform like Twitter. Start by walking me through the high-level architecture and key components you would need.",
    timestamp: new Date().toISOString()
  },
  progress: {
    completed: 2,
    total: 6,
    currentPhase: 'Requirements Gathering'
  },
  tips: [
    'Start with clarifying questions about scale and features',
    'Think about the core entities: Users, Tweets, Followers',
    'Consider read vs write patterns - Twitter is read-heavy'
  ]
};

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: string;
  type?: 'text' | 'audio' | 'file';
  attachments?: Array<{
    name: string;
    type: string;
    url: string;
  }>;
}

export const ActiveSession: React.FC = () => {
  // const { sessionId } = useParams<{ sessionId: string }>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize with welcome message
  useEffect(() => {
    const welcomeMessage: Message = {
      id: 'welcome',
      content: `Welcome to your ${mockSession.type} interview session. I'll be your interviewer today. Let's start with: ${mockSession.topic}`,
      sender: 'ai',
      timestamp: new Date().toISOString(),
      type: 'text'
    };
    setMessages([welcomeMessage]);
  }, []);

  // Auto scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Timer for session duration
  useEffect(() => {
    const interval = setInterval(() => {
      setElapsedTime(prev => prev + 1);
    }, 1000);
    
    return () => clearInterval(interval);
  }, []);

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    const newMessage: Message = {
      id: `user_${Date.now()}`,
      content: inputValue,
      sender: 'user',
      timestamp: new Date().toISOString(),
      type: 'text'
    };
    
    setMessages(prev => [...prev, newMessage]);
    setInputValue('');
    
    // Simulate AI typing
    setIsTyping(true);
    setTimeout(() => {
      const aiResponse: Message = {
        id: `ai_${Date.now()}`,
        content: "That's a great start! Can you elaborate on how you would handle the scale of millions of users posting tweets simultaneously? What database choices would you make?",
        sender: 'ai',
        timestamp: new Date().toISOString(),
        type: 'text'
      };
      setMessages(prev => [...prev, aiResponse]);
      setIsTyping(false);
    }, 2000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="h-screen flex flex-col bg-space-900">
      {/* Session Header */}
      <div className="glass border-b border-white/10 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Brain className="h-6 w-6 text-cyber-400" />
              <div>
                <h1 className="text-lg font-semibold text-white">{mockSession.topic}</h1>
                <p className="text-sm text-white/60">{mockSession.type} • {mockSession.difficulty}</p>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-white/70">
              <Clock className="h-4 w-4" />
              <span className="text-sm font-mono">{formatTime(elapsedTime)}</span>
            </div>
            
            <div className="flex items-center space-x-1">
              <Button variant="ghost" size="sm">
                <Pause className="h-4 w-4" />
              </Button>
              <Button variant="danger" size="sm">
                <Square className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
        
        {/* Progress Bar */}
        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-white/70">Progress: {mockSession.progress.currentPhase}</span>
            <span className="text-sm text-white/70">{mockSession.progress.completed}/{mockSession.progress.total}</span>
          </div>
          <div className="w-full bg-space-700 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-cyber-500 to-electric-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${(mockSession.progress.completed / mockSession.progress.total) * 100}%` }}
            />
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
            <AnimatePresence>
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-3xl p-4 rounded-lg ${
                    message.sender === 'user' 
                      ? 'bg-cyber-500/20 border border-cyber-500/30' 
                      : 'bg-white/5 border border-white/10'
                  }`}>
                    <div className="flex items-start space-x-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                        message.sender === 'user'
                          ? 'bg-cyber-500 text-white'
                          : 'bg-electric-500 text-white'
                      }`}>
                        {message.sender === 'user' ? 'U' : 'AI'}
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <span className="text-sm font-medium text-white">
                            {message.sender === 'user' ? 'You' : 'AI Interviewer'}
                          </span>
                          {message.type === 'audio' && <Volume2 className="h-4 w-4 text-neon-400" />}
                          {message.type === 'file' && <FileText className="h-4 w-4 text-orange-400" />}
                          <span className="text-xs text-white/50">
                            {new Date(message.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        
                        <p className="text-white/90 leading-relaxed">{message.content}</p>
                        
                        {message.attachments && (
                          <div className="mt-3 space-y-2">
                            {message.attachments.map((attachment, index) => (
                              <div key={index} className="flex items-center space-x-2 p-2 bg-white/5 rounded border border-white/10">
                                <FileText className="h-4 w-4 text-orange-400" />
                                <span className="text-sm text-white/70">{attachment.name}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            
            {/* Typing Indicator */}
            {isTyping && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-start"
              >
                <div className="bg-white/5 border border-white/10 p-4 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-full bg-electric-500 flex items-center justify-center text-sm font-medium text-white">
                      AI
                    </div>
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-electric-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-electric-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-electric-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-white/10 p-4">
            <div className="flex items-end space-x-4">
              <div className="flex-1">
                <Textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your response or thoughts..."
                  className="min-h-[60px] max-h-[120px]"
                  rows={3}
                />
              </div>
              
              <div className="flex items-center space-x-2">
                <Button
                  variant="cyber"
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim()}
                  className="h-10 px-6"
                >
                  <Send className="h-4 w-4 mr-2" />
                  Send
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="w-80 border-l border-white/10 flex flex-col">
          {/* Tips & Hints */}
          <div className="p-4 border-b border-white/10">
            <Card variant="glass">
              <CardHeader>
                <h3 className="text-sm font-medium text-white flex items-center">
                  <Lightbulb className="h-4 w-4 mr-2 text-neon-400" />
                  Tips & Hints
                </h3>
              </CardHeader>
              <CardContent className="space-y-2">
                {mockSession.tips.map((tip, index) => (
                  <div key={index} className="flex items-start space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-400 mt-0.5 flex-shrink-0" />
                    <p className="text-xs text-white/70">{tip}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Session Actions */}
          <div className="p-4">
            <Card variant="glass">
              <CardHeader>
                <h3 className="text-sm font-medium text-white flex items-center">
                  <Target className="h-4 w-4 mr-2 text-electric-400" />
                  Session Actions
                </h3>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button variant="ghost" size="sm" className="w-full justify-start">
                  <MessageSquare className="h-4 w-4 mr-2" />
                  Ask for Clarification
                </Button>
                <Button variant="ghost" size="sm" className="w-full justify-start">
                  <FileText className="h-4 w-4 mr-2" />
                  Request Feedback
                </Button>
                <Button variant="ghost" size="sm" className="w-full justify-start">
                  <Settings className="h-4 w-4 mr-2" />
                  Adjust Difficulty
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};
