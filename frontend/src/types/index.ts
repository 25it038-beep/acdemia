export interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  role: 'student' | 'teacher' | 'admin' | 'university';
  avatar_url?: string;
  university?: string;
  course?: string;
  semester?: number;
  education_level?: string;
  occupation?: string;
  domain?: string;
  learning_mode: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface Subject {
  id: string;
  name: string;
  description?: string;
  university?: string;
  semester?: number;
  subject_code?: string;
  icon?: string;
  color?: string;
  progress: number;
  unit_count: number;
  file_count: number;
  created_at: string;
}

export interface Unit {
  id: string;
  subject_id: string;
  name: string;
  description?: string;
  order: number;
  chapter_count: number;
  created_at: string;
}

export interface Chapter {
  id: string;
  unit_id: string;
  name: string;
  description?: string;
  order: number;
  estimated_hours: number;
  difficulty: number;
  topic_count: number;
  progress: number;
  created_at: string;
}

export interface Topic {
  id: string;
  chapter_id: string;
  name: string;
  content?: string;
  summary?: string;
  order: number;
  difficulty: number;
  importance: number;
  prerequisites: string[];
  tags: string[];
  concept_count: number;
  progress: number;
  created_at: string;
}

export interface Concept {
  id: string;
  topic_id: string;
  name: string;
  explanation?: string;
  definition?: string;
  difficulty: number;
  importance: number;
  created_at: string;
}

export interface FileUpload {
  id: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  status: string;
  pages: number;
  chunks: number;
  subject_id?: string | null;
  content_preview?: string | null;
  created_at: string;
}

export interface Quiz {
  id: string;
  title: string;
  quiz_type: string;
  difficulty: string;
  total_questions: number;
  score?: number;
  completed_at?: string;
  created_at: string;
}

export interface Question {
  id: string;
  question_text: string;
  question_type: string;
  options?: string[];
  difficulty: number;
  marks: number;
}

export interface KnowledgeGraphData {
  nodes: Array<{
    id: string;
    name: string;
    topic: string;
    difficulty: number;
    importance: number;
  }>;
  edges: Array<{
    source: string;
    target: string;
    type: string;
    weight: number;
  }>;
}

export interface WorkflowNode {
  id: string;
  type: string;
  label: string;
  data: {
    id: string;
    type: string;
    status?: string;
    confidence?: number;
    estimated_hours?: number;
    difficulty?: number;
  };
}

export interface WorkflowEdge {
  source: string;
  target: string;
  label?: string;
}

export interface Memory {
  id: string;
  memory_type: string;
  content: string;
  context?: string;
  importance: number;
  recall_count: number;
  created_at: string;
}

export interface StudyPlan {
  id: string;
  title: string;
  exam_date?: string;
  daily_hours: number;
  progress: number;
  is_active: boolean;
  created_at: string;
}

export interface Flashcard {
  id: string;
  front: string;
  back: string;
  easiness: number;
  interval: number;
  next_review?: string;
}

export interface ChatMessage {
  session_id: string;
  message: string;
  mode: string;
  subject_id?: string;
  topic_id?: string;
}

export interface ChatResponse {
  session_id: string;
  message: string;
  metadata?: Record<string, unknown>;
}