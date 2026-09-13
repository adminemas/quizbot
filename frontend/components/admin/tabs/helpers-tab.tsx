'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Trash2, UserCog } from 'lucide-react';
import { toast } from 'sonner';
import { adminAPI } from '@/lib/api';
import { GlassCard } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { LoadingSkeleton } from '@/components/ui/loading-skeleton';

export function HelpersTab() {
  const [userId, setUserId] = useState('');
  const queryClient = useQueryClient();

  const { data: helpers, isLoading } = useQuery({
    queryKey: ['helpers'],
    queryFn: adminAPI.getHelpers,
  });

  const addMutation = useMutation({
    mutationFn: (userId: number) => adminAPI.addHelper(userId),
    onSuccess: () => {
      toast.success('Admin qo\'shildi');
      setUserId('');
      queryClient.invalidateQueries({ queryKey: ['helpers'] });
    },
    onError: () => toast.error('Xatolik yuz berdi'),
  });

  const deleteMutation = useMutation({
    mutationFn: adminAPI.deleteHelper,
    onSuccess: () => {
      toast.success('Admin o\'chirildi');
      queryClient.invalidateQueries({ queryKey: ['helpers'] });
    },
    onError: () => toast.error('Xatolik yuz berdi'),
  });

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    const id = parseInt(userId);
    if (!id) {
      toast.error('To\'g\'ri ID kiriting');
      return;
    }
    addMutation.mutate(id);
  };

  return (
    <div className="space-y-4">
      {/* Add Form */}
      <form onSubmit={handleAdd}>
        <GlassCard className="flex gap-3">
          <Input
            type="number"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="Telegram User ID..."
            className="bg-white/5 border-white/10 text-white placeholder:text-white/30"
          />
          <Button
            type="submit"
            disabled={addMutation.isPending || !userId}
            className="bg-gradient-to-r from-blue-500 to-purple-500 px-6"
          >
            <Plus className="mr-1 size-4" />
            Qo&apos;shish
          </Button>
        </GlassCard>
      </form>

      {/* Helpers List */}
      {isLoading ? (
        <div className="space-y-2">
          <LoadingSkeleton className="h-14" count={3} />
        </div>
      ) : helpers?.length === 0 ? (
        <div className="py-12 text-center text-white/50">
          Hozircha adminlar yo&apos;q
        </div>
      ) : (
        <AnimatePresence>
          <div className="space-y-2">
            {helpers?.map((helper) => (
              <motion.div
                key={helper.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
              >
                <GlassCard className="flex items-center gap-3 !p-3">
                  <div className="rounded-lg bg-purple-500/20 p-2">
                    <UserCog className="size-5 text-purple-400" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-white">
                      {helper.username || `User #${helper.user_id}`}
                    </p>
                    <p className="text-xs text-white/50">ID: {helper.user_id}</p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      if (confirm('Bu adminni o\'chirmoqchimisiz?')) {
                        deleteMutation.mutate(helper.id);
                      }
                    }}
                    className="size-8 p-0 text-red-400 hover:bg-red-500/20 hover:text-red-400"
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </GlassCard>
              </motion.div>
            ))}
          </div>
        </AnimatePresence>
      )}
    </div>
  );
}
