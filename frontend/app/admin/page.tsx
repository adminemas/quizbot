'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AdminSidebar, type AdminSection } from '@/components/admin/admin-sidebar';
import { DashboardSection } from '@/components/admin/dashboard-section';
import { AdminSection as AdminManageSection } from '@/components/admin/admin-section';
import { CoinsSection } from '@/components/admin/coins-section';

export default function AdminPanel() {
  const [activeSection, setActiveSection] = useState<AdminSection>('dashboard');

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-900 to-black">
      <AdminSidebar
        activeSection={activeSection}
        onSectionChange={setActiveSection}
      />

      {/* Main Content */}
      <main className="min-h-screen lg:ml-64">
        <div className="p-4 pt-16 lg:p-8 lg:pt-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeSection}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.2 }}
            >
              {activeSection === 'dashboard' && <DashboardSection />}
              {activeSection === 'admin' && <AdminManageSection />}
              {activeSection === 'coins' && <CoinsSection />}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
