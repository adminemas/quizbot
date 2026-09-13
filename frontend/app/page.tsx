'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BottomNav, type TabType } from '@/components/user/bottom-nav';
import { CabinetTab } from '@/components/user/cabinet-tab';
import { RankingTab } from '@/components/user/ranking-tab';
import { ExchangeTab } from '@/components/user/exchange-tab';

export default function UserApp() {
  const [activeTab, setActiveTab] = useState<TabType>('cabinet');

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-900 to-black">
      <div className="mx-auto max-w-lg px-4 pt-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6 text-center"
        >
          <h1 className="text-2xl font-bold">
            <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Quiz Bot
            </span>
          </h1>
        </motion.div>

        {/* Tab Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === 'cabinet' && <CabinetTab />}
            {activeTab === 'ranking' && <RankingTab />}
            {activeTab === 'exchange' && <ExchangeTab />}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Bottom Navigation */}
      <BottomNav activeTab={activeTab} onTabChange={setActiveTab} />
    </main>
  );
}
