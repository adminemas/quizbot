import type {
  UserStats,
  RankingUser,
  ExchangeInfo,
  AdminStats,
  Subject,
  Question,
  AdminHelper,
  RateSettings,
  Withdrawal,
  RankingPeriod,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

function getTelegramUserId(): string {
  if (typeof window !== 'undefined' && window.Telegram?.WebApp) {
    return String(window.Telegram.WebApp.initDataUnsafe?.user?.id || '');
  }
  return '';
}

async function fetchAPI<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const userId = getTelegramUserId();
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': userId,
      ...options.headers,
    },
  });

  if (response.status === 403) {
    throw new Error('FORBIDDEN');
  }

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
}

// User API
export const userAPI = {
  getStats: () => fetchAPI<UserStats>('/api/user/stats'),
  
  getRankings: (period: RankingPeriod) => 
    fetchAPI<RankingUser[]>(`/api/rankings?period=${period}`),
  
  getExchangeInfo: () => fetchAPI<ExchangeInfo>('/api/exchange/info'),
  
  requestExchange: (amount: number, card_number: string, card_name: string) =>
    fetchAPI<{ success: boolean }>('/api/exchange/request', {
      method: 'POST',
      body: JSON.stringify({ amount, card_number, card_name }),
    }),
    
  getUserWithdrawals: () => fetchAPI<Withdrawal[]>('/api/user/withdrawals'),
};

// Admin API
export const adminAPI = {
  getStats: () => fetchAPI<AdminStats>('/api/admin/stats'),
  
  // Subjects
  getSubjects: () => fetchAPI<Subject[]>('/api/admin/subjects'),
  
  addSubject: (name: string) =>
    fetchAPI<Subject>('/api/admin/subjects', {
      method: 'POST',
      body: JSON.stringify({ name }),
    }),
  
  deleteSubject: (id: string | number) =>
    fetchAPI<{ success: boolean }>(`/api/admin/subjects?id=${id}`, {
      method: 'DELETE',
    }),
  
  // Questions
  addQuestion: (data: {
    subject: string;
    question: string;
    options: string[];
    correct_option: number;
  }) =>
    fetchAPI<{ success: boolean }>('/api/admin/questions/add', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  bulkAddQuestions: (subject: string, text: string) =>
    fetchAPI<{ success: boolean; count: number }>('/api/admin/questions/bulk_txt', {
      method: 'POST',
      body: JSON.stringify({ subject, text }),
    }),
  
  searchQuestions: (q: string, subject?: string) => {
    const params = new URLSearchParams({ q });
    if (subject) params.append('subject', subject);
    return fetchAPI<Question[]>(`/api/admin/questions/search?${params}`);
  },
  
  deleteQuestion: (id: number) =>
    fetchAPI<{ success: boolean }>(`/api/admin/questions/delete?id=${id}`, {
      method: 'DELETE',
    }),
  
  // Helpers/Admins
  getHelpers: () => fetchAPI<AdminHelper[]>('/api/admin/helpers'),
  
  addHelper: (userId: number) =>
    fetchAPI<AdminHelper>('/api/admin/helpers', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    }),
  
  deleteHelper: (id: number) =>
    fetchAPI<{ success: boolean }>(`/api/admin/helpers?id=${id}`, {
      method: 'DELETE',
    }),
  
  // Rate & Settings
  getRate: () => fetchAPI<RateSettings>('/api/admin/rate'),
  
  setRate: (rate: number, min_withdrawal: number) =>
    fetchAPI<{ success: boolean }>('/api/admin/rate', {
      method: 'POST',
      body: JSON.stringify({ rate, min_withdrawal }),
    }),
  
  setSetting: (key: string, value: string | number) =>
    fetchAPI<{ success: boolean }>('/api/admin/settings', {
      method: 'POST',
      body: JSON.stringify({ key, value }),
    }),
  
  // Withdrawals
  getWithdrawals: () => fetchAPI<Withdrawal[]>('/api/admin/withdrawals'),
  
  processWithdrawal: (id: number, status: 'approved' | 'rejected') =>
    fetchAPI<{ success: boolean }>('/api/admin/withdrawals', {
      method: 'POST',
      body: JSON.stringify({ id, status }),
    }),
};
