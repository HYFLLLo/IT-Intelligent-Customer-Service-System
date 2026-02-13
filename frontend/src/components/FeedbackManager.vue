<template>
  <div class="feedback-manager cyber-panel">
    <!-- 发光边框效果 -->
    <div class="panel-glow-border"></div>
    <div class="panel-grid-bg"></div>
    
    <!-- 头部统计和操作区 -->
    <div class="feedback-header">
      <div class="header-title">
        <span class="title-icon">📊</span>
        <h2>用户反馈收集</h2>
        <span v-if="unreadCount > 0" class="unread-badge cyber-badge">{{ unreadCount }}</span>
      </div>
      
      <!-- 统计卡片 -->
      <div class="stats-cards">
        <div class="stat-card cyber-stat-card">
          <div class="stat-glow"></div>
          <div class="stat-value">{{ stats.total_count }}</div>
          <div class="stat-label">总反馈</div>
        </div>
        <div class="stat-card cyber-stat-card satisfied">
          <div class="stat-glow"></div>
          <div class="stat-value">{{ stats.satisfied_count }}</div>
          <div class="stat-label">满意</div>
        </div>
        <div class="stat-card cyber-stat-card dissatisfied">
          <div class="stat-glow"></div>
          <div class="stat-value">{{ stats.dissatisfied_count }}</div>
          <div class="stat-label">不满意</div>
        </div>
        <div class="stat-card cyber-stat-card rate">
          <div class="stat-glow"></div>
          <div class="stat-value">{{ stats.satisfaction_rate }}%</div>
          <div class="stat-label">满意度</div>
        </div>
      </div>
    </div>
    
    <!-- 筛选和搜索区 -->
    <div class="filter-section">
      <div class="filter-group">
        <select v-model="filters.feedback_type" class="cyber-select" @change="handleFilterChange">
          <option value="">全部类型</option>
          <option value="satisfied">满意</option>
          <option value="dissatisfied">不满意</option>
        </select>
        
        <select v-model="filters.time_range" class="cyber-select" @change="handleFilterChange">
          <option value="all">全部时间</option>
          <option value="today">今日</option>
          <option value="yesterday">昨日</option>
          <option value="week">近7天</option>
          <option value="month">近30天</option>
        </select>
        
        <select v-model="filters.is_read" class="cyber-select" @change="handleFilterChange">
          <option value="">全部状态</option>
          <option value="false">未读</option>
          <option value="true">已读</option>
        </select>
        
        <select v-model="filters.is_processed" class="cyber-select" @change="handleFilterChange">
          <option value="">全部处理</option>
          <option value="false">未处理</option>
          <option value="true">已处理</option>
        </select>
      </div>
      
      <div class="search-group">
        <input 
          v-model="filters.search"
          type="text"
          class="cyber-search-input"
          placeholder="搜索问题关键词..."
          @input="handleSearch"
        />
        <button class="cyber-btn-refresh" @click="refreshData" :class="{ loading: isRefreshing }">
          <span class="refresh-icon" :class="{ spinning: isRefreshing }">↻</span>
        </button>
        <button class="cyber-btn-export" @click="exportData">
          <span>导出Excel</span>
        </button>
      </div>
    </div>
    
    <!-- 反馈列表 -->
    <div class="feedback-list-container">
      <div v-if="loading" class="loading-state">
        <div class="cyber-spinner"></div>
        <p>加载中...</p>
      </div>
      
      <div v-else-if="feedbackList.length === 0" class="empty-state">
        <div class="empty-icon">📭</div>
        <p>暂无反馈数据</p>
      </div>
      
      <div v-else class="feedback-list">
        <div 
          v-for="item in feedbackList" 
          :key="item.id"
          class="feedback-item cyber-card"
          :class="{ 
            unread: !item.is_read, 
            satisfied: item.feedback_type === 'satisfied',
            dissatisfied: item.feedback_type === 'dissatisfied'
          }"
          @click="viewDetail(item)"
        >
          <div class="item-glow-bar"></div>
          <div class="item-content">
            <div class="item-header">
              <span class="feedback-type-badge" :class="item.feedback_type">
                {{ item.feedback_type === 'satisfied' ? '满意' : '不满意' }}
              </span>
              <span class="feedback-time">{{ formatTime(item.feedback_submitted_at) }}</span>
            </div>
            <div class="item-body">
              <p class="question-summary">{{ truncateText(item.question_text, 50) }}</p>
            </div>
            <div class="item-footer">
              <span class="device-info">{{ item.device_info || '未知设备' }}</span>
              <span v-if="item.issue_options && item.issue_options.length > 0" class="issue-tags">
                <span v-for="(issue, idx) in item.issue_options.slice(0, 2)" :key="idx" class="issue-tag">
                  {{ getIssueLabel(issue) }}
                </span>
                <span v-if="item.issue_options.length > 2" class="issue-tag more">+{{ item.issue_options.length - 2 }}</span>
              </span>
            </div>
          </div>
          <div class="item-actions">
            <button 
              v-if="!item.is_read" 
              class="action-btn mark-read"
              @click.stop="markAsRead(item.id)"
              title="标记为已读"
            >
              ✓
            </button>
            <button 
              class="action-btn view-detail"
              title="查看详情"
            >
              →
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 分页 -->
    <div v-if="total > pageSize" class="pagination">
      <button 
        class="cyber-page-btn" 
        :disabled="page === 1"
        @click="changePage(page - 1)"
      >
        上一页
      </button>
      <span class="page-info">{{ page }} / {{ Math.ceil(total / pageSize) }}</span>
      <button 
        class="cyber-page-btn" 
        :disabled="page >= Math.ceil(total / pageSize)"
        @click="changePage(page + 1)"
      >
        下一页
      </button>
    </div>
    
    <!-- 详情弹窗 -->
    <transition name="modal">
      <div v-if="showDetailModal" class="detail-modal-overlay" @click.self="closeDetail">
        <div class="detail-modal cyber-modal">
          <div class="modal-glow-border"></div>
          <div class="modal-header">
            <h3>反馈详情</h3>
            <button class="modal-close" @click="closeDetail">×</button>
          </div>
          <div v-if="selectedFeedback" class="modal-body">
            <div class="detail-section">
              <label class="section-label">反馈类型</label>
              <span class="detail-type-badge" :class="selectedFeedback.feedback_type">
                {{ selectedFeedback.feedback_type === 'satisfied' ? '满意' : '不满意' }}
              </span>
            </div>
            
            <div class="detail-section">
              <label class="section-label">提交时间</label>
              <p class="detail-text">{{ formatDateTime(selectedFeedback.feedback_submitted_at) }}</p>
            </div>
            
            <div class="detail-section">
              <label class="section-label">用户问题</label>
              <div class="detail-box">{{ selectedFeedback.question_text }}</div>
            </div>
            
            <div class="detail-section">
              <label class="section-label">系统回答</label>
              <div class="detail-box answer">{{ selectedFeedback.answer_text }}</div>
            </div>
            
            <div v-if="selectedFeedback.issue_options && selectedFeedback.issue_options.length > 0" class="detail-section">
              <label class="section-label">问题选项</label>
              <div class="issue-options-list">
                <span v-for="(issue, idx) in selectedFeedback.issue_options" :key="idx" class="detail-issue-tag">
                  {{ getIssueLabel(issue) }}
                </span>
              </div>
            </div>
            
            <div v-if="selectedFeedback.detailed_description" class="detail-section">
              <label class="section-label">详细描述</label>
              <div class="detail-box">{{ selectedFeedback.detailed_description }}</div>
            </div>
            
            <div class="detail-section">
              <label class="section-label">设备信息</label>
              <p class="detail-text">{{ selectedFeedback.device_info || '未知' }}</p>
            </div>
            
            <div class="detail-section">
              <label class="section-label">浏览器信息</label>
              <p class="detail-text">{{ selectedFeedback.browser_info || '未知' }}</p>
            </div>
          </div>
          <div class="modal-footer">
            <button class="cyber-btn-secondary" @click="closeDetail">关闭</button>
            <button 
              v-if="!selectedFeedback?.is_processed" 
              class="cyber-btn-primary"
              @click="markAsProcessed(selectedFeedback.id)"
            >
              标记为已处理
            </button>
          </div>
        </div>
      </div>
    </transition>
    
    <!-- 新反馈通知条 -->
    <transition name="notification">
      <div v-if="newFeedbackNotification.show" class="new-feedback-notification cyber-notification">
        <span class="notification-icon">🔔</span>
        <span class="notification-text">{{ newFeedbackNotification.message }}</span>
        <button class="notification-action" @click="handleNewFeedbackClick">查看</button>
        <button class="notification-close" @click="dismissNotification">×</button>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'

// 状态
const loading = ref(false)
const isRefreshing = ref(false)
const feedbackList = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const unreadCount = ref(0)
const stats = reactive({
  total_count: 0,
  satisfied_count: 0,
  dissatisfied_count: 0,
  satisfaction_rate: 0
})

const filters = reactive({
  feedback_type: '',
  time_range: 'all',
  is_read: '',
  is_processed: '',
  search: ''
})

const showDetailModal = ref(false)
const selectedFeedback = ref(null)

const newFeedbackNotification = reactive({
  show: false,
  message: '',
  count: 0
})

// 搜索防抖
let searchTimer = null
let refreshTimer = null

// 问题选项映射
const issueLabels = {
  inaccurate: '回答不准确',
  misunderstood: '未理解问题',
  slow: '响应太慢'
}

const getIssueLabel = (issue) => issueLabels[issue] || issue

// 截断文本
const truncateText = (text, length) => {
  if (!text) return ''
  return text.length > length ? text.substring(0, length) + '...' : text
}

// 格式化时间
const formatTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return date.toLocaleDateString()
}

// 格式化日期时间
const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 获取反馈列表
const fetchFeedbackList = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams({
      page: page.value,
      page_size: pageSize.value,
      ...(filters.feedback_type && { feedback_type: filters.feedback_type }),
      ...(filters.time_range && { time_range: filters.time_range }),
      ...(filters.is_read !== '' && { is_read: filters.is_read }),
      ...(filters.is_processed !== '' && { is_processed: filters.is_processed }),
      ...(filters.search && { search: filters.search })
    })
    
    const response = await fetch(`http://localhost:8000/api/v1/feedback/list?${params}`)
    if (response.ok) {
      const data = await response.json()
      feedbackList.value = data.items
      total.value = data.total
    }
  } catch (error) {
    console.error('获取反馈列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 获取统计数据
const fetchStats = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/v1/feedback/stats')
    if (response.ok) {
      const data = await response.json()
      Object.assign(stats, data)
      unreadCount.value = data.unread_count
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

// 获取未读数量
const fetchUnreadCount = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/v1/feedback/unread-count')
    if (response.ok) {
      const data = await response.json()
      unreadCount.value = data.unread_count
    }
  } catch (error) {
    console.error('获取未读数量失败:', error)
  }
}

// 筛选变化
const handleFilterChange = () => {
  page.value = 1
  fetchFeedbackList()
}

// 搜索
const handleSearch = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    fetchFeedbackList()
  }, 500)
}

// 刷新数据
const refreshData = async () => {
  isRefreshing.value = true
  await Promise.all([fetchFeedbackList(), fetchStats()])
  setTimeout(() => {
    isRefreshing.value = false
  }, 500)
}

// 导出数据
const exportData = () => {
  // 创建CSV内容
  const headers = ['反馈ID', '类型', '问题', '回答', '提交时间', '设备', '浏览器']
  const rows = feedbackList.value.map(item => [
    item.id,
    item.feedback_type === 'satisfied' ? '满意' : '不满意',
    item.question_text,
    item.answer_text,
    item.feedback_submitted_at,
    item.device_info,
    item.browser_info
  ])
  
  const csvContent = [headers, ...rows]
    .map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
    .join('\n')
  
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `用户反馈_${new Date().toLocaleDateString()}.csv`
  link.click()
}

// 分页
const changePage = (newPage) => {
  page.value = newPage
  fetchFeedbackList()
}

// 查看详情
const viewDetail = (item) => {
  selectedFeedback.value = item
  showDetailModal.value = true
  if (!item.is_read) {
    markAsRead(item.id)
  }
}

// 关闭详情
const closeDetail = () => {
  showDetailModal.value = false
  selectedFeedback.value = null
}

// 标记为已读
const markAsRead = async (id) => {
  try {
    const response = await fetch(`http://localhost:8000/api/v1/feedback/${id}/mark-read`, {
      method: 'POST'
    })
    if (response.ok) {
      const item = feedbackList.value.find(i => i.id === id)
      if (item) item.is_read = true
      fetchUnreadCount()
    }
  } catch (error) {
    console.error('标记已读失败:', error)
  }
}

// 标记为已处理
const markAsProcessed = async (id) => {
  try {
    const response = await fetch(`http://localhost:8000/api/v1/feedback/${id}/mark-processed`, {
      method: 'POST'
    })
    if (response.ok) {
      const item = feedbackList.value.find(i => i.id === id)
      if (item) item.is_processed = true
      closeDetail()
    }
  } catch (error) {
    console.error('标记已处理失败:', error)
  }
}

// 处理新反馈通知
const handleNewFeedbackClick = () => {
  newFeedbackNotification.show = false
  refreshData()
}

// 关闭通知
const dismissNotification = () => {
  newFeedbackNotification.show = false
}

// WebSocket连接
let ws = null
let wsReconnectTimer = null
let heartbeatTimer = null

// 初始化WebSocket连接
const initWebSocket = () => {
  const wsUrl = 'ws://localhost:8000/api/v1/ws/feedback?client_type=agent'
  ws = new WebSocket(wsUrl)
  
  ws.onopen = () => {
    console.log('[WebSocket] 反馈管理连接已建立')
    // 发送订阅消息
    ws.send(JSON.stringify({ type: 'subscribe', channel: 'feedback' }))
    // 启动心跳
    startHeartbeat()
  }
  
  ws.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data)
      handleWebSocketMessage(message)
    } catch (error) {
      console.error('[WebSocket] 解析消息失败:', error)
    }
  }
  
  ws.onclose = () => {
    console.log('[WebSocket] 连接已关闭，尝试重连...')
    stopHeartbeat()
    // 5秒后重连
    wsReconnectTimer = setTimeout(() => {
      initWebSocket()
    }, 5000)
  }
  
  ws.onerror = (error) => {
    console.error('[WebSocket] 连接错误:', error)
  }
}

// 处理WebSocket消息
const handleWebSocketMessage = (message) => {
  switch (message.type) {
    case 'ping':
      // 响应心跳
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'pong' }))
      }
      break
    case 'new_feedback':
      // 收到新反馈通知
      handleNewFeedback(message.data)
      break
    case 'feedback_read':
      // 反馈已读状态更新
      updateFeedbackReadStatus(message.feedback_id)
      break
  }
}

// 处理新反馈
const handleNewFeedback = (data) => {
  // 更新未读数量
  unreadCount.value++
  
  // 显示通知
  newFeedbackNotification.message = `收到新反馈：${data.question_text}`
  newFeedbackNotification.count = 1
  newFeedbackNotification.show = true
  
  // 播放提示音（可选）
  playNotificationSound()
  
  // 5秒后自动关闭通知
  setTimeout(() => {
    newFeedbackNotification.show = false
  }, 5000)
  
  // 如果当前在反馈页面，刷新列表
  if (page.value === 1) {
    fetchFeedbackList()
  }
}

// 更新反馈已读状态
const updateFeedbackReadStatus = (feedbackId) => {
  const item = feedbackList.value.find(i => i.id === feedbackId)
  if (item) {
    item.is_read = true
  }
}

// 播放通知音
const playNotificationSound = () => {
  try {
    const audio = new Audio('/notification.mp3')
    audio.volume = 0.5
    audio.play().catch(() => {
      // 自动播放可能被浏览器阻止，忽略错误
    })
  } catch (error) {
    console.error('播放通知音失败:', error)
  }
}

// 启动心跳
const startHeartbeat = () => {
  heartbeatTimer = setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }))
    }
  }, 30000) // 每30秒发送一次心跳
}

// 停止心跳
const stopHeartbeat = () => {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
}

// 自动刷新
const startAutoRefresh = () => {
  refreshTimer = setInterval(() => {
    fetchUnreadCount()
  }, 120000) // 2分钟刷新一次
}

onMounted(() => {
  fetchFeedbackList()
  fetchStats()
  startAutoRefresh()
  initWebSocket() // 初始化WebSocket连接
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  if (searchTimer) clearTimeout(searchTimer)
  if (wsReconnectTimer) clearTimeout(wsReconnectTimer)
  stopHeartbeat()
  
  // 关闭WebSocket连接
  if (ws) {
    ws.close()
    ws = null
  }
})
</script>

<style scoped>
/* 反馈管理器容器 */
.feedback-manager {
  position: relative;
  padding: 24px;
  background: linear-gradient(135deg, rgba(17, 24, 39, 0.98) 0%, rgba(31, 41, 55, 0.95) 100%);
  border-radius: 12px;
  min-height: 600px;
}

.cyber-panel {
  border: 1px solid rgba(6, 182, 212, 0.3);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.panel-glow-border {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--neon-cyan), var(--neon-purple), transparent);
  animation: borderGlow 3s linear infinite;
}

@keyframes borderGlow {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.panel-grid-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(90deg, rgba(6, 182, 212, 0.02) 1px, transparent 1px),
    linear-gradient(rgba(6, 182, 212, 0.02) 1px, transparent 1px);
  background-size: 30px 30px;
  pointer-events: none;
  border-radius: 12px;
}

/* 头部区域 */
.feedback-header {
  position: relative;
  z-index: 1;
  margin-bottom: 24px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.title-icon {
  font-size: 1.5rem;
}

.header-title h2 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--neon-cyan);
  text-shadow: 0 0 10px rgba(6, 182, 212, 0.3);
}

.cyber-badge {
  background: linear-gradient(135deg, var(--neon-pink), #f43f5e);
  color: white;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
  box-shadow: 0 0 10px rgba(236, 72, 153, 0.4);
  animation: badgePulse 2s ease-in-out infinite;
}

@keyframes badgePulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

/* 统计卡片 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  position: relative;
  padding: 20px;
  background: linear-gradient(135deg, rgba(31, 41, 55, 0.9) 0%, rgba(55, 65, 81, 0.8) 100%);
  border: 1px solid rgba(6, 182, 212, 0.3);
  border-radius: 8px;
  text-align: center;
  overflow: hidden;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(6, 182, 212, 0.2);
}

.stat-card.satisfied {
  border-color: rgba(6, 182, 212, 0.5);
}

.stat-card.satisfied .stat-value {
  color: var(--neon-cyan);
}

.stat-card.dissatisfied {
  border-color: rgba(236, 72, 153, 0.5);
}

.stat-card.dissatisfied .stat-value {
  color: var(--neon-pink);
}

.stat-card.rate {
  border-color: rgba(168, 85, 247, 0.5);
}

.stat-card.rate .stat-value {
  color: var(--neon-purple);
}

.stat-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, currentColor, transparent);
  opacity: 0.5;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
  margin-bottom: 4px;
  text-shadow: 0 0 10px currentColor;
}

.stat-label {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

/* 筛选区域 */
.filter-section {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: rgba(17, 24, 39, 0.5);
  border-radius: 8px;
  border: 1px solid rgba(6, 182, 212, 0.2);
}

.filter-group {
  display: flex;
  gap: 12px;
}

.cyber-select {
  padding: 8px 12px;
  background: rgba(31, 41, 55, 0.8);
  border: 1px solid rgba(6, 182, 212, 0.3);
  border-radius: 6px;
  color: white;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cyber-select:hover,
.cyber-select:focus {
  border-color: var(--neon-cyan);
  box-shadow: 0 0 10px rgba(6, 182, 212, 0.2);
  outline: none;
}

.search-group {
  display: flex;
  gap: 12px;
}

.cyber-search-input {
  width: 200px;
  padding: 8px 12px;
  background: rgba(31, 41, 55, 0.8);
  border: 1px solid rgba(6, 182, 212, 0.3);
  border-radius: 6px;
  color: white;
  font-size: 0.85rem;
  transition: all 0.3s ease;
}

.cyber-search-input:focus {
  outline: none;
  border-color: var(--neon-cyan);
  box-shadow: 0 0 10px rgba(6, 182, 212, 0.2);
  width: 250px;
}

.cyber-btn-refresh {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(31, 41, 55, 0.8);
  border: 1px solid rgba(6, 182, 212, 0.3);
  border-radius: 6px;
  color: var(--neon-cyan);
  cursor: pointer;
  transition: all 0.3s ease;
}

.cyber-btn-refresh:hover {
  border-color: var(--neon-cyan);
  box-shadow: 0 0 10px rgba(6, 182, 212, 0.3);
}

.refresh-icon {
  font-size: 1.2rem;
  transition: transform 0.3s ease;
}

.refresh-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.cyber-btn-export {
  padding: 8px 16px;
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(168, 85, 247, 0.2));
  border: 1px solid rgba(6, 182, 212, 0.5);
  border-radius: 6px;
  color: var(--neon-cyan);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cyber-btn-export:hover {
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.3), rgba(168, 85, 247, 0.3));
  box-shadow: 0 0 15px rgba(6, 182, 212, 0.3);
}

/* 反馈列表 */
.feedback-list-container {
  position: relative;
  z-index: 1;
  min-height: 300px;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--text-secondary);
}

.cyber-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(6, 182, 212, 0.2);
  border-top-color: var(--neon-cyan);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 12px;
  opacity: 0.5;
}

.feedback-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.feedback-item {
  position: relative;
  display: flex;
  align-items: stretch;
  background: linear-gradient(135deg, rgba(31, 41, 55, 0.9) 0%, rgba(55, 65, 81, 0.8) 100%);
  border: 1px solid rgba(6, 182, 212, 0.2);
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
}

.feedback-item:hover {
  border-color: rgba(6, 182, 212, 0.5);
  box-shadow: 0 4px 20px rgba(6, 182, 212, 0.15);
  transform: translateX(4px);
}

.feedback-item.unread {
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.1) 0%, rgba(31, 41, 55, 0.95) 100%);
}

.feedback-item.unread .item-glow-bar {
  opacity: 1;
}

.item-glow-bar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, var(--neon-cyan), var(--neon-purple));
  opacity: 0;
  transition: opacity 0.3s ease;
}

.item-content {
  flex: 1;
  padding: 16px;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.feedback-type-badge {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.feedback-type-badge.satisfied {
  background: rgba(6, 182, 212, 0.2);
  color: var(--neon-cyan);
  border: 1px solid rgba(6, 182, 212, 0.3);
}

.feedback-type-badge.dissatisfied {
  background: rgba(236, 72, 153, 0.2);
  color: var(--neon-pink);
  border: 1px solid rgba(236, 72, 153, 0.3);
}

.feedback-time {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.item-body {
  margin-bottom: 8px;
}

.question-summary {
  margin: 0;
  font-size: 0.9rem;
  color: var(--text-primary);
  line-height: 1.5;
}

.item-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.device-info {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.issue-tags {
  display: flex;
  gap: 6px;
}

.issue-tag {
  padding: 2px 8px;
  background: rgba(168, 85, 247, 0.2);
  border: 1px solid rgba(168, 85, 247, 0.3);
  border-radius: 4px;
  font-size: 0.7rem;
  color: var(--neon-purple);
}

.issue-tag.more {
  background: rgba(6, 182, 212, 0.2);
  border-color: rgba(6, 182, 212, 0.3);
  color: var(--neon-cyan);
}

.item-actions {
  display: flex;
  align-items: center;
  padding: 0 12px;
  gap: 8px;
  border-left: 1px solid rgba(6, 182, 212, 0.1);
}

.action-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid rgba(6, 182, 212, 0.3);
  border-radius: 6px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-btn:hover {
  border-color: var(--neon-cyan);
  color: var(--neon-cyan);
  box-shadow: 0 0 10px rgba(6, 182, 212, 0.3);
}

.action-btn.mark-read:hover {
  border-color: var(--neon-cyan);
  background: rgba(6, 182, 212, 0.1);
}

/* 分页 */
.pagination {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid rgba(6, 182, 212, 0.1);
}

.cyber-page-btn {
  padding: 8px 16px;
  background: rgba(31, 41, 55, 0.8);
  border: 1px solid rgba(6, 182, 212, 0.3);
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cyber-page-btn:hover:not(:disabled) {
  border-color: var(--neon-cyan);
  color: var(--neon-cyan);
  box-shadow: 0 0 10px rgba(6, 182, 212, 0.2);
}

.cyber-page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

/* 详情弹窗 */
.detail-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.detail-modal {
  position: relative;
  width: 100%;
  max-width: 600px;
  max-height: 80vh;
  background: linear-gradient(135deg, rgba(17, 24, 39, 0.98) 0%, rgba(31, 41, 55, 0.95) 100%);
  border: 1px solid rgba(6, 182, 212, 0.5);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-glow-border {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--neon-cyan), var(--neon-purple), transparent);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid rgba(6, 182, 212, 0.2);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: var(--neon-cyan);
  text-shadow: 0 0 10px rgba(6, 182, 212, 0.3);
}

.modal-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.5);
  border-radius: 6px;
  color: var(--neon-pink);
  font-size: 1.2rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.modal-close:hover {
  background: rgba(239, 68, 68, 0.4);
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.4);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.detail-section {
  margin-bottom: 16px;
}

.section-label {
  display: block;
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.detail-type-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 600;
}

.detail-type-badge.satisfied {
  background: rgba(6, 182, 212, 0.2);
  color: var(--neon-cyan);
  border: 1px solid rgba(6, 182, 212, 0.3);
}

.detail-type-badge.dissatisfied {
  background: rgba(236, 72, 153, 0.2);
  color: var(--neon-pink);
  border: 1px solid rgba(236, 72, 153, 0.3);
}

.detail-text {
  margin: 0;
  font-size: 0.9rem;
  color: var(--text-primary);
}

.detail-box {
  padding: 12px;
  background: rgba(17, 24, 39, 0.8);
  border: 1px solid rgba(6, 182, 212, 0.2);
  border-radius: 6px;
  font-size: 0.85rem;
  color: var(--text-primary);
  line-height: 1.6;
  max-height: 150px;
  overflow-y: auto;
}

.detail-box.answer {
  background: rgba(6, 182, 212, 0.05);
  border-color: rgba(6, 182, 212, 0.3);
}

.issue-options-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.detail-issue-tag {
  padding: 4px 10px;
  background: rgba(168, 85, 247, 0.2);
  border: 1px solid rgba(168, 85, 247, 0.3);
  border-radius: 4px;
  font-size: 0.8rem;
  color: var(--neon-purple);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid rgba(6, 182, 212, 0.2);
}

.cyber-btn-secondary {
  padding: 10px 20px;
  background: transparent;
  border: 1px solid rgba(156, 163, 175, 0.5);
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cyber-btn-secondary:hover {
  border-color: var(--neon-pink);
  color: var(--neon-pink);
  box-shadow: 0 0 10px rgba(236, 72, 153, 0.2);
}

.cyber-btn-primary {
  padding: 10px 20px;
  background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple));
  border: none;
  border-radius: 6px;
  color: white;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(6, 182, 212, 0.3);
}

.cyber-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(6, 182, 212, 0.4);
}

/* 新反馈通知 */
.new-feedback-notification {
  position: fixed;
  top: 20px;
  right: 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(168, 85, 247, 0.2));
  border: 1px solid rgba(6, 182, 212, 0.5);
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 20px rgba(6, 182, 212, 0.2);
  z-index: 1001;
}

.notification-icon {
  font-size: 1.2rem;
  animation: bellRing 1s ease-in-out infinite;
}

@keyframes bellRing {
  0%, 100% { transform: rotate(0); }
  10%, 30%, 50% { transform: rotate(10deg); }
  20%, 40% { transform: rotate(-10deg); }
}

.notification-text {
  font-size: 0.9rem;
  color: white;
}

.notification-action {
  padding: 6px 12px;
  background: var(--neon-cyan);
  border: none;
  border-radius: 4px;
  color: #0f172a;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.notification-action:hover {
  background: #22d3ee;
  box-shadow: 0 0 10px rgba(6, 182, 212, 0.5);
}

.notification-close {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.notification-close:hover {
  background: rgba(239, 68, 68, 0.3);
  border-color: rgba(239, 68, 68, 0.5);
}

/* 过渡动画 */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from,
.notification-leave-to {
  opacity: 0;
  transform: translateX(100px);
}
</style>
