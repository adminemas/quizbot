'use client';

import { motion } from 'framer-motion';
import { User, Trophy, ArrowRightLeft } from 'lucide-react';
import { cn } from '@/lib/utils';

export type TabType = 'cabinet' | 'ranking' | 'exchange';

interface BottomNavProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
}

const tabs = [
  { id: 'cabinet' as const, label: 'Kabinet', icon: User },
  { id: 'ranking' as const, label: 'Reyting', icon: Trophy },
  { id: 'exchange' as const, label: 'Almashtirish', icon: ArrowRightLeft },
];

export function BottomNav({ activeTab, onTabChange }: BottomNavProps) {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50">
      <div className="mx-auto max-w-lg">
        <div className="mx-3 mb-3 rounded-2xl border border-white/10 bg-black/80 backdrop-blur-xl">
          <div className="flex items-center justify-around p-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              
              return (
                <button
                  key={tab.id}
                  onClick={() => {
                    onTabChange(tab.id);
                    window.Telegram?.WebApp?.HapticFeedback?.selectionChanged();
                  }}
                  className={cn(
                    'relative flex flex-1 flex-col items-center gap-1 rounded-xl py-2 transition-colors',
                    isActive ? 'text-white' : 'text-white/50'
                  )}
                >
                  {isActive && (
                    <motion.div
                      layoutId="activeTab"
                      className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-500/30 to-purple-500/30"
                      transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                    />
                  )}
                  <Icon className="relative size-5" />
                  <span className="relative text-xs font-medium">{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
