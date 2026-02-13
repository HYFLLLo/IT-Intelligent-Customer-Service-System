/**
 * 埋点系统类型定义
 * IT Intelligent Customer Service System - Analytics Module
 */

// 埋点事件类型枚举
export enum EventType {
  PAGE_VIEW = 'page_view',
  CLICK = 'click',
  API = 'api',
  ERROR = 'error',
  PERFORMANCE = 'performance',
  BUSINESS = 'business'
}

// 业务事件类型枚举（员工侧）
export enum BusinessEventType {
  SUBMIT_QUESTION = 'submit_question',
  CREATE_TICKET = 'create_ticket',
  RATE_RESPONSE = 'rate_response'
}

// 用户角色枚举
export enum UserRole {
  EMPLOYEE = 'employee',
  AGENT = 'agent',
  ADMIN = 'admin'
}

// 埋点事件基础数据结构
export interface TrackEvent {
  id?: string;
  eventType: EventType;
  eventName: string;
  timestamp: number;
  sessionId: string;
  userId?: string;
  userRole?: UserRole;
  userDepartment?: string;
  pageUrl: string;
  pageTitle?: string;
  ipAddress?: string;
  userAgent?: string;
  data?: Record<string, any>;
}

// 提交问题事件数据
export interface SubmitQuestionEvent {
  questionId: string;
  questionType: string;
  questionSummary: string;
  questionLength: number;
  hasAttachment: boolean;
  submitDuration: number;
}

// 创建工单事件数据
export interface CreateTicketEvent {
  ticketId: string;
  ticketTitle: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  department: string;
  descriptionLength: number;
  createStartTime: number;
  createEndTime: number;
  duration: number;
}

// 评价回复事件数据
export interface RateResponseEvent {
  ratingId: string;
  ticketId: string;
  ratingScore: number;
  replyContentLength: number;
  hasReply: boolean;
}

// 埋点配置选项
export interface AnalyticsConfig {
  enabled: boolean;
  endpoint: string;
  sampleRate: number;
  maxBatchSize: number;
  flushInterval: number;
  enablePerformance: boolean;
  enableError: boolean;
  maxRetries: number;
  retryDelay: number;
}

// 默认配置
export const defaultConfig: AnalyticsConfig = {
  enabled: true,
  endpoint: 'http://localhost:8000/api/v1/analytics',
  sampleRate: 1,
  maxBatchSize: 10,
  flushInterval: 3000,
  enablePerformance: true,
  enableError: true,
  maxRetries: 3,
  retryDelay: 1000
};

// 埋点数据查询参数
export interface AnalyticsQueryParams {
  page?: number;
  pageSize?: number;
  eventType?: EventType | string;
  eventName?: string;
  userId?: string;
  userRole?: UserRole | string;
  userDepartment?: string;
  startTime?: number;
  endTime?: number;
  keyword?: string;
}

// 埋点数据列表响应
export interface AnalyticsListResponse {
  total: number;
  page: number;
  pageSize: number;
  data: TrackEvent[];
}

// 统计概览数据
export interface AnalyticsOverview {
  totalEvents: number;
  todayEvents: number;
  uniqueUsers: number;
  eventTypeDistribution: Record<string, number>;
  topEvents: Array<{ eventName: string; count: number }>;
}
