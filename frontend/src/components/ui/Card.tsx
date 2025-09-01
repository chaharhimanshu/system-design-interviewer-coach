import React from 'react';
import { clsx } from 'clsx';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'glass' | 'solid' | 'outline';
  hover?: boolean;
  glow?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'glass',
  hover = false,
  glow = false,
  className,
  ...props
}) => {
  const baseClasses = 'relative overflow-hidden transition-all duration-300';

  const variantClasses = {
    glass: 'glass',
    solid: 'bg-space-800 border border-space-700 rounded-lg',
    outline: 'border border-cyber-500/30 rounded-lg bg-transparent',
  };

  const interactiveClasses = clsx({
    'card-hover cursor-pointer': hover,
    'shadow-cyber': glow && variant === 'glass',
    'shadow-lg': glow && variant === 'solid',
  });

  return (
    <div
      className={clsx(baseClasses, variantClasses[variant], interactiveClasses, className)}
      {...props}
    >
      {children}
    </div>
  );
};

interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {}

export const CardHeader: React.FC<CardHeaderProps> = ({
  children,
  className,
  ...props
}) => {
  return (
    <div
      className={clsx('px-6 py-4 border-b border-white/10', className)}
      {...props}
    >
      {children}
    </div>
  );
};

interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {}

export const CardContent: React.FC<CardContentProps> = ({
  children,
  className,
  ...props
}) => {
  return (
    <div
      className={clsx('px-6 py-4', className)}
      {...props}
    >
      {children}
    </div>
  );
};

interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {}

export const CardFooter: React.FC<CardFooterProps> = ({
  children,
  className,
  ...props
}) => {
  return (
    <div
      className={clsx('px-6 py-4 border-t border-white/10', className)}
      {...props}
    >
      {children}
    </div>
  );
};
