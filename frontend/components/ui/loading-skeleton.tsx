'use client';

import { cn } from '@/lib/utils';

interface LoadingSkeletonProps {
  className?: string;
  count?: number;
}

export function LoadingSkeleton({ className, count = 1 }: LoadingSkeletonProps) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className={cn(
            'animate-pulse rounded-xl bg-white/10',
            className
          )}
        />
      ))}
    </>
  );
}

export function CardSkeleton() {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4 space-y-3">
      <LoadingSkeleton className="h-6 w-1/3" />
      <LoadingSkeleton className="h-10 w-2/3" />
      <LoadingSkeleton className="h-4 w-1/2" />
    </div>
  );
}

export function StatsSkeleton() {
  return (
    <div className="space-y-4">
      <CardSkeleton />
      <div className="grid grid-cols-2 gap-3">
        <CardSkeleton />
        <CardSkeleton />
      </div>
    </div>
  );
}

export function LeaderboardSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          className="flex items-center gap-3 rounded-xl bg-white/5 p-3"
        >
          <LoadingSkeleton className="size-8 rounded-full" />
          <LoadingSkeleton className="h-5 flex-1" />
          <LoadingSkeleton className="h-5 w-16" />
        </div>
      ))}
    </div>
  );
}
