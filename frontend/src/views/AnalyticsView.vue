<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { analytics } from '@/analytics'
import { EventType, UserRole } from '@/analytics/types'

// 引入赛博朋克样式
import '@/assets/cyberpunk-analytics.css'

// 路由
const router = useRouter()

// 返回坐席端主界面
const goBack = () => {
  router.push('/agent')
}

// ========== 状态管理 ==========

// 埋点数据列表
const analyticsData = ref<any[]>([])
const loading = ref(false)
const total = ref(0)

// 分页
const currentPage = ref(1)
const pageSize = ref(10) // 每页最多10条数据

// 筛选条件
const filters = ref({
  eventType: '',
  eventName: '',
  userId: '',
  userRole: '',
  userDepartment: '',
  timeRange: 'today', // today, yesterday, week, month, custom
  startTime: '',
  endTime: '',
  keyword: ''
})

// 时间范围选项
const timeRangeOptions = [
  { label: '今日', value: 'today' },
  { label: '昨日', value: 'yesterday' },
  { label: '近7天', value: 'week' },
  { label: '近30天', value: 'month' },
  { label: '自定义', value: 'custom' }
]

// 事件类型选项（仅三个业务事件类型）
const eventTypeOptions = [
  { label: '全部类型', value: '' },
  { label: '问题提交事件', value: 'submit_question' },
  { label: '业务事件', value: 'create_ticket' },
  { label: '评论事件', value: 'rate_response' }
]

// 用户角色选项
const userRoleOptions = [
  { label: '全部角色', value: '' },
  { label: '员工', value: UserRole.EMPLOYEE },
  { label: '坐席', value: UserRole.AGENT }
]

// 概览统计
const overview = ref({
  totalEvents: 0,
  todayEvents: 0,
  uniqueUsers: 0,
  eventTypeDistribution: {},
  topEvents: []
})

// 详情弹窗
const showDetailModal = ref(false)
const selectedEvent = ref<any>(null)

// 导出状态
const exporting = ref(false)

// 清除确认弹窗
const showClearConfirmModal = ref(false)
const clearing = ref(false)

// ========== 计算属性 ==========

// 总页数
const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

// 分页显示
const paginationRange = computed(() => {
  const range = []
  const maxVisible = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
  let end = Math.min(totalPages.value, start + maxVisible - 1)
  
  if (end - start < maxVisible - 1) {
    start = Math.max(1, end - maxVisible + 1)
  }
  
  for (let i = start; i <= end; i++) {
    range.push(i)
  }
  return range
})

// 是否显示自定义时间选择
const showCustomTime = computed(() => filters.value.timeRange === 'custom')

// ========== 方法 ==========

// 获取时间戳范围
const getTimeRange = () => {
  const now = new Date()
  let start = new Date()
  let end = new Date()
  
  switch (filters.value.timeRange) {
    case 'today':
      start.setHours(0, 0, 0, 0)
      break
    case 'yesterday':
      start.setDate(start.getDate() - 1)
      start.setHours(0, 0, 0, 0)
      end.setDate(end.getDate() - 1)
      end.setHours(23, 59, 59, 999)
      break
    case 'week':
      start.setDate(start.getDate() - 7)
      break
    case 'month':
      start.setDate(start.getDate() - 30)
      break
    case 'custom':
      if (filters.value.startTime) {
        start = new Date(filters.value.startTime)
      }
      if (filters.value.endTime) {
        end = new Date(filters.value.endTime)
        end.setHours(23, 59, 59, 999)
      }
      break
  }
  
  return {
    startTime: start.getTime(),
    endTime: end.getTime()
  }
}

// 加载埋点数据
const loadAnalyticsData = async () => {
  loading.value = true
  try {
    const timeRange = getTimeRange()
    const params = new URLSearchParams({
      page: currentPage.value.toString(),
      page_size: pageSize.value.toString(),
      start_time: timeRange.startTime.toString(),
      end_time: timeRange.endTime.toString()
    })
    
    if (filters.value.eventType) {
      // 事件类型筛选实际上是按事件名称筛选（submit_question, create_ticket, rate_response）
      params.append('event_name', filters.value.eventType)
    }
    if (filters.value.eventName) {
      params.append('event_name', filters.value.eventName)
    }
    if (filters.value.userId) {
      params.append('user_id', filters.value.userId)
    }
    if (filters.value.userRole) {
      params.append('user_role', filters.value.userRole)
    }
    if (filters.value.userDepartment) {
      params.append('user_department', filters.value.userDepartment)
    }
    if (filters.value.keyword) {
      params.append('keyword', filters.value.keyword)
    }
    
    const response = await fetch(`http://localhost:8000/api/v1/analytics?${params}`)
    if (response.ok) {
      const data = await response.json()
      analyticsData.value = data.data
      total.value = data.total
    }
  } catch (error) {
    console.error('加载埋点数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 加载概览统计
const loadOverview = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/v1/analytics/overview?days=7')
    if (response.ok) {
      const data = await response.json()
      overview.value = data
    }
  } catch (error) {
    console.error('加载概览统计失败:', error)
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  loadAnalyticsData()
}

// 显示清除确认弹窗
const showClearConfirm = () => {
  showClearConfirmModal.value = true
}

// 关闭清除确认弹窗
const closeClearConfirm = () => {
  showClearConfirmModal.value = false
}

// 确认清除所有埋点记录
const confirmClearAll = async () => {
  clearing.value = true
  try {
    const response = await fetch('http://localhost:8000/api/v1/analytics/clear', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      // 清除成功后刷新数据
      analyticsData.value = []
      total.value = 0
      overview.value = {
        totalEvents: 0,
        todayEvents: 0,
        uniqueUsers: 0,
        eventTypeDistribution: {},
        topEvents: []
      }
      showClearConfirmModal.value = false
    } else {
      console.error('清除失败')
    }
  } catch (err) {
    console.error('清除埋点记录失败:', err)
  } finally {
    clearing.value = false
  }
}

// 分页
const goToPage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    loadAnalyticsData()
  }
}

// 查看详情
const viewDetail = (event: any) => {
  selectedEvent.value = event
  showDetailModal.value = true
}

// 关闭详情
const closeDetail = () => {
  showDetailModal.value = false
  selectedEvent.value = null
}

// 导出数据
const exportData = async () => {
  exporting.value = true
  try {
    const timeRange = getTimeRange()
    const params = new URLSearchParams({
      start_time: timeRange.startTime.toString(),
      end_time: timeRange.endTime.toString()
    })
    
    if (filters.value.eventType) {
      // 事件类型筛选实际上是按事件名称筛选（submit_question, create_ticket, rate_response）
      params.append('event_name', filters.value.eventType)
    }
    
    const response = await fetch(`http://localhost:8000/api/v1/analytics/export?${params}`)
    if (response.ok) {
      const data = await response.json()
      
      // 生成CSV
      const headers = Object.keys(data.data[0] || {})
      const csvContent = [
        headers.join(','),
        ...data.data.map((row: any) => 
          headers.map(h => {
            const cell = row[h] || ''
            // 处理包含逗号或换行符的单元格
            if (typeof cell === 'string' && (cell.includes(',') || cell.includes('\n'))) {
              return `"${cell.replace(/"/g, '""')}"`
            }
            return cell
          }).join(',')
        )
      ].join('\n')
      
      // 下载文件
      const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `analytics_export_${new Date().toISOString().slice(0, 10)}.csv`
      link.click()
    }
  } catch (error) {
    console.error('导出数据失败:', error)
    alert('导出失败，请重试')
  } finally {
    exporting.value = false
  }
}

// 格式化时间
const formatTime = (timestamp: number) => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

// 格式化日期
const formatDate = (timestamp: number) => {
  return new Date(timestamp).toLocaleDateString('zh-CN')
}

// 截断文本
const truncateText = (text: string, maxLength: number = 50) => {
  if (!text) return '-'
  return text.length > maxLength ? text.slice(0, maxLength) + '...' : text
}

// 获取事件类型样式（根据事件名称映射）
const getEventTypeClass = (eventName: string) => {
  const classMap: Record<string, string> = {
    'submit_question': 'type-question',
    'create_ticket': 'type-business',
    'rate_response': 'type-rate'
  }
  return classMap[eventName] || 'type-default'
}

// 获取事件类型标签（根据事件名称映射到三个分类）
const getEventTypeLabel = (eventName: string) => {
  const labelMap: Record<string, string> = {
    'submit_question': '问题提交事件',
    'create_ticket': '业务事件',
    'rate_response': '评论事件'
  }
  return labelMap[eventName] || eventName
}

// 监听筛选条件变化
watch(() => filters.value.timeRange, (newVal) => {
  if (newVal !== 'custom') {
    filters.value.startTime = ''
    filters.value.endTime = ''
  }
})

// 初始化
onMounted(() => {
  loadAnalyticsData()
  loadOverview()
  
  // 埋点：页面浏览
  analytics.pageView('/agent/analytics', { pageName: '埋点收集管理' })
})
</script>

<template>
  <div class="analytics-view">
    <!-- 头部标题区 -->
    <header class="analytics-header">
      <!-- 返回按钮 -->
      <button class="back-btn cyber-btn-back" @click="goBack">
        <span class="back-icon">←</span>
        <span class="back-text">返回</span>
      </button>
      <div class="header-glitch">
        <h1 class="cyber-title">
          <span class="glitch-text" data-text="埋点收集">埋点收集</span>
          <span class="cyber-subtitle">ANALYTICS_COLLECTOR</span>
        </h1>
      </div>

    </header>

    <!-- 筛选区 -->
    <section class="filter-section cyber-panel">
      <div class="filter-grid">
        <!-- 时间范围 -->
        <div class="filter-item">
          <label class="cyber-label">时间范围</label>
          <select v-model="filters.timeRange" class="cyber-select">
            <option v-for="opt in timeRangeOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>
        
        <!-- 自定义时间 -->
        <template v-if="showCustomTime">
          <div class="filter-item">
            <label class="cyber-label">开始日期</label>
            <input 
              v-model="filters.startTime" 
              type="date" 
              class="cyber-input"
            />
          </div>
          <div class="filter-item">
            <label class="cyber-label">结束日期</label>
            <input 
              v-model="filters.endTime" 
              type="date" 
              class="cyber-input"
            />
          </div>
        </template>
        
        <!-- 事件类型 -->
        <div class="filter-item">
          <label class="cyber-label">事件类型</label>
          <select v-model="filters.eventType" class="cyber-select">
            <option v-for="opt in eventTypeOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>
        
        <!-- 关键词搜索 -->
        <div class="filter-item filter-search">
          <label class="cyber-label">关键词搜索</label>
          <div class="search-box">
            <input 
              v-model="filters.keyword" 
              type="text" 
              class="cyber-input"
              placeholder="搜索事件名称、URL等"
              @keyup.enter="handleSearch"
            />
            <button class="cyber-btn search-btn" @click="handleSearch">
              <span class="btn-text">搜索</span>
            </button>
          </div>
        </div>
      </div>
      
      <!-- 筛选操作按钮 -->
      <div class="filter-actions">
        <button class="cyber-btn cyan" @click="loadAnalyticsData" :disabled="loading">
          <span class="btn-icon">🔄</span>
          <span class="btn-text">{{ loading ? '刷新中...' : '刷新' }}</span>
        </button>
        <button class="cyber-btn pink" @click="showClearConfirm">
          <span class="btn-icon">🗑</span>
          <span class="btn-text">清除全部</span>
        </button>
        <button class="cyber-btn purple" @click="exportData" :disabled="exporting">
          <span class="btn-icon">⬇</span>
          <span class="btn-text">{{ exporting ? '导出中...' : '导出数据' }}</span>
        </button>
      </div>
    </section>

    <!-- 数据列表 -->
    <section class="data-section cyber-panel">
      <div class="section-header">
        <h2 class="section-title">
          <span class="title-icon">📊</span>
          埋点数据列表
        </h2>
        <div class="section-meta">
          共 <span class="neon-cyan">{{ total }}</span> 条记录
        </div>
      </div>
      
      <!-- 表格 -->
      <div class="table-container">
        <table class="cyber-table">
          <thead>
            <tr>
              <th>事件ID</th>
              <th>事件类型</th>
              <th>事件名称</th>
              <th>触发时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="5" class="loading-cell">
                <div class="cyber-loading">
                  <div class="loading-bar"></div>
                  <div class="loading-bar"></div>
                  <div class="loading-bar"></div>
                </div>
              </td>
            </tr>
            <tr v-else-if="analyticsData.length === 0">
              <td colspan="5" class="empty-cell">
                <div class="cyber-empty">
                  <div class="empty-icon">📭</div>
                  <div class="empty-text">暂无数据</div>
                </div>
              </td>
            </tr>
            <tr 
              v-for="event in analyticsData" 
              :key="event.id"
              class="data-row"
              @click="viewDetail(event)"
            >
              <td class="mono-font">{{ truncateText(event.id, 12) }}</td>
              <td>
                <span class="event-type-tag" :class="getEventTypeClass(event.eventName)">
                  {{ getEventTypeLabel(event.eventName) }}
                </span>
              </td>
              <td>{{ truncateText(event.eventName, 20) }}</td>
              <td>{{ formatTime(event.timestamp) }}</td>
              <td>
                <button class="cyber-btn-mini cyan" @click.stop="viewDetail(event)">
                  详情
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- 分页 -->
      <div class="pagination" v-if="totalPages > 1">
        <button 
          class="page-btn" 
          :disabled="currentPage === 1"
          @click="goToPage(currentPage - 1)"
        >
          ←
        </button>
        <button 
          v-for="page in paginationRange" 
          :key="page"
          class="page-btn"
          :class="{ active: page === currentPage }"
          @click="goToPage(page)"
        >
          {{ page }}
        </button>
        <button 
          class="page-btn" 
          :disabled="currentPage === totalPages"
          @click="goToPage(currentPage + 1)"
        >
          →
        </button>
      </div>
    </section>

    <!-- 清除确认弹窗 -->
    <div v-if="showClearConfirmModal" class="cyber-modal confirm-modal" @click.self="closeClearConfirm">
      <div class="modal-content confirm-content">
        <div class="modal-header danger-header">
          <h3 class="modal-title">
            <span class="title-glitch danger-text" data-text="⚠ WARNING">⚠ WARNING</span>
          </h3>
          <button class="close-btn" @click="closeClearConfirm">✕</button>
        </div>
        <div class="modal-body confirm-body">
          <div class="warning-icon">🗑</div>
          <div class="confirm-message">
            <p class="main-text">确认清除所有埋点记录？</p>
            <p class="sub-text">此操作将永久删除所有已收集的埋点数据，无法恢复。</p>
          </div>
          <div class="data-preview" v-if="total > 0">
            <div class="preview-item">
              <span class="preview-label">待清除记录数:</span>
              <span class="preview-value neon-pink">{{ total }} 条</span>
            </div>
          </div>
          <div class="confirm-actions">
            <button class="cyber-btn-outline" @click="closeClearConfirm">
              <span class="btn-icon">✕</span>
              <span class="btn-text">取消</span>
            </button>
            <button class="cyber-btn-danger" @click="confirmClearAll" :disabled="clearing">
              <span class="btn-icon">⚡</span>
              <span class="btn-text">{{ clearing ? '清除中...' : '确认清除' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <div v-if="showDetailModal" class="cyber-modal" @click.self="closeDetail">
      <div class="modal-content">
        <div class="modal-header">
          <h3 class="modal-title">
            <span class="title-glitch" data-text="事件详情">事件详情</span>
          </h3>
          <button class="close-btn" @click="closeDetail">✕</button>
        </div>
        <div class="modal-body" v-if="selectedEvent">
          <div class="detail-grid">
            <div class="detail-item">
              <label>事件ID</label>
              <value class="mono-font">{{ selectedEvent.id }}</value>
            </div>
            <div class="detail-item">
              <label>事件类型</label>
              <value>
                <span class="event-type-tag" :class="getEventTypeClass(selectedEvent.eventName)">
                  {{ getEventTypeLabel(selectedEvent.eventName) }}
                </span>
              </value>
            </div>
            <div class="detail-item">
              <label>事件名称</label>
              <value>{{ selectedEvent.eventName }}</value>
            </div>
            <div class="detail-item">
              <label>触发时间</label>
              <value>{{ formatTime(selectedEvent.timestamp) }}</value>
            </div>
            <div class="detail-item full-width">
              <label>页面URL</label>
              <value class="url-value">{{ selectedEvent.pageUrl }}</value>
            </div>
            <div class="detail-item full-width" v-if="selectedEvent.data">
              <label>详细数据</label>
              <value class="json-value">
                <pre>{{ JSON.stringify(selectedEvent.data, null, 2) }}</pre>
              </value>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
