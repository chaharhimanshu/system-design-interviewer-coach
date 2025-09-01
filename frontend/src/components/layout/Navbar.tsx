import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { clsx } from 'clsx';
import { 
  Home, 
  Plus, 
  History, 
  BarChart3, 
  User, 
  Settings,
  Zap,
  Brain
} from 'lucide-react';
import { Button } from '../ui/Button';

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'New Session', href: '/new-session', icon: Plus },
  { name: 'History', href: '/history', icon: History },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
];

const userNavigation = [
  { name: 'Profile', href: '/profile', icon: User },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export const Navbar: React.FC = () => {
  const location = useLocation();

  return (
    <nav className="fixed top-0 left-0 right-0 z-40 glass border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2 group">
              <motion.div
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="p-2 rounded-lg bg-gradient-to-r from-cyber-500 to-electric-500 shadow-cyber"
              >
                <Brain className="h-6 w-6 text-white" />
              </motion.div>
              <span className="text-xl font-bold bg-gradient-to-r from-cyber-400 to-electric-400 bg-clip-text text-transparent">
                InterviewCoach
              </span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:block">
            <div className="ml-10 flex items-center space-x-1">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href;
                const Icon = item.icon;
                
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={clsx(
                      'px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center space-x-2 relative group',
                      isActive
                        ? 'text-cyber-400 bg-cyber-500/10'
                        : 'text-white/70 hover:text-white hover:bg-white/5'
                    )}
                  >
                    <Icon size={16} />
                    <span>{item.name}</span>
                    {isActive && (
                      <motion.div
                        layoutId="navbar-active"
                        className="absolute inset-0 rounded-lg border border-cyber-500/30 bg-cyber-500/5"
                        transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                      />
                    )}
                  </Link>
                );
              })}
            </div>
          </div>

          {/* User Menu */}
          <div className="flex items-center space-x-4">
            {/* Quick Action Button */}
            <Link to="/new-session" className="hidden sm:block">
              <Button 
                variant="cyber" 
                size="sm"
              >
                <Zap size={16} className="mr-2" />
                Quick Start
              </Button>
            </Link>

            {/* User Navigation */}
            <div className="flex items-center space-x-1">
              {userNavigation.map((item) => {
                const Icon = item.icon;
                
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className="p-2 rounded-lg text-white/70 hover:text-white hover:bg-white/5 transition-all duration-200"
                    title={item.name}
                  >
                    <Icon size={18} />
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      <div className="md:hidden border-t border-white/10">
        <div className="flex items-center justify-around py-2">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href;
            const Icon = item.icon;
            
            return (
              <Link
                key={item.name}
                to={item.href}
                className={clsx(
                  'flex flex-col items-center p-2 rounded-lg text-xs transition-all duration-200',
                  isActive
                    ? 'text-cyber-400'
                    : 'text-white/60 hover:text-white'
                )}
              >
                <Icon size={20} />
                <span className="mt-1">{item.name}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
};
