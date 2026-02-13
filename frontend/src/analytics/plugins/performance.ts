/**
 * 性能监控插件
 * 监控页面加载性能、API响应时间等
 */

import { analytics } from '../core';
import { EventType } from '../types';

export function setupPerformanceTracking() {
  // 页面加载完成后上报性能数据
  window.addEventListener('load', () => {
    // 使用 setTimeout 确保所有性能数据已收集
    setTimeout(() => {
      reportPagePerformance();
      reportResourcePerformance();
    }, 0);
  });

  // 包装 fetch 监控 API 性能
  wrapFetch();

  // 监控长任务（阻塞主线程的任务）
  observeLongTasks();

  // 监控首次内容绘制 (FCP)
  observeFCP();

  // 监控最大内容绘制 (LCP)
  observeLCP();

  // 监控首次输入延迟 (FID)
  observeFID();
}

// 上报页面加载性能
function reportPagePerformance() {
  const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
  if (!navigation) return;

  const metrics = {
    // DNS 解析时间
    dnsTime: navigation.domainLookupEnd - navigation.domainLookupStart,
    // TCP 连接时间
    tcpTime: navigation.connectEnd - navigation.connectStart,
    // SSL 握手时间
    sslTime: navigation.secureConnectionStart > 0
      ? navigation.connectEnd - navigation.secureConnectionStart
      : 0,
    // 首字节时间 (TTFB)
    ttfb: navigation.responseStart - navigation.requestStart,
    // 下载时间
    downloadTime: navigation.responseEnd - navigation.responseStart,
    // DOM 解析时间
    domParseTime: navigation.domInteractive - navigation.responseEnd,
    // DOM 加载完成时间
    domReadyTime: navigation.domContentLoadedEventEnd - navigation.startTime,
    // 页面完全加载时间
    loadTime: navigation.loadEventEnd - navigation.startTime,
    // 重定向时间
    redirectTime: navigation.redirectEnd - navigation.redirectStart
  };

  // 上报各阶段耗时
  Object.entries(metrics).forEach(([name, value]) => {
    if (value > 0) {
      analytics.performance(`page_${name}`, value);
    }
  });

  // 上报总体性能事件
  analytics.track('page_load_performance', metrics, EventType.PERFORMANCE);
}

// 上报资源加载性能
function reportResourcePerformance() {
  const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[];

  // 只上报慢资源（加载时间 > 1秒）
  const slowResources = resources.filter(r => r.duration > 1000);

  if (slowResources.length > 0) {
    analytics.track('slow_resources', {
      count: slowResources.length,
      resources: slowResources.map(r => ({
        name: r.name.split('/').pop(),
        duration: Math.round(r.duration),
        size: r.transferSize
      }))
    }, EventType.PERFORMANCE);
  }
}

// 包装 fetch 监控 API 性能
function wrapFetch() {
  const originalFetch = window.fetch;

  window.fetch = async function (...args) {
    const startTime = performance.now();
    const url = typeof args[0] === 'string' ? args[0] : args[0].url;
    const method = (args[1]?.method || 'GET').toUpperCase();

    try {
      const response = await originalFetch.apply(this, args);
      const duration = performance.now() - startTime;

      // 上报 API 性能
      analytics.api(
        `${method} ${url.replace('http://localhost:8000', '')}`,
        Math.round(duration),
        response.ok,
        {
          status: response.status,
          statusText: response.statusText
        }
      );

      // 慢 API 警告（> 3秒）
      if (duration > 3000) {
        analytics.track('slow_api_warning', {
          url,
          method,
          duration: Math.round(duration),
          status: response.status
        }, EventType.PERFORMANCE);
      }

      return response;
    } catch (error) {
      const duration = performance.now() - startTime;

      analytics.api(
        `${method} ${url}`,
        Math.round(duration),
        false,
        { error: error instanceof Error ? error.message : String(error) }
      );

      throw error;
    }
  };
}

// 监控长任务
function observeLongTasks() {
  if ('PerformanceObserver' in window) {
    try {
      const observer = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          analytics.track('long_task', {
            duration: entry.duration,
            startTime: entry.startTime
          }, EventType.PERFORMANCE);
        });
      });

      observer.observe({ entryTypes: ['longtask'] });
    } catch (e) {
      // 浏览器不支持长任务监控
    }
  }
}

// 监控首次内容绘制 (FCP)
function observeFCP() {
  if ('PerformanceObserver' in window) {
    try {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const fcpEntry = entries.find(e => e.name === 'first-contentful-paint');
        if (fcpEntry) {
          analytics.performance('fcp', fcpEntry.startTime);
          observer.disconnect();
        }
      });

      observer.observe({ entryTypes: ['paint'] });
    } catch (e) {
      // 浏览器不支持
    }
  }
}

// 监控最大内容绘制 (LCP)
function observeLCP() {
  if ('PerformanceObserver' in window) {
    try {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        analytics.performance('lcp', lastEntry.startTime);
      });

      observer.observe({ entryTypes: ['largest-contentful-paint'] });
    } catch (e) {
      // 浏览器不支持
    }
  }
}

// 监控首次输入延迟 (FID)
function observeFID() {
  if ('PerformanceObserver' in window) {
    try {
      const observer = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          const fid = entry.processingStart - entry.startTime;
          analytics.performance('fid', fid);
        });
        observer.disconnect();
      });

      observer.observe({ entryTypes: ['first-input'] });
    } catch (e) {
      // 浏览器不支持
    }
  }
}
