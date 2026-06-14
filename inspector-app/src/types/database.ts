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

export interface UserProfile {
  id: string;
  email: string | null;
  display_name: string | null;
  contributor_score: number;
  badges: string[];
  created_at: string;
  updated_at: string;
}

export interface Inspection {
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

export interface Room {
  id: string;
  inspection_id: string;
  room_type: string;
  notes: string | null;
  pros: string | null;
  cons: string | null;
  position: number | null;
  created_at: string;
}

export interface Photo {
  id: string;
  room_id: string | null;
  inspection_id: string | null;
  file_path: string;
  source: PhotoSource;
  confidence_flag: PhotoConfidence | null;
  flagged_issue: boolean;
  created_at: string;
}

export interface VoiceNote {
  id: string;
  inspection_id: string | null;
  room_id: string | null;
  file_path: string;
  transcript: string | null;
  transcription_status: TranscriptionStatus;
  created_at: string;
}

export interface PromptedAnswer {
  id: string;
  inspection_id: string;
  room_id: string | null;
  question_key: string;
  answer: string | null;
  created_at: string;
}

/** Minimal generated-style shape so createClient<Database> is typed. */
export interface Database {
  public: {
    Tables: {
      users: {
        Row: UserProfile;
        Insert: Partial<UserProfile> & { id: string };
        Update: Partial<UserProfile>;
      };
      inspections: {
        Row: Inspection;
        Insert: Partial<Inspection> & { user_id: string; address: string };
        Update: Partial<Inspection>;
      };
      rooms: {
        Row: Room;
        Insert: Partial<Room> & { inspection_id: string; room_type: string };
        Update: Partial<Room>;
      };
      photos: {
        Row: Photo;
        Insert: Partial<Photo> & { file_path: string };
        Update: Partial<Photo>;
      };
      voice_notes: {
        Row: VoiceNote;
        Insert: Partial<VoiceNote> & { file_path: string };
        Update: Partial<VoiceNote>;
      };
      prompted_answers: {
        Row: PromptedAnswer;
        Insert: Partial<PromptedAnswer> & {
          inspection_id: string;
          question_key: string;
        };
        Update: Partial<PromptedAnswer>;
      };
    };
    Views: Record<string, never>;
    Functions: Record<string, never>;
    Enums: Record<string, never>;
  };
}
