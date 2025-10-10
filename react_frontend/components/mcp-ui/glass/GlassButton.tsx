import React from 'react';
import { cn } from '@/lib/utils';

interface GlassButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  className?: string;
  icon?: React.ReactNode;
  loading?: boolean;
}

export function GlassButton({
  children,
  onClick,
  variant = 'primary',
  size = 'md',
  disabled = false,
  className,
  icon,
  loading = false,
}: GlassButtonProps) {
  const baseClasses = [
    'inline-flex',
    'items-center',
    'justify-center',
    'rounded-lg',
    'font-medium',
    'transition-all',
    'duration-200',
    'ease-out',
    'focus:outline-none',
    'focus:ring-2',
    'focus:ring-white/20',
    'disabled:opacity-50',
    'disabled:cursor-not-allowed',
  ];

  const variantClasses = {
    primary: [
      'bg-white/10',
      'backdrop-blur-sm',
      'border',
      'border-white/20',
      'text-white/95',
      'hover:bg-white/15',
      'hover:border-white/30',
      'active:bg-white/20',
    ],
    secondary: [
      'bg-white/5',
      'backdrop-blur-sm',
      'border',
      'border-white/12',
      'text-white/75',
      'hover:bg-white/10',
      'hover:border-white/20',
      'active:bg-white/15',
    ],
    outline: [
      'border',
      'border-white/20',
      'text-white/85',
      'hover:bg-white/5',
      'hover:border-white/30',
      'backdrop-blur-sm',
    ],
    ghost: ['text-white/75', 'hover:text-white/95', 'hover:bg-white/5'],
  };

  const sizeClasses = {
    sm: ['px-3', 'py-1.5', 'text-sm'],
    md: ['px-4', 'py-2', 'text-base'],
    lg: ['px-6', 'py-3', 'text-lg'],
  };

  const allClasses = cn(baseClasses, variantClasses[variant], sizeClasses[size], className);

  return (
    <button className={allClasses} onClick={onClick} disabled={disabled || loading}>
      {loading && (
        <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white/20 border-t-white/60" />
      )}
      {icon && !loading && <span className="mr-2">{icon}</span>}
      {children}
    </button>
  );
}

// Specialized glass buttons for common use cases
export function GlassIconButton({
  icon,
  onClick,
  active = false,
  size = 'md',
  className,
}: {
  icon: React.ReactNode;
  onClick?: () => void;
  active?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}) {
  const sizeClasses = {
    sm: 'p-2',
    md: 'p-3',
    lg: 'p-4',
  };

  return (
    <button
      onClick={onClick}
      className={cn(
        'inline-flex items-center justify-center rounded-lg',
        'backdrop-blur-sm transition-all duration-200 ease-out',
        'hover:bg-white/10 active:bg-white/15',
        'focus:ring-2 focus:ring-white/20 focus:outline-none',
        sizeClasses[size],
        active && 'border border-blue-500/25 bg-blue-500/15',
        className
      )}
    >
      <span
        className={cn(
          'text-white/75 transition-colors',
          active && 'text-blue-300',
          !active && 'hover:text-white/95'
        )}
      >
        {icon}
      </span>
    </button>
  );
}
