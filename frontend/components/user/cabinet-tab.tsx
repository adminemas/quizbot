'use client';

import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Coins, Target, CheckCircle, XCircle, Medal } from 'lucide-react';
import { userAPI } from '@/lib/api';
import { GlassCard } from '@/components/ui/glass-card';
import { StatsSkeleton } from '@/components/ui/loading-skeleton';

export function CabinetTab() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['userStats'],
    queryFn: userAPI.getStats,
  });

  if (isLoading) {
    return <StatsSkeleton />;
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <p className="text-red-400">Xatolik yuz berdi</p>
        <p className="text-sm text-white/50">Iltimos, qaytadan urinib ko&apos;ring</p>
      </div>
    );
  }

  if (!data) return null;

  const { user, stats, rank } = data;

  return (
    <div className="space-y-4 pb-24">
      {/* User Profile Card */}
      <GlassCard gradient className="text-center">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', bounce: 0.5 }}
          className="mx-auto mb-4 flex size-20 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-600"
        >
          <span className="text-3xl font-bold text-white">
            {user.name.charAt(0).toUpperCase()}
          </span>
        </motion.div>
        <h2 className="text-xl font-bold text-white">{user.name}</h2>
        <p className="text-sm text-white/50">ID: {user.id}</p>
        
        <div className="mt-4 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-yellow-500/20 to-orange-500/20 px-4 py-3">
          <Coins className="size-6 text-yellow-400" />
          <span className="text-2xl font-bold text-yellow-400">{user.coins}</span>
          <span className="text-white/50">tanga</span>
        </div>
      </GlassCard>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3">
        <GlassCard className="text-center">
          <div className="mb-2 inline-flex rounded-xl bg-blue-500/20 p-2">
            <Target className="size-5 text-blue-400" />
          </div>
          <p className="text-2xl font-bold text-white">{stats.total}</p>
          <p className="text-xs text-white/50">Jami savollar</p>
        </GlassCard>

        <GlassCard className="text-center">
          <div className="mb-2 inline-flex rounded-xl bg-green-500/20 p-2">
            <CheckCircle className="size-5 text-green-400" />
          </div>
          <p className="text-2xl font-bold text-green-400">{stats.correct}</p>
          <p className="text-xs text-white/50">To&apos;g&apos;ri javoblar</p>
        </GlassCard>

        <GlassCard className="text-center">
          <div className="mb-2 inline-flex rounded-xl bg-red-500/20 p-2">
            <XCircle className="size-5 text-red-400" />
          </div>
          <p className="text-2xl font-bold text-red-400">{stats.incorrect}</p>
          <p className="text-xs text-white/50">Xato javoblar</p>
        </GlassCard>

        <GlassCard className="text-center">
          <div className="mb-2 inline-flex rounded-xl bg-purple-500/20 p-2">
            <Medal className="size-5 text-purple-400" />
          </div>
          <p className="text-2xl font-bold text-purple-400">#{rank}</p>
          <p className="text-xs text-white/50">Reyting o&apos;rni</p>
        </GlassCard>
      </div>

      {/* Score Progress */}
      <GlassCard>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-white/70">Umumiy ball</span>
          <span className="text-lg font-bold text-white">{user.score}</span>
        </div>
        <div className="h-2 rounded-full bg-white/10 overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.min((stats.correct / Math.max(stats.total, 1)) * 100, 100)}%` }}
            transition={{ duration: 1, ease: 'easeOut' }}
            className="h-full rounded-full bg-gradient-to-r from-blue-500 to-purple-500"
          />
        </div>
        <p className="mt-2 text-xs text-white/50 text-center">
          To&apos;g&apos;ri javoblar: {stats.total > 0 ? Math.round((stats.correct / stats.total) * 100) : 0}%
        </p>
      </GlassCard>
    </div>
  );
}
