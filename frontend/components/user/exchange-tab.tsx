'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Coins, ArrowDown, Banknote, Send } from 'lucide-react';
import { toast } from 'sonner';
import { userAPI } from '@/lib/api';
import { GlassCard } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { CardSkeleton } from '@/components/ui/loading-skeleton';

export function ExchangeTab() {
  const [amount, setAmount] = useState('');
  const [cardNumber, setCardNumber] = useState('');
  const [cardName, setCardName] = useState('');
  const queryClient = useQueryClient();

  const { data: stats } = useQuery({
    queryKey: ['userStats'],
    queryFn: userAPI.getStats,
  });

  const { data: exchangeInfo, isLoading } = useQuery({
    queryKey: ['exchangeInfo'],
    queryFn: userAPI.getExchangeInfo,
  });

  const { data: history } = useQuery({
    queryKey: ['userWithdrawals'],
    queryFn: userAPI.getUserWithdrawals,
  });

  const mutation = useMutation({
    mutationFn: ({ numAmount, cardNo, holderName }: { numAmount: number; cardNo: string; holderName: string }) => 
      userAPI.requestExchange(numAmount, cardNo, holderName),
    onSuccess: () => {
      toast.success('So\'rov muvaffaqiyatli yuborildi!');
      setAmount('');
      setCardNumber('');
      setCardName('');
      queryClient.invalidateQueries({ queryKey: ['userStats'] });
      queryClient.invalidateQueries({ queryKey: ['userWithdrawals'] });
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('success');
    },
    onError: (err: any) => {
      toast.error(err?.error || 'Xatolik yuz berdi');
      window.Telegram?.WebApp?.HapticFeedback?.notificationOccurred('error');
    },
  });

  const handleCardNumberChange = (val: string) => {
    const value = val.replace(/\D/g, '');
    let formatted = '';
    for (let i = 0; i < value.length && i < 16; i++) {
      if (i > 0 && i % 4 === 0) {
        formatted += ' ';
      }
      formatted += value[i];
    }
    setCardNumber(formatted);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const numAmount = parseInt(amount);
    const cleanCard = cardNumber.replace(/\s/g, '');
    
    if (!numAmount || numAmount <= 0) {
      toast.error('Miqdorni kiriting');
      return;
    }
    
    if (stats && numAmount > stats.user.coins) {
      toast.error('Yetarli tanga mavjud emas');
      return;
    }

    if (cleanCard.length !== 16) {
      toast.error('Karta raqami 16 xonali bo\'lishi shart');
      return;
    }

    if (!cardName.trim()) {
      toast.error('Kartadagi ismingizni kiriting');
      return;
    }

    mutation.mutate({ numAmount, cardNo: cardNumber, holderName: cardName.trim() });
  };

  const uzsAmount = amount && exchangeInfo
    ? parseInt(amount) * exchangeInfo.rate
    : 0;

  if (isLoading) {
    return (
      <div className="space-y-4 pb-24">
        <CardSkeleton />
        <CardSkeleton />
      </div>
    );
  }

  return (
    <div className="space-y-4 pb-24">
      {/* Balance Card */}
      <GlassCard gradient className="text-center">
        <p className="text-sm text-white/70 mb-2">Joriy balans</p>
        <div className="flex items-center justify-center gap-2">
          <Coins className="size-8 text-yellow-400" />
          <span className="text-4xl font-bold text-white">
            {stats?.user.coins || 0}
          </span>
        </div>
        <p className="mt-2 text-white/50">tanga</p>
      </GlassCard>

      {/* Exchange Rate */}
      <GlassCard>
        <div className="flex items-center justify-between">
          <span className="text-white/70">Ayirboshlash kursi</span>
          <span className="font-bold text-white">
            1 tanga = {exchangeInfo?.rate || 0} so&apos;m
          </span>
        </div>
      </GlassCard>

      {/* Exchange Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <GlassCard>
          <label className="mb-2 block text-sm text-white/70">
            Tanga miqdori
          </label>
          <div className="relative">
            <Coins className="absolute left-3 top-1/2 size-5 -translate-y-1/2 text-yellow-400" />
            <Input
              type="number"
              placeholder="0"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="bg-white/5 border-white/10 pl-10 text-white placeholder:text-white/30 text-lg h-12"
            />
          </div>
        </GlassCard>

        <motion.div
          className="flex justify-center"
          animate={{ y: [0, 5, 0] }}
          transition={{ repeat: Infinity, duration: 1.5 }}
        >
          <div className="rounded-full bg-gradient-to-r from-blue-500 to-purple-500 p-2">
            <ArrowDown className="size-5 text-white" />
          </div>
        </motion.div>

        <GlassCard>
          <label className="mb-2 block text-sm text-white/70">
            So&apos;m miqdori (UZS)
          </label>
          <div className="relative">
            <Banknote className="absolute left-3 top-1/2 size-5 -translate-y-1/2 text-green-400" />
            <Input
              type="text"
              readOnly
              value={uzsAmount.toLocaleString('uz-UZ')}
              className="bg-white/5 border-white/10 pl-10 text-white text-lg h-12"
            />
          </div>
        </GlassCard>

        <GlassCard>
          <label className="mb-2 block text-sm text-white/70">
            Karta raqami (16 xonalik)
          </label>
          <Input
            type="text"
            placeholder="4879 7889 7878 8998"
            value={cardNumber}
            onChange={(e) => handleCardNumberChange(e.target.value)}
            className="bg-white/5 border-white/10 text-white placeholder:text-white/30 text-lg h-12"
          />
        </GlassCard>

        <GlassCard>
          <label className="mb-2 block text-sm text-white/70">
            Kartadagi ismingiz
          </label>
          <Input
            type="text"
            placeholder="Mamarayim Teshaboyev"
            value={cardName}
            onChange={(e) => setCardName(e.target.value)}
            className="bg-white/5 border-white/10 text-white placeholder:text-white/30 text-lg h-12"
          />
        </GlassCard>

        <Button
          type="submit"
          disabled={
            mutation.isPending || 
            !amount || 
            parseInt(amount) <= 0 || 
            cardNumber.replace(/\s/g, '').length !== 16 || 
            !cardName.trim()
          }
          className="w-full h-12 bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold hover:from-blue-600 hover:to-purple-600 disabled:opacity-50"
        >
          {mutation.isPending ? (
            <motion.div
              className="size-5 rounded-full border-2 border-white border-t-transparent"
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
            />
          ) : (
            <>
              <Send className="mr-2 size-5" />
              So&apos;rov yuborish
            </>
          )}
        </Button>
      </form>

      {/* History Section */}
      {history && history.length > 0 && (
        <div className="mt-8 space-y-4">
          <h3 className="text-lg font-bold text-white mb-4">So&apos;rovlar tarixi</h3>
          <div className="space-y-3">
            {history.map((item) => (
              <GlassCard key={item.id} className="p-4 flex flex-col gap-2 border-white/5">
                <div className="flex items-center justify-between">
                  <span className="text-white/50 text-sm">
                    {new Date(item.created_at).toLocaleDateString('uz-UZ')}
                  </span>
                  {item.status === 'pending' && <span className="text-yellow-400 text-sm font-medium">🟡 Kutilmoqda</span>}
                  {item.status === 'approved' && <span className="text-green-400 text-sm font-medium">🟢 Tasdiqlandi</span>}
                  {item.status === 'rejected' && <span className="text-red-400 text-sm font-medium">🔴 Rad etildi</span>}
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1">
                    <Coins className="size-4 text-yellow-400" />
                    <span className="text-white font-bold">{item.amount_coins}</span>
                  </div>
                  <div className="flex items-center gap-1 text-green-400">
                    <span className="font-bold">{item.amount_money.toLocaleString('uz-UZ')} so&apos;m</span>
                  </div>
                </div>
              </GlassCard>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
