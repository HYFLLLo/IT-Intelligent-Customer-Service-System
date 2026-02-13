/**
 * 埋点系统入口文件
 * IT Intelligent Customer Service System - Analytics Module
 * 
 * 仅用于员工端业务事件埋点：
 * - 提交问题
 * - 创建工单
 * - 评价回复
 */

// 核心模块
export { analytics, AnalyticsCore } from './core';

// 枚举和常量（值导出）
export {
  EventType,
  BusinessEventType,
  UserRole,
  defaultConfig
} from './types';

// 类型导出（使用 export type）
export type {
  TrackEvent,
  AnalyticsConfig,
  AnalyticsQueryParams,
  AnalyticsListResponse,
  AnalyticsOverview,
  SubmitQuestionEvent,
  CreateTicketEvent,
  RateResponseEvent
} from './types';

// 便捷导出
export { analytics as $analytics };
