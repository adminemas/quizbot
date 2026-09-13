'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Plus, FileText, Upload, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import { adminAPI } from '@/lib/api';
import { GlassCard } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';

const modes = [
  { id: 'single', label: 'Donalab', icon: Plus },
  { id: 'bulk', label: 'TXT bulk', icon: FileText },
  { id: 'file', label: 'Fayl', icon: Upload },
] as const;

type Mode = typeof modes[number]['id'];

export function QuestionsAddTab() {
  const [mode, setMode] = useState<Mode>('single');
  const queryClient = useQueryClient();

  const { data: subjects } = useQuery({
    queryKey: ['subjects'],
    queryFn: adminAPI.getSubjects,
  });

  // Single question form
  const [singleForm, setSingleForm] = useState({
    subject: '',
    question: '',
    options: ['', '', '', ''],
    correct_option: 0,
  });

  // Bulk form
  const [bulkForm, setBulkForm] = useState({
    subject: '',
    text: '',
  });

  const singleMutation = useMutation({
    mutationFn: () => adminAPI.addQuestion({
      subject: singleForm.subject,
      question: singleForm.question,
      options: singleForm.options,
      correct_option: singleForm.correct_option,
    }),
    onSuccess: () => {
      toast.success('Savol muvaffaqiyatli qo\'shildi!');
      setSingleForm({ subject: '', question: '', options: ['', '', '', ''], correct_option: 0 });
      queryClient.invalidateQueries({ queryKey: ['adminStats'] });
    },
    onError: () => toast.error('Xatolik yuz berdi'),
  });

  const bulkMutation = useMutation({
    mutationFn: () => adminAPI.bulkAddQuestions(bulkForm.subject, bulkForm.text),
    onSuccess: (data) => {
      toast.success(`${data.count} ta savol qo'shildi!`);
      setBulkForm({ subject: '', text: '' });
      queryClient.invalidateQueries({ queryKey: ['adminStats'] });
    },
    onError: () => toast.error('Xatolik yuz berdi'),
  });

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const text = await file.text();
    setBulkForm((prev) => ({ ...prev, text }));
    toast.success('Fayl yuklandi');
  };

  return (
    <div className="space-y-4">
      {/* Mode Tabs */}
      <div className="flex gap-2">
        {modes.map((m) => {
          const Icon = m.icon;
          return (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              className={cn(
                'flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition-colors',
                mode === m.id
                  ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white'
                  : 'bg-white/5 text-white/60 hover:text-white'
              )}
            >
              <Icon className="size-4" />
              {m.label}
            </button>
          );
        })}
      </div>

      {/* Single Question Form */}
      {mode === 'single' && (
        <GlassCard className="space-y-4">
          <div>
            <label className="mb-2 block text-sm text-white/70">Fan</label>
            <select
              value={singleForm.subject}
              onChange={(e) => setSingleForm({ ...singleForm, subject: e.target.value })}
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-white"
            >
              <option value="">Tanlang...</option>
              {subjects?.map((s) => (
                <option key={s.id} value={s.name} className="bg-gray-900">
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-2 block text-sm text-white/70">Savol</label>
            <Textarea
              value={singleForm.question}
              onChange={(e) => setSingleForm({ ...singleForm, question: e.target.value })}
              placeholder="Savolni kiriting..."
              className="bg-white/5 border-white/10 text-white placeholder:text-white/30"
            />
          </div>

          <div className="space-y-2">
            <label className="block text-sm text-white/70">Javoblar</label>
            {singleForm.options.map((opt, i) => (
              <div key={i} className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setSingleForm({ ...singleForm, correct_option: i })}
                  className={cn(
                    'flex size-8 items-center justify-center rounded-lg border transition-colors',
                    singleForm.correct_option === i
                      ? 'border-green-500 bg-green-500/20 text-green-400'
                      : 'border-white/10 text-white/50'
                  )}
                >
                  {singleForm.correct_option === i ? (
                    <CheckCircle className="size-4" />
                  ) : (
                    String.fromCharCode(65 + i)
                  )}
                </button>
                <Input
                  value={opt}
                  onChange={(e) => {
                    const newOptions = [...singleForm.options];
                    newOptions[i] = e.target.value;
                    setSingleForm({ ...singleForm, options: newOptions });
                  }}
                  placeholder={`Javob ${String.fromCharCode(65 + i)}`}
                  className="bg-white/5 border-white/10 text-white placeholder:text-white/30"
                />
              </div>
            ))}
          </div>

          <Button
            onClick={() => singleMutation.mutate()}
            disabled={singleMutation.isPending || !singleForm.subject || !singleForm.question}
            className="w-full bg-gradient-to-r from-blue-500 to-purple-500"
          >
            {singleMutation.isPending ? 'Yuklanmoqda...' : 'Qo\'shish'}
          </Button>
        </GlassCard>
      )}

      {/* Bulk Text Form */}
      {mode === 'bulk' && (
        <GlassCard className="space-y-4">
          <div>
            <label className="mb-2 block text-sm text-white/70">Fan</label>
            <select
              value={bulkForm.subject}
              onChange={(e) => setBulkForm({ ...bulkForm, subject: e.target.value })}
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-white"
            >
              <option value="">Tanlang...</option>
              {subjects?.map((s) => (
                <option key={s.id} value={s.name} className="bg-gray-900">
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-2 block text-sm text-white/70">
              Savollar (format: Savol | A,B,C,D | to&apos;g&apos;ri_raqam)
            </label>
            <Textarea
              value={bulkForm.text}
              onChange={(e) => setBulkForm({ ...bulkForm, text: e.target.value })}
              placeholder="Poytaxtimiz qaysi? | Toshkent,Samarqand,Buxoro,Navoiy | 0"
              rows={8}
              className="bg-white/5 border-white/10 text-white placeholder:text-white/30 font-mono text-sm"
            />
          </div>

          <Button
            onClick={() => bulkMutation.mutate()}
            disabled={bulkMutation.isPending || !bulkForm.subject || !bulkForm.text}
            className="w-full bg-gradient-to-r from-blue-500 to-purple-500"
          >
            {bulkMutation.isPending ? 'Yuklanmoqda...' : 'Barchasini qo\'shish'}
          </Button>
        </GlassCard>
      )}

      {/* File Upload Form */}
      {mode === 'file' && (
        <GlassCard className="space-y-4">
          <div>
            <label className="mb-2 block text-sm text-white/70">Fan</label>
            <select
              value={bulkForm.subject}
              onChange={(e) => setBulkForm({ ...bulkForm, subject: e.target.value })}
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-white"
            >
              <option value="">Tanlang...</option>
              {subjects?.map((s) => (
                <option key={s.id} value={s.name} className="bg-gray-900">
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-2 block text-sm text-white/70">TXT fayl</label>
            <label className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-white/20 bg-white/5 p-8 transition-colors hover:border-white/40">
              <Upload className="mb-2 size-8 text-white/50" />
              <span className="text-sm text-white/70">Faylni tanlang</span>
              <input
                type="file"
                accept=".txt"
                onChange={handleFileUpload}
                className="hidden"
              />
            </label>
          </div>

          {bulkForm.text && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="rounded-xl bg-green-500/10 p-3 text-sm text-green-400"
            >
              Fayl yuklandi: {bulkForm.text.split('\n').length} qator
            </motion.div>
          )}

          <Button
            onClick={() => bulkMutation.mutate()}
            disabled={bulkMutation.isPending || !bulkForm.subject || !bulkForm.text}
            className="w-full bg-gradient-to-r from-blue-500 to-purple-500"
          >
            {bulkMutation.isPending ? 'Yuklanmoqda...' : 'Fayldan qo\'shish'}
          </Button>
        </GlassCard>
      )}
    </div>
  );
}
