// User API Types
export interface UserStats {
  user: {
    id: number;
    name: string;
    coins: number;
    score: number;
  };
  stats: {
    total: number;
    correct: number;
    incorrect: number;
  };
  rank: number;
}

export interface RankingUser {
  user_id: number;
  name: string;
  score: number;
}

export interface ExchangeInfo {
  rate: number;
  min_withdrawal?: number;
}

// Admin API Types
export interface AdminStats {
  total_questions: number;
  total_users: number;
  active_users: number;
  inactive_users: number;
}

export interface Subject {
  id: string | number;
  name: string;
}

export interface Question {
  id: number;
  subject: string;
  question: string;
  options: string[];
  correct_option_id: number;
}

export interface AdminHelper {
  id: number;
  user_id: number;
  username?: string;
}

export interface RateSettings {
  rate: number;
  min_withdrawal: number;
}

export interface Withdrawal {
  id: number;
  user_id: number;
  username: string;
  amount_coins: number;
  amount_money: number;
  created_at: string;
  status: 'pending' | 'approved' | 'rejected';
}

export type RankingPeriod = 'all' | 'week' | 'month';
