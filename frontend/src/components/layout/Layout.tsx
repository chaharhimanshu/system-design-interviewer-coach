import React from 'react';
import { Navbar } from './Navbar';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-space-900 relative overflow-x-hidden">
      {/* Background Elements */}
      <div className="fixed inset-0 z-0">
        <div className="cyber-grid opacity-20"></div>
        <div className="absolute inset-0 bg-gradient-to-br from-cyber-900/20 via-transparent to-electric-900/20"></div>
      </div>
      
      {/* Navigation */}
      <Navbar />
      
      {/* Main Content */}
      <main className="relative z-10 pt-16">
        {children}
      </main>
    </div>
  );
};
