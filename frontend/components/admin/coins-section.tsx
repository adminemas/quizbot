'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Settings, 
  Check, 
  X, 
  Clock, 
  Coins, 
  ArrowDownToLine,
  RefreshCw
} from 'lucide-react';
import { toast } from 'sonner';
import { adminAPI } from '@/lib/api';
import { GlassCard } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { LoadingSkeleton } from '@/components/ui/loading-skeleton';
import { cn } from '@/lib/utils';

export function CoinsSection() {
  const queryClient = useQueryClient();

  // Rate settings
  const { data: rateData, isLoading: rateLoading } = useQuery({
    queryKey: ['rate'],
    queryFn: adminAPI.getRate,
  });

  const [rateForm, setRateForm] = useState({
    rate: '',
    min_withdrawal: '',
  });

  // Update form when data loads
  useState(() => {
    if (rateData) {
      setRateForm({
        rate: String(rateData.rate),
        min_withdrawal: String(rateData.min_withdrawal),
      });
    }
  });

  const rateMutation = useMutation({
    mutationFn: () =>
      adminAPI.setRate(
        parseFloat(rateForm.rate) || rateData?.rate || 0,
        parseFloat(rateForm.min_withdrawal) || rateData?.min_withdrawal || 0
      ),
    onSuccess: () => {
      toast.success('Sozlamalar saqlandi');
      queryClient.invalidateQueries({ queryKey: ['rate'] });
    },
    onError: () => toast.error('Xatolik yuz berdi'),
  });

  // Withdrawals
  const { data: withdrawals, isLoading: withdrawalsLoading, refetch } = useQuery({
    queryKey: ['withdrawals'],
    queryFn: adminAPI.getWithdrawals,
  });

  const withdrawalMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: 'approved' | 'rejected' }) =>
      adminAPI.processWithdrawal(id, status),
    onSuccess: (_, { status }) => {
      toast.success(status === 'approved' ? 'Tasdiqlandi' : 'Rad etildi');
      queryClient.invalidateQueries({ queryKey: ['withdrawals'] });
    },
    onError: () => toast.error('Xatolik yuz berdi'),
  });

  const pendingWithdrawals = withdrawals?.filter((w) => w.status === 'pending') || [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Tanga tizimi</h2>
        <p className="text-white/60">Kurs va to&apos;lovlarni boshqaring</p>
      </div>

      {/* Rate Settings */}
      <GlassCard>
        <div className="mb-4 flex items-center gap-2">
          <Settings className="size-5 text-blue-400" />
          <h3 className="font-semibold text-white">Kurs sozlamalari</h3>
        </div>

        {rateLoading ? (
          <div className="space-y-3">
            <LoadingSkeleton className="h-12" />
            <LoadingSkeleton className="h-12" />
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="mb-2 block text-sm text-white/70">
                1 tanga = X so&apos;m
              </label>
              <Input
                type="number"
                value={rateForm.rate || rateData?.rate || ''}
                onChange={(e) => setRateForm({ ...rateForm, rate: e.target.value })}
                placeholder={String(rateData?.rate || 0)}
                className="bg-white/5 border-white/10 text-white"
              />
            </div>
            <div>
              <label className="mb-2 block text-sm text-white/70">
                Minimal chiqarish (tanga)
              </label>
              <Input
                type="number"
                value={rateForm.min_withdrawal || rateData?.min_withdrawal || ''}
                onChange={(e) => setRateForm({ ...rateForm, min_withdrawal: e.target.value })}
                placeholder={String(rateData?.min_withdrawal || 0)}
                className="bg-white/5 border-white/10 text-white"
              />
            </div>
            <Button
              onClick={() => rateMutation.mutate()}
              disabled={rateMutation.isPending}
              className="w-full bg-gradient-to-r from-blue-500 to-purple-500"
            >
              {rateMutation.isPending ? 'Saqlanmoqda...' : 'Saqlash'}
            </Button>
          </div>
        )}
      </GlassCard>

      {/* Withdrawal Requests */}
      <div>
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ArrowDownToLine className="size-5 text-yellow-400" />
            <h3 className="font-semibold text-white">To&apos;lov arizalari</h3>
            {pendingWithdrawals.length > 0 && (
              <span className="rounded-full bg-yellow-500/20 px-2 py-0.5 text-xs text-yellow-400">
                {pendingWithdrawals.length}
              </span>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => refetch()}
            className="text-white/60"
          >
            <RefreshCw className="mr-1 size-4" />
            Yangilash
          </Button>
        </div>

        {withdrawalsLoading ? (
          <div className="space-y-2">
            <LoadingSkeleton className="h-24" count={3} />
          </div>
        ) : pendingWithdrawals.length === 0 ? (
          <GlassCard className="py-8 text-center">
            <Clock className="mx-auto mb-2 size-8 text-white/30" />
            <p className="text-white/50">Kutilayotgan arizalar yo&apos;q</p>
          </GlassCard>
        ) : (
          <AnimatePresence>
            <div className="space-y-2">
              {pendingWithdrawals.map((w) => (
                <motion.div
                  key={w.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -100 }}
                >
                  <GlassCard className="!p-4">
                    <div className="mb-3 flex items-start justify-between">
                      <div>
                        <p className="font-medium text-white">{w.username}</p>
                        <p className="text-xs text-white/50">ID: {w.user_id}</p>
                      </div>
                      <span className={cn(
                        'rounded-full px-2 py-1 text-xs',
                        w.status === 'pending' && 'bg-yellow-500/20 text-yellow-400',
                        w.status === 'approved' && 'bg-green-500/20 text-green-400',
                        w.status === 'rejected' && 'bg-red-500/20 text-red-400'
                      )}>
                        {w.status === 'pending' && 'Kutilmoqda'}
                        {w.status === 'approved' && 'Tasdiqlangan'}
                        {w.status === 'rejected' && 'Rad etilgan'}
                      </span>
                    </div>

                    <div className="mb-3 flex items-center gap-4">
                      <div className="flex items-center gap-1">
                        <Coins className="size-4 text-yellow-400" />
                        <span className="font-semibold text-white">
                          {w.amount_coins.toLocaleString()}
                        </span>
                        <span className="text-xs text-white/50">tanga</span>
                      </div>
                      <span className="text-white/30">→</span>
                      <div className="text-green-400">
                        {w.amount_money.toLocaleString()} so&apos;m
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Button
                        onClick={() =>
                          withdrawalMutation.mutate({ id: w.id, status: 'approved' })
                        }
                        disabled={withdrawalMutation.isPending}
                        className="flex-1 bg-green-500/20 text-green-400 hover:bg-green-500/30"
                      >
                        <Check className="mr-1 size-4" />
                        Tasdiqlash
                      </Button>
                      <Button
                        onClick={() =>
                          withdrawalMutation.mutate({ id: w.id, status: 'rejected' })
                        }
                        disabled={withdrawalMutation.isPending}
                        className="flex-1 bg-red-500/20 text-red-400 hover:bg-red-500/30"
                      >
                        <X className="mr-1 size-4" />
                        Rad etish
                      </Button>
                    </div>

                    <p className="mt-2 text-xs text-white/40">
                      {new Date(w.created_at).toLocaleString('uz-UZ')}
                    </p>
                  </GlassCard>
                </motion.div>
              ))}
            </div>
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
