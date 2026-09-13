'use client';

import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { HelpCircle, Users, UserCheck, UserX } from 'lucide-react';
import { adminAPI } from '@/lib/api';
import { GlassCard } from '@/components/ui/glass-card';
import { LoadingSkeleton } from '@/components/ui/loading-skeleton';

const statCards = [
  { key: 'total_questions', label: 'Jami savollar', icon: HelpCircle, color: 'from-blue-500 to-cyan-500' },
  { key: 'total_users', label: 'Jami foydalanuvchilar', icon: Users, color: 'from-purple-500 to-pink-500' },
  { key: 'active_users', label: 'Aktiv foydalanuvchilar', icon: UserCheck, color: 'from-green-500 to-emerald-500' },
  { key: 'inactive_users', label: 'Noaktiv foydalanuvchilar', icon: UserX, color: 'from-orange-500 to-red-500' },
] as const;

export function DashboardSection() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['adminStats'],
    queryFn: adminAPI.getStats,
  });

  if (error && (error as Error).message === 'FORBIDDEN') {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <GlassCard className="max-w-md text-center">
          <div className="mb-4 inline-flex rounded-full bg-red-500/20 p-4">
            <UserX className="size-8 text-red-400" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Ruxsat yo&apos;q</h2>
          <p className="text-white/60">
            Sizda admin paneliga kirish huquqi mavjud emas.
          </p>
        </GlassCard>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Dashboard</h2>
        <p className="text-white/60">Umumiy statistika</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {isLoading ? (
          <>
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="rounded-2xl border border-white/10 bg-white/5 p-6">
                <LoadingSkeleton className="mb-4 size-12 rounded-xl" />
                <LoadingSkeleton className="mb-2 h-8 w-24" />
                <LoadingSkeleton className="h-4 w-32" />
              </div>
            ))}
          </>
        ) : (
          statCards.map((stat, index) => {
            const Icon = stat.icon;
            const value = data?.[stat.key] || 0;

            return (
              <motion.div
                key={stat.key}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <GlassCard className="relative overflow-hidden">
                  <div className={`absolute -right-4 -top-4 size-24 rounded-full bg-gradient-to-br ${stat.color} opacity-20 blur-2xl`} />
                  <div className={`mb-4 inline-flex rounded-xl bg-gradient-to-br ${stat.color} p-3`}>
                    <Icon className="size-6 text-white" />
                  </div>
                  <p className="text-3xl font-bold text-white">{value.toLocaleString()}</p>
                  <p className="text-sm text-white/60">{stat.label}</p>
                </GlassCard>
              </motion.div>
            );
          })
        )}
      </div>
    </div>
  );
}
