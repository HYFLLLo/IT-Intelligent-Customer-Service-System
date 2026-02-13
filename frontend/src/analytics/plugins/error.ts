/**
 * 错误监控插件
 * 捕获 JS 错误、Promise 错误、资源加载错误等
 */

import { analytics } from '../core';
import { EventType } from '../types';

// Vue 错误处理函数类型
export type VueErrorHandler = (err: unknown, vm: any, info: string) => void;

export function setupErrorTracking() {
  // JS 运行时错误
  window.addEventListener('error', (event) => {
    analytics.track(
      'js_runtime_error',
      {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack,
        tagName: event.target?.tagName,
        url: window.location.href
      },
      EventType.ERROR
    );
  }, true);

  // Promise 未捕获错误
  window.addEventListener('unhandledrejection', (event) => {
    const error = event.reason;
    analytics.track(
      'unhandled_promise_rejection',
      {
        message: error?.message || String(error),
        stack: error?.stack,
        type: typeof error
      },
      EventType.ERROR
    );
  });

  // 资源加载错误（图片、CSS、JS 等）
  window.addEventListener('error', (event) => {
    const target = event.target as HTMLElement;
    if (target && (target.tagName === 'IMG' || target.tagName === 'SCRIPT' || target.tagName === 'LINK')) {
      analytics.track(
        'resource_load_error',
        {
          tagName: target.tagName,
          src: (target as any).src || (target as any).href,
          url: window.location.href
        },
        EventType.ERROR
      );
    }
  }, true);

  // 控制台错误拦截（可选）
  interceptConsoleError();
}

// Vue 专用错误处理
export const onVueError: VueErrorHandler = (err, vm, info) => {
  const componentName = vm?.$options?.name || vm?.$options?._componentTag || 'anonymous';
  const props = vm?.$options?.propsData || {};

  analytics.track(
    'vue_component_error',
    {
      message: err instanceof Error ? err.message : String(err),
      stack: err instanceof Error ? err.stack : undefined,
      component: componentName,
      props: JSON.stringify(props),
      info,
      lifecycle: info,
      url: window.location.href
    },
    EventType.ERROR
  );
};

// 拦截控制台错误
function interceptConsoleError() {
  const originalError = console.error;

  console.error = function (...args: any[]) {
    // 过滤掉 Vue 的警告（避免重复上报）
    const message = args[0]?.toString() || '';
    if (!message.includes('[Vue warn]')) {
      analytics.track(
        'console_error',
        {
          message: args.map(arg =>
            typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
          ).join(' '),
          url: window.location.href
        },
        EventType.ERROR
      );
    }

    originalError.apply(console, args);
  };
}

// 主动上报错误
export function reportError(errorType: string, error: Error, extraData?: Record<string, any>) {
  analytics.track(
    errorType,
    {
      message: error.message,
      stack: error.stack,
      ...extraData
    },
    EventType.ERROR
  );
}
