import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/employee'
  },
  {
    path: '/employee',
    name: 'Employee',
    component: () => import('./views/EmployeeView.vue'),
    meta: {
      title: 'IT智能助手 - 员工端'
    }
  },
  {
    path: '/agent',
    name: 'Agent',
    component: () => import('./views/AgentView.vue'),
    meta: {
      title: '工单作战指挥台 - 坐席端'
    }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('./views/AdminView.vue'),
    meta: {
      title: '系统管理 - 管理端'
    }
  },
  {
    path: '/agent/analytics',
    name: 'Analytics',
    component: () => import('./views/AnalyticsView.vue'),
    meta: {
      title: '埋点收集 - 坐席端'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/employee'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  document.title = to.meta.title as string || 'IT智能客服系统'
  next()
})

export default router
