'use client';

import { cn } from '@/lib/utils';
import { motion, type HTMLMotionProps } from 'framer-motion';

interface GlassCardProps extends HTMLMotionProps<'div'> {
  children: React.ReactNode;
  className?: string;
  gradient?: boolean;
}

export function GlassCard({
  children,
  className,
  gradient = false,
  ...props
}: GlassCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        'relative rounded-2xl border border-white/10 p-4',
        'bg-white/5 backdrop-blur-xl',
        'shadow-lg shadow-black/5',
        gradient && 'bg-gradient-to-br from-blue-500/10 to-purple-500/10',
        className
      )}
      {...props}
    >
      {children}
    </motion.div>
  );
}
