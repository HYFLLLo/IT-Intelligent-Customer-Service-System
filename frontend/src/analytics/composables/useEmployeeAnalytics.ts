/**
 * 员工侧埋点 Composable
 * 提供员工端业务事件的便捷埋点方法
 */

import { ref } from 'vue';
import { analytics } from '../core';
import {
  BusinessEventType,
  SubmitQuestionEvent,
  CreateTicketEvent,
  RateResponseEvent,
  UserRole
} from '../types';

// 问题提交开始时间（用于计算耗时）
const questionStartTime = ref<number>(0);
// 工单创建开始时间
const ticketStartTime = ref<number>(0);

/**
 * 设置当前用户信息
 */
export function setEmployeeUser(userId: string, department?: string) {
  analytics.setUser(userId, UserRole.EMPLOYEE, department);
}

/**
 * 开始记录问题提交
 */
export function startQuestionSubmit() {
  questionStartTime.value = Date.now();
}

/**
 * 记录问题提交完成
 */
export function trackQuestionSubmit(
  questionId: string,
  questionType: string,
  questionContent: string,
  hasAttachment: boolean = false
) {
  const duration = questionStartTime.value > 0
    ? Date.now() - questionStartTime.value
    : 0;

  const eventData: SubmitQuestionEvent = {
    questionId,
    questionType,
    questionSummary: questionContent.substring(0, 100),
    questionLength: questionContent.length,
    hasAttachment,
    submitDuration: duration
  };

  analytics.trackSubmitQuestion(eventData);

  // 同时记录点击事件
  analytics.click('submit_question_button', {
    questionId,
    questionType,
    duration
  });

  // 重置开始时间
  questionStartTime.value = 0;
}

/**
 * 开始记录工单创建
 */
export function startTicketCreate() {
  ticketStartTime.value = Date.now();
}

/**
 * 记录工单创建完成
 */
export function trackTicketCreate(
  ticketId: string,
  ticketTitle: string,
  priority: 'low' | 'medium' | 'high' | 'urgent',
  department: string,
  description: string
) {
  const endTime = Date.now();
  const duration = ticketStartTime.value > 0
    ? endTime - ticketStartTime.value
    : 0;

  const eventData: CreateTicketEvent = {
    ticketId,
    ticketTitle,
    priority,
    department,
    descriptionLength: description.length,
    createStartTime: ticketStartTime.value,
    createEndTime: endTime,
    duration
  };

  analytics.trackCreateTicket(eventData);

  // 同时记录点击事件
  analytics.click('create_ticket_button', {
    ticketId,
    priority,
    department,
    duration
  });

  // 重置开始时间
  ticketStartTime.value = 0;
}

/**
 * 记录评价回复
 */
export function trackRateResponse(
  ratingId: string,
  ticketId: string,
  ratingScore: number,
  replyContent?: string
) {
  const eventData: RateResponseEvent = {
    ratingId,
    ticketId,
    ratingScore,
    replyContentLength: replyContent?.length || 0,
    hasReply: !!replyContent && replyContent.length > 0
  };

  analytics.trackRateResponse(eventData);

  // 同时记录点击事件
  analytics.click('submit_rating_button', {
    ratingId,
    ticketId,
    ratingScore,
    hasReply: !!replyContent
  });
}

/**
 * 记录员工端页面浏览
 */
export function trackEmployeePageView(pageName: string, extraData?: Record<string, any>) {
  analytics.pageView(pageName, {
    userRole: 'employee',
    ...extraData
  });
}

/**
 * 记录员工端点击事件
 */
export function trackEmployeeClick(elementName: string, extraData?: Record<string, any>) {
  analytics.click(elementName, {
    userRole: 'employee',
    ...extraData
  });
}

/**
 * 记录会话相关事件
 */
export function trackConversationEvent(
  eventName: 'create_conversation' | 'switch_conversation' | 'delete_conversation',
  conversationId: number,
  extraData?: Record<string, any>
) {
  analytics.track(`conversation_${eventName}`, {
    conversationId,
    userRole: 'employee',
    ...extraData
  });
}

/**
 * 记录通知相关事件
 */
export function trackNotificationEvent(
  eventName: 'view_notification' | 'mark_read' | 'click_notification',
  notificationId: number,
  notificationType?: string
) {
  analytics.click(`notification_${eventName}`, {
    notificationId,
    notificationType,
    userRole: 'employee'
  });
}

/**
 * 记录热门问题点击
 */
export function trackHotQuestionClick(question: string, index: number) {
  analytics.click('hot_question', {
    question,
    index,
    userRole: 'employee'
  });
}

/**
 * 记录标签点击
 */
export function trackTagClick(tag: string) {
  analytics.click('suggested_tag', {
    tag,
    userRole: 'employee'
  });
}

// 导出所有方法
export const useEmployeeAnalytics = () => ({
  setEmployeeUser,
  startQuestionSubmit,
  trackQuestionSubmit,
  startTicketCreate,
  trackTicketCreate,
  trackRateResponse,
  trackEmployeePageView,
  trackEmployeeClick,
  trackConversationEvent,
  trackNotificationEvent,
  trackHotQuestionClick,
  trackTagClick
});

export default useEmployeeAnalytics;
