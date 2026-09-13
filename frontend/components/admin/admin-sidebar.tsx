'use client';

import { motion } from 'framer-motion';
import { LayoutDashboard, UserCog, Coins, Menu, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useState } from 'react';

export type AdminSection = 'dashboard' | 'admin' | 'coins';

interface AdminSidebarProps {
  activeSection: AdminSection;
  onSectionChange: (section: AdminSection) => void;
}

const sections = [
  { id: 'dashboard' as const, label: 'Dashboard', icon: LayoutDashboard },
  { id: 'admin' as const, label: 'Admin', icon: UserCog },
  { id: 'coins' as const, label: 'Tanga', icon: Coins },
];

export function AdminSidebar({ activeSection, onSectionChange }: AdminSidebarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="fixed left-4 top-4 z-50 rounded-xl bg-white/10 p-2 backdrop-blur-xl lg:hidden"
      >
        {mobileOpen ? (
          <X className="size-6 text-white" />
        ) : (
          <Menu className="size-6 text-white" />
        )}
      </button>

      {/* Overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed left-0 top-0 z-40 h-full w-64 border-r border-white/10 bg-black/90 backdrop-blur-xl transition-transform lg:translate-x-0',
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="p-6">
          <h1 className="text-xl font-bold text-white">
            <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Admin Panel
            </span>
          </h1>
        </div>

        <nav className="space-y-1 px-3">
          {sections.map((section) => {
            const Icon = section.icon;
            const isActive = activeSection === section.id;

            return (
              <button
                key={section.id}
                onClick={() => {
                  onSectionChange(section.id);
                  setMobileOpen(false);
                }}
                className={cn(
                  'relative flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left transition-colors',
                  isActive ? 'text-white' : 'text-white/60 hover:text-white/80'
                )}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeSection"
                    className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-500/20 to-purple-500/20"
                    transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                  />
                )}
                <Icon className="relative size-5" />
                <span className="relative font-medium">{section.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>
    </>
  );
}
