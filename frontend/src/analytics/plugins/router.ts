/**
 * 路由埋点插件
 * 自动追踪页面浏览和路由切换
 */

import type { Router } from 'vue-router';
import { analytics } from '../core';
import { EventType } from '../types';

export function setupRouterTracking(router: Router) {
  // 记录路由切换开始时间
  let routeStartTime = Date.now();
  let currentPage = '';

  // 路由切换前
  router.beforeEach((to, from, next) => {
    routeStartTime = Date.now();
    next();
  });

  // 路由切换后埋点
  router.afterEach((to, from) => {
    const duration = Date.now() - routeStartTime;
    currentPage = to.path;

    // 页面浏览埋点
    analytics.track(
      to.path,
      {
        from: from.path,
        routeName: to.name,
        params: to.params,
        query: to.query,
        duration: duration,
        title: to.meta.title || document.title
      },
      EventType.PAGE_VIEW
    );

    // 性能埋点：页面切换耗时
    if (duration > 0) {
      analytics.performance('route_switch_duration', duration, {
        from: from.path,
        to: to.path
      });
    }
  });

  // 路由错误埋点
  router.onError((error) => {
    analytics.error('route_error', error.message, {
      currentPage,
      stack: error.stack
    });
  });
}
