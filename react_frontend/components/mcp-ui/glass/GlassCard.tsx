import React from 'react';
import { cn } from '@/lib/utils';

interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  depth?: 'surface' | 'overlay' | 'elevated';
  variant?: 'default' | 'interactive' | 'price' | 'warning' | 'error';
  interactive?: boolean;
  onClick?: () => void;
}

export function GlassCard({
  children,
  className,
  depth = 'surface',
  variant = 'default',
  interactive = false,
  onClick,
}: GlassCardProps) {
  const baseClasses = [
    // Base glass effect
    'backdrop-blur-md',
    'border',
    'border-white/12',
    'rounded-xl',
    'shadow-lg',
    'shadow-black/8',
    'transition-all',
    'duration-200',
    'ease-out',
  ];

  // Depth-based background
  const depthClasses = {
    surface: 'bg-white/8',
    overlay: 'bg-white/5',
    elevated: 'bg-white/12',
  };

  // Variant-specific colors
  const variantClasses = {
    default: '',
    interactive: 'hover:bg-white/12 hover:shadow-xl hover:shadow-black/12 hover:-translate-y-0.5',
    price: 'bg-gradient-to-br from-white/8 to-white/4',
    warning: 'border-yellow-500/20 bg-yellow-500/5',
    error: 'border-red-500/20 bg-red-500/5',
  };

  const interactiveClasses = interactive
    ? [
        'cursor-pointer',
        'hover:bg-white/12',
        'hover:shadow-xl',
        'hover:shadow-black/12',
        'hover:-translate-y-0.5',
        'active:translate-y-0',
        'active:shadow-lg',
        'active:shadow-black/8',
      ]
    : [];

  const allClasses = cn(
    baseClasses,
    depthClasses[depth],
    variantClasses[variant],
    interactiveClasses,
    className
  );

  return (
    <div
      className={allClasses}
      onClick={interactive ? onClick : undefined}
      style={{
        // Fallback for browsers without backdrop-filter
        background:
          variant === 'error'
            ? 'rgba(239, 68, 68, 0.1)'
            : variant === 'warning'
              ? 'rgba(251, 191, 36, 0.1)'
              : depth === 'surface'
                ? 'rgba(255, 255, 255, 0.08)'
                : depth === 'overlay'
                  ? 'rgba(255, 255, 255, 0.05)'
                  : 'rgba(255, 255, 255, 0.12)',
        // Ensure border is visible
        borderColor:
          variant === 'error'
            ? 'rgba(239, 68, 68, 0.2)'
            : variant === 'warning'
              ? 'rgba(251, 191, 36, 0.2)'
              : 'rgba(255, 255, 255, 0.12)',
      }}
    >
      {children}
    </div>
  );
}

// Glass card content areas with consistent spacing
export function GlassCardHeader({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={cn('p-6 pb-4', className)}>{children}</div>;
}

export function GlassCardContent({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={cn('px-6 pb-6', className)}>{children}</div>;
}

export function GlassCardTitle({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <h3
      className={cn('text-sm font-medium tracking-wide text-white/75 uppercase', 'mb-2', className)}
    >
      {children}
    </h3>
  );
}

export function GlassCardValue({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={cn('text-2xl font-bold text-white/95', className)}>{children}</div>;
}

export function GlassCardSubtitle({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <p className={cn('mt-1 text-xs text-white/55', className)}>{children}</p>;
}
