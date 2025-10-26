export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export interface Database {
  public: {
    Tables: {
      upload_events: {
        Row: {
          id: number;
          upload_id: string;
          filename: string | null;
          bucket: string | null;
          object_key: string | null;
          status: string | null;
          progress: number | null;
          error_message: string | null;
          size_bytes: number | null;
          content_type: string | null;
          meta: Json | null;
          created_at: string;
          updated_at: string;
          owner_id: string | null;
        };
        Insert: {
          id?: number;
          upload_id: string;
          filename?: string | null;
          bucket?: string | null;
          object_key?: string | null;
          status?: string | null;
          progress?: number | null;
          error_message?: string | null;
          size_bytes?: number | null;
          content_type?: string | null;
          meta?: Json | null;
          created_at?: string;
          updated_at?: string;
          owner_id?: string | null;
        };
        Update: {
          id?: number;
          upload_id?: string;
          filename?: string | null;
          bucket?: string | null;
          object_key?: string | null;
          status?: string | null;
          progress?: number | null;
          error_message?: string | null;
          size_bytes?: number | null;
          content_type?: string | null;
          meta?: Json | null;
          created_at?: string;
          updated_at?: string;
          owner_id?: string | null;
        };
        Relationships: [
          {
            foreignKeyName: 'upload_events_owner_id_fkey';
            columns: ['owner_id'];
            referencedRelation: 'users';
            referencedColumns: ['id'];
          }
        ];
      };
    } & {
      [key: string]: any;
    };
    Views: Record<string, never>;
    Functions: Record<string, never>;
    Enums: Record<string, never>;
    CompositeTypes: Record<string, never>;
  };
}
