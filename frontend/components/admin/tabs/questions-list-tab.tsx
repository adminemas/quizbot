'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Trash2, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import { adminAPI } from '@/lib/api';
import { GlassCard } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { LoadingSkeleton } from '@/components/ui/loading-skeleton';

export function QuestionsListTab() {
  const [search, setSearch] = useState('');
  const [subject, setSubject] = useState('');
  const queryClient = useQueryClient();

  const { data: subjects } = useQuery({
    queryKey: ['subjects'],
    queryFn: adminAPI.getSubjects,
  });

  const { data: questions, isLoading, refetch } = useQuery({
    queryKey: ['questions', search, subject],
    queryFn: () => adminAPI.searchQuestions(search, subject || undefined),
    enabled: search.length > 0 || subject.length > 0,
  });

  const deleteMutation = useMutation({
    mutationFn: adminAPI.deleteQuestion,
    onSuccess: () => {
      toast.success('Savol o\'chirildi');
      refetch();
      queryClient.invalidateQueries({ queryKey: ['adminStats'] });
    },
    onError: () => toast.error('Xatolik yuz berdi'),
  });

  return (
    <div className="space-y-4">
      {/* Search & Filter */}
      <GlassCard className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-white/50" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Qidirish..."
            className="bg-white/5 border-white/10 pl-10 text-white placeholder:text-white/30"
          />
        </div>
        <select
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-white"
        >
          <option value="">Barcha fanlar</option>
          {subjects?.map((s) => (
            <option key={s.id} value={s.name} className="bg-gray-900">
              {s.name}
            </option>
          ))}
        </select>
      </GlassCard>

      {/* Results */}
      {!search && !subject ? (
        <div className="py-12 text-center text-white/50">
          Savollarni qidirish uchun matn kiriting yoki fan tanlang
        </div>
      ) : isLoading ? (
        <div className="space-y-2">
          <LoadingSkeleton className="h-24" count={3} />
        </div>
      ) : questions?.length === 0 ? (
        <div className="py-12 text-center text-white/50">
          Hech narsa topilmadi
        </div>
      ) : (
        <AnimatePresence>
          <div className="space-y-2">
            {questions?.map((q) => (
              <motion.div
                key={q.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
              >
                <GlassCard className="!p-4">
                  <div className="mb-2 flex items-start justify-between gap-2">
                    <span className="rounded-lg bg-blue-500/20 px-2 py-1 text-xs text-blue-400">
                      {q.subject}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        if (confirm('Rostdan o\'chirmoqchimisiz?')) {
                          deleteMutation.mutate(q.id);
                        }
                      }}
                      className="size-8 p-0 text-red-400 hover:bg-red-500/20 hover:text-red-400"
                    >
                      <Trash2 className="size-4" />
                    </Button>
                  </div>
                  <p className="mb-3 text-white">{q.question}</p>
                  <div className="grid grid-cols-2 gap-2">
                    {q.options.map((opt, i) => (
                      <div
                        key={i}
                        className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${
                          i === q.correct_option_id
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-white/5 text-white/70'
                        }`}
                      >
                        {i === q.correct_option_id && (
                          <CheckCircle className="size-4" />
                        )}
                        <span>
                          {String.fromCharCode(65 + i)}) {opt}
                        </span>
                      </div>
                    ))}
                  </div>
                </GlassCard>
              </motion.div>
            ))}
          </div>
        </AnimatePresence>
      )}
    </div>
  );
}
