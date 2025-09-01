import React from 'react';
import type { LucideIcon } from 'lucide-react';
import { clsx } from 'clsx';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'cyber' | 'neon' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: LucideIcon;
  rightIcon?: LucideIcon;
  fullWidth?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'cyber',
  size = 'md',
  isLoading = false,
  leftIcon: LeftIcon,
  rightIcon: RightIcon,
  fullWidth = false,
  className,
  disabled,
  ...props
}) => {
  const baseClasses = clsx(
    'inline-flex items-center justify-center font-medium transition-all duration-300',
    'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-space-900',
    'disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:transform-none',
    {
      'w-full': fullWidth,
      'px-3 py-1.5 text-sm rounded-md': size === 'sm',
      'px-4 py-2 text-base rounded-lg': size === 'md',
      'px-6 py-3 text-lg rounded-xl': size === 'lg',
    }
  );

  const variantClasses = {
    cyber: clsx(
      'bg-gradient-to-r from-cyber-500 to-cyber-400 text-white',
      'hover:from-cyber-400 hover:to-cyber-300 hover:-translate-y-1',
      'shadow-cyber hover:shadow-lg focus:ring-cyber-500',
      'active:transform-none'
    ),
    neon: clsx(
      'bg-gradient-to-r from-neon-500 to-electric-500 text-white',
      'hover:from-neon-400 hover:to-electric-400 hover:-translate-y-1',
      'shadow-neon hover:shadow-lg focus:ring-neon-500',
      'active:transform-none'
    ),
    ghost: clsx(
      'border border-cyber-500 text-cyber-400 bg-transparent',
      'hover:bg-cyber-500 hover:text-white hover:-translate-y-1',
      'focus:ring-cyber-500',
      'active:transform-none'
    ),
    danger: clsx(
      'bg-gradient-to-r from-red-600 to-red-500 text-white',
      'hover:from-red-500 hover:to-red-400 hover:-translate-y-1',
      'shadow-lg hover:shadow-red-500/25 focus:ring-red-500',
      'active:transform-none'
    ),
  };

  return (
    <button
      className={clsx(baseClasses, variantClasses[variant], className)}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <svg
          className="animate-spin -ml-1 mr-2 h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      
      {!isLoading && LeftIcon && <LeftIcon className="mr-2 h-4 w-4" />}
      
      <span>{children}</span>
      
      {!isLoading && RightIcon && <RightIcon className="ml-2 h-4 w-4" />}
    </button>
  );
};
