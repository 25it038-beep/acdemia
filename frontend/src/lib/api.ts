import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { ChatMessage } from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

let tokenProvider: () => Promise<string | null> = async () => null;

export function setTokenProvider(provider: () => Promise<string | null>) {
  tokenProvider = provider;
}

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });

    this.client.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
      const token = await tokenProvider();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
  }

  // Auth (Clerk-backed)
  async getMe() {
    const res = await this.client.get('/api/auth/me');
    return res.data;
  }

  async updateMe(data: any) {
    const res = await this.client.put('/api/auth/me', data);
    return res.data;
  }

  // Subjects
  async getSubjects() {
    const res = await this.client.get('/api/subjects/');
    return res.data;
  }

  async createSubject(data: any) {
    const res = await this.client.post('/api/subjects/', data);
    return res.data;
  }

  async getSubject(id: string) {
    const res = await this.client.get(`/api/subjects/${id}`);
    return res.data;
  }

  async deleteSubject(id: string) {
    const res = await this.client.delete(`/api/subjects/${id}`);
    return res.data;
  }

  async getUnits(subjectId: string) {
    const res = await this.client.get(`/api/subjects/${subjectId}/units`);
    return res.data;
  }

  async createUnit(subjectId: string, data: any) {
    const res = await this.client.post(`/api/subjects/${subjectId}/units`, data);
    return res.data;
  }

  async getChapters(subjectId: string, unitId: string) {
    const res = await this.client.get(`/api/subjects/${subjectId}/units/${unitId}/chapters`);
    return res.data;
  }

  async createChapter(subjectId: string, unitId: string, data: any) {
    const res = await this.client.post(`/api/subjects/${subjectId}/units/${unitId}/chapters`, data);
    return res.data;
  }

  async getTopics(subjectId: string, unitId: string, chapterId: string) {
    const res = await this.client.get(`/api/subjects/${subjectId}/units/${unitId}/chapters/${chapterId}/topics`);
    return res.data;
  }

  async createTopic(subjectId: string, unitId: string, chapterId: string, data: any) {
    const res = await this.client.post(
      `/api/subjects/${subjectId}/units/${unitId}/chapters/${chapterId}/topics`,
      data
    );
    return res.data;
  }

  // Files
  async uploadFile(file: File, subjectId?: string) {
    const formData = new FormData();
    formData.append('file', file);
    if (subjectId) formData.append('subject_id', subjectId);
    const res = await this.client.post('/api/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  }

  async getFiles(subjectId?: string) {
    const params = subjectId ? { subject_id: subjectId } : {};
    const res = await this.client.get('/api/files/', { params });
    return res.data;
  }

  async deleteFile(id: string) {
    const res = await this.client.delete(`/api/files/${id}`);
    return res.data;
  }

  // Tutor
  async chat(data: ChatMessage) {
    const res = await this.client.post('/api/tutor/chat', data, { timeout: 300000 });
    return res.data;
  }

  async getChatSessions() {
    const res = await this.client.get('/api/tutor/sessions');
    return res.data;
  }

  async getChatHistory(sessionId: string) {
    const res = await this.client.get('/api/tutor/history', {
      params: { session_id: sessionId },
    });
    return res.data;
  }

  async generateQuiz(data: any) {
    const res = await this.client.post('/api/tutor/quiz/generate', data, {
      timeout: 300000,
    });
    return res.data;
  }

  async getQuiz(id: string) {
    const res = await this.client.get(`/api/tutor/quiz/${id}`);
    return res.data;
  }

  async submitQuiz(id: string, answers: any[]) {
    const res = await this.client.post(`/api/tutor/quiz/${id}/submit`, { answers });
    return res.data;
  }

  // Knowledge Graph
  async getKnowledgeGraph(subjectId?: string) {
    const params = subjectId ? { subject_id: subjectId } : {};
    const res = await this.client.get('/api/knowledge-graph', { params });
    return res.data;
  }

  // Workflow
  async getWorkflow(subjectId: string) {
    const res = await this.client.get(`/api/workflow/${subjectId}`);
    return res.data;
  }

  async exploreUnit(unitId: string) {
    const res = await this.client.post(`/api/units/${unitId}/explore`, {}, {
      timeout: 300000,
    });
    return res.data;
  }

  async createUnitAssessment(unitId: string) {
    const res = await this.client.post(`/api/units/${unitId}/assessment`, {}, {
      timeout: 300000,
    });
    return res.data;
  }

  async generateSubjectWorkflow(subjectId: string) {
    const res = await this.client.post(`/api/subjects/${subjectId}/generate-workflow`, {});
    return res.data;
  }

  // Memories
  async getMemories() {
    const res = await this.client.get('/api/memories');
    return res.data;
  }

  async recallMemory(id: string) {
    const res = await this.client.post(`/api/memories/recall/${id}`);
    return res.data;
  }

  // Flashcards
  async createFlashcard(data: any) {
    const res = await this.client.post('/api/flashcards', data);
    return res.data;
  }

  async generateFlashcards(subjectId: string, count: number = 10) {
    const res = await this.client.post('/api/flashcards/generate', { subject_id: subjectId, count }, {
      timeout: 300000,
    });
    return res.data;
  }

  async getDueFlashcards() {
    const res = await this.client.get('/api/flashcards/due');
    return res.data;
  }

  async reviewFlashcard(id: string, quality: number) {
    const res = await this.client.post(`/api/flashcards/${id}/review?quality=${quality}`);
    return res.data;
  }

  // Study Plans
  async createStudyPlan(data: any) {
    const res = await this.client.post('/api/study-plans', data);
    return res.data;
  }

  async getStudyPlans() {
    const res = await this.client.get('/api/study-plans');
    return res.data;
  }

  // Whiteboard
  async createWhiteboard(data: any) {
    const res = await this.client.post('/api/whiteboards', data);
    return res.data;
  }

  async getWhiteboards() {
    const res = await this.client.get('/api/whiteboards');
    return res.data;
  }

  async getWhiteboard(id: string) {
    const res = await this.client.get(`/api/whiteboards/${id}`);
    return res.data;
  }

  async updateWhiteboard(id: string, data: any) {
    const res = await this.client.put(`/api/whiteboards/${id}`, data);
    return res.data;
  }

  // Projects
  async getProjects() {
    const res = await this.client.get('/api/projects/');
    return res.data;
  }

  async createProject(data: any) {
    const res = await this.client.post('/api/projects/', data);
    return res.data;
  }

  async deleteProject(id: string) {
    const res = await this.client.delete(`/api/projects/${id}`);
    return res.data;
  }

  // Progress
  async getProgressSummary() {
    const res = await this.client.get('/api/progress/summary');
    return res.data;
  }

  // Notifications
  async getNotifications() {
    const res = await this.client.get('/api/notifications');
    return res.data;
  }

  async markNotificationRead(id: string) {
    const res = await this.client.post(`/api/notifications/${id}/read`);
    return res.data;
  }

  async markAllNotificationsRead() {
    const res = await this.client.post('/api/notifications/read-all');
    return res.data;
  }

  // Health
  async health() {
    const res = await this.client.get('/api/health');
    return res.data;
  }
}

export const api = new ApiClient();