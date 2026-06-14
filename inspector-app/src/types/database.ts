/**
 * Hand-maintained DB types mirroring the Supabase schema (Phase 1).
 * Regenerate later with `supabase gen types` once the CLI is wired up.
 */

export type InspectionStatus = 'upcoming' | 'in_progress' | 'done';
export type PhotoSource = 'user' | 'listing' | 'prior_listing';
export type PhotoConfidence =
  | 'accurate'
  | 'some_enhancements'
  | 'significant_editing';
export type TranscriptionStatus =
  | 'pending'
  | 'processing'
  | 'done'
  | 'failed';

export type UserProfile = {
  id: string;
  email: string | null;
  display_name: string | null;
  contributor_score: number;
  badges: string[];
  created_at: string;
  updated_at: string;
}

export type Inspection = {
  id: string;
  user_id: string;
  address: string;
  listing_url: string | null;
  listing_summary: string | null;
  listing_facts: Record<string, unknown> | null;
  red_flags: string[];
  floor_plan_url: string | null;
  photo_confidence: PhotoConfidence | null;
  schedule_time: string | null;
  status: InspectionStatus;
  overall_feel: number | null;
  value_for_money: number | null;
  livability: number | null;
  summary: string | null;
  created_at: string;
  updated_at: string;
}

export type Room = {
  id: string;
  inspection_id: string;
  room_type: string;
  notes: string | null;
  pros: string | null;
  cons: string | null;
  position: number | null;
  created_at: string;
}

export type Photo = {
  id: string;
  room_id: string | null;
  inspection_id: string | null;
  file_path: string;
  source: PhotoSource;
  confidence_flag: PhotoConfidence | null;
  flagged_issue: boolean;
  created_at: string;
}

export type VoiceNote = {
  id: string;
  inspection_id: string | null;
  room_id: string | null;
  file_path: string;
  transcript: string | null;
  transcription_status: TranscriptionStatus;
  created_at: string;
}

export type PromptedAnswer = {
  id: string;
  inspection_id: string;
  room_id: string | null;
  question_key: string;
  answer: string | null;
  created_at: string;
}

/**
 * Generated-style Database shape so createClient<Database> is fully typed.
 *
 * NOTE: Insert types are written as explicit object literals (not
 * `Partial<Row> & {…}` intersections). supabase-js's insert type machinery
 * collapses intersection-based Insert types to `never`, so keep these plain.
 */
export interface Database {
  public: {
    Tables: {
      users: {
        Row: UserProfile;
        Insert: {
          id: string;
          email?: string | null;
          display_name?: string | null;
          contributor_score?: number;
          badges?: string[];
          created_at?: string;
          updated_at?: string;
        };
        Update: Partial<UserProfile>;
        Relationships: [];
      };
      inspections: {
        Row: Inspection;
        Insert: {
          id?: string;
          user_id: string;
          address: string;
          listing_url?: string | null;
          listing_summary?: string | null;
          listing_facts?: Record<string, unknown> | null;
          red_flags?: string[];
          floor_plan_url?: string | null;
          photo_confidence?: PhotoConfidence | null;
          schedule_time?: string | null;
          status?: InspectionStatus;
          overall_feel?: number | null;
          value_for_money?: number | null;
          livability?: number | null;
          summary?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: Partial<Inspection>;
        Relationships: [];
      };
      rooms: {
        Row: Room;
        Insert: {
          id?: string;
          inspection_id: string;
          room_type: string;
          notes?: string | null;
          pros?: string | null;
          cons?: string | null;
          position?: number | null;
          created_at?: string;
        };
        Update: Partial<Room>;
        Relationships: [];
      };
      photos: {
        Row: Photo;
        Insert: {
          id?: string;
          room_id?: string | null;
          inspection_id?: string | null;
          file_path: string;
          source?: PhotoSource;
          confidence_flag?: PhotoConfidence | null;
          flagged_issue?: boolean;
          created_at?: string;
        };
        Update: Partial<Photo>;
        Relationships: [];
      };
      voice_notes: {
        Row: VoiceNote;
        Insert: {
          id?: string;
          inspection_id?: string | null;
          room_id?: string | null;
          file_path: string;
          transcript?: string | null;
          transcription_status?: TranscriptionStatus;
          created_at?: string;
        };
        Update: Partial<VoiceNote>;
        Relationships: [];
      };
      prompted_answers: {
        Row: PromptedAnswer;
        Insert: {
          id?: string;
          inspection_id: string;
          room_id?: string | null;
          question_key: string;
          answer?: string | null;
          created_at?: string;
        };
        Update: Partial<PromptedAnswer>;
        Relationships: [];
      };
    };
    Views: { [_ in never]: never };
    Functions: { [_ in never]: never };
    Enums: { [_ in never]: never };
    CompositeTypes: { [_ in never]: never };
  };
}
