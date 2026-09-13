'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Trash2, BookOpen } from 'lucide-react';
import { toast } from 'sonner';
import { adminAPI } from '@/lib/api';
import { GlassCard } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { LoadingSkeleton } from '@/components/ui/loading-skeleton';

export function SubjectsTab() {
  const [newSubject, setNewSubject] = useState('');
  const queryClient = useQueryClient();

  const { data: subjects, isLoading } = useQuery({
    queryKey: ['subjects'],
    queryFn: adminAPI.getSubjects,
  });

  const addMutation = useMutation({
    mutationFn: adminAPI.addSubject,
    onSuccess: () => {
      toast.success('Fan qo\'shildi');
      setNewSubject('');
      queryClient.invalidateQueries({ queryKey: ['subjects'] });
    },
    onError: () => toast.error('Xatolik yuz berdi'),
  });

  const deleteMutation = useMutation({
    mutationFn: adminAPI.deleteSubject,
    onSuccess: () => {
      toast.success('Fan o\'chirildi');
      queryClient.invalidateQueries({ queryKey: ['subjects'] });
    },
    onError: () => toast.error('Xatolik yuz berdi'),
  });

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSubject.trim()) return;
    addMutation.mutate(newSubject.trim());
  };

  return (
    <div className="space-y-4">
      {/* Add Form */}
      <form onSubmit={handleAdd}>
        <GlassCard className="flex gap-3">
          <Input
            value={newSubject}
            onChange={(e) => setNewSubject(e.target.value)}
            placeholder="Yangi fan nomi..."
            className="bg-white/5 border-white/10 text-white placeholder:text-white/30"
          />
          <Button
            type="submit"
            disabled={addMutation.isPending || !newSubject.trim()}
            className="bg-gradient-to-r from-blue-500 to-purple-500 px-6"
          >
            <Plus className="mr-1 size-4" />
            Qo&apos;shish
          </Button>
        </GlassCard>
      </form>

      {/* Subjects List */}
      {isLoading ? (
        <div className="space-y-2">
          <LoadingSkeleton className="h-14" count={4} />
        </div>
      ) : subjects?.length === 0 ? (
        <div className="py-12 text-center text-white/50">
          Hozircha fanlar yo&apos;q
        </div>
      ) : (
        <AnimatePresence>
          <div className="space-y-2">
            {subjects?.map((subject) => (
              <motion.div
                key={subject.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
              >
                <GlassCard className="flex items-center gap-3 !p-3">
                  <div className="rounded-lg bg-blue-500/20 p-2">
                    <BookOpen className="size-5 text-blue-400" />
                  </div>
                  <span className="flex-1 font-medium text-white">
                    {subject.name}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      if (confirm(`"${subject.name}" fanini o'chirmoqchimisiz?`)) {
                        deleteMutation.mutate(subject.id);
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
