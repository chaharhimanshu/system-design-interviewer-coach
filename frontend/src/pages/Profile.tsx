import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  User,
  Settings,
  Bell,
  Shield,
  Palette,
  Download,
  Upload,
  Save,
  Camera,
  Mail,
  Phone,
  MapPin,
  Calendar,
  Target,
  Star,
  Lock,
  Eye,
  Trash2,
  Clock,
  Zap
} from 'lucide-react';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';

// Mock user data
const mockUser = {
  id: '1',
  name: 'Alex Chen',
  email: 'alex.chen@email.com',
  phone: '+1 (555) 123-4567',
  location: 'San Francisco, CA',
  joinedDate: '2024-01-01',
  role: 'Senior Software Engineer',
  company: 'Tech Corp',
  avatar: '/api/placeholder/150/150',
  goals: [
    'System Design Expert',
    'FAANG Interview Ready',
    'Leadership Skills'
  ],
  preferences: {
    theme: 'dark',
    language: 'en',
    timezone: 'PST',
    notifications: {
      email: true,
      push: true,
      reminders: true,
      weeklyReport: true
    }
  },
  stats: {
    totalSessions: 12,
    averageScore: 8.5,
    hoursSpent: 24.5,
    streak: 7
  }
};

export const Profile: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'profile' | 'settings' | 'privacy' | 'export'>('profile');
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: mockUser.name,
    email: mockUser.email,
    phone: mockUser.phone,
    location: mockUser.location,
    role: mockUser.role,
    company: mockUser.company
  });

  const [notifications, setNotifications] = useState(mockUser.preferences.notifications);

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'settings', label: 'Settings', icon: Settings },
    { id: 'privacy', label: 'Privacy', icon: Shield },
    { id: 'export', label: 'Data Export', icon: Download }
  ];

  const handleSave = () => {
    setIsEditing(false);
    // Here you would typically save to backend
    console.log('Saving profile data:', formData);
  };

  const handleNotificationChange = (key: string, value: boolean) => {
    setNotifications(prev => ({ ...prev, [key]: value }));
  };

  const renderProfile = () => (
    <div className="space-y-6">
      {/* Profile Header */}
      <Card variant="glass" glow>
        <CardContent className="p-6">
          <div className="flex items-start space-x-6">
            <div className="relative group">
              <div className="w-24 h-24 rounded-full bg-gradient-to-r from-cyber-500 to-electric-500 flex items-center justify-center text-white text-2xl font-bold">
                {mockUser.name.split(' ').map(n => n[0]).join('')}
              </div>
              {isEditing && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="absolute -bottom-2 -right-2 w-8 h-8 rounded-full bg-cyber-500 hover:bg-cyber-600"
                >
                  <Camera size={14} />
                </Button>
              )}
            </div>
            
            <div className="flex-1">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-2xl font-bold text-white">{mockUser.name}</h2>
                  <p className="text-white/70">{mockUser.role} at {mockUser.company}</p>
                </div>
                <Button
                  variant={isEditing ? 'cyber' : 'ghost'}
                  onClick={isEditing ? handleSave : () => setIsEditing(true)}
                >
                  {isEditing ? <Save size={16} className="mr-2" /> : <Settings size={16} className="mr-2" />}
                  {isEditing ? 'Save Changes' : 'Edit Profile'}
                </Button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div className="flex items-center text-white/70">
                  <Mail size={16} className="mr-2 text-cyber-400" />
                  {mockUser.email}
                </div>
                <div className="flex items-center text-white/70">
                  <Phone size={16} className="mr-2 text-electric-400" />
                  {mockUser.phone}
                </div>
                <div className="flex items-center text-white/70">
                  <MapPin size={16} className="mr-2 text-neon-400" />
                  {mockUser.location}
                </div>
                <div className="flex items-center text-white/70">
                  <Calendar size={16} className="mr-2 text-orange-400" />
                  Joined {new Date(mockUser.joinedDate).toLocaleDateString()}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Profile Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Sessions', value: mockUser.stats.totalSessions, icon: Target, color: 'cyber' },
          { label: 'Avg Score', value: mockUser.stats.averageScore, icon: Star, color: 'electric' },
          { label: 'Hours', value: `${mockUser.stats.hoursSpent}h`, icon: Clock, color: 'neon' },
          { label: 'Streak', value: `${mockUser.stats.streak}d`, icon: Zap, color: 'orange' }
        ].map((stat, index) => (
          <motion.div key={stat.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.1 }}>
            <Card variant="glass">
              <CardContent className="p-4 text-center">
                <stat.icon size={24} className={`mx-auto mb-2 text-${stat.color}-400`} />
                <div className="text-xl font-bold text-white">{stat.value}</div>
                <div className="text-sm text-white/60">{stat.label}</div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Edit Form */}
      {isEditing && (
        <Card variant="glass">
          <CardHeader>
            <h3 className="text-lg font-semibold text-white">Edit Profile</h3>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2">Full Name</label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Enter your full name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2">Email</label>
                <Input
                  value={formData.email}
                  onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                  placeholder="Enter your email"
                  type="email"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2">Phone</label>
                <Input
                  value={formData.phone}
                  onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                  placeholder="Enter your phone"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2">Location</label>
                <Input
                  value={formData.location}
                  onChange={(e) => setFormData(prev => ({ ...prev, location: e.target.value }))}
                  placeholder="Enter your location"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2">Role</label>
                <Input
                  value={formData.role}
                  onChange={(e) => setFormData(prev => ({ ...prev, role: e.target.value }))}
                  placeholder="Enter your role"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2">Company</label>
                <Input
                  value={formData.company}
                  onChange={(e) => setFormData(prev => ({ ...prev, company: e.target.value }))}
                  placeholder="Enter your company"
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Goals */}
      <Card variant="glass">
        <CardHeader>
          <h3 className="text-lg font-semibold text-white flex items-center">
            <Target size={18} className="mr-2 text-electric-400" />
            Learning Goals
          </h3>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {mockUser.goals.map((goal) => (
              <div key={goal} className="px-3 py-1 bg-cyber-500/20 border border-cyber-500/30 rounded-full text-sm text-cyber-400">
                {goal}
              </div>
            ))}
            {isEditing && (
              <Button variant="ghost" size="sm" className="px-3 py-1 text-sm border-dashed border-white/30">
                + Add Goal
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderSettings = () => (
    <div className="space-y-6">
      {/* Notifications */}
      <Card variant="glass">
        <CardHeader>
          <h3 className="text-lg font-semibold text-white flex items-center">
            <Bell size={18} className="mr-2 text-cyber-400" />
            Notification Preferences
          </h3>
        </CardHeader>
        <CardContent className="space-y-4">
          {[
            { key: 'email', label: 'Email Notifications', description: 'Receive updates via email' },
            { key: 'push', label: 'Push Notifications', description: 'Browser push notifications' },
            { key: 'reminders', label: 'Session Reminders', description: 'Reminders before scheduled sessions' },
            { key: 'weeklyReport', label: 'Weekly Reports', description: 'Weekly progress summaries' }
          ].map((item) => (
            <div key={item.key} className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/10">
              <div>
                <div className="text-white font-medium">{item.label}</div>
                <div className="text-sm text-white/60">{item.description}</div>
              </div>
              <Button
                variant={notifications[item.key as keyof typeof notifications] ? 'cyber' : 'ghost'}
                size="sm"
                onClick={() => handleNotificationChange(item.key, !notifications[item.key as keyof typeof notifications])}
              >
                {notifications[item.key as keyof typeof notifications] ? 'On' : 'Off'}
              </Button>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Appearance */}
      <Card variant="glass">
        <CardHeader>
          <h3 className="text-lg font-semibold text-white flex items-center">
            <Palette size={18} className="mr-2 text-electric-400" />
            Appearance & Language
          </h3>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">Theme</label>
              <select className="w-full p-2 bg-space-800 border border-white/20 rounded-lg text-white focus:border-cyber-500">
                <option value="dark">Dark (Current)</option>
                <option value="light">Light</option>
                <option value="auto">System</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">Language</label>
              <select className="w-full p-2 bg-space-800 border border-white/20 rounded-lg text-white focus:border-cyber-500">
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Session Defaults */}
      <Card variant="glass">
        <CardHeader>
          <h3 className="text-lg font-semibold text-white flex items-center">
            <Settings size={18} className="mr-2 text-neon-400" />
            Session Defaults
          </h3>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">Default Session Duration</label>
              <select className="w-full p-2 bg-space-800 border border-white/20 rounded-lg text-white focus:border-cyber-500">
                <option value="30">30 minutes</option>
                <option value="45">45 minutes</option>
                <option value="60">60 minutes</option>
                <option value="90">90 minutes</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-white/70 mb-2">Difficulty Level</label>
              <select className="w-full p-2 bg-space-800 border border-white/20 rounded-lg text-white focus:border-cyber-500">
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
                <option value="expert">Expert</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderPrivacy = () => (
    <div className="space-y-6">
      {/* Account Security */}
      <Card variant="glass">
        <CardHeader>
          <h3 className="text-lg font-semibold text-white flex items-center">
            <Lock size={18} className="mr-2 text-red-400" />
            Account Security
          </h3>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-white font-medium">Password</div>
                <div className="text-sm text-white/60">Last changed 2 months ago</div>
              </div>
              <Button variant="ghost" size="sm">Change Password</Button>
            </div>
          </div>
          
          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-white font-medium">Two-Factor Authentication</div>
                <div className="text-sm text-white/60">Add an extra layer of security</div>
              </div>
              <Button variant="cyber" size="sm">Enable 2FA</Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Data Privacy */}
      <Card variant="glass">
        <CardHeader>
          <h3 className="text-lg font-semibold text-white flex items-center">
            <Eye size={18} className="mr-2 text-electric-400" />
            Data Privacy
          </h3>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-white font-medium">Session Recordings</div>
                <div className="text-sm text-white/60">Allow system to record sessions for feedback</div>
              </div>
              <Button variant="cyber" size="sm">Enabled</Button>
            </div>
          </div>
          
          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-white font-medium">Analytics Tracking</div>
                <div className="text-sm text-white/60">Help improve the platform with usage data</div>
              </div>
              <Button variant="cyber" size="sm">Enabled</Button>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-white/5 border border-white/10">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-white font-medium">Profile Visibility</div>
                <div className="text-sm text-white/60">Control who can see your profile</div>
              </div>
              <select className="p-1 bg-space-800 border border-white/20 rounded text-white text-sm">
                <option>Private</option>
                <option>Public</option>
                <option>Friends Only</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Danger Zone */}
      <Card variant="glass" className="border-red-500/30">
        <CardHeader>
          <h3 className="text-lg font-semibold text-red-400 flex items-center">
            <Trash2 size={18} className="mr-2" />
            Danger Zone
          </h3>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-red-400 font-medium">Delete Account</div>
                <div className="text-sm text-white/60">Permanently delete your account and all data</div>
              </div>
              <Button variant="ghost" size="sm" className="border-red-500 text-red-400 hover:bg-red-500/10">
                Delete Account
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderExport = () => (
    <div className="space-y-6">
      {/* Data Export */}
      <Card variant="glass">
        <CardHeader>
          <h3 className="text-lg font-semibold text-white flex items-center">
            <Download size={18} className="mr-2 text-cyber-400" />
            Export Your Data
          </h3>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-white/70">
            Download all your data including session history, feedback, and analytics in a structured format.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-white/5 border border-white/10">
              <h4 className="text-white font-medium mb-2">Session Data</h4>
              <p className="text-sm text-white/60 mb-3">All your interview sessions and recordings</p>
              <Button variant="cyber" size="sm">
                <Download size={14} className="mr-2" />
                Export Sessions
              </Button>
            </div>
            
            <div className="p-4 rounded-lg bg-white/5 border border-white/10">
              <h4 className="text-white font-medium mb-2">Analytics Data</h4>
              <p className="text-sm text-white/60 mb-3">Progress reports and performance metrics</p>
              <Button variant="cyber" size="sm">
                <Download size={14} className="mr-2" />
                Export Analytics
              </Button>
            </div>
            
            <div className="p-4 rounded-lg bg-white/5 border border-white/10">
              <h4 className="text-white font-medium mb-2">Profile Data</h4>
              <p className="text-sm text-white/60 mb-3">Account information and preferences</p>
              <Button variant="neon" size="sm">
                <Download size={14} className="mr-2" />
                Export Profile
              </Button>
            </div>
            
            <div className="p-4 rounded-lg bg-white/5 border border-white/10">
              <h4 className="text-white font-medium mb-2">Complete Export</h4>
              <p className="text-sm text-white/60 mb-3">All data in a single archive</p>
              <Button variant="ghost" size="sm" className="border-white/30">
                <Download size={14} className="mr-2" />
                Export All
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Import Data */}
      <Card variant="glass">
        <CardHeader>
          <h3 className="text-lg font-semibold text-white flex items-center">
            <Upload size={18} className="mr-2 text-electric-400" />
            Import Data
          </h3>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-white/70">
            Import data from other interview preparation platforms or your previous exports.
          </p>
          
          <div className="p-4 rounded-lg bg-white/5 border border-white/10 border-dashed">
            <div className="text-center">
              <Upload size={32} className="mx-auto mb-3 text-white/40" />
              <p className="text-white/60 mb-2">Drag and drop your data file here</p>
              <Button variant="ghost" size="sm">
                Choose File
              </Button>
            </div>
          </div>
          
          <div className="text-sm text-white/50">
            <p>Supported formats: JSON, CSV, ZIP</p>
            <p>Maximum file size: 100MB</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold text-white mb-2">Profile & Settings</h1>
        <p className="text-white/70">
          Manage your account preferences and privacy settings
        </p>
      </motion.div>

      {/* Tabs */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mb-8"
      >
        <div className="flex space-x-1 p-1 bg-space-900/50 rounded-lg border border-white/10">
          {tabs.map((tab) => (
            <Button
              key={tab.id}
              variant={activeTab === tab.id ? 'cyber' : 'ghost'}
              size="sm"
              onClick={() => setActiveTab(tab.id as any)}
              className="flex-1"
            >
              <tab.icon size={16} className="mr-2" />
              {tab.label}
            </Button>
          ))}
        </div>
      </motion.div>

      {/* Tab Content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3 }}
      >
        {activeTab === 'profile' && renderProfile()}
        {activeTab === 'settings' && renderSettings()}
        {activeTab === 'privacy' && renderPrivacy()}
        {activeTab === 'export' && renderExport()}
      </motion.div>
    </div>
  );
};
