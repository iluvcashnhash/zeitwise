// Auto-generated TypeScript types from database schema
// Generated at: 2025-06-26T06:43:55.592Z

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export type Database = {
  public: {
    Tables: {
      chat_messages: {
        Row: {
          id: string;
          session_id: string;
          user_id: string;
          content: string;
          role: 'user' | 'assistant' | 'system';
          created_at: string;
          updated_at: string;
          metadata?: Json;
        };
        Insert: {
          id?: string;
          session_id: string;
          user_id: string;
          content: string;
          role: 'user' | 'assistant' | 'system';
          created_at?: string;
          updated_at?: string;
          metadata?: Json;
        };
        Update: {
          session_id?: string | null;
          user_id?: string | null;
          content?: string | null;
          role?: 'user' | 'assistant' | 'system' | null;
          created_at?: string | null;
          updated_at?: string | null;
          metadata?: Json | null;
        };
      };
      chat_sessions: {
        Row: {
          id: string;
          user_id: string;
          title: string;
          created_at: string;
          updated_at: string;
          is_active?: boolean;
        };
        Insert: {
          id?: string;
          user_id: string;
          title: string;
          created_at?: string;
          updated_at?: string;
          is_active?: boolean;
        };
        Update: {
          user_id?: string | null;
          title?: string | null;
          created_at?: string | null;
          updated_at?: string | null;
          is_active?: boolean | null;
        };
      };
      detox_items: {
        Row: {
          id: string;
          user_id: string;
          content: string;
          content_type: 'text' | 'image' | 'video' | 'link';
          source_type: 'telegram' | 'web' | 'api' | 'manual';
          source_id?: string;
          is_processed?: boolean;
          is_toxic?: boolean;
          toxicity_score?: number;
          categories?: Json;
          created_at: string;
          updated_at: string;
          processed_at?: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          content: string;
          content_type: 'text' | 'image' | 'video' | 'link';
          source_type: 'telegram' | 'web' | 'api' | 'manual';
          source_id?: string;
          is_processed?: boolean;
          is_toxic?: boolean;
          toxicity_score?: number;
          categories?: Json;
          created_at?: string;
          updated_at?: string;
          processed_at?: string;
        };
        Update: {
          user_id?: string | null;
          content?: string | null;
          content_type?: 'text' | 'image' | 'video' | 'link' | null;
          source_type?: 'telegram' | 'web' | 'api' | 'manual' | null;
          source_id?: string | null;
          is_processed?: boolean | null;
          is_toxic?: boolean | null;
          toxicity_score?: number | null;
          categories?: Json | null;
          created_at?: string | null;
          updated_at?: string | null;
          processed_at?: string | null;
        };
      };
      tg_posts_raw: {
        Row: {
          id: string;
          user_id: string;
          post_id: number;
          channel_id: number;
          channel_username?: string;
          content?: string;
          raw_data: Json;
          created_at: string;
          post_date?: string;
          processed?: boolean;
        };
        Insert: {
          id?: string;
          user_id: string;
          post_id: number;
          channel_id: number;
          channel_username?: string;
          content?: string;
          raw_data: Json;
          created_at?: string;
          post_date?: string;
          processed?: boolean;
        };
        Update: {
          user_id?: string | null;
          post_id?: number | null;
          channel_id?: number | null;
          channel_username?: string | null;
          content?: string | null;
          raw_data?: Json | null;
          created_at?: string | null;
          post_date?: string | null;
          processed?: boolean | null;
        };
      };
      user_achievements: {
        Row: {
          id: string;
          user_id: string;
          achievement_type: string;
          achieved_at: string;
          progress?: number;
          metadata?: Json;
        };
        Insert: {
          id?: string;
          user_id: string;
          achievement_type: string;
          achieved_at?: string;
          progress?: number;
          metadata?: Json;
        };
        Update: {
          user_id?: string | null;
          achievement_type?: string | null;
          achieved_at?: string | null;
          progress?: number | null;
          metadata?: Json | null;
        };
      };
      users: {
        Row: {
          id: string;
          email: string;
          username?: string;
          hashed_password: string;
          full_name?: string;
          is_active?: boolean;
          is_superuser?: boolean;
          created_at: string;
          updated_at: string;
          last_login?: string;
        };
        Insert: {
          id?: string;
          email: string;
          username?: string;
          hashed_password: string;
          full_name?: string;
          is_active?: boolean;
          is_superuser?: boolean;
          created_at?: string;
          updated_at?: string;
          last_login?: string;
        };
        Update: {
          email?: string | null;
          username?: string | null;
          hashed_password?: string | null;
          full_name?: string | null;
          is_active?: boolean | null;
          is_superuser?: boolean | null;
          created_at?: string | null;
          updated_at?: string | null;
          last_login?: string | null;
        };
      };
    };
  };
};

// This type is used to type the Supabase client
export type Tables<T extends keyof Database['public']['Tables']> = Database['public']['Tables'][T]['Row'];
