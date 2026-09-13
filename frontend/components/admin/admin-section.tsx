'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { QuestionsAddTab } from './tabs/questions-add-tab';
import { QuestionsListTab } from './tabs/questions-list-tab';
import { SubjectsTab } from './tabs/subjects-tab';
import { HelpersTab } from './tabs/helpers-tab';

const tabs = [
  { id: 'add', label: 'Savol qo\'shish' },
  { id: 'list', label: 'Savollar' },
  { id: 'subjects', label: 'Fanlar' },
  { id: 'helpers', label: 'Adminlar' },
] as const;

type TabId = typeof tabs[number]['id'];

export function AdminSection() {
  const [activeTab, setActiveTab] = useState<TabId>('add');

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Admin boshqaruvi</h2>
        <p className="text-white/60">Savollar, fanlar va adminlarni boshqaring</p>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 rounded-xl bg-white/5 p-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'relative flex-1 min-w-[120px] rounded-lg px-4 py-2 text-sm font-medium transition-colors',
              activeTab === tab.id ? 'text-white' : 'text-white/50'
            )}
          >
            {activeTab === tab.id && (
              <motion.div
                layoutId="adminTab"
                className="absolute inset-0 rounded-lg bg-gradient-to-r from-blue-500/30 to-purple-500/30"
                transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
              />
            )}
            <span className="relative">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'add' && <QuestionsAddTab />}
        {activeTab === 'list' && <QuestionsListTab />}
        {activeTab === 'subjects' && <SubjectsTab />}
        {activeTab === 'helpers' && <HelpersTab />}
      </div>
    </div>
  );
}
