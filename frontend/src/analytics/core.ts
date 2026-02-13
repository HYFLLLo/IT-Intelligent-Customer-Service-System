/**
 * 埋点系统核心模块
 * IT Intelligent Customer Service System - Analytics Core
 */

import {
  EventType,
  UserRole,
  defaultConfig,
  BusinessEventType,
} from './types';
import type {
  TrackEvent,
  AnalyticsConfig,
  SubmitQuestionEvent,
  CreateTicketEvent,
  RateResponseEvent
} from './types';

class AnalyticsCore {
  private config: AnalyticsConfig;
  private eventQueue: TrackEvent[] = [];
  private retryQueue: TrackEvent[] = [];
  private sessionId: string;
  private flushTimer: ReturnType<typeof setInterval> | null = null;
  private userInfo: {
    userId?: string;
    userRole?: UserRole;
    userDepartment?: string;
  } = {};
  private isOnline: boolean = navigator.onLine;

  constructor(config: Partial<AnalyticsConfig> = {}) {
    this.config = { ...defaultConfig, ...config };
    this.sessionId = this.generateSessionId();
    this.init();
  }

  private generateSessionId(): string {
    return `sess_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private init() {
    if (!this.config.enabled) return;

    // 启动定时上报
    this.startFlushTimer();

    // 监听网络状态
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.flush();
    });
    window.addEventListener('offline', () => {
      this.isOnline = false;
    });

    // 页面卸载前上报
    window.addEventListener('beforeunload', () => {
      this.flush(true);
    });

    // 页面可见性变化时上报
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        this.flush(true);
      }
    });
  }

  // 设置用户信息
  setUser(userId: string, userRole: UserRole, userDepartment?: string) {
    this.userInfo = { userId, userRole, userDepartment };
  }

  // 获取当前用户信息
  getUserInfo() {
    return { ...this.userInfo };
  }

  // 生成事件ID
  private generateEventId(): string {
    return `evt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // 创建基础事件对象
  private createBaseEvent(
    eventType: EventType,
    eventName: string,
    data?: Record<string, any>
  ): TrackEvent {
    return {
      id: this.generateEventId(),
      eventType,
      eventName,
      timestamp: Date.now(),
      sessionId: this.sessionId,
      ...this.userInfo,
      pageUrl: window.location.href,
      pageTitle: document.title,
      userAgent: navigator.userAgent,
      data
    };
  }

  // 上报事件（核心方法）
  track(eventName: string, data?: Record<string, any>, eventType: EventType = EventType.BUSINESS) {
    if (!this.config.enabled) return;
    if (Math.random() > this.config.sampleRate) return;

    const event = this.createBaseEvent(eventType, eventName, data);
    this.eventQueue.push(event);

    // 达到批量上限立即上报
    if (this.eventQueue.length >= this.config.maxBatchSize) {
      this.flush();
    }
  }

  // 页面浏览埋点
  pageView(pageName: string, extraData?: Record<string, any>) {
    this.track(pageName, {
      title: document.title,
      referrer: document.referrer,
      ...extraData
    }, EventType.PAGE_VIEW);
  }

  // 点击事件埋点
  click(elementName: string, extraData?: Record<string, any>) {
    this.track(elementName, extraData, EventType.CLICK);
  }

  // API调用埋点
  api(apiName: string, duration: number, success: boolean, extraData?: Record<string, any>) {
    this.track(apiName, {
      duration,
      success,
      ...extraData
    }, EventType.API);
  }

  // 错误埋点
  error(errorType: string, errorMessage: string, extraData?: Record<string, any>) {
    this.track(errorType, {
      message: errorMessage,
      userAgent: navigator.userAgent,
      ...extraData
    }, EventType.ERROR);
  }

  // 性能埋点
  performance(metricName: string, value: number, extraData?: Record<string, any>) {
    this.track(metricName, {
      value,
      ...extraData
    }, EventType.PERFORMANCE);
  }

  // ========== 员工侧业务事件专用方法 ==========

  // 提交问题埋点
  trackSubmitQuestion(data: SubmitQuestionEvent) {
    this.track(BusinessEventType.SUBMIT_QUESTION, {
      ...data,
      businessType: 'employee_action'
    });
  }

  // 创建工单埋点
  trackCreateTicket(data: CreateTicketEvent) {
    this.track(BusinessEventType.CREATE_TICKET, {
      ...data,
      businessType: 'employee_action'
    });
  }

  // 评价回复埋点
  trackRateResponse(data: RateResponseEvent) {
    this.track(BusinessEventType.RATE_RESPONSE, {
      ...data,
      businessType: 'employee_action'
    });
  }

  // 立即上报（支持同步/异步）
  private flush(immediate = false) {
    const allEvents = [...this.retryQueue, ...this.eventQueue];
    if (allEvents.length === 0) return;

    this.eventQueue = [];
    this.retryQueue = [];

    if (immediate && !this.isOnline) {
      // 离线时存入 localStorage
      this.saveToLocalStorage(allEvents);
      return;
    }

    if (immediate && navigator.sendBeacon) {
      // 使用 sendBeacon 同步上报
      const blob = new Blob([JSON.stringify({ events: allEvents })], {
        type: 'application/json'
      });
      const success = navigator.sendBeacon(this.config.endpoint, blob);
      if (!success) {
        this.retryQueue.push(...allEvents);
      }
    } else {
      // 异步上报
      this.uploadEvents(allEvents);
    }
  }

  // 异步上传事件
  private async uploadEvents(events: TrackEvent[], retryCount = 0) {
    try {
      const response = await fetch(this.config.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ events }),
        keepalive: true
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      // 成功后检查 localStorage 中是否有缓存数据
      this.flushLocalStorage();
    } catch (err) {
      console.error('[Analytics] Upload failed:', err);

      // 重试机制
      if (retryCount < this.config.maxRetries) {
        setTimeout(() => {
          this.uploadEvents(events, retryCount + 1);
        }, this.config.retryDelay * Math.pow(2, retryCount));
      } else {
        // 重试失败，加入重试队列
        this.retryQueue.push(...events);
      }
    }
  }

  // 保存到 localStorage（离线缓存）
  private saveToLocalStorage(events: TrackEvent[]) {
    try {
      const key = 'analytics_offline_cache';
      const cached = JSON.parse(localStorage.getItem(key) || '[]');
      cached.push(...events);
      // 最多缓存 1000 条
      if (cached.length > 1000) {
        cached.splice(0, cached.length - 1000);
      }
      localStorage.setItem(key, JSON.stringify(cached));
    } catch (e) {
      console.error('[Analytics] Failed to save to localStorage:', e);
    }
  }

  // 上报 localStorage 缓存的数据
  private flushLocalStorage() {
    try {
      const key = 'analytics_offline_cache';
      const cached = JSON.parse(localStorage.getItem(key) || '[]');
      if (cached.length > 0) {
        localStorage.removeItem(key);
        this.uploadEvents(cached);
      }
    } catch (e) {
      console.error('[Analytics] Failed to flush localStorage:', e);
    }
  }

  // 启动定时上报
  private startFlushTimer() {
    this.flushTimer = setInterval(() => {
      if (this.isOnline && (this.eventQueue.length > 0 || this.retryQueue.length > 0)) {
        this.flush();
      }
    }, this.config.flushInterval);
  }

  // 获取当前队列状态（用于调试）
  getQueueStatus() {
    return {
      pending: this.eventQueue.length,
      retry: this.retryQueue.length,
      sessionId: this.sessionId,
      isOnline: this.isOnline
    };
  }

  // 销毁实例
  destroy() {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }
    this.flush(true);
  }
}

// 创建单例实例
export const analytics = new AnalyticsCore();

// 导出类以便需要时创建新实例
export { AnalyticsCore };
