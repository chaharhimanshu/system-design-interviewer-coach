import React, { forwardRef } from 'react';
import { clsx } from 'clsx';
import { Eye, EyeOff } from 'lucide-react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helper?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  variant?: 'default' | 'cyber';
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({
    className,
    type,
    label,
    error,
    helper,
    leftIcon,
    rightIcon,
    variant = 'default',
    ...props
  }, ref) => {
    const [showPassword, setShowPassword] = React.useState(false);
    const isPassword = type === 'password';
    const inputType = isPassword && showPassword ? 'text' : type;

    const baseClasses = clsx(
      'flex h-12 w-full rounded-lg border px-4 py-2 text-sm file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-white/40 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50 transition-all duration-200',
      leftIcon && 'pl-11',
      (rightIcon || isPassword) && 'pr-11'
    );

    const variantClasses = {
      default: clsx(
        'border-space-600 bg-space-800/50 backdrop-blur-sm text-white',
        'focus-visible:border-cyber-500 focus-visible:ring-1 focus-visible:ring-cyber-500/20',
        'hover:border-cyber-600/50'
      ),
      cyber: clsx(
        'border-cyber-500/30 bg-transparent text-cyan-100',
        'focus-visible:border-cyber-400 focus-visible:ring-1 focus-visible:ring-cyber-400/30',
        'hover:border-cyber-500/50 hover:shadow-[0_0_10px_rgba(0,255,255,0.1)]'
      )
    };

    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-white/80 mb-2">
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-white/60">
              {leftIcon}
            </div>
          )}
          <input
            type={inputType}
            className={clsx(baseClasses, variantClasses[variant], className)}
            ref={ref}
            {...props}
          />
          {(rightIcon || isPassword) && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              {isPassword ? (
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="text-white/60 hover:text-white/80 transition-colors"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              ) : (
                <div className="text-white/60">{rightIcon}</div>
              )}
            </div>
          )}
        </div>
        {error && (
          <p className="mt-2 text-sm text-red-400 flex items-center gap-1">
            <span className="inline-block w-1 h-1 bg-red-400 rounded-full"></span>
            {error}
          </p>
        )}
        {helper && !error && (
          <p className="mt-2 text-sm text-white/60">{helper}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helper?: string;
  variant?: 'default' | 'cyber';
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({
    className,
    label,
    error,
    helper,
    variant = 'default',
    ...props
  }, ref) => {
    const baseClasses = clsx(
      'flex min-h-[80px] w-full rounded-lg border px-4 py-3 text-sm placeholder:text-white/40 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50 resize-vertical transition-all duration-200'
    );

    const variantClasses = {
      default: clsx(
        'border-space-600 bg-space-800/50 backdrop-blur-sm text-white',
        'focus-visible:border-cyber-500 focus-visible:ring-1 focus-visible:ring-cyber-500/20',
        'hover:border-cyber-600/50'
      ),
      cyber: clsx(
        'border-cyber-500/30 bg-transparent text-cyan-100',
        'focus-visible:border-cyber-400 focus-visible:ring-1 focus-visible:ring-cyber-400/30',
        'hover:border-cyber-500/50 hover:shadow-[0_0_10px_rgba(0,255,255,0.1)]'
      )
    };

    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-white/80 mb-2">
            {label}
          </label>
        )}
        <textarea
          className={clsx(baseClasses, variantClasses[variant], className)}
          ref={ref}
          {...props}
        />
        {error && (
          <p className="mt-2 text-sm text-red-400 flex items-center gap-1">
            <span className="inline-block w-1 h-1 bg-red-400 rounded-full"></span>
            {error}
          </p>
        )}
        {helper && !error && (
          <p className="mt-2 text-sm text-white/60">{helper}</p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';
