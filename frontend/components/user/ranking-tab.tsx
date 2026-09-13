'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Trophy, Medal, Award } from 'lucide-react';
import { userAPI } from '@/lib/api';
import type { RankingPeriod } from '@/lib/types';
import { GlassCard } from '@/components/ui/glass-card';
import { LeaderboardSkeleton } from '@/components/ui/loading-skeleton';
import { cn } from '@/lib/utils';

const periods: { id: RankingPeriod; label: string }[] = [
  { id: 'week', label: 'Haftalik' },
  { id: 'month', label: 'Oylik' },
  { id: 'all', label: 'Umumiy' },
];

const medalIcons = [
  { Icon: Trophy, color: 'text-yellow-400', bg: 'bg-yellow-400/20' },
  { Icon: Medal, color: 'text-gray-300', bg: 'bg-gray-300/20' },
  { Icon: Award, color: 'text-amber-600', bg: 'bg-amber-600/20' },
];

export function RankingTab() {
  const [period, setPeriod] = useState<RankingPeriod>('week');

  const { data, isLoading, error } = useQuery({
    queryKey: ['rankings', period],
    queryFn: () => userAPI.getRankings(period),
  });

  return (
    <div className="space-y-4 pb-24">
      {/* Period Tabs */}
      <div className="flex gap-2 rounded-xl bg-white/5 p-1">
        {periods.map((p) => (
          <button
            key={p.id}
            onClick={() => {
              setPeriod(p.id);
              window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
            }}
            className={cn(
              'relative flex-1 rounded-lg py-2 text-sm font-medium transition-colors',
              period === p.id ? 'text-white' : 'text-white/50'
            )}
          >
            {period === p.id && (
              <motion.div
                layoutId="periodTab"
                className="absolute inset-0 rounded-lg bg-gradient-to-r from-blue-500/30 to-purple-500/30"
                transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
              />
            )}
            <span className="relative">{p.label}</span>
          </button>
        ))}
      </div>

      {/* Leaderboard */}
      {isLoading ? (
        <LeaderboardSkeleton />
      ) : error ? (
        <div className="py-8 text-center text-red-400">
          Xatolik yuz berdi
        </div>
      ) : (
        <AnimatePresence mode="wait">
          <motion.div
            key={period}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-2"
          >
            {data?.length === 0 ? (
              <div className="py-12 text-center text-white/50">
                Hozircha reyting yo&apos;q
              </div>
            ) : (
              data?.map((user, index) => {
                const medal = medalIcons[index];
                const isTop3 = index < 3;
                const isCurrentUser = user.user_id === window.Telegram?.WebApp?.initDataUnsafe?.user?.id;

                return (
                  <GlassCard
                    key={index}
                    className={cn(
                      'flex items-center gap-3 !p-3',
                      isTop3 && 'border-white/20',
                      isCurrentUser && 'border-blue-500 bg-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.5)]'
                    )}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <div
                      className={cn(
                        'flex size-10 items-center justify-center rounded-full',
                        isTop3 ? medal?.bg : 'bg-white/10'
                      )}
                    >
                      {isTop3 && medal ? (
                        <medal.Icon className={cn('size-5', medal.color)} />
                      ) : (
                        <span className="text-sm font-bold text-white/70">
                          {index + 1}
                        </span>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="truncate font-medium text-white">
                        {user.name}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-white">{user.score}</p>
                      <p className="text-xs text-white/50">ball</p>
                    </div>
                  </GlassCard>
                );
              })
            )}
          </motion.div>
        </AnimatePresence>
      )}
    </div>
  );
}
