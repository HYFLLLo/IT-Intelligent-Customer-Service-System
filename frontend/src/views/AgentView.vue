<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Delete, Close, Loading } from '@element-plus/icons-vue'
// 引入赛博朋克样式
import '@/assets/cyberpunk-agent.css'
import FeedbackManager from '@/components/FeedbackManager.vue'

// 路由
const router = useRouter()

// 状态管理
const tickets = ref([])
const myTickets = ref([])  // 我的工单列表
const isRefreshingTickets = ref(false)  // 工单刷新状态
const isRefreshingDashboard = ref(false)  // 仪表盘刷新状态

const selectedTicket = ref(tickets.value[0])
const agentStatus = ref('online')
const pendingTicketsCount = ref(0)
const myTicketsCount = ref(0)
const todayProcessedCount = ref(0)
const qualityScore = ref(0)
const inspectedTicketsCount = ref(0)
const excellentRate = ref('0%')
const notifications = ref([])
const feedbackUnreadCount = ref(0)

// 计算属性：知识库文章数量
const knowledgeCount = computed(() => knowledgeArticles.value.length)

// 计算属性：质检报告数量
const qualityReportsCount = computed(() => qualityReports.value.length)

// 获取未读反馈数量
const fetchFeedbackUnreadCount = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/v1/feedback/unread-count')
    if (response.ok) {
      const data = await response.json()
      feedbackUnreadCount.value = data.unread_count
    }
  } catch (error) {
    console.error('获取未读反馈数量失败:', error)
  }
}

// 生成时间描述
const getTimeDescription = (dateString) => {
  if (!dateString || dateString === '刚刚') return '刚刚'
  
  const now = new Date()
  const targetTime = new Date(dateString)
  
  // 检查是否是有效日期
  if (isNaN(targetTime.getTime())) return '刚刚'
  
  const diffMs = now - targetTime
  const diffMinutes = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffMinutes < 1) {
    return '刚刚'
  } else if (diffMinutes < 60) {
    return `${diffMinutes}分钟前`
  } else if (diffHours < 24) {
    return `${diffHours}小时前`
  } else if (diffDays < 30) {
    return `${diffDays}天前`
  } else if (diffDays < 365) {
    const months = Math.floor(diffDays / 30)
    return `${months}个月前`
  } else {
    const years = Math.floor(diffDays / 365)
    return `${years}年前`
  }
}

// 格式化日期为本地字符串
const formatDateTime = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return ''
  
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 生成通知
const generateNotifications = (tickets) => {
  const newNotifications = []
  let id = 1
  
  // 为每个工单生成通知
  tickets.forEach((ticket, index) => {
    // 新工单通知 - 保存原始时间戳用于动态计算
    newNotifications.push({
      id: id++,
      content: `新工单：${ticket.title}`,
      time: getTimeDescription(ticket.created_at || new Date().toISOString()),
      rawTime: ticket.created_at || new Date().toISOString(),
      isRead: false
    })
    
    // 工单分配通知
    if (index < 3) { // 只显示最近3个工单的分配通知
      newNotifications.push({
        id: id++,
        content: `工单 #${ticket.id} 已由系统自动分配给您`,
        time: getTimeDescription(ticket.created_at || new Date().toISOString()),
        rawTime: ticket.created_at || new Date().toISOString(),
        isRead: false
      })
    }
  })
  
  // 如果没有工单，显示默认通知
  if (newNotifications.length === 0) {
    newNotifications.push({
      id: 1,
      content: '系统运行正常',
      time: '刚刚',
      rawTime: new Date().toISOString(),
      isRead: true
    })
  }
  
  notifications.value = newNotifications
}

// 更新所有通知的时间显示
const updateNotificationTimes = () => {
  notifications.value.forEach(notification => {
    if (notification.rawTime) {
      notification.time = getTimeDescription(notification.rawTime)
    }
  })
}

// 启动时间更新定时器
let timeUpdateInterval = null
const startTimeUpdate = () => {
  // 每分钟更新一次时间显示
  timeUpdateInterval = setInterval(updateNotificationTimes, 60000)
}

// 停止时间更新定时器
const stopTimeUpdate = () => {
  if (timeUpdateInterval) {
    clearInterval(timeUpdateInterval)
    timeUpdateInterval = null
  }
}

// 从localStorage加载通知已读状态
const loadNotificationsReadStatus = () => {
  try {
    const readStatus = localStorage.getItem('agent_notifications_read_status')
    if (readStatus) {
      const readIds = JSON.parse(readStatus)
      notifications.value.forEach(notification => {
        if (readIds.includes(notification.id)) {
          notification.isRead = true
        }
      })
    }
  } catch (error) {
    console.error('加载通知已读状态失败:', error)
  }
}

// 保存通知已读状态到localStorage
const saveNotificationsReadStatus = () => {
  try {
    const readIds = notifications.value
      .filter(notification => notification.isRead)
      .map(notification => notification.id)
    localStorage.setItem('agent_notifications_read_status', JSON.stringify(readIds))
  } catch (error) {
    console.error('保存通知已读状态失败:', error)
  }
}

// 标记所有通知为已读
const markAllNotificationsAsRead = () => {
  notifications.value.forEach(notification => {
    notification.isRead = true
  })
  saveNotificationsReadStatus()
  console.log('所有通知已标记为已读')
}

// 标记单个通知为已读
const markNotificationAsRead = (notificationId) => {
  const notification = notifications.value.find(n => n.id === notificationId)
  if (notification && !notification.isRead) {
    notification.isRead = true
    saveNotificationsReadStatus()
  }
}

// 计算未读通知数量
const unreadNotificationsCount = () => {
  return notifications.value.filter(notification => !notification.isRead).length
}

const showNotifications = ref(false)
const quickReplies = [
  '密码已重置，请重启验证',
  '已为您安排技术人员上门处理',
  '请尝试重启设备后再试',
  '问题已记录，我们将尽快处理'
]// AI回复建议（切换工单时从工单对象中获取，保持各自状态）
const aiSuggestions = ref([])
const isLoading = ref(false)
const showLoadingModal = ref(false)  // 赛博朋克风格加载弹窗
const loadingModalText = ref('正在处理...')  // 加载弹窗文本
const knowledgeItems = ref([])
const extractedFields = ref([])
const activeNavItem = ref('dashboard')
const currentView = ref('tickets')
const selectedArticle = ref(null)
const replyContent = ref('')
const isDragging = ref(false)

// 质检报告列表
const qualityReports = ref([])
const isRefreshingQuality = ref(false)  // 质检报告刷新状态

const selectedQualityReport = ref(null)

// 选择质检报告
const selectQualityReport = (report) => {
  selectedQualityReport.value = report
}

// 获取质检报告列表
const fetchQualityReports = async () => {
  console.log('开始刷新质检报告列表...')
  isRefreshingQuality.value = true
  try {
    const response = await fetch('http://localhost:8000/api/v1/agent/quality-reports', {
      headers: {
        'Accept': 'application/json; charset=utf-8'
      }
    })
    console.log('质检报告 API 响应状态:', response.status)
    if (response.ok) {
      // 确保使用正确的编码解析响应
      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let result = ''
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        result += decoder.decode(value, { stream: true })
      }
      
      result += decoder.decode()
      console.log('Raw quality reports response text:', result)
      const data = JSON.parse(result)
      
      // 转换后端数据格式为前端所需格式
      qualityReports.value = data.map(report => ({
        id: report.id,
        title: report.title,
        content: report.content,
        response: report.response,
        score: report.score,
        user: report.user || '用户',
        department: report.department || '未知部门',
        createdAt: report.created_at || new Date().toISOString()
      }))
    } else {
      console.error('获取质检报告列表失败:', response.statusText)
      // 如果获取质检报告失败，使用模拟数据
      qualityReports.value = [
        {
          id: 1,
          title: '业务系统登錄时出现错误',
          content: '用户无法登錄业务系统，提示密码错误，但用户确认密码正确。',
          response: '已为您重置密码，请使用新密码登錄系统。',
          score: '4.0',
          user: '用户',
          department: '未知部门',
          createdAt: new Date().toISOString()
        },
        {
          id: 2,
          title: '网络连接不稳定',
          content: '用户反馈网络连接不稳定，经常断开。',
          response: '已为您检查网络连接，发现是路由器故障，建议更换路由器。',
          score: '4.5',
          user: '用户',
          department: '未知部门',
          createdAt: new Date().toISOString()
        }
      ]
    }
  } catch (error) {
    console.error('获取质检报告列表时发生错误:', error)
    // 如果获取质检报告失败，使用模拟数据
    qualityReports.value = [
      {
        id: 1,
        title: '业务系统登錄时出现错误',
        content: '用户无法登錄业务系统，提示密码错误，但用户确认密码正确。',
        response: '已为您重置密码，请使用新密码登錄系统。',
        score: '4.0',
        user: '用户',
        department: '未知部门',
        createdAt: new Date().toISOString()
      },
      {
        id: 2,
        title: '网络连接不稳定',
        content: '用户反馈网络连接不稳定，经常断开。',
        response: '已为您检查网络连接，发现是路由器故障，建议更换路由器。',
        score: '4.5',
        user: '用户',
        department: '未知部门',
        createdAt: new Date().toISOString()
      }
    ]
  } finally {
    isRefreshingQuality.value = false
    console.log('质检报告列表刷新完成')
  }
}

// 知识库文章数据
const knowledgeArticles = ref([
  {
    title: 'MacBook WiFi 连接问题排查指南',
    content: '## MacBook WiFi 连接问题排查指南\n\n### 常见原因\n1. **网络信号弱**：距离路由器太远或有障碍物\n2. **DNS配置错误**：DNS服务器设置不当\n3. **网络驱动问题**：无线网卡驱动需要更新\n4. **系统设置问题**：网络偏好设置异常\n\n### 解决方案\n1. **重启网络设备**：重启路由器和MacBook\n2. **重置网络设置**：\n   - 打开系统偏好设置 → 网络\n   - 选择WiFi → 高级 → TCP/IP\n   - 点击"续订DHCP租约"\n3. **更新系统**：确保MacOS系统为最新版本\n4. **检查DNS设置**：使用Google DNS (8.8.8.8)\n\n### 注意事项\n- 确保路由器固件为最新版本\n- 检查是否有防火墙阻止网络连接\n- 尝试在安全模式下测试网络连接',
    category: '网络问题',
    updatedTime: '2小时前'
  },
  {
    title: 'Office 365 登录失败解决方法',
    content: '## Office 365 登录失败解决方法\n\n### 常见原因\n1. **密码错误**：输入的密码不正确\n2. **账户锁定**：多次密码错误导致账户被锁定\n3. **网络问题**：网络连接不稳定\n4. **Office 365服务故障**：微软服务器问题\n\n### 解决方案\n1. **重置密码**：通过Microsoft账户页面重置密码\n2. **检查网络连接**：确保网络连接正常\n3. **清除浏览器缓存**：清除浏览器缓存和Cookie\n4. **使用Microsoft支持和恢复助手**：运行诊断工具\n\n### 注意事项\n- 检查账户是否到期\n- 确认是否有多重身份验证要求\n- 联系IT管理员确认账户状态',
    category: '软件问题',
    updatedTime: '1天前'
  },
  {
    title: '打印机常见故障排查',
    content: '## 打印机常见故障排查\n\n### 常见问题\n1. **打印机卡纸**：纸张卡在打印机内部\n2. **打印机不打印**：发送打印任务后无反应\n3. **打印质量差**：打印内容模糊或有条纹\n4. **打印机离线**：无法连接到打印机\n\n### 解决方案\n1. **卡纸问题**：\n   - 关闭打印机电源\n   - 打开打印机盖，小心取出卡纸\n   - 检查是否有碎纸残留\n   - 重新启动打印机\n\n2. **不打印问题**：\n   - 检查打印机电源和连接\n   - 确认打印机为默认打印机\n   - 清除打印队列\n   - 重启打印机和电脑\n\n3. **打印质量问题**：\n   - 检查墨盒或硒鼓\n   - 清洁打印头\n   - 调整打印质量设置\n\n4. **离线问题**：\n   - 检查网络连接\n   - 重启打印机网络设置\n   - 重新安装打印机驱动',
    category: '硬件问题',
    updatedTime: '3天前'
  }
])

const selectArticle = (article) => {
  selectedArticle.value = article
}

// 获取工单列表
// 获取工单统计数据
const fetchTicketStatistics = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/v1/agent/tickets/statistics', {
      headers: {
        'Accept': 'application/json; charset=utf-8'
      }
    })
    if (response.ok) {
      const data = await response.json()
      console.log('工单统计数据:', data)
      
      // 更新今日已处理工单数量（实时计算当前客服完成的）
      todayProcessedCount.value = data.today_processed || 0
      
      // 我的工单数量由 fetchTickets 更新（tickets数组的长度）
      // 这里不再从统计数据更新
      
      return data
    } else {
      console.error('获取工单统计失败:', await response.text())
      return null
    }
  } catch (error) {
    console.error('获取工单统计时发生错误:', error)
    return null
  }
}

// 获取质检统计数据
const fetchQualityStatistics = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/v1/agent/quality/statistics', {
      headers: {
        'Accept': 'application/json; charset=utf-8'
      }
    })
    if (response.ok) {
      const data = await response.json()
      console.log('质检统计数据:', data)
      
      // 更新质检评分
      qualityScore.value = data.average_score ? data.average_score.toFixed(1) : '0.0'
      
      // 更新已质检工单数量
      inspectedTicketsCount.value = data.total_checked || 0
      
      // 更新优秀率
      excellentRate.value = data.excellent_rate ? `${data.excellent_rate}%` : '0%'
      
      return data
    } else {
      console.error('获取质检统计失败:', await response.text())
      return null
    }
  } catch (error) {
    console.error('获取质检统计时发生错误:', error)
    return null
  }
}

// 加载状态
const isLoadingTickets = ref(false)
const ticketsError = ref(null)

const fetchTickets = async () => {
  console.log('开始刷新工单列表...')
  isRefreshingTickets.value = true
  ticketsError.value = null
  
  try {
    const response = await fetch('http://localhost:8000/api/v1/agent/tickets/pending', {
      headers: {
        'Accept': 'application/json; charset=utf-8'
      }
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    // 确保使用正确的编码解析响应
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let result = ''
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      result += decoder.decode(value, { stream: true })
    }
    
    result += decoder.decode()
    console.log('Raw response text:', result)
    
    let data
    try {
      data = JSON.parse(result)
    } catch (parseError) {
      throw new Error('解析响应数据失败: ' + parseError.message)
    }
    
    // 确保数据是数组
    if (!Array.isArray(data)) {
      console.warn('返回的数据不是数组，尝试转换:', data)
      data = data.tickets || data.data || []
    }
    
    // 转换后端数据格式为前端所需格式
    const formattedTickets = data.map(ticket => {
      // 计算提交时间
      const now = new Date()
      const createdTime = new Date(ticket.created_at || ticket.createdAt || new Date())
      const diffMinutes = Math.floor((now - createdTime) / (1000 * 60))
      let submittedTime
      if (diffMinutes < 1) {
        submittedTime = '刚刚'
      } else if (diffMinutes < 60) {
        submittedTime = `${diffMinutes}分钟前`
      } else if (diffMinutes < 1440) {
        submittedTime = `${Math.floor(diffMinutes / 60)}小时前`
      } else {
        submittedTime = `${Math.floor(diffMinutes / 1440)}天前`
      }
      
      // 从工单描述中提取用户姓名和部门信息
      let user = ticket.user_name || ticket.userName || '未知用户'
      let department = ticket.department || '未知部门'
      
      // 检查工单描述中是否包含用户和部门信息
      if (ticket.content && (user === '未知用户' || department === '未知部门')) {
        const userMatch = ticket.content.match(/用户[:：]\s*(.+?)(?:\s|$)/)
        const deptMatch = ticket.content.match(/部门[:：]\s*(.+?)(?:\s|$)/)
        
        if (userMatch && userMatch[1] && user === '未知用户') {
          user = userMatch[1].trim()
        }
        if (deptMatch && deptMatch[1] && department === '未知部门') {
          department = deptMatch[1].trim()
        }
      }
      
      return {
        id: ticket.id,
        title: ticket.title,
        content: ticket.content,
        priority: ticket.priority || 'MEDIUM',
        user: user,
        department: department,
        category: ticket.category || '未分类',
        submittedTime: submittedTime,
        isSelected: false
      }
    })
    
    // 更新工单列表
    tickets.value = formattedTickets
    
    // 更新待处理工单数量（关键修复）
    pendingTicketsCount.value = formattedTickets.length
    console.log('✅ 待处理工单数量已更新:', pendingTicketsCount.value)
    
    // 如果有工单，默认选择第一个
    if (formattedTickets.length > 0 && !selectedTicket.value) {
      selectedTicket.value = formattedTickets[0]
      selectedTicket.value.isSelected = true
    }
    
    // 生成基于实际工单数据的通知
    generateNotifications(formattedTickets)
    
    // 加载已读状态
    loadNotificationsReadStatus()
    
    console.log('✅ 已更新工单列表，共', formattedTickets.length, '个待处理工单')
    console.log('✅ 通知已更新，共', notifications.value.length, '条')
    
  } catch (error) {
    console.error('❌ 获取工单列表时发生错误:', error)
    ticketsError.value = error.message
  } finally {
    isRefreshingTickets.value = false
    console.log('工单列表刷新完成')
  }
}

// 获取我的工单列表（分配给当前客服的工单）
const fetchMyTickets = async () => {
  console.log('开始刷新我的工单列表...')
  isRefreshingTickets.value = true
  try {
    const response = await fetch('http://localhost:8000/api/v1/agent/tickets', {
      headers: {
        'Accept': 'application/json; charset=utf-8'
      }
    })
    console.log('我的工单 API 响应状态:', response.status)
    if (response.ok) {
      // 确保使用正确的编码解析响应
      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let result = ''
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        result += decoder.decode(value, { stream: true })
      }
      
      result += decoder.decode()
      console.log('Raw my tickets response:', result)
      const data = JSON.parse(result)
      
      // 转换后端数据格式为前端所需格式
      const formattedTickets = data.map(ticket => {
        // 计算提交时间
        const now = new Date()
        const createdTime = new Date(ticket.created_at)
        const diffMinutes = Math.floor((now - createdTime) / (1000 * 60))
        let submittedTime
        if (diffMinutes < 1) {
          submittedTime = '刚刚'
        } else if (diffMinutes < 60) {
          submittedTime = `${diffMinutes}分钟前`
        } else if (diffMinutes < 1440) {
          submittedTime = `${Math.floor(diffMinutes / 60)}小时前`
        } else {
          submittedTime = `${Math.floor(diffMinutes / 1440)}天前`
        }
        
        // 从content中提取用户和部门信息
        let user = '未知用户'
        let department = '未知部门'
        const content = ticket.content || ''
        
        // 尝试从内容中提取用户信息
        const userMatch = content.match(/用户[:：]\s*(.+?)(?:\s|$)/)
        const deptMatch = content.match(/部门[:：]\s*(.+?)(?:\s|$)/)
        
        if (userMatch && userMatch[1]) {
          user = userMatch[1]
        }
        if (deptMatch && deptMatch[1]) {
          department = deptMatch[1]
        }
        
        return {
          id: ticket.id,
          title: ticket.title,
          content: ticket.content,
          priority: ticket.priority,
          user: user,
          department: department,
          category: ticket.category || '未分类',
          submittedTime: submittedTime,
          isSelected: false
        }
      })
      
      // 更新我的工单列表
      myTickets.value = formattedTickets
      
      // 更新我的工单数量（与"我的工单"页面显示的工单数量一致）
      myTicketsCount.value = formattedTickets.length
      
      console.log('已更新我的工单列表，共', formattedTickets.length, '个工单')
    } else {
      console.error('获取我的工单列表失败:', await response.text())
    }
  } catch (error) {
    console.error('获取我的工单列表时发生错误:', error)
  } finally {
    isRefreshingTickets.value = false
    console.log('我的工单列表刷新完成')
  }
}

// 刷新所有数据（包括统计数据）
const refreshAllData = async () => {
  console.log('开始刷新所有数据...')
  isRefreshingDashboard.value = true
  try {
    await Promise.all([
      fetchTickets(),
      fetchMyTickets(),
      fetchTicketStatistics(),
      fetchQualityStatistics()
    ])
    
    // 确保待处理工单数量与 tickets 数组同步
    pendingTicketsCount.value = tickets.value.length
    
    console.log('所有数据刷新完成，待处理工单:', pendingTicketsCount.value)
  } catch (error) {
    console.error('刷新数据时发生错误:', error)
  } finally {
    isRefreshingDashboard.value = false
    console.log('仪表盘数据刷新完成')
  }
}

const selectNavItem = (item) => {
  activeNavItem.value = item

  // 根据选择的导航项更新当前视图
  switch (item) {
    case 'dashboard':
      currentView.value = 'dashboard'
      console.log('切换到仪表盘')
      break
    case 'tickets':
      currentView.value = 'tickets'
      console.log('切换到待处理工单')
      break
    case 'my-tickets':
      currentView.value = 'my-tickets'
      console.log('切换到我的工单')
      break
    case 'knowledge':
      currentView.value = 'knowledge'
      console.log('切换到知识库')
      break
    case 'quality':
      currentView.value = 'quality'
      console.log('切换到质检报告')
      break
    case 'feedback':
      currentView.value = 'feedback'
      console.log('切换到反馈收集')
      break
  }
}

// 导航到埋点收集页面
const navigateToAnalytics = () => {
  router.push('/agent/analytics')
}

// 方法
const getAIReplySuggestions = async (ticketId) => {
  isLoading.value = true
  try {
    const response = await fetch('http://localhost:8000/api/v1/agent/tickets/ai-suggestion', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        ticket_id: ticketId
      })
    })
    
    if (response.ok) {
      const data = await response.json()
      aiSuggestions.value = data.suggestions
    } else {
      aiSuggestions.value = []
    }
  } catch (error) {
    aiSuggestions.value = []
  } finally {
    isLoading.value = false
  }
}

// 生成智能回复
const generateAiSuggestion = async () => {
  if (!selectedTicket.value) return
  
  isLoading.value = true
  aiSuggestions.value = []
  
  try {
    console.log('正在调用后端API生成智能回复...')
    console.log('工单ID:', selectedTicket.value.id)
    
    // 调用后端API获取AI回复建议
    const response = await fetch('http://localhost:8000/api/v1/agent/tickets/ai-suggestion', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json; charset=utf-8'
      },
      body: JSON.stringify({
        ticket_id: selectedTicket.value.id,
        user_message: '' // 暂时为空，后续可以从对话历史中获取
      })
    })
    
    if (response.ok) {
      const data = await response.json()
      
      // 添加模拟延迟，让用户感觉是LLM在生成回复
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      aiSuggestions.value = data.suggestions
      knowledgeItems.value = data.knowledge_items || []
      extractedFields.value = data.extracted_fields || []
      console.log('AI智能回复生成成功:', data.suggestions)
      console.log('相关知识片段:', data.knowledge_items)
      console.log('字段提取结果:', data.extracted_fields)
    } else {
      console.error('生成智能回复失败，后端返回错误:', response.status)
      
      // 添加模拟延迟，让用户感觉是在处理
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      // 如果后端API调用失败，使用备用方案（模拟数据）
      console.log('后端API调用失败，使用备用方案生成回复...')
      
      // 根据工单内容生成不同的回复 - 只返回一个高质量回复
      let suggestions = []
      if (selectedTicket.value.title.includes('网络') || selectedTicket.value.title.includes('WiFi')) {
        suggestions = [
          '尊敬的用户，针对您的网络连接问题，建议您重启路由器和设备，检查WiFi密码是否正确，确保设备在信号覆盖范围内。如问题仍存在，请提供更多网络环境信息。'
        ]
      } else if (selectedTicket.value.title.includes('电脑') || selectedTicket.value.title.includes('开机')) {
        suggestions = [
          '尊敬的用户，针对您的电脑无法开机问题，建议您检查电源连接是否正常，尝试长按电源键10秒强制关机后再开机，如问题仍存在，可能需要专业技术人员检测。'
        ]
      } else {
        suggestions = [
          '尊敬的用户，关于您的问题，我们已经收到并正在处理。我们会尽快为您提供解决方案。'
        ]
      }
      
      aiSuggestions.value = suggestions
      console.log('备用方案生成智能回复成功:', suggestions)
    }
  } catch (error) {
    console.error('生成智能回复失败:', error)
    
    // 添加模拟延迟，让用户感觉是在处理
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    // 如果发生网络错误，使用备用方案 - 只返回一个高质量回复
    const suggestions = [
      '尊敬的用户，关于您的问题，我们已经收到并正在处理。我们会尽快为您提供解决方案。'
    ]
    aiSuggestions.value = suggestions
    console.log('网络错误，使用备用方案生成回复:', suggestions)
  } finally {
    isLoading.value = false
    
    // 将生成的AI回复保存到当前工单对象
    if (selectedTicket.value) {
      selectedTicket.value.aiSuggestions = [...aiSuggestions.value]
      selectedTicket.value.extractedFields = [...extractedFields.value]
      selectedTicket.value.knowledgeItems = [...knowledgeItems.value]
    }
  }
}

// 选择预置回答
const selectQuickReply = (reply) => {
  replyContent.value = reply
  console.log('已选择预置回答:', reply)
}

const selectTicket = (ticket) => {
  // 保存当前工单的AI状态到工单对象
  if (selectedTicket.value) {
    selectedTicket.value.aiSuggestions = [...aiSuggestions.value]
    selectedTicket.value.extractedFields = [...extractedFields.value]
    selectedTicket.value.knowledgeItems = [...knowledgeItems.value]
  }
  
  tickets.value.forEach(t => t.isSelected = t.id === ticket.id)
  selectedTicket.value = ticket
  
  // 加载新工单的AI状态（如果有的话）
  aiSuggestions.value = ticket.aiSuggestions || []
  extractedFields.value = ticket.extractedFields || []
  knowledgeItems.value = ticket.knowledgeItems || []
}

const toggleNotifications = () => {
  showNotifications.value = !showNotifications.value
}

const changeStatus = (status) => {
  agentStatus.value = status
}

const sendAndClose = async () => {
  if (!selectedTicket.value) return
  
  // 显示赛博朋克风格加载弹窗
  loadingModalText.value = '正在发送回复并关闭工单...'
  showLoadingModal.value = true
  isLoading.value = true
  
  try {
    console.log('开始关闭工单:', selectedTicket.value.id)
    console.log('回复内容:', replyContent.value)
    
    // 调用后端API关闭工单并发送回复
    const url = `http://localhost:8000/api/v1/agent/tickets/${selectedTicket.value.id}/close`
    console.log('API URL:', url)
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json; charset=utf-8'
      },
      body: JSON.stringify({
        reply_content: replyContent.value
      })
    })
    
    console.log('API响应状态:', response.status, response.statusText)
    
    if (response.ok) {
      const data = await response.json()
      console.log('API响应数据:', data)
      
      // 保存当前工单信息，因为后面会清空selectedTicket
      const closedTicket = {
        id: selectedTicket.value.id,
        title: selectedTicket.value.title,
        content: selectedTicket.value.content,
        user: selectedTicket.value.user,
        department: selectedTicket.value.department
      }
      
      // 计算质检评分
      const scoreResult = calculateQualityScore(closedTicket.content, replyContent.value)
      
      // 生成质检报告
      const qualityReport = {
        id: Date.now(),
        ticketId: closedTicket.id,
        user: closedTicket.user,
        department: closedTicket.department,
        title: closedTicket.title,
        content: closedTicket.content,
        response: replyContent.value,
        createdAt: new Date().toISOString(),
        score: scoreResult.total,
        scoreDetails: scoreResult.items
      }
      
      // 添加到质检报告列表
      qualityReports.value.unshift(qualityReport)
      console.log('生成质检报告:', qualityReport)
      
      // 显示成功消息（在清空selectedTicket之前）
      alert(`✅ 工单已成功关闭：${closedTicket.title}\n工单ID: ${data.ticket_id}\n\n质检报告已生成，您可以在质检报告模块查看详细信息。`)
      console.log('工单关闭成功:', closedTicket.title)
      
      // 从列表中移除工单
      tickets.value = tickets.value.filter(t => t.id !== closedTicket.id)
      
      // 更新待处理工单数量（使用数组长度确保准确性）
      pendingTicketsCount.value = tickets.value.length
      console.log('✅ 工单关闭后，待处理工单数量更新为:', pendingTicketsCount.value)
      
      if (tickets.value.length > 0) {
        await selectTicket(tickets.value[0])
      } else {
        selectedTicket.value = null
      }
      
      // 清空回复内容
      replyContent.value = ''
      
      // 更新今日已处理工单数量
      if (typeof updateDashboardStats === 'function') {
        updateDashboardStats()
      }
      
      // 从后端获取最新的质检报告列表
      await fetchQualityReports()
      console.log('获取最新质检报告列表成功')
    } else {
      const errorData = await response.json().catch(() => ({}))
      console.error('关闭工单失败:', errorData)
      alert(`❌ 关闭工单失败：${errorData.detail || '请稍后再试'}`)
    }
  } catch (error) {
    console.error('关闭工单失败:', error)
    // 显示更详细的错误信息
    alert(`❌ 网络连接失败，请检查您的网络设置\n错误信息: ${error.message}`)
  } finally {
    // 关闭加载弹窗
    showLoadingModal.value = false
    isLoading.value = false
  }
}

const transferTicket = () => {
  // 模拟转交工单
  alert('转功能开发中...')
}

const uploadAttachment = () => {
  // 创建文件选择输入
  const fileInput = document.createElement('input')
  fileInput.type = 'file'
  fileInput.multiple = true
  fileInput.accept = 'image/*,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  
  fileInput.onchange = async (event) => {
    const files = event.target.files
    if (files.length === 0) return
    
    console.log('选择的文件:', files)
    
    // 模拟文件上传
    try {
      // 实际项目中应该调用真实的上传API
      console.log('正在上传文件...')
      
      // 模拟上传延迟
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      // 显示上传成功提示
      alert(`成功上传 ${files.length} 个文件`)
      console.log('文件上传成功')
      
      // 这里可以添加已上传附件的显示逻辑
      // 例如：attachments.value = [...attachments.value, ...files]
    } catch (error) {
      console.error('文件上传失败:', error)
      alert('文件上传失败，请稍后重试')
    }
  }
  
  // 触发文件选择
  fileInput.click()
}

// 质检预览相关状态
const showQualityPreview = ref(false)
const qualityPreviewData = ref({
  score: 0,
  user: '',
  department: '',
  content: '',
  response: ''
})

const previewQualityCheck = () => {
  if (!selectedTicket.value) return
  
  // 计算质检评分
  const scoreResult = calculateQualityScore(selectedTicket.value.content, replyContent.value)
  
  // 填充质检预览数据
  qualityPreviewData.value = {
    score: scoreResult.total,
    scoreDetails: scoreResult.items,
    user: selectedTicket.value.user,
    department: selectedTicket.value.department,
    content: selectedTicket.value.content,
    response: replyContent.value
  }
  
  // 显示质检预览卡片
  showQualityPreview.value = true
}

// 计算平均评分
const calculateAverageScore = () => {
  if (qualityReports.value.length === 0) return '0.0'
  const sum = qualityReports.value.reduce((acc, report) => acc + parseFloat(report.score), 0)
  return (sum / qualityReports.value.length).toFixed(1)
}

// 计算优秀率
const calculateExcellentRate = () => {
  if (qualityReports.value.length === 0) return '0%'
  const excellentCount = qualityReports.value.filter(report => parseFloat(report.score) >= 4.5).length
  return Math.round((excellentCount / qualityReports.value.length) * 100) + '%'
}

// 格式化日期
const formatDate = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  
  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`
  return date.toLocaleDateString('zh-CN')
}

// 计算质检评分（返回详细评分项）
const calculateQualityScore = (content, response) => {
  // 基础评分
  let baseScore = 3.0
  
  // 1. 回复内容长度评分（0-0.5分）
  const responseLength = response.length
  let lengthScore = 0
  if (responseLength > 500) lengthScore = 0.5
  else if (responseLength > 300) lengthScore = 0.4
  else if (responseLength > 200) lengthScore = 0.3
  else if (responseLength > 100) lengthScore = 0.2
  else if (responseLength > 50) lengthScore = 0.1
  baseScore += lengthScore
  
  // 2. 问题覆盖率评分（0-0.5分）
  const contentWords = content.toLowerCase().split(/\s+/).filter(word => word.length > 2)
  const responseWords = response.toLowerCase().split(/\s+/).filter(word => word.length > 2)
  const matchedWords = contentWords.filter(word => responseWords.includes(word))
  const coverageRate = contentWords.length > 0 ? matchedWords.length / contentWords.length : 0
  const coverageScore = coverageRate * 0.5
  baseScore += coverageScore
  
  // 3. 解决方案完整性评分（0-0.5分）
  const solutionKeywords = ['建议', '解决', '步骤', '方法', '措施', '检查', '确认', '验证', '测试']
  const solutionWords = solutionKeywords.filter(keyword => response.includes(keyword))
  const solutionScore = Math.min(solutionWords.length / 3, 0.5)
  baseScore += solutionScore
  
  // 4. 专业性评分（0-0.5分）
  const professionalKeywords = ['专业', '技术', '系统', '配置', '设置', '驱动', '更新', '重启', '升级', '优化']
  const professionalWords = professionalKeywords.filter(keyword => response.includes(keyword))
  const professionalScore = Math.min(professionalWords.length / 3, 0.5)
  baseScore += professionalScore
  
  // 5. 服务态度评分（0-0.5分）
  const attitudeKeywords = ['感谢', '抱歉', '理解', '支持', '帮助', '随时', '欢迎', '咨询', '服务', '满意']
  const attitudeWords = attitudeKeywords.filter(keyword => response.includes(keyword))
  const attitudeScore = Math.min(attitudeWords.length / 3, 0.5)
  baseScore += attitudeScore
  
  // 确保评分在4.0-5.0之间
  const finalScore = Math.max(4.0, Math.min(5.0, baseScore))
  
  // 返回详细评分数据
  return {
    total: finalScore.toFixed(1),
    items: [
      { name: '回复内容长度', score: lengthScore, maxScore: 0.5, percentage: (lengthScore / 0.5 * 100).toFixed(0) },
      { name: '问题覆盖率', score: coverageScore, maxScore: 0.5, percentage: (coverageRate * 100).toFixed(0) },
      { name: '解决方案完整性', score: solutionScore, maxScore: 0.5, percentage: (solutionScore / 0.5 * 100).toFixed(0) },
      { name: '专业性', score: professionalScore, maxScore: 0.5, percentage: (professionalScore / 0.5 * 100).toFixed(0) },
      { name: '服务态度', score: attitudeScore, maxScore: 0.5, percentage: (attitudeScore / 0.5 * 100).toFixed(0) }
    ]
  }
}

// 从后端获取知识库文章
const fetchKnowledgeArticles = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/v1/admin/knowledge', {
      headers: {
        'Accept': 'application/json; charset=utf-8'
      }
    })
    if (response.ok) {
      // 确保使用正确的编码解析响应
      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let result = ''
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        result += decoder.decode(value, { stream: true })
      }
      
      result += decoder.decode()
      console.log('Raw knowledge response text:', result)
      const data = JSON.parse(result)
      
      // 转换后端数据格式为前端所需格式
      knowledgeArticles.value = data.map(item => ({
        id: item.id,
        title: item.title,
        content: item.content,
        category: item.category,
        updatedTime: item.updated_at ? new Date(item.updated_at).toLocaleString() : new Date().toLocaleString()
      }))
    } else {
      console.error('获取知识库文章失败:', response.statusText)
    }
  } catch (error) {
    console.error('获取知识库文章时发生错误:', error)
  }
}

// 删除知识库相关状态
const showDeleteKnowledgeModal = ref(false)
const knowledgeToDelete = ref(null)
const isDeletingKnowledge = ref(false)
const deleteConfirmText = ref('')

// 打开删除知识库确认弹窗
const openDeleteKnowledgeModal = (article, event) => {
  event.stopPropagation()
  knowledgeToDelete.value = article
  deleteConfirmText.value = ''
  showDeleteKnowledgeModal.value = true
}

// 关闭删除知识库确认弹窗
const closeDeleteKnowledgeModal = () => {
  showDeleteKnowledgeModal.value = false
  knowledgeToDelete.value = null
  deleteConfirmText.value = ''
}

// 确认删除知识库
const confirmDeleteKnowledge = async () => {
  if (!knowledgeToDelete.value) return

  isDeletingKnowledge.value = true
  try {
    const response = await fetch(`http://localhost:8000/api/v1/admin/knowledge/${knowledgeToDelete.value.id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      // 从列表中移除
      knowledgeArticles.value = knowledgeArticles.value.filter(
        article => article.id !== knowledgeToDelete.value.id
      )
      console.log('知识库文章已删除:', knowledgeToDelete.value.title)
    } else if (response.status === 404) {
      alert('删除失败: 知识库文章不存在')
    } else {
      const errorData = await response.json().catch(() => ({}))
      console.error('删除知识库文章失败:', response.status, errorData)
      alert(`删除失败: ${errorData.detail || response.statusText || '未知错误'}`)
    }
  } catch (error) {
    console.error('删除知识库文章时发生错误:', error)
    alert('删除失败，请检查网络连接或稍后重试')
  } finally {
    isDeletingKnowledge.value = false
    closeDeleteKnowledgeModal()
  }
}

// 处理文件上传
const processFiles = async (files) => {
  if (files.length === 0) return
  
  console.log('处理知识库文件:', files)
  
  try {
    console.log('正在上传知识库文件...')
    
    // 处理每个文件
    const uploadedFiles = []
    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      console.log('处理文件:', file.name, file.type)
      let content = ''
      
      try {
        // 根据文件类型处理内容
        if (file.type === 'text/plain' || file.type === 'text/markdown' || file.name.endsWith('.md')) {
          // 读取文本文件内容
          console.log('读取文本文件内容:', file.name)
          content = await readTextFile(file)
          console.log('文件内容读取成功:', file.name, content.length, '字符')
        } else {
          // 对于其他文件类型，使用友好的占位符
          console.log('使用占位符内容:', file.name)
          content = `## ${file.name}\n\n### 文件信息\n- **文件类型**: ${file.type}\n- **文件大小**: ${(file.size / 1024).toFixed(2)} KB\n\n### 内容预览\n> 提示：这是一个${getFileTypeDescription(file.type)}文件，无法在浏览器中直接预览完整内容。\n> 建议：\n> 1. 下载原始文件查看详细内容\n> 2. 手动编辑此知识库文章，添加关键信息\n> 3. 或者将文件转换为Markdown格式后重新上传\n\n### 上传时间\n${new Date().toLocaleString()}`
        }
        
        // 调用后端API上传知识库
        console.log('调用后端API上传知识库:', file.name)
        const response = await fetch('http://localhost:8000/api/v1/admin/knowledge', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json; charset=utf-8'
          },
          body: JSON.stringify({
            title: file.name,
            content: content,
            category: '未分类',
            tags: [],
            is_active: true
          })
        })
        
        console.log('API响应状态:', response.status, response.statusText)
        
        if (response.ok) {
          uploadedFiles.push(file.name)
          console.log('已上传知识库文章:', file.name)
        } else {
          // 只读取响应体一次
          const errorText = await response.text()
          console.error('上传知识库文件失败:', errorText)
          alert(`上传 ${file.name} 失败: ${errorText}`)
        }
      } catch (fileError) {
        console.error('处理文件时发生错误:', file.name, fileError)
        alert(`处理 ${file.name} 时发生错误: ${fileError.message}`)
      }
    }
    
    if (uploadedFiles.length > 0) {
      // 重新从后端获取知识库数据，确保数据一致性
      console.log('重新从后端获取知识库数据')
      await fetchKnowledgeArticles()
      
      // 显示上传成功提示
      alert(`成功上传 ${uploadedFiles.length} 个知识库文件，并已添加到知识库列表：\n${uploadedFiles.join('\n')}`)
      console.log('知识库文件上传成功')
    }
    
  } catch (error) {
    console.error('知识库文件上传失败:', error)
    alert('知识库文件上传失败，请稍后重试: ' + error.message)
  }
}

// 上传知识库文件
const uploadKnowledge = () => {
  // 创建文件选择输入
  const fileInput = document.createElement('input')
  fileInput.type = 'file'
  fileInput.multiple = true
  fileInput.accept = 'application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain,text/markdown,.md'
  
  fileInput.onchange = async (event) => {
    const files = event.target.files
    await processFiles(files)
  }
  
  // 触发文件选择
  fileInput.click()
}

// 处理拖拽上传
const handleDragDrop = async (event) => {
  isDragging.value = false
  const files = event.dataTransfer.files
  await processFiles(files)
}

// 处理拖拽进入
const handleDragEnter = (event) => {
  event.preventDefault()
  isDragging.value = true
}

// 处理拖拽离开
const handleDragLeave = (event) => {
  event.preventDefault()
  isDragging.value = false
}

// 读取文本文件内容
const readTextFile = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (event) => {
      resolve(event.target.result)
    }
    reader.onerror = (error) => {
      reject(error)
    }
    reader.readAsText(file, 'utf-8')
  })
}

// 获取文件类型描述
const getFileTypeDescription = (fileType) => {
  if (fileType.includes('pdf')) return 'PDF'
  if (fileType.includes('word') || fileType.includes('docx')) return 'Word'
  if (fileType.includes('excel') || fileType.includes('xlsx')) return 'Excel'
  if (fileType.includes('powerpoint') || fileType.includes('ppt')) return 'PowerPoint'
  return '文档'
}

const adoptSuggestion = () => {
  if (aiSuggestions.value.length > 0) {
    // 将AI建议填充到回复框
    replyContent.value = aiSuggestions.value[0]
    console.log('已采纳AI建议:', aiSuggestions.value[0])
    alert('已采纳AI建议到回复框')
  }
}

// 更新仪表盘统计数据
const updateDashboardStats = () => {
  // 模拟更新今日已处理工单数量
  // 实际项目中应该从后端获取最新数据
  console.log('更新仪表盘统计数据...')
  
  // 增加今日已处理工单数量
  todayProcessedCount.value++
  console.log('今日已处理工单数量更新为:', todayProcessedCount.value)
  
  // 显示成功提示
  console.log('仪表盘统计数据已更新')
}

// 获取优先级颜色
const getPriorityColor = (priority) => {
  switch (priority) {
    case 'urgent':
    case 'emergency':
      return 'var(--priority-emergency)'
    case 'high':
      return 'var(--priority-high)'
    case 'medium':
      return 'var(--priority-medium)'
    case 'low':
      return 'var(--priority-low)'
    default:
      return 'var(--priority-medium)'
  }
}

// 根据评分获取样式类名
const getScoreClass = (score) => {
  const numScore = parseFloat(score)
  if (numScore >= 4.5) return 'excellent'
  if (numScore >= 4.0) return 'good'
  if (numScore >= 3.0) return 'average'
  return 'poor'
}

// 获取优先级文本
const getPriorityText = (priority) => {
  switch (priority) {
    case 'urgent':
    case 'emergency':
      return '紧急'
    case 'high':
      return '高'
    case 'medium':
      return '中'
    case 'low':
      return '低'
    default:
      return '中'
  }
}

// 实时更新相关
let pollingInterval = null
let fastPollingInterval = null

// 初始化
onMounted(() => {
  // 从后端获取知识库文章
  fetchKnowledgeArticles()

  // 初始加载所有数据（包括工单列表和统计数据）
  refreshAllData()

  // 初始加载质检报告列表
  fetchQualityReports()

  // 初始加载未读反馈数量
  fetchFeedbackUnreadCount()

  // 启动时间更新定时器
  startTimeUpdate()

  // 设置快速轮询，每5秒更新一次工单数量（确保实时性）
  fastPollingInterval = setInterval(() => {
    fetchTickets()
  }, 5000)

  // 设置常规轮询，每30秒更新一次完整数据
  pollingInterval = setInterval(() => {
    refreshAllData()
    // 每60秒更新一次质检报告列表
    if (Math.random() > 0.5) {
      fetchQualityReports()
    }
    // 每30秒更新一次未读反馈数量
    fetchFeedbackUnreadCount()
  }, 30000)

  // 组件卸载时清除轮询
  onUnmounted(() => {
    if (pollingInterval) clearInterval(pollingInterval)
    if (fastPollingInterval) clearInterval(fastPollingInterval)
    stopTimeUpdate()
  })
})
</script>

<template>
  <div class="agent-view">
    <!-- 顶部状态栏 -->
    <header class="agent-header">
      <div class="header-left">
        <div class="logo">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <path d="M16 4L28 10V22L16 28L4 22V10L16 4Z" fill="#43B7C2" opacity="0.1"/>
            <path d="M16 4L28 10V22L16 28L4 22V10L16 4Z" stroke="#43B7C2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <rect x="10" y="12" width="12" height="3" rx="1" fill="#43B7C2"/>
            <rect x="10" y="17" width="12" height="3" rx="1" fill="#43B7C2"/>
            <rect x="10" y="22" width="12" height="3" rx="1" fill="#43B7C2"/>
          </svg>
        </div>
        <h1 class="app-title">坐席端控制平台</h1>
      </div>
      <div class="header-right">
        <div class="status-switcher">
          <button 
            class="cyber-btn-card status-btn-card online" 
            :class="{ active: agentStatus === 'online' }"
            @click="changeStatus('online')"
          >
            <span class="glitch-layer"></span>
            <span class="grid-lines"></span>
            <span class="btn-text">在线</span>
          </button>
          <button 
            class="cyber-btn-card status-btn-card busy" 
            :class="{ active: agentStatus === 'busy' }"
            @click="changeStatus('busy')"
          >
            <span class="glitch-layer"></span>
            <span class="grid-lines"></span>
            <span class="btn-text">忙碌</span>
          </button>
          <button 
            class="cyber-btn-card status-btn-card offline" 
            :class="{ active: agentStatus === 'offline' }"
            @click="changeStatus('offline')"
          >
            <span class="glitch-layer"></span>
            <span class="grid-lines"></span>
            <span class="btn-text">离线</span>
          </button>
        </div>
        <div class="pending-count" @click="selectNavItem('tickets')" style="cursor: pointer;">
          <span class="count-badge">{{ pendingTicketsCount }}</span>
          <span class="count-text">待处理</span>
        </div>
        <div class="notification-bell">
          <button @click="toggleNotifications" class="cyber-btn-card bell-btn-card" :class="{ 'has-notifications': unreadNotificationsCount() > 0 }">
            <span class="glitch-layer"></span>
            <span class="grid-lines"></span>
            <div class="bell-icon-container">
              <svg class="bell-svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
              </svg>
              <span v-if="unreadNotificationsCount() > 0" class="notification-badge">{{ unreadNotificationsCount() }}</span>
            </div>
          </button>
          <div v-if="showNotifications" class="notification-dropdown-cyber">
            <div class="notification-header-cyber">
              <h4>系统通知</h4>
              <button v-if="unreadNotificationsCount() > 0" @click="markAllNotificationsAsRead" class="cyber-btn-card action-btn-card cyan" style="padding: 0.5rem 0.875rem;">
                <span class="glitch-layer"></span>
                <span class="grid-lines"></span>
                <span class="btn-text" style="font-size: 0.75rem;">全部已读</span>
              </button>
            </div>
            <div class="notification-list-cyber">
              <!-- 空状态 -->
              <div v-if="notifications.length === 0" class="notification-empty-cyber">
                <div class="empty-icon">📭</div>
                <div class="empty-text">暂无通知</div>
                <div class="empty-subtext">当有新消息时会在这里显示</div>
              </div>
              <!-- 通知列表 -->
              <div v-for="notification in notifications" :key="notification.id" 
                   class="notification-item-cyber" 
                   :class="{ 'unread': !notification.isRead, 'read': notification.isRead }"
                   @click="markNotificationAsRead(notification.id)">
                <span class="glitch-effect"></span>
                <span class="grid-overlay"></span>
                <span v-if="!notification.isRead" class="unread-dot"></span>
                <span class="notification-icon">{{ notification.type === 'ticket' ? '🎫' : notification.type === 'quality' ? '📊' : notification.type === 'system' ? '⚙️' : '📢' }}</span>
                <p class="notification-content">{{ notification.content }}</p>
                <span class="notification-time">{{ notification.time }}</span>
              </div>
            </div>
          </div>
        </div>

      </div>
    </header>

    <!-- 三栏布局 -->
    <main class="agent-main">
      <!-- 左侧导航栏 -->
      <aside class="nav-sidebar">
        <nav class="sidebar-nav">
          <div 
            class="nav-item-card" 
            :class="{ active: activeNavItem === 'dashboard' }"
            @click="selectNavItem('dashboard')"
          >
            <span class="nav-glow-bar"></span>
            <span class="nav-grid"></span>
            <span class="nav-icon">📊</span>
            <span class="nav-text">仪表盘</span>
            <span class="nav-badge">{{ pendingTicketsCount }}</span>
          </div>
          <div 
            class="nav-item-card" 
            :class="{ active: activeNavItem === 'tickets' }"
            @click="selectNavItem('tickets')"
          >
            <span class="nav-glow-bar"></span>
            <span class="nav-grid"></span>
            <span class="nav-icon">🔥</span>
            <span class="nav-text">待处理工单</span>
            <span class="nav-badge urgent">{{ pendingTicketsCount }}</span>
          </div>
          <div 
            class="nav-item-card" 
            :class="{ active: activeNavItem === 'my-tickets' }"
            @click="selectNavItem('my-tickets')"
          >
            <span class="nav-glow-bar"></span>
            <span class="nav-grid"></span>
            <span class="nav-icon">📋</span>
            <span class="nav-text">我的工单</span>
            <span class="nav-badge">{{ myTicketsCount }}</span>
          </div>
          <div 
            class="nav-item-card" 
            :class="{ active: activeNavItem === 'knowledge' }"
            @click="selectNavItem('knowledge')"
          >
            <span class="nav-glow-bar"></span>
            <span class="nav-grid"></span>
            <span class="nav-icon">🧠</span>
            <span class="nav-text">知识库</span>
            <span class="nav-badge">{{ knowledgeCount }}</span>
          </div>
          <div
            class="nav-item-card"
            :class="{ active: activeNavItem === 'quality' }"
            @click="selectNavItem('quality')"
          >
            <span class="nav-glow-bar"></span>
            <span class="nav-grid"></span>
            <span class="nav-icon">📈</span>
            <span class="nav-text">质检报告</span>
            <span class="nav-badge">{{ qualityReportsCount }}</span>
          </div>
          <div
            class="nav-item-card"
            :class="{ active: activeNavItem === 'feedback' }"
            @click="selectNavItem('feedback')"
          >
            <span class="nav-glow-bar"></span>
            <span class="nav-grid"></span>
            <span class="nav-icon">💬</span>
            <span class="nav-text">反馈收集</span>
            <span class="nav-badge" v-if="feedbackUnreadCount > 0">{{ feedbackUnreadCount }}</span>
          </div>
          <div
            class="nav-item-card"
            :class="{ active: activeNavItem === 'analytics' }"
            @click="navigateToAnalytics"
          >
            <span class="nav-glow-bar"></span>
            <span class="nav-grid"></span>
            <span class="nav-icon">📊</span>
            <span class="nav-text">埋点收集</span>
            <span class="nav-badge neon-badge">NEW</span>
          </div>
        </nav>
      </aside>

      <!-- 中央内容区 -->
      <section class="ticket-pool" :class="{ 'expanded-pool': activeNavItem === 'feedback' }">
        <!-- 统一显示最近工单 -->
        <div class="content-section-card">
          <div class="section-title">
            {{ activeNavItem === 'tickets' ? '工单池' :
                  activeNavItem === 'my-tickets' ? '我的工单' :
                  activeNavItem === 'knowledge' ? '知识库' :
                  activeNavItem === 'quality' ? '质检报告' :
                  activeNavItem === 'feedback' ? '反馈收集' : '最近工单' }}
            <div class="pool-actions">
              <button class="cyber-btn-card action-btn-card cyan" v-if="activeNavItem === 'dashboard'" @click="refreshAllData" :disabled="isRefreshingDashboard">
                <span class="glitch-layer"></span>
                <span class="grid-lines"></span>
                <span class="btn-text">{{ isRefreshingDashboard ? '刷新中...' : '刷新' }}</span>
              </button>
              <button class="cyber-btn-card action-btn-card cyan" v-if="activeNavItem === 'tickets' || activeNavItem === 'my-tickets'" @click="activeNavItem === 'my-tickets' ? fetchMyTickets() : fetchTickets()" :disabled="isRefreshingTickets">
                <span class="glitch-layer"></span>
                <span class="grid-lines"></span>
                <span class="btn-text">{{ isRefreshingTickets ? '刷新中...' : '刷新' }}</span>
              </button>
              <button class="cyber-btn-card action-btn-card cyan" v-if="activeNavItem === 'quality'" @click="fetchQualityReports" :disabled="isRefreshingQuality">
                <span class="glitch-layer"></span>
                <span class="grid-lines"></span>
                <span class="btn-text">{{ isRefreshingQuality ? '刷新中...' : '刷新' }}</span>
              </button>
            </div>
          </div>
          
          <!-- 工单列表 (适用于仪表盘、待处理工单、我的工单) -->
          <div 
            v-if="activeNavItem === 'dashboard' || activeNavItem === 'tickets' || activeNavItem === 'my-tickets'" 
            class="ticket-list"
            style="flex: 1; overflow-y: auto;"
            @dragover="(e) => {
              e.preventDefault();
              console.log('列表dragover事件触发');
            }"
            @drop="(e) => {
              e.preventDefault();
              console.log('列表drop事件触发');
            }"
          >
            <div 
              v-for="ticket in (activeNavItem === 'my-tickets' ? myTickets : tickets)" 
              :key="ticket.id"
              class="ticket-card-cyber"
              :class="{ selected: ticket.isSelected }"
              draggable="true"
              @mousedown="(e) => {
                // 确保鼠标按下时能够正确触发拖拽
                e.currentTarget.style.cursor = 'grabbing';
              }"
              @mouseup="(e) => {
                e.currentTarget.style.cursor = 'grab';
              }"
              @dragstart="(e) => {
                e.dataTransfer.effectAllowed = 'move';
                e.currentTarget.classList.add('dragging');
              }"
              @dragend="(e) => {
                e.currentTarget.classList.remove('dragging');
              }"
              @dragover="(e) => {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
                e.currentTarget.classList.add('drag-over');
              }"
              @dragleave="(e) => {
                e.currentTarget.classList.remove('drag-over');
              }"
              @drop="(e) => {
                e.preventDefault();
                e.currentTarget.classList.remove('drag-over');
              }"
              @click="selectTicket(ticket); currentView = 'tickets'"
            >
              <span class="card-glow"></span>
              <span class="card-grid"></span>
              <div class="ticket-content">
                <h3 class="ticket-title">{{ ticket.title }}</h3>
                <p class="ticket-desc">{{ ticket.content.substring(0, 80) }}...</p>
                <div class="ticket-meta">
                  <span class="priority-badge" :class="ticket.priority.toLowerCase()">{{ ticket.priority }}</span>
                  <span class="ticket-user">{{ ticket.user }}</span>
                  <span class="ticket-department">{{ ticket.department }}</span>
                  <span class="ticket-time">{{ ticket.submittedTime }}</span>
                </div>
              </div>
              <div class="ticket-quick-actions" v-if="activeNavItem === 'tickets'">
                <button class="cyber-btn-card quick-action-btn-card green" title="采纳建议">
                  <span class="glitch-layer"></span>
                  <span class="grid-lines"></span>
                  <span class="btn-icon">✅</span>
                </button>
                <button class="cyber-btn-card quick-action-btn-card cyan" title="转交">
                  <span class="glitch-layer"></span>
                  <span class="grid-lines"></span>
                  <span class="btn-icon">➡️</span>
                </button>
                <button class="cyber-btn-card quick-action-btn-card orange" title="标记紧急">
                  <span class="glitch-layer"></span>
                  <span class="grid-lines"></span>
                  <span class="btn-icon">🔥</span>
                </button>
              </div>
            </div>
            <div v-if="(activeNavItem === 'my-tickets' ? myTickets.length : tickets.length) === 0" class="no-tickets">
              <p>{{ activeNavItem === 'my-tickets' ? '您暂无分配的工单' : '暂无待处理工单' }}</p>
            </div>
          </div>

          <!-- 知识库视图 -->
          <div v-else-if="activeNavItem === 'knowledge'" class="knowledge-content" style="flex: 1; overflow-y: auto; max-height: calc(100vh - 200px);">
            <!-- 拖拽上传区域 -->
            <div 
              class="upload-area"
              :class="{ dragging: isDragging.value }"
              @dragover.prevent
              @dragenter.prevent
              @dragleave.prevent
              @drop.prevent="handleDragDrop"
            >
              <div class="upload-content">
                <div class="upload-icon">📁</div>
                <h3>{{ isDragging.value ? '释放文件以上传' : '拖拽文件到此处上传' }}</h3>
                <p>或点击按钮选择文件</p>
                <button class="cyber-btn-card action-btn-card cyan" @click="uploadKnowledge">
                  <span class="glitch-layer"></span>
                  <span class="grid-lines"></span>
                  <span class="btn-icon">📁</span>
                  <span class="btn-text">上传知识库</span>
                </button>
              </div>
            </div>
            
            <div class="knowledge-articles" v-if="knowledgeArticles.length > 0">
              <div
                v-for="(article, index) in knowledgeArticles"
                :key="index"
                class="article-item"
                @click="selectArticle(article)"
              >
                <div class="article-header">
                  <h3>{{ article.title }}</h3>
                  <button
                    class="delete-knowledge-btn"
                    @click="openDeleteKnowledgeModal(article, $event)"
                    title="删除知识库"
                  >
                    <span class="btn-glow"></span>
                    <el-icon class="delete-icon"><Delete /></el-icon>
                  </button>
                </div>
                <p>{{ article.content.substring(0, 80) }}...</p>
                <span class="article-meta">更新于 {{ article.updatedTime }}</span>
              </div>
            </div>
            <div class="empty-state" v-else>
              <p>暂无知识库文章</p>
            </div>
          </div>

          <!-- 质检报告视图 -->
          <div v-else-if="activeNavItem === 'quality'" class="quality-content">
            <div class="quality-header">
              <h2>质检报告</h2>
            </div>
            <div class="quality-summary">
              <div class="summary-item">
                <h3>平均评分</h3>
                <span class="summary-value">{{ calculateAverageScore() }}</span>
              </div>
              <div class="summary-item">
                <h3>已质检工单</h3>
                <span class="summary-value">{{ qualityReports.length }}</span>
              </div>
              <div class="summary-item">
                <h3>优秀率</h3>
                <span class="summary-value">{{ calculateExcellentRate() }}</span>
              </div>
            </div>
            <div class="quality-records-container">
              <h3>最近质检记录</h3>
              <div class="quality-records">
                <div
                  v-for="report in qualityReports"
                  :key="report.id"
                  class="record-item"
                  :class="{ active: selectedQualityReport && selectedQualityReport.id === report.id }"
                  @click="selectQualityReport(report)"
                >
                  <div class="record-info">
                    <h4>{{ report.title }}</h4>
                    <div class="record-meta">
                      <span class="record-user">{{ report.user }} - {{ report.department }}</span>
                      <span class="record-time">{{ formatDate(report.createdAt) }}</span>
                    </div>
                  </div>
                  <div class="record-score">{{ report.score }}</div>
                </div>
                <div v-if="qualityReports.length === 0" class="empty-records">
                  <p>暂无质检报告</p>
                  <p>当您关闭工单后，系统会自动生成质检报告</p>
                </div>
              </div>
            </div>
          </div>

          <!-- 反馈收集视图 -->
          <div v-else-if="activeNavItem === 'feedback'" class="feedback-content feedback-full-width">
            <FeedbackManager />
          </div>
        </div>
      </section>

      <!-- 右侧处理台 -->
      <section class="ticket-processing" :class="{ 'hidden-section': activeNavItem === 'feedback' }">
        <!-- 仪表盘视图 (移到右侧) -->
        <div v-if="activeNavItem === 'dashboard'" class="dashboard-right-view">
          <div class="content-section-card">
            <div class="section-title">仪表盘</div>
            <div style="display: flex; justify-content: flex-end; margin-bottom: 1rem;">
              <button class="cyber-btn-card action-btn-card cyan" @click="refreshAllData" :disabled="isRefreshingDashboard">
                <span class="glitch-layer"></span>
                <span class="grid-lines"></span>
                <span class="btn-text">{{ isRefreshingDashboard ? '刷新中...' : '刷新' }}</span>
              </button>
            </div>
            
            <!-- 统计卡片网格 -->
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 1.5rem;">
              <!-- 待处理工单 -->
              <div 
                class="info-card-cyber"
                @click="selectNavItem('tickets')"
                style="cursor: pointer; position: relative; overflow: hidden;"
              >
                <span style="position: absolute; top: 0; right: 0; width: 40px; height: 40px; background: linear-gradient(135deg, var(--neon-cyan) 0%, transparent 100%); opacity: 0.3; border-bottom-left-radius: 100%;"></span>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                  <h3 style="margin: 0; font-size: 0.875rem; color: var(--text-muted); font-weight: 500;">待处理工单</h3>
                  <span style="font-size: 1.5rem; font-weight: 700; color: var(--neon-cyan); text-shadow: 0 0 10px rgba(6, 182, 212, 0.5);">{{ pendingTicketsCount }}</span>
                </div>
                <p style="margin: 0; font-size: 0.75rem; color: var(--text-muted);">需要您处理的工单数量</p>
              </div>
              
              <!-- 我的工单 -->
              <div 
                class="info-card-cyber"
                @click="selectNavItem('my-tickets')"
                style="cursor: pointer; position: relative; overflow: hidden;"
              >
                <span style="position: absolute; top: 0; right: 0; width: 40px; height: 40px; background: linear-gradient(135deg, var(--neon-purple) 0%, transparent 100%); opacity: 0.3; border-bottom-left-radius: 100%;"></span>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                  <h3 style="margin: 0; font-size: 0.875rem; color: var(--text-muted); font-weight: 500;">我的工单</h3>
                  <span style="font-size: 1.5rem; font-weight: 700; color: var(--neon-purple); text-shadow: 0 0 10px rgba(168, 85, 247, 0.5);">{{ myTicketsCount }}</span>
                </div>
                <p style="margin: 0; font-size: 0.75rem; color: var(--text-muted);">分配给您的所有工单记录</p>
              </div>
              
              <!-- 今日已处理 -->
              <div 
                class="info-card-cyber"
                @click="selectNavItem('tickets')"
                style="cursor: pointer; position: relative; overflow: hidden;"
              >
                <span style="position: absolute; top: 0; right: 0; width: 40px; height: 40px; background: linear-gradient(135deg, var(--neon-green) 0%, transparent 100%); opacity: 0.3; border-bottom-left-radius: 100%;"></span>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                  <h3 style="margin: 0; font-size: 0.875rem; color: var(--text-muted); font-weight: 500;">今日已处理</h3>
                  <span style="font-size: 1.5rem; font-weight: 700; color: var(--neon-green); text-shadow: 0 0 10px rgba(16, 185, 129, 0.5);">{{ todayProcessedCount }}</span>
                </div>
                <p style="margin: 0; font-size: 0.75rem; color: var(--text-muted);">今天已处理的工单数量</p>
              </div>
              
              <!-- 质检评分 -->
              <div 
                class="info-card-cyber"
                @click="selectNavItem('quality')"
                style="cursor: pointer; position: relative; overflow: hidden;"
              >
                <span style="position: absolute; top: 0; right: 0; width: 40px; height: 40px; background: linear-gradient(135deg, var(--neon-orange) 0%, transparent 100%); opacity: 0.3; border-bottom-left-radius: 100%;"></span>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                  <h3 style="margin: 0; font-size: 0.875rem; color: var(--text-muted); font-weight: 500;">质检评分</h3>
                  <span style="font-size: 1.5rem; font-weight: 700; color: var(--neon-orange); text-shadow: 0 0 10px rgba(249, 115, 22, 0.5);">{{ qualityScore }}</span>
                </div>
                <p style="margin: 0; font-size: 0.75rem; color: var(--text-muted);">您的平均质检评分</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 质检报告详情视图 -->
        <div v-else-if="activeNavItem === 'quality'" class="quality-report-detail-view">
          <div class="quality-report-detail-header">
            <h2>质检报告详情</h2>
          </div>
          <div v-if="selectedQualityReport" class="quality-report-detail-content">
            <!-- 报告头部信息 -->
            <div class="report-header">
              <h3>{{ selectedQualityReport.title }}</h3>
              <div class="report-meta">
                <span class="report-user">{{ selectedQualityReport.user }} - {{ selectedQualityReport.department }}</span>
                <span class="report-time">{{ formatDate(selectedQualityReport.createdAt) }}</span>
              </div>
            </div>
            
            <!-- 总评分展示 -->
            <div class="report-total-score">
              <div class="total-score-value" :class="getScoreClass(selectedQualityReport.score)">
                {{ selectedQualityReport.score }}
              </div>
              <div class="total-score-label">综合评分</div>
              <div class="total-score-stars">
                <span v-for="n in 5" :key="n" class="star" :class="{ 'filled': n <= Math.round(selectedQualityReport.score) }">★</span>
              </div>
            </div>
            
            <!-- 详细评分项 -->
            <div class="report-score-details" v-if="selectedQualityReport.scoreDetails">
              <h4 class="score-details-title">📊 评分详情</h4>
              <div class="score-items">
                <div v-for="(item, index) in selectedQualityReport.scoreDetails" :key="index" class="score-item">
                  <div class="score-item-header">
                    <span class="score-item-name">{{ item.name }}</span>
                    <span class="score-item-value">{{ item.score.toFixed(2) }} / {{ item.maxScore }}</span>
                  </div>
                  <div class="score-item-bar">
                    <div class="score-item-progress" :style="{ width: item.percentage + '%' }"></div>
                  </div>
                  <div class="score-item-percentage">{{ item.percentage }}%</div>
                </div>
              </div>
            </div>
            
            <!-- 报告内容 -->
            <div class="report-body">
              <div class="report-section">
                <h4>📝 问题描述</h4>
                <div class="report-content-box">{{ selectedQualityReport.content }}</div>
              </div>
              <div class="report-section">
                <h4>💬 工程师回复</h4>
                <div class="report-content-box" :class="{ 'empty': !selectedQualityReport.response }">
                  {{ selectedQualityReport.response || '暂无工程师回复' }}
                </div>
              </div>
            </div>
          </div>
          <div v-else class="report-detail-empty">
            <div class="empty-icon">📋</div>
            <p>请选择一条质检记录查看详情</p>
            <p class="empty-subtitle">点击左侧列表中的记录即可查看详细评分信息</p>
          </div>
        </div>

        <!-- 工单处理视图 -->
        <div v-else-if="currentView === 'tickets' && selectedTicket" class="processing-content">
          <!-- 工单摘要区 -->
          <div class="content-section-card">
            <div class="section-title">工单详情</div>
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
              <div style="display: flex; align-items: center; gap: 0.75rem;">
                <div style="width: 40px; height: 40px; background: var(--gradient-blue-cyan); border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: var(--glow-cyan);">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="8" r="4" fill="white"/>
                    <rect x="8" y="12" width="8" height="9" rx="4" fill="white"/>
                  </svg>
                </div>
                <div>
                  <h3 style="margin: 0; font-size: 1rem; color: white;">{{ selectedTicket.user }}</h3>
                  <span style="font-size: 0.8125rem; color: var(--text-muted);">{{ selectedTicket.department }}</span>
                </div>
              </div>
              <span class="priority-badge" :class="selectedTicket.priority.toLowerCase()" style="padding: 0.375rem 0.75rem; border-radius: 0.375rem; font-size: 0.75rem; font-weight: 600;">
                {{ getPriorityText(selectedTicket.priority) }}
              </span>
            </div>
            <div>
              <h2 style="margin: 0 0 0.75rem 0; font-size: 1.125rem; color: white; text-shadow: 0 0 10px rgba(6, 182, 212, 0.3);">{{ selectedTicket.title }}</h2>
              <div class="info-card-cyber" style="font-size: 0.9375rem; color: var(--text-secondary); line-height: 1.6;">
                {{ selectedTicket.content }}
              </div>
            </div>
          </div>

          <!-- AI作战面板 -->
          <div class="ai-panel-card">
            <div class="ai-panel-title">
              <span class="btn-icon">💡</span>
              <span>AI智能回复</span>
            </div>
            
            <!-- 智能回复建议 -->
            <div class="ai-content" style="margin-bottom: 1rem;">
              <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;">
                <h4 style="font-size: 0.9375rem; color: var(--text-secondary); margin: 0;">智能回复建议</h4>
                <button 
                  v-if="aiSuggestions.length > 0 && !isLoading"
                  class="cyber-btn-card action-btn-card cyan"
                  @click="generateAiSuggestion"
                  :disabled="isLoading"
                >
                  <span class="glitch-layer"></span>
                  <span class="grid-lines"></span>
                  <span class="btn-icon">🔄</span>
                  <span class="btn-text">刷新</span>
                </button>
              </div>
              
              <button 
                v-if="aiSuggestions.length === 0"
                class="ai-generate-btn"
                @click="generateAiSuggestion"
                :disabled="isLoading"
              >
                <span class="btn-icon">📝</span>
                <span class="btn-text">{{ isLoading ? '生成中...' : '生成智能回复' }}</span>
              </button>
              
              <div v-if="isLoading" class="loading-suggestions" style="text-align: center; padding: 2rem;">
                <div class="loading-dots"><span></span></div>
                <p style="color: var(--text-muted); margin-top: 1rem;">AI正在生成回复建议...</p>
              </div>
              
              <div v-else-if="aiSuggestions.length > 0" style="margin-top: 0.75rem;">
                <div class="input-area-card" style="margin-bottom: 0.75rem;">
                  <span class="input-glow"></span>
                  <textarea :value="aiSuggestions[0]" readonly style="min-height: 80px; background: transparent; border: none; color: var(--text-primary); width: 100%; resize: none; outline: none;"></textarea>
                </div>
                <button class="cyber-btn-card action-btn-card green" @click="adoptSuggestion" style="width: 100%;">
                  <span class="glitch-layer"></span>
                  <span class="grid-lines"></span>
                  <span class="btn-icon">✅</span>
                  <span class="btn-text">采纳建议</span>
                </button>
              </div>
              
              <div v-else class="empty-state-card" style="margin-top: 0.75rem;">
                <div class="empty-icon">🤖</div>
                <p class="empty-text">点击上方按钮生成AI智能回复</p>
              </div>
            </div>
            
            <!-- 字段提取结果 -->
            <div class="ai-content" style="margin-bottom: 1rem;">
              <h4 style="font-size: 0.9375rem; color: var(--text-secondary); margin: 0 0 0.75rem 0;">字段提取结果</h4>
              <div v-if="extractedFields.length > 0" style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                <span v-for="(field, index) in extractedFields" :key="index" class="info-card-cyber" style="font-size: 0.8125rem;">
                  {{ field.name }}: {{ field.value }}
                </span>
              </div>
              <div v-else class="empty-state-card">
                <p class="empty-text">点击生成智能回复以提取关键字段</p>
              </div>
            </div>
            
            <!-- 相关知识片段 -->
            <div class="ai-content">
              <h4 style="font-size: 0.9375rem; color: var(--text-secondary); margin: 0 0 0.75rem 0;">相关知识片段</h4>
              <div v-if="knowledgeItems.length > 0">
                <div class="info-card-cyber" v-for="(item, index) in knowledgeItems" :key="index" style="margin-bottom: 0.5rem;">
                  <p style="margin: 0 0 0.5rem 0; color: var(--text-secondary);">{{ item.content }}</p>
                  <span style="font-size: 0.75rem; color: var(--neon-cyan);">来源：{{ item.source }}</span>
                </div>
              </div>
              <div v-else class="empty-state-card">
                <div class="empty-icon">📚</div>
                <p class="empty-text">暂无相关知识片段</p>
              </div>
            </div>
          </div>

          <!-- 操作工作区 -->
          <div class="content-section-card">
            <div class="section-title">操作工作区</div>
            
            <!-- 回复输入区 -->
            <div class="input-area-card" style="margin-bottom: 1rem;">
              <span class="input-glow"></span>
              <textarea 
                placeholder="请输入回复内容..."
                v-model="replyContent"
                style="min-height: 120px; background: transparent; border: none; color: var(--text-primary); width: 100%; resize: vertical; outline: none;"
              ></textarea>
            </div>
            
            <!-- 快捷回复 -->
            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem;">
              <button 
                v-for="(reply, index) in quickReplies" 
                :key="index"
                class="cyber-btn-card action-btn-card"
                @click="selectQuickReply(reply)"
              >
                <span class="glitch-layer"></span>
                <span class="grid-lines"></span>
                <span class="btn-text">{{ reply }}</span>
              </button>
            </div>
            
            <!-- 附件和质检 -->
            <div style="display: flex; gap: 0.75rem; margin-bottom: 1rem;">
              <button class="cyber-btn-card action-btn-card cyan" @click="uploadAttachment" style="flex: 1;">
                <span class="glitch-layer"></span>
                <span class="grid-lines"></span>
                <span class="btn-icon">📎</span>
                <span class="btn-text">上传附件</span>
              </button>
              <button class="cyber-btn-card action-btn-card purple" @click="previewQualityCheck" style="flex: 1;">
                <span class="glitch-layer"></span>
                <span class="grid-lines"></span>
                <span class="btn-icon">📋</span>
                <span class="btn-text">质检预览</span>
              </button>
            </div>
            
            <!-- 主要操作按钮 -->
            <div style="display: flex; gap: 0.75rem;">
              <button class="cyber-btn-card action-btn-card orange" @click="transferTicket" style="flex: 1;">
                <span class="glitch-layer"></span>
                <span class="grid-lines"></span>
                <span class="btn-icon">➡️</span>
                <span class="btn-text">转交</span>
              </button>
              <button class="send-btn-cyber" @click="sendAndClose" style="flex: 2;">
                <span class="btn-icon">📤</span>
                <span class="btn-text">发送并关闭</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 无工单选中视图 -->
        <div v-else-if="currentView === 'tickets' && !selectedTicket" class="no-ticket-selected">
          <p>请从左侧选择一个工单进行处理</p>
        </div>

        <!-- 反馈收集视图 - 右侧不显示内容，因为FeedbackManager已包含完整界面 -->
        <div v-else-if="activeNavItem === 'feedback'" class="feedback-empty-view">
          <!-- 反馈收集模块在左侧已完整展示，右侧保持简洁 -->
        </div>

        <!-- 其他视图的右侧内容 -->
        <div v-else class="other-view-content">
          <div class="view-header">
            <h2>{{ activeNavItem === 'my-tickets' ? '我的工单详情' : 
                  activeNavItem === 'knowledge' ? '知识库详情' : '质检报告详情' }}</h2>
          </div>
          <div class="view-body">
            <p v-if="activeNavItem === 'my-tickets'">
              这里显示您负责的工单详情。您可以查看工单的处理状态、优先级和详细信息。
            </p>
            <div v-else-if="activeNavItem === 'knowledge'">
              <div v-if="selectedArticle" class="article-detail">
                <h3>{{ selectedArticle.title }}</h3>
                <div class="article-meta-info">
                  <span class="article-category">{{ selectedArticle.category }}</span>
                  <span class="article-updated">{{ selectedArticle.updatedTime }}</span>
                </div>
                <div class="article-content">
                  {{ selectedArticle.content }}
                </div>
              </div>
              <p v-else>
                请从左侧选择一篇知识库文章查看详细内容
              </p>
            </div>
            <p v-else-if="activeNavItem === 'quality'">
              质检报告详情页面正在建设中，敬请期待！
            </p>
          </div>
        </div>
      </section>
    </main>

    <!-- 赛博朋克风格加载弹窗 -->
    <div v-if="showLoadingModal" class="cyber-loading-overlay">
      <div class="cyber-loading-modal">
        <div class="cyber-loading-content">
          <div class="cyber-spinner">
            <div class="spinner-ring"></div>
            <div class="spinner-ring"></div>
            <div class="spinner-ring"></div>
          </div>
          <div class="cyber-loading-text">
            <span class="loading-title">系统处理中</span>
            <span class="loading-subtitle">{{ loadingModalText }}</span>
          </div>
          <div class="cyber-loading-progress">
            <div class="progress-bar">
              <div class="progress-fill"></div>
            </div>
            <div class="progress-grid"></div>
          </div>
        </div>
        <div class="cyber-corner top-left"></div>
        <div class="cyber-corner top-right"></div>
        <div class="cyber-corner bottom-left"></div>
        <div class="cyber-corner bottom-right"></div>
        <div class="cyber-scan-line"></div>
      </div>
    </div>

    <!-- 质检预览卡片 -->
    <div v-if="showQualityPreview" class="quality-preview-overlay" @click="showQualityPreview = false">
      <div class="quality-preview-card" @click.stop>
        <div class="quality-preview-header">
          <h3>质检预览</h3>
          <button class="close-btn" @click="showQualityPreview = false">×</button>
        </div>
        <div class="quality-preview-content">
          <div class="preview-section">
            <h4>评分</h4>
            <div class="preview-score">{{ qualityPreviewData.score }}</div>
          </div>
          <div class="preview-section">
            <h4>用户信息</h4>
            <div class="preview-user-info">
              <span class="preview-user">{{ qualityPreviewData.user }}</span>
              <span class="preview-department">{{ qualityPreviewData.department }}</span>
            </div>
          </div>
          <div class="preview-section">
            <h4>问题描述</h4>
            <p class="preview-content">{{ qualityPreviewData.content }}</p>
          </div>
          <div class="preview-section">
            <h4>解决方案</h4>
            <p class="preview-response">{{ qualityPreviewData.response || '请先输入解决方案' }}</p>
          </div>
        </div>
        <div class="quality-preview-footer">
          <button class="confirm-btn" @click="showQualityPreview = false">确定</button>
        </div>
      </div>
    </div>

    <!-- 删除知识库确认弹窗 -->
    <div v-if="showDeleteKnowledgeModal" class="cyber-delete-modal" @click.self="closeDeleteKnowledgeModal">
      <div class="cyber-delete-content">
        <!-- 扫描线效果 -->
        <div class="scan-line"></div>
        <div class="scan-line-delayed"></div>

        <!-- 角落装饰 -->
        <div class="corner-decoration top-left"></div>
        <div class="corner-decoration top-right"></div>
        <div class="corner-decoration bottom-left"></div>
        <div class="corner-decoration bottom-right"></div>

        <!-- 头部 -->
        <div class="cyber-delete-header">
          <div class="header-glitch">
            <span class="glitch-text" data-text="SYSTEM WARNING">SYSTEM WARNING</span>
          </div>
          <button class="cyber-close-btn" @click="closeDeleteKnowledgeModal">
            <el-icon><Close /></el-icon>
          </button>
        </div>

        <!-- 主体内容 -->
        <div class="cyber-delete-body">
          <!-- 警告图标区域 -->
          <div class="warning-zone">
            <div class="warning-hologram">
              <el-icon class="warning-icon-large"><Delete /></el-icon>
              <div class="hologram-ring"></div>
              <div class="hologram-ring delayed"></div>
            </div>
            <div class="warning-code">ERR_DELETE_CONFIRMATION_REQUIRED</div>
          </div>

          <!-- 警告信息 -->
          <div class="alert-message">
            <div class="alert-title">
              <span class="alert-prefix">[</span>
              <span class="alert-blink">CRITICAL</span>
              <span class="alert-suffix">]</span>
              <span class="alert-text"> 数据删除确认</span>
            </div>
            <div class="alert-desc">
              <span class="code-comment">// 警告: 此操作不可逆</span>
              <br>
              <span class="code-line">目标数据将被永久擦除，无法通过任何手段恢复。</span>
            </div>
          </div>

          <!-- 数据预览面板 -->
          <div class="data-terminal" v-if="knowledgeToDelete">
            <div class="terminal-header">
              <span class="terminal-dot red"></span>
              <span class="terminal-dot yellow"></span>
              <span class="terminal-dot green"></span>
              <span class="terminal-title">TARGET_DATA_PREVIEW</span>
            </div>
            <div class="terminal-body">
              <div class="terminal-line">
                <span class="terminal-prompt">$</span>
                <span class="terminal-command">cat article_info.json</span>
              </div>
              <div class="terminal-output">
                <div class="json-line">
                  <span class="json-key">"title"</span>
                  <span class="json-colon">:</span>
                  <span class="json-value string">"{{ knowledgeToDelete.title }}"</span>
                </div>
                <div class="json-line">
                  <span class="json-key">"updated_at"</span>
                  <span class="json-colon">:</span>
                  <span class="json-value string">"{{ knowledgeToDelete.updatedTime }}"</span>
                </div>
                <div class="json-line">
                  <span class="json-key">"status"</span>
                  <span class="json-colon">:</span>
                  <span class="json-value warning">"PENDING_DELETION"</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 确认输入 -->
          <div class="confirmation-input">
            <div class="input-label">
              <span class="label-icon">></span>
              <span>输入 "DELETE" 以确认操作</span>
            </div>
            <input
              type="text"
              v-model="deleteConfirmText"
              class="cyber-input"
              placeholder="DELETE"
              @keyup.enter="confirmDeleteKnowledge"
            />
          </div>
        </div>

        <!-- 底部按钮 -->
        <div class="cyber-delete-footer">
          <button class="cyber-btn-secondary" @click="closeDeleteKnowledgeModal">
            <el-icon><Close /></el-icon>
            <span>中止操作</span>
          </button>
          <button
            class="cyber-btn-destroy"
            @click="confirmDeleteKnowledge"
            :disabled="isDeletingKnowledge || deleteConfirmText !== 'DELETE'"
          >
            <el-icon v-if="!isDeletingKnowledge"><Delete /></el-icon>
            <el-icon v-else class="rotating"><Loading /></el-icon>
            <span>{{ isDeletingKnowledge ? '正在擦除数据...' : '执行删除' }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ============================================
   赛博朋克设计系统 - Cyberpunk Design System
   ============================================ */
.agent-view {
  /* 霓虹色系 - Neon Colors */
  --neon-purple: #a855f7;
  --neon-pink: #ec4899;
  --neon-blue: #3b82f6;
  --neon-cyan: #06b6d4;
  --neon-green: #10b981;
  --neon-yellow: #f59e0b;
  --neon-red: #ef4444;
  --neon-orange: #f97316;

  /* 霓虹渐变 */
  --gradient-purple-pink: linear-gradient(135deg, #a855f7 0%, #ec4899 100%);
  --gradient-blue-cyan: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
  --gradient-cyan-green: linear-gradient(135deg, #06b6d4 0%, #10b981 100%);
  --gradient-pink-orange: linear-gradient(135deg, #ec4899 0%, #f97316 100%);
  --gradient-rainbow: linear-gradient(90deg, #a855f7, #ec4899, #f97316, #f59e0b, #10b981, #06b6d4, #3b82f6, #a855f7);

  /* 深色主题背景 */
  --bg-deepest: #030712;
  --bg-darker: #0a0f1a;
  --bg-dark: #111827;
  --bg-card: rgba(31, 41, 55, 0.9);
  --bg-surface: rgba(55, 65, 81, 0.8);
  --bg-elevated: rgba(75, 85, 99, 0.9);

  /* 全息效果 */
  --hologram-bg: linear-gradient(135deg, rgba(10, 15, 26, 0.95) 0%, rgba(17, 24, 39, 0.9) 50%, rgba(31, 41, 55, 0.85) 100%);
  --grid-overlay: repeating-linear-gradient(0deg, transparent, transparent 40px, rgba(6, 182, 212, 0.03) 40px, rgba(6, 182, 212, 0.03) 41px), repeating-linear-gradient(90deg, transparent, transparent 40px, rgba(6, 182, 212, 0.03) 40px, rgba(6, 182, 212, 0.03) 41px);

  /* 文字颜色 */
  --text-primary: #f9fafb;
  --text-secondary: #e5e7eb;
  --text-tertiary: #d1d5db;
  --text-muted: #9ca3af;
  --text-disabled: #6b7280;

  /* 霓虹边框 */
  --border-cyan: rgba(6, 182, 212, 0.3);
  --border-purple: rgba(168, 85, 247, 0.3);
  --border-pink: rgba(236, 72, 153, 0.3);
  --border-blue: rgba(59, 130, 246, 0.3);

  /* 霓虹发光 */
  --glow-cyan: 0 0 10px rgba(6, 182, 212, 0.5), 0 0 20px rgba(6, 182, 212, 0.3), 0 0 30px rgba(6, 182, 212, 0.2);
  --glow-purple: 0 0 10px rgba(168, 85, 247, 0.5), 0 0 20px rgba(168, 85, 247, 0.3), 0 0 30px rgba(168, 85, 247, 0.2);
  --glow-pink: 0 0 10px rgba(236, 72, 153, 0.5), 0 0 20px rgba(236, 72, 153, 0.3), 0 0 30px rgba(236, 72, 153, 0.2);
  --glow-green: 0 0 10px rgba(16, 185, 129, 0.5), 0 0 20px rgba(16, 185, 129, 0.3), 0 0 30px rgba(16, 185, 129, 0.2);

  /* 阴影系统 */
  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.5);
  --shadow-md: 0 4px 8px rgba(0, 0, 0, 0.5), 0 0 20px rgba(6, 182, 212, 0.1);
  --shadow-lg: 0 8px 16px rgba(0, 0, 0, 0.5), 0 0 30px rgba(6, 182, 212, 0.15);
  --shadow-glow: 0 0 20px rgba(6, 182, 212, 0.3);

  /* 间距系统 */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;

  /* 圆角系统 */
  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;
  --radius-xl: 0.75rem;
  --radius-2xl: 1rem;
  --radius-full: 9999px;

  /* 过渡动画 - 赛博朋克风格 */
  --transition-fast: 150ms cubic-bezier(0.68, -0.55, 0.265, 1.55);
  --transition-base: 200ms cubic-bezier(0.68, -0.55, 0.265, 1.55);
  --transition-slow: 300ms cubic-bezier(0.68, -0.55, 0.265, 1.55);

  /* 字体 */
  --font-sans: 'Orbitron', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;

  /* 状态颜色 */
  --success-color: #10b981;
  --warning-color: #f59e0b;
  --error-color: #ef4444;
  --info-color: #3b82f6;

  /* 优先级颜色 */
  --priority-emergency: #ef4444;
  --priority-high: #f97316;
  --priority-medium: #06b6d4;
  --priority-low: #10b981;

  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-deepest);
  color: var(--text-primary);
  font-family: var(--font-sans);
  position: relative;
  overflow: hidden;
}

/* 背景动画效果 */
.agent-view::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--hologram-bg);
  z-index: -2;
  pointer-events: none;
}

.agent-view::after {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--grid-overlay);
  z-index: -1;
  animation: gridMove 20s linear infinite;
  pointer-events: none;
}

@keyframes gridMove {
  0% {
    background-position: 0 0;
  }
  100% {
    background-position: 40px 40px;
  }
}

@keyframes rainbowBorder {
  0% {
    background-position: 0% 50%;
  }
  100% {
    background-position: 200% 50%;
  }
}

@keyframes hologramScan {
  0% {
    left: -100%;
  }
  50%, 100% {
    left: 100%;
  }
}

@keyframes pulseBorder {
  0% {
    opacity: 1;
    transform: scale(1);
  }
  100% {
    opacity: 0;
    transform: scale(1.2);
  }
}

@keyframes badgePulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: var(--glow-cyan);
  }
  50% {
    transform: scale(1.15);
    box-shadow: 0 0 25px rgba(6, 182, 212, 0.6);
  }
}

@keyframes cyberSlideIn {
  0% {
    opacity: 0;
    transform: translateY(20px) scale(0.9);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* ============================================
   顶部状态栏 - Cyberpunk Header
   ============================================ */
.agent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4) var(--space-8);
  background: rgba(17, 24, 39, 0.9);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-cyan);
  position: relative;
  z-index: 100;
  box-shadow: var(--shadow-md);
}

.agent-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--gradient-rainbow);
  background-size: 200% 100%;
  animation: rainbowBorder 3s linear infinite;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.logo {
  width: 44px;
  height: 44px;
  background: var(--gradient-blue-cyan);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  box-shadow: var(--glow-cyan);
  position: relative;
  overflow: hidden;
}

.logo::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  animation: hologramScan 3s ease-in-out infinite;
}

.logo:hover {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 0 30px rgba(6, 182, 212, 0.5);
}

.app-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
  background: var(--gradient-blue-cyan);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 0.05em;
  text-shadow: 0 0 20px rgba(6, 182, 212, 0.3);
  position: relative;
}

.app-title::after {
  content: attr(data-text);
  position: absolute;
  top: 0;
  left: 0;
  color: var(--neon-pink);
  opacity: 0;
  animation: glitchText 3s infinite;
  clip-path: polygon(0 0, 100% 0, 100% 35%, 0 35%);
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--tech-space-6);
}

.status-switcher {
  display: flex;
  gap: var(--tech-space-1);
  background: rgba(15, 23, 42, 0.6);
  padding: var(--tech-space-1);
  border-radius: var(--tech-radius-full);
  border: 1px solid var(--tech-border);
}

.status-btn {
  background: transparent;
  border: none;
  color: var(--tech-text-muted);
  padding: var(--tech-space-2) var(--tech-space-4);
  border-radius: var(--tech-radius-full);
  cursor: pointer;
  transition: var(--tech-transition-base);
  font-size: 0.875rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: var(--tech-space-2);
}

.status-btn:hover {
  color: var(--tech-text-secondary);
  background: rgba(255, 255, 255, 0.05);
}

.status-btn.active {
  background: var(--tech-gradient-primary);
  color: white;
  box-shadow: var(--tech-shadow-glow);
}

.status-btn::before {
  content: '';
  width: 8px;
  height: 8px;
  border-radius: var(--tech-radius-full);
  background: currentColor;
}

/* ============================================
   待处理计数和通知 - Cyberpunk Notifications
   ============================================ */
.pending-count {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(17, 24, 39, 0.8);
  padding: 0.5rem 1rem;
  border-radius: 9999px;
  border: 1px solid rgba(6, 182, 212, 0.3);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.pending-count:hover {
  background: rgba(6, 182, 212, 0.1);
  border-color: #06b6d4;
  box-shadow: 0 0 10px rgba(6, 182, 212, 0.5), 0 0 20px rgba(6, 182, 212, 0.3);
  transform: translateY(-2px);
}

.count-badge {
  background: linear-gradient(135deg, #a855f7 0%, #ec4899 100%);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 700;
  min-width: 24px;
  text-align: center;
  box-shadow: 0 0 10px rgba(236, 72, 153, 0.5), 0 0 20px rgba(236, 72, 153, 0.3);
  animation: badgePulse 2s ease-in-out infinite;
}

@keyframes badgePulse {
  0%, 100% { 
    box-shadow: 0 0 10px rgba(236, 72, 153, 0.5), 0 0 20px rgba(236, 72, 153, 0.3);
  }
  50% { 
    box-shadow: 0 0 15px rgba(236, 72, 153, 0.7), 0 0 30px rgba(236, 72, 153, 0.5), 0 0 40px rgba(236, 72, 153, 0.3);
  }
}

.count-text {
  font-size: 0.875rem;
  color: #e5e7eb;
  font-weight: 500;
}

.notification-bell {
  position: relative;
}

.bell-btn-card {
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid var(--border-cyan);
  cursor: pointer;
  position: relative;
  padding: var(--space-3);
  border-radius: var(--radius-lg);
  transition: var(--transition-base);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.bell-btn-card:hover {
  background: rgba(6, 182, 212, 0.2);
  border-color: var(--neon-cyan);
  transform: scale(1.05);
  box-shadow: var(--glow-cyan);
}

.bell-btn-card.has-notifications {
  animation: bellPulse 2s ease-in-out infinite;
}

@keyframes bellPulse {
  0%, 100% {
    box-shadow: var(--glow-cyan);
  }
  50% {
    box-shadow: 0 0 25px rgba(6, 182, 212, 0.6), 0 0 40px rgba(6, 182, 212, 0.3);
  }
}

.bell-icon-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.bell-svg {
  color: currentColor;
  transition: var(--transition-base);
}

.bell-btn-card:hover .bell-svg {
  transform: scale(1.1) rotate(5deg);
  color: var(--neon-cyan);
}

.bell-btn-card.has-notifications .bell-svg {
  animation: bellRing 1s ease-in-out infinite;
}

@keyframes bellRing {
  0%, 100% {
    transform: rotate(0deg);
  }
  25% {
    transform: rotate(15deg);
  }
  75% {
    transform: rotate(-15deg);
  }
}

.notification-badge {
  position: absolute;
  top: -6px;
  right: -6px;
  background: linear-gradient(135deg, var(--neon-red), var(--neon-orange));
  color: white;
  font-size: 0.625rem;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-full);
  min-width: 18px;
  text-align: center;
  font-weight: 700;
  box-shadow: 0 0 15px rgba(239, 68, 68, 0.6);
  animation: badgePulse 2s ease-in-out infinite;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

@keyframes badgePulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 0 15px rgba(239, 68, 68, 0.6);
  }
  50% {
    transform: scale(1.15);
    box-shadow: 0 0 25px rgba(239, 68, 68, 0.8), 0 0 40px rgba(239, 68, 68, 0.4);
  }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

.notification-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: var(--tech-space-3);
  background: rgba(30, 41, 59, 0.95);
  border: 1px solid var(--tech-border);
  border-radius: var(--tech-radius-xl);
  box-shadow: var(--tech-shadow-lg);
  width: 320px;
  z-index: 100;
  backdrop-filter: blur(12px);
  overflow: hidden;
}

.notification-dropdown::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--tech-gradient-primary);
}

.notification-dropdown h4 {
  padding: var(--tech-space-4);
  margin: 0;
  border-bottom: 1px solid var(--tech-border);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--tech-text-primary);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.notification-list {
  max-height: 300px;
  overflow-y: auto;
}

.notification-item {
  padding: var(--spacing-md);
  border-bottom: 1px solid var(--agent-border);
  transition: var(--transition);
}

.notification-item:hover {
  background-color: var(--agent-bg-primary);
}

.notification-content {
  margin: 0 0 var(--spacing-xs) 0;
  font-size: 0.875rem;
}

.notification-time {
  font-size: 0.75rem;
  color: var(--agent-text-secondary);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  transition: var(--transition);
}

.user-avatar:hover {
  transform: scale(1.05);
}

/* 三栏布局 */
.agent-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ============================================
   左侧导航栏 - Tech Navigation Sidebar
   ============================================ */
.nav-sidebar {
  width: 240px;
  background: linear-gradient(180deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%);
  border-right: 1px solid var(--tech-border);
  overflow-y: auto;
  backdrop-filter: blur(8px);
}

.nav-sidebar::-webkit-scrollbar {
  width: 4px;
}

.nav-sidebar::-webkit-scrollbar-track {
  background: transparent;
}

.nav-sidebar::-webkit-scrollbar-thumb {
  background: var(--tech-border);
  border-radius: var(--tech-radius-full);
}

.sidebar-nav {
  padding: var(--tech-space-4) 0;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: var(--tech-space-4) var(--tech-space-6);
  cursor: pointer;
  transition: var(--tech-transition-base);
  position: relative;
  margin: var(--tech-space-1) var(--tech-space-3);
  border-radius: var(--tech-radius-lg);
}

.nav-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 0;
  background: var(--tech-gradient-primary);
  border-radius: var(--tech-radius-full);
  transition: var(--tech-transition-base);
}

.nav-item:hover {
  background: rgba(59, 130, 246, 0.1);
  color: var(--tech-primary-400);
}

.nav-item:hover::before {
  height: 60%;
}

.nav-item.active {
  background: rgba(59, 130, 246, 0.15);
  color: var(--tech-primary-400);
}

.nav-item.active::before {
  height: 80%;
}

.nav-icon {
  font-size: 1.25rem;
  margin-right: var(--tech-space-3);
  transition: var(--tech-transition-base);
}

.nav-item:hover .nav-icon {
  transform: scale(1.1);
}

.nav-text {
  flex: 1;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--tech-text-secondary);
  transition: var(--tech-transition-base);
}

.nav-item:hover .nav-text,
.nav-item.active .nav-text {
  color: var(--tech-text-primary);
}

/* nav-badge 样式已移至 cyberpunk-agent.css 全局样式 */

/* 中央内容区 */
.ticket-pool {
  width: 35%;
  background-color: var(--agent-bg-primary);
  border-right: 1px solid var(--agent-border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width 0.3s ease;
}

/* 反馈收集视图下左侧区域扩展 */
.ticket-pool.expanded-pool {
  width: 100%;
  border-right: none;
}

/* 最近工单视图 */
.recent-tickets-view {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.pool-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--agent-border);
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--agent-border);
}

.dashboard-header h2 {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
}

.dashboard-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.pool-header h2 {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
}

.pool-actions {
  display: flex;
  gap: var(--spacing-sm);
}

/* ============================================
   按钮样式 - Tech Buttons
   ============================================ */
.action-btn {
  background: rgba(30, 41, 59, 0.6);
  color: var(--tech-text-secondary);
  border: 1px solid var(--tech-border);
  padding: var(--tech-space-2) var(--tech-space-4);
  border-radius: var(--tech-radius-md);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: var(--tech-transition-base);
  display: inline-flex;
  align-items: center;
  gap: var(--tech-space-2);
}

.action-btn:hover {
  background: var(--tech-gradient-primary);
  border-color: transparent;
  color: white;
  transform: translateY(-2px);
  box-shadow: var(--tech-shadow-glow);
}

.action-btn:active {
  transform: translateY(0);
}

/* 仪表盘视图 */
.dashboard-view,
.dashboard-right-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.dashboard-right-view {
  padding: var(--spacing-lg);
}

.dashboard-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
}

/* 待处理工单视图 */
.tickets-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.tickets-view .ticket-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
}

/* 我的工单视图 */
.my-tickets-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.my-tickets-view .ticket-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
}

/* 知识库视图 */
.knowledge-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.knowledge-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
}

/* 质检报告视图 */

/* 工单卡片拖拽样式 */
.ticket-card {
  transition: all 0.2s ease;
}

.ticket-card.dragging {
  opacity: 0.5;
  transform: rotate(2deg);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 1000;
}

.ticket-card.drag-over {
  border: 2px dashed #43b7c2;
  background-color: rgba(67, 183, 194, 0.1);
  box-shadow: 0 0 0 2px rgba(67, 183, 194, 0.5);
}

.ticket-list {
  min-height: 200px;
}
.quality-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.quality-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
}

/* 反馈收集视图样式 */
.feedback-content {
  flex: 1;
  overflow-y: auto;
  height: 100%;
}

/* 反馈收集全宽模式 - 当右侧隐藏时左侧扩展 */
.feedback-full-width {
  width: 100%;
  max-width: 100%;
}

/* 隐藏右侧处理台 */
.hidden-section {
  display: none !important;
}

/* ============================================
   仪表盘统计卡片 - Tech Dashboard Cards
   ============================================ */
.dashboard-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--tech-space-5);
  margin-bottom: var(--tech-space-8);
}

.dashboard-card {
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(51, 65, 85, 0.4) 100%);
  border: 1px solid var(--tech-border);
  border-radius: var(--tech-radius-xl);
  padding: var(--tech-space-6);
  position: relative;
  overflow: hidden;
  transition: var(--tech-transition-base);
  backdrop-filter: blur(8px);
}

.dashboard-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--tech-gradient-primary);
  opacity: 0.8;
}

.dashboard-card:hover {
  transform: translateY(-4px);
  border-color: var(--tech-primary-500);
  box-shadow: var(--tech-shadow-glow);
}

.dashboard-card:nth-child(2)::before {
  background: var(--tech-gradient-success);
}

.dashboard-card:nth-child(2):hover {
  box-shadow: var(--tech-shadow-glow-success);
}

.dashboard-card:nth-child(3)::before {
  background: var(--tech-gradient-warning);
}

.dashboard-card:nth-child(3):hover {
  box-shadow: var(--tech-shadow-glow-warning);
}

.dashboard-card:nth-child(4)::before {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--tech-space-4);
}

.card-header h3 {
  font-size: 0.875rem;
  font-weight: 500;
  margin: 0;
  color: var(--tech-text-muted);
  display: flex;
  align-items: center;
  gap: var(--tech-space-2);
}

.card-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--tech-radius-lg);
  background: var(--tech-gradient-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
}

.card-value {
  font-size: 2rem;
  font-weight: 800;
  color: var(--tech-text-primary);
  margin-bottom: var(--tech-space-2);
  background: linear-gradient(135deg, var(--tech-text-primary) 0%, var(--tech-primary-400) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.card-body p {
  font-size: 0.75rem;
  color: var(--tech-text-muted);
  margin: 0;
  display: flex;
  align-items: center;
  gap: var(--tech-space-2);
}

.trend-indicator {
  display: inline-flex;
  align-items: center;
  gap: var(--tech-space-1);
  padding: var(--tech-space-1) var(--tech-space-2);
  border-radius: var(--tech-radius-full);
  font-size: 0.75rem;
  font-weight: 600;
}

.trend-up {
  background: rgba(16, 185, 129, 0.2);
  color: var(--tech-success);
}

.trend-down {
  background: rgba(239, 68, 68, 0.2);
  color: var(--tech-danger);
}

.recent-tickets h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 var(--spacing-md) 0;
}

/* 我的工单视图 */
.my-tickets-view .ticket-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
}

.no-tickets {
  text-align: center;
  padding: var(--spacing-xl);
  color: var(--agent-text-secondary);
}

/* 知识库视图 */
.knowledge-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
}

.knowledge-categories {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
}

.category-item {
  background-color: var(--agent-bg-secondary);
  color: var(--agent-text-primary);
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.875rem;
  cursor: pointer;
  transition: var(--transition);
}

.category-item:hover {
  background-color: var(--employee-accent);
  color: white;
}

.knowledge-articles {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.article-item {
  background-color: var(--agent-bg-secondary);
  border-radius: var(--border-radius);
  padding: var(--spacing-md);
  cursor: pointer;
  transition: var(--transition);
}

.article-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.article-item h3 {
  font-size: 0.9375rem;
  font-weight: 600;
  margin: 0 0 var(--spacing-sm) 0;
  color: var(--agent-text-primary);
}

.article-item p {
  font-size: 0.8125rem;
  color: var(--agent-text-secondary);
  margin: 0 0 var(--spacing-xs) 0;
  line-height: 1.4;
}

.article-meta {
  font-size: 0.75rem;
  color: var(--agent-text-tertiary);
}

/* 质检报告视图 */
.quality-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
  display: flex;
  flex-direction: column;
}

.quality-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
}

.quality-header h2 {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
  color: var(--agent-text-primary);
}

.quality-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.quality-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.summary-item {
  background-color: var(--agent-bg-secondary);
  border-radius: var(--border-radius);
  padding: var(--spacing-md);
  text-align: center;
}

.summary-item h3 {
  font-size: 0.875rem;
  font-weight: 500;
  margin: 0 0 var(--spacing-sm) 0;
  color: var(--agent-text-secondary);
}

.summary-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--employee-accent);
}

.quality-records-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.quality-records-container h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 var(--spacing-md) 0;
  color: var(--neon-cyan);
  text-shadow: 0 0 10px rgba(6, 182, 212, 0.3);
}

.quality-records {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  padding-right: var(--spacing-sm);
}

/* 赛博朋克滚动条样式 */
.quality-records::-webkit-scrollbar {
  width: 6px;
}

.quality-records::-webkit-scrollbar-track {
  background: rgba(6, 182, 212, 0.1);
  border-radius: 3px;
}

.quality-records::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, var(--neon-cyan), var(--neon-purple));
  border-radius: 3px;
  box-shadow: 0 0 6px rgba(6, 182, 212, 0.5);
}

.record-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, rgba(31, 41, 55, 0.95) 0%, rgba(55, 65, 81, 0.9) 100%);
  border: 1px solid var(--border-cyan);
  border-radius: var(--border-radius);
  padding: var(--spacing-md);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  position: relative;
  overflow: visible;
  min-height: 60px;
}

.record-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 3px;
  height: 100%;
  background: linear-gradient(180deg, var(--neon-cyan), var(--neon-purple));
  opacity: 0;
  transition: opacity 0.3s ease;
}

.record-item:hover {
  border-color: var(--neon-cyan);
  box-shadow: 0 0 20px rgba(6, 182, 212, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  transform: translateX(5px);
}

.record-item:hover::before {
  opacity: 1;
}

.record-item.active {
  border-color: var(--neon-cyan);
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.15) 0%, rgba(168, 85, 247, 0.1) 100%);
  box-shadow: 0 0 20px rgba(6, 182, 212, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.record-item.active::before {
  opacity: 1;
  box-shadow: 0 0 10px rgba(6, 182, 212, 0.8);
}

.record-info h4 {
  font-size: 0.875rem;
  font-weight: 500;
  margin: 0 0 var(--spacing-xs) 0;
  color: var(--agent-text-primary);
}

.record-meta {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.record-user {
  font-size: 0.75rem;
  color: var(--agent-text-secondary);
}

.record-time {
  font-size: 0.75rem;
  color: var(--agent-text-secondary);
}

.record-score {
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--neon-cyan);
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%);
  padding: 0.25rem 0.75rem;
  border-radius: 16px;
  border: 1px solid rgba(6, 182, 212, 0.3);
  box-shadow: 0 0 10px rgba(6, 182, 212, 0.2);
  text-shadow: 0 0 5px rgba(6, 182, 212, 0.5);
}

/* 右侧质检报告详情视图样式 */
.quality-report-detail-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.quality-report-detail-header {
  margin-bottom: var(--spacing-md);
}

.quality-report-detail-header h2 {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
  color: var(--agent-text-primary);
}

.quality-report-detail-content {
  background-color: var(--agent-bg-secondary);
  border-radius: var(--border-radius);
  padding: var(--spacing-md);
  flex: 1;
  overflow-y: auto;
}

.report-header {
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--agent-border);
}

.report-header h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 var(--spacing-sm) 0;
  color: var(--agent-text-primary);
}

.report-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-md);
  font-size: 0.75rem;
  color: var(--agent-text-secondary);
}

.report-score {
  font-weight: 600;
  color: var(--employee-accent);
}

.report-body {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.report-section h4 {
  font-size: 0.875rem;
  font-weight: 600;
  margin: 0 0 var(--spacing-sm) 0;
  color: var(--agent-text-primary);
}

.report-section p {
  font-size: 0.875rem;
  line-height: 1.5;
  margin: 0;
  color: var(--agent-text-primary);
  white-space: pre-wrap;
}

.report-detail-empty {
  background: linear-gradient(135deg, rgba(31, 41, 55, 0.9) 0%, rgba(55, 65, 81, 0.8) 100%);
  border: 1px solid rgba(6, 182, 212, 0.3);
  border-radius: 0.75rem;
  padding: 3rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #9ca3af;
}

.report-detail-empty .empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.6;
}

.report-detail-empty .empty-subtitle {
  font-size: 0.875rem;
  color: #6b7280;
  margin-top: 0.5rem;
}

/* 总评分展示 */
.report-total-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  background: linear-gradient(135deg, rgba(17, 24, 39, 0.8) 0%, rgba(31, 41, 55, 0.9) 100%);
  border: 1px solid rgba(168, 85, 247, 0.3);
  border-radius: 0.75rem;
  position: relative;
  overflow: hidden;
}

.report-total-score::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #a855f7, #ec4899, #f97316);
  background-size: 200% 100%;
  animation: rainbowBorder 3s linear infinite;
}

.total-score-value {
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  text-shadow: 0 0 20px currentColor;
}

.total-score-value.excellent {
  color: #10b981;
  text-shadow: 0 0 20px rgba(16, 185, 129, 0.5);
}

.total-score-value.good {
  color: #06b6d4;
  text-shadow: 0 0 20px rgba(6, 182, 212, 0.5);
}

.total-score-value.average {
  color: #f59e0b;
  text-shadow: 0 0 20px rgba(245, 158, 11, 0.5);
}

.total-score-value.poor {
  color: #ef4444;
  text-shadow: 0 0 20px rgba(239, 68, 68, 0.5);
}

.total-score-label {
  font-size: 0.875rem;
  color: #9ca3af;
  margin-bottom: 0.75rem;
}

.total-score-stars {
  display: flex;
  gap: 0.25rem;
}

.total-score-stars .star {
  font-size: 1.25rem;
  color: #4b5563;
  transition: all 0.3s ease;
}

.total-score-stars .star.filled {
  color: #f59e0b;
  text-shadow: 0 0 10px rgba(245, 158, 11, 0.5);
}

/* 详细评分项 */
.report-score-details {
  margin-bottom: 1.5rem;
  padding: 1.25rem;
  background: rgba(31, 41, 55, 0.6);
  border: 1px solid rgba(6, 182, 212, 0.2);
  border-radius: 0.625rem;
}

.score-details-title {
  font-size: 1rem;
  font-weight: 600;
  color: #f9fafb;
  margin: 0 0 1rem 0;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid rgba(6, 182, 212, 0.2);
}

.score-items {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.score-item {
  display: grid;
  grid-template-columns: 1fr auto;
  grid-template-rows: auto auto;
  gap: 0.5rem;
  align-items: center;
}

.score-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  grid-column: 1 / -1;
}

.score-item-name {
  font-size: 0.875rem;
  color: #e5e7eb;
  font-weight: 500;
}

.score-item-value {
  font-size: 0.875rem;
  color: #06b6d4;
  font-weight: 600;
  font-family: 'Courier New', monospace;
}

.score-item-bar {
  height: 8px;
  background: rgba(75, 85, 99, 0.5);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.score-item-progress {
  height: 100%;
  background: linear-gradient(90deg, #06b6d4 0%, #a855f7 100%);
  border-radius: 4px;
  transition: width 0.5s ease;
  box-shadow: 0 0 10px rgba(6, 182, 212, 0.3);
}

.score-item-percentage {
  font-size: 0.75rem;
  color: #9ca3af;
  text-align: right;
  min-width: 40px;
}

/* 报告内容区域 */
.report-content-box {
  padding: 1rem;
  background: rgba(17, 24, 39, 0.6);
  border: 1px solid rgba(75, 85, 99, 0.3);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  line-height: 1.6;
  color: #e5e7eb;
  white-space: pre-wrap;
  word-break: break-word;
}

.report-content-box.empty {
  color: #6b7280;
  font-style: italic;
}

/* 其他视图的右侧内容 */
.other-view-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: var(--spacing-lg);
}

/* 反馈收集视图的右侧空状态 */
.feedback-empty-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(17, 24, 39, 0.5) 0%, rgba(31, 41, 55, 0.3) 100%);
  position: relative;
  overflow: hidden;
}

.feedback-empty-view::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(rgba(6, 182, 212, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(6, 182, 212, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  pointer-events: none;
}

.view-header h2 {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0 0 var(--spacing-lg) 0;
}

.view-body p {
  font-size: 0.875rem;
  color: var(--agent-text-secondary);
  line-height: 1.5;
  margin: 0;
}

/* 知识库文章详情 */
.article-detail {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

/* 知识库文章头部 - 包含标题和删除按钮 */
.article-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--spacing-sm);
}

.article-header h3 {
  flex: 1;
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--agent-text-primary);
}

/* 删除知识库按钮 - 赛博朋克风格 */
.delete-knowledge-btn {
  position: relative;
  width: 28px;
  height: 28px;
  border: 1.5px solid rgba(239, 68, 68, 0.6);
  border-radius: 6px;
  background: rgba(239, 68, 68, 0.15);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  flex-shrink: 0;
}

.delete-knowledge-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.3) 0%, rgba(220, 38, 38, 0.15) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.delete-knowledge-btn:hover {
  border-color: rgba(239, 68, 68, 0.9);
  background: rgba(239, 68, 68, 0.25);
  transform: scale(1.1);
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.4), inset 0 0 10px rgba(239, 68, 68, 0.1);
}

.delete-knowledge-btn:hover::before {
  opacity: 1;
}

.delete-knowledge-btn:active {
  transform: scale(0.95);
}

.delete-knowledge-btn .delete-icon {
  font-size: 16px;
  color: rgba(239, 68, 68, 0.9);
  transition: all 0.3s ease;
  z-index: 1;
}

.delete-knowledge-btn:hover .delete-icon {
  color: #ff4444;
  filter: drop-shadow(0 0 6px rgba(239, 68, 68, 0.8));
}

.delete-knowledge-btn .btn-glow {
  position: absolute;
  inset: -3px;
  background: radial-gradient(circle, rgba(239, 68, 68, 0.5) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.delete-knowledge-btn:hover .btn-glow {
  opacity: 1;
  animation: pulse-danger 1.5s ease-in-out infinite;
}

@keyframes pulse-danger {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.15); }
}

/* ============================================
   赛博朋克删除确认弹窗 - Cyberpunk Delete Modal
   ============================================ */
.cyber-delete-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: modalFadeIn 0.3s ease;
}

@keyframes modalFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.cyber-delete-content {
  position: relative;
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.98) 0%, rgba(30, 41, 59, 0.98) 100%);
  border: 2px solid rgba(239, 68, 68, 0.5);
  border-radius: 4px;
  width: 90%;
  max-width: 520px;
  box-shadow:
    0 0 60px rgba(239, 68, 68, 0.3),
    0 0 120px rgba(239, 68, 68, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  overflow: hidden;
  animation: modalSlideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* 扫描线效果 */
.scan-line {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(239, 68, 68, 0.8), transparent);
  animation: scanLine 3s linear infinite;
  pointer-events: none;
}

.scan-line-delayed {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(239, 68, 68, 0.4), transparent);
  animation: scanLine 3s linear infinite;
  animation-delay: 1.5s;
  pointer-events: none;
}

@keyframes scanLine {
  0% { transform: translateY(0); opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { transform: translateY(400px); opacity: 0; }
}

/* 角落装饰 */
.corner-decoration {
  position: absolute;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(239, 68, 68, 0.6);
  pointer-events: none;
}

.corner-decoration.top-left {
  top: -2px;
  left: -2px;
  border-right: none;
  border-bottom: none;
}

.corner-decoration.top-right {
  top: -2px;
  right: -2px;
  border-left: none;
  border-bottom: none;
}

.corner-decoration.bottom-left {
  bottom: -2px;
  left: -2px;
  border-right: none;
  border-top: none;
}

.corner-decoration.bottom-right {
  bottom: -2px;
  right: -2px;
  border-left: none;
  border-top: none;
}

/* 头部 */
.cyber-delete-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(90deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.05) 100%);
  border-bottom: 1px solid rgba(239, 68, 68, 0.3);
}

.header-glitch {
  position: relative;
}

.glitch-text {
  font-size: 14px;
  font-weight: 700;
  color: #ef4444;
  letter-spacing: 2px;
  text-transform: uppercase;
  position: relative;
  animation: glitchText 2s infinite;
}

.glitch-text::before,
.glitch-text::after {
  content: attr(data-text);
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.glitch-text::before {
  color: #00ffff;
  animation: glitch-1 0.3s infinite linear alternate-reverse;
  clip-path: polygon(0 0, 100% 0, 100% 35%, 0 35%);
}

.glitch-text::after {
  color: #ff00ff;
  animation: glitch-2 0.3s infinite linear alternate-reverse;
  clip-path: polygon(0 65%, 100% 65%, 100% 100%, 0 100%);
}

@keyframes glitch-1 {
  0% { transform: translateX(0); }
  20% { transform: translateX(-2px); }
  40% { transform: translateX(2px); }
  60% { transform: translateX(-1px); }
  80% { transform: translateX(1px); }
  100% { transform: translateX(0); }
}

@keyframes glitch-2 {
  0% { transform: translateX(0); }
  20% { transform: translateX(2px); }
  40% { transform: translateX(-2px); }
  60% { transform: translateX(1px); }
  80% { transform: translateX(-1px); }
  100% { transform: translateX(0); }
}

.cyber-close-btn {
  width: 28px;
  height: 28px;
  border: 1px solid rgba(239, 68, 68, 0.4);
  border-radius: 4px;
  background: rgba(239, 68, 68, 0.1);
  color: rgba(239, 68, 68, 0.8);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.cyber-close-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.6);
  color: #ef4444;
}

/* 主体内容 */
.cyber-delete-body {
  padding: 24px 20px;
}

/* 警告区域 */
.warning-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 20px;
}

.warning-hologram {
  position: relative;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}

.warning-icon-large {
  font-size: 40px;
  color: #ef4444;
  z-index: 2;
  animation: iconPulse 2s ease-in-out infinite;
}

@keyframes iconPulse {
  0%, 100% { transform: scale(1); filter: drop-shadow(0 0 10px rgba(239, 68, 68, 0.5)); }
  50% { transform: scale(1.1); filter: drop-shadow(0 0 20px rgba(239, 68, 68, 0.8)); }
}

.hologram-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 2px solid rgba(239, 68, 68, 0.3);
  border-radius: 50%;
  animation: ringExpand 2s ease-out infinite;
}

.hologram-ring.delayed {
  animation-delay: 1s;
}

@keyframes ringExpand {
  0% { transform: scale(0.8); opacity: 1; }
  100% { transform: scale(1.3); opacity: 0; }
}

.warning-code {
  font-family: 'Courier New', monospace;
  font-size: 11px;
  color: rgba(239, 68, 68, 0.7);
  letter-spacing: 1px;
}

/* 警告信息 */
.alert-message {
  text-align: center;
  margin-bottom: 20px;
}

.alert-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
}

.alert-prefix,
.alert-suffix {
  color: rgba(239, 68, 68, 0.8);
}

.alert-blink {
  color: #ef4444;
  animation: blinkText 1s step-end infinite;
}

@keyframes blinkText {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0.3; }
}

.alert-text {
  color: #fff;
}

.alert-desc {
  font-size: 13px;
  color: rgba(148, 163, 184, 0.8);
  line-height: 1.6;
}

.code-comment {
  color: rgba(100, 116, 139, 0.8);
  font-style: italic;
}

.code-line {
  color: rgba(148, 163, 184, 0.9);
}

/* 数据终端 */
.data-terminal {
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 6px;
  margin-bottom: 20px;
  overflow: hidden;
}

.terminal-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: rgba(239, 68, 68, 0.1);
  border-bottom: 1px solid rgba(239, 68, 68, 0.2);
}

.terminal-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.terminal-dot.red { background: #ef4444; }
.terminal-dot.yellow { background: #f59e0b; }
.terminal-dot.green { background: #10b981; }

.terminal-title {
  margin-left: 8px;
  font-family: 'Courier New', monospace;
  font-size: 11px;
  color: rgba(148, 163, 184, 0.8);
  letter-spacing: 1px;
}

.terminal-body {
  padding: 12px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.terminal-line {
  margin-bottom: 8px;
}

.terminal-prompt {
  color: #10b981;
  margin-right: 8px;
}

.terminal-command {
  color: rgba(148, 163, 184, 0.9);
}

.terminal-output {
  padding-left: 16px;
}

.json-line {
  margin: 4px 0;
}

.json-key {
  color: #a855f7;
}

.json-colon {
  color: rgba(148, 163, 184, 0.6);
  margin: 0 4px;
}

.json-value.string {
  color: #10b981;
}

.json-value.warning {
  color: #f59e0b;
  animation: warningPulse 1.5s ease-in-out infinite;
}

@keyframes warningPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* 确认输入 */
.confirmation-input {
  margin-bottom: 20px;
}

.input-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: rgba(148, 163, 184, 0.9);
  margin-bottom: 8px;
}

.label-icon {
  color: #ef4444;
  font-weight: bold;
}

.cyber-input {
  width: 100%;
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 4px;
  color: #fff;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  letter-spacing: 2px;
  text-transform: uppercase;
  transition: all 0.3s ease;
  outline: none;
}

.cyber-input::placeholder {
  color: rgba(148, 163, 184, 0.4);
}

.cyber-input:focus {
  border-color: rgba(239, 68, 68, 0.6);
  box-shadow: 0 0 15px rgba(239, 68, 68, 0.2), inset 0 0 10px rgba(239, 68, 68, 0.05);
}

/* 底部按钮 */
.cyber-delete-footer {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(0, 0, 0, 0.3);
  border-top: 1px solid rgba(239, 68, 68, 0.2);
}

.cyber-btn-secondary {
  flex: 1;
  padding: 12px 20px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 4px;
  background: rgba(148, 163, 184, 0.1);
  color: rgba(148, 163, 184, 0.9);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.cyber-btn-secondary:hover {
  background: rgba(148, 163, 184, 0.15);
  border-color: rgba(148, 163, 184, 0.5);
  color: #fff;
}

.cyber-btn-destroy {
  flex: 1;
  padding: 12px 20px;
  border: 1px solid rgba(239, 68, 68, 0.5);
  border-radius: 4px;
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.1) 100%);
  color: #ef4444;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s ease;
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.1);
}

.cyber-btn-destroy:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.3) 0%, rgba(220, 38, 38, 0.2) 100%);
  border-color: rgba(239, 68, 68, 0.8);
  box-shadow: 0 0 25px rgba(239, 68, 68, 0.3);
  transform: translateY(-1px);
}

.cyber-btn-destroy:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.danger-header {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.1) 100%);
  border-bottom: 1px solid rgba(239, 68, 68, 0.3);
}

.danger-text {
  color: #ef4444;
  text-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
}

.confirm-body {
  padding: var(--spacing-lg);
  text-align: center;
}

.warning-icon {
  font-size: 3rem;
  margin-bottom: var(--spacing-md);
  animation: shake 0.5s ease-in-out;
}

@keyframes shake {
  0%, 100% { transform: rotate(0deg); }
  25% { transform: rotate(-10deg); }
  75% { transform: rotate(10deg); }
}

.confirm-message {
  margin-bottom: var(--spacing-lg);
}

.confirm-message .main-text {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--agent-text-primary);
  margin-bottom: var(--spacing-sm);
}

.confirm-message .sub-text {
  font-size: 0.875rem;
  color: var(--agent-text-secondary);
}

.data-preview {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: var(--tech-radius-md);
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
  text-align: left;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-xs) 0;
}

.preview-label {
  font-size: 0.875rem;
  color: var(--agent-text-secondary);
}

.preview-value {
  font-size: 0.875rem;
  font-weight: 600;
}

.neon-pink {
  color: #ec4899;
  text-shadow: 0 0 8px rgba(236, 72, 153, 0.4);
}

.neon-cyan {
  color: #06b6d4;
  text-shadow: 0 0 8px rgba(6, 182, 212, 0.4);
}

.confirm-actions {
  display: flex;
  gap: var(--spacing-md);
  justify-content: center;
}

.cyber-btn-outline {
  position: relative;
  padding: var(--spacing-sm) var(--spacing-lg);
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: var(--tech-radius-md);
  background: transparent;
  color: var(--agent-text-secondary);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  transition: all 0.3s ease;
}

.cyber-btn-outline:hover {
  border-color: rgba(148, 163, 184, 0.6);
  background: rgba(148, 163, 184, 0.1);
  color: var(--agent-text-primary);
}

.cyber-btn-danger {
  position: relative;
  padding: var(--spacing-sm) var(--spacing-lg);
  border: 1px solid rgba(239, 68, 68, 0.5);
  border-radius: var(--tech-radius-md);
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.1) 100%);
  color: #ef4444;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  transition: all 0.3s ease;
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.1);
}

.cyber-btn-danger:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.3) 0%, rgba(220, 38, 38, 0.2) 100%);
  border-color: rgba(239, 68, 68, 0.8);
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.3);
  transform: translateY(-1px);
}

.cyber-btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cyber-btn-danger .btn-icon {
  font-size: 1rem;
}

.article-detail h3 {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
  color: var(--agent-text-primary);
}

.article-meta-info {
  display: flex;
  gap: var(--spacing-md);
  font-size: 0.75rem;
  color: var(--agent-text-tertiary);
}

.article-content {
  flex: 1;
  overflow-y: auto;
  font-size: 0.875rem;
  line-height: 1.6;
  color: var(--agent-text-primary);
  white-space: pre-wrap;
}

.article-content h2 {
  font-size: 1rem;
  font-weight: 600;
  margin: 1.5em 0 0.5em 0;
  color: var(--employee-accent);
}

.article-content h3 {
  font-size: 0.9375rem;
  font-weight: 600;
  margin: 1.2em 0 0.4em 0;
  color: var(--agent-text-primary);
}

.article-content p {
  margin: 0.5em 0;
  color: var(--agent-text-primary);
}

.article-content ul, .article-content ol {
  margin: 0.5em 0 0.5em 1.5em;
  padding-left: 0;
}

.article-content li {
  margin: 0.3em 0;
  color: var(--agent-text-primary);
}

/* ============================================
   工单卡片 - Tech Ticket Card
   ============================================ */
.ticket-card {
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(51, 65, 85, 0.3) 100%);
  border: 1px solid var(--tech-border);
  border-radius: var(--tech-radius-lg);
  margin-bottom: var(--tech-space-4);
  cursor: pointer;
  transition: var(--tech-transition-base);
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(8px);
}

.ticket-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: var(--tech-primary-500);
  opacity: 0;
  transition: var(--tech-transition-base);
}

.ticket-card:hover {
  transform: translateY(-3px);
  border-color: var(--tech-primary-500);
  box-shadow: var(--tech-shadow-lg), var(--tech-shadow-glow);
}

.ticket-card:hover::before {
  opacity: 1;
}

.ticket-card.selected {
  border: 1px solid var(--tech-primary-500);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(30, 41, 59, 0.6) 100%);
  box-shadow: var(--tech-shadow-glow);
}

.ticket-card.selected::before {
  opacity: 1;
  background: var(--tech-gradient-primary);
}

/* 拖拽相关样式 */
.ticket-card.dragging {
  opacity: 0.7;
  transform: rotate(2deg) scale(1.02);
  box-shadow: var(--tech-shadow-lg);
  cursor: grabbing;
  border: 2px dashed var(--tech-primary-400);
}

.ticket-card.drag-over {
  border: 2px dashed var(--tech-primary-500);
  background: rgba(59, 130, 246, 0.1);
  transform: translateY(4px);
}

/* ============================================
   AI建议生成按钮样式 - Tech AI Buttons
   ============================================ */
.generate-suggestion-btn {
  background: var(--tech-gradient-primary);
  color: white;
  border: none;
  padding: var(--tech-space-3) var(--tech-space-5);
  border-radius: var(--tech-radius-lg);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: var(--tech-transition-base);
  margin-bottom: var(--tech-space-4);
  display: inline-flex;
  align-items: center;
  gap: var(--tech-space-2);
  position: relative;
  overflow: hidden;
}

.generate-suggestion-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--tech-shadow-glow);
}

.generate-suggestion-btn:disabled {
  background: var(--tech-bg-hover);
  color: var(--tech-text-muted);
  cursor: not-allowed;
  opacity: 0.7;
}

/* 建议控件区域 */
.suggestion-controls {
  display: flex;
  gap: var(--tech-space-3);
  margin-bottom: var(--tech-space-4);
}

/* 刷新按钮样式 */
.refresh-suggestion-btn {
  background: linear-gradient(135deg, var(--tech-success) 0%, #059669 100%);
  color: white;
  border: none;
  padding: var(--tech-space-3) var(--tech-space-5);
  border-radius: var(--tech-radius-lg);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: var(--tech-transition-base);
  display: inline-flex;
  align-items: center;
  gap: var(--tech-space-2);
  min-width: auto;
}



.refresh-suggestion-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--tech-shadow-glow-success);
}

.refresh-suggestion-btn:disabled {
  background: var(--tech-bg-hover);
  color: var(--tech-text-muted);
  cursor: not-allowed;
  opacity: 0.7;
}

/* 通知相关样式 */
.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid var(--employee-border);
}

.notification-header h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--agent-text-primary);
}

.mark-read-btn {
  background-color: var(--employee-accent);
  color: white;
  border: none;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: var(--transition);
}

.mark-read-btn:hover {
  background-color: #36a0a8;
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

/* ============================================
   通知项 - Tech Notification Item
   ============================================ */
.notification-item {
  padding: var(--tech-space-4) var(--tech-space-5);
  border-bottom: 1px solid var(--tech-border);
  transition: var(--tech-transition-base);
  cursor: pointer;
}

.notification-item:last-child {
  border-bottom: none;
}

.notification-item:hover {
  background: rgba(59, 130, 246, 0.05);
}

.notification-item.unread {
  background: rgba(59, 130, 246, 0.1);
  border-left: 3px solid var(--tech-primary-500);
  padding-left: calc(var(--tech-space-5) - 3px);
}

.notification-item.read {
  background: transparent;
  border-left: 3px solid transparent;
  opacity: 0.7;
}

.notification-item.read .notification-content {
  color: var(--tech-text-muted);
}

.notification-content {
  margin: 0 0 var(--tech-space-2) 0;
  font-size: 0.875rem;
  color: var(--tech-text-primary);
  line-height: 1.5;
  padding-left: var(--tech-space-2);
}

.notification-time {
  font-size: 0.75rem;
  color: var(--tech-text-muted);
  padding-left: var(--tech-space-2);
  display: flex;
  align-items: center;
  gap: var(--tech-space-2);
}

.notification-time::before {
  content: '🕐';
  font-size: 0.625rem;
}

/* 全部已读按钮 */
.mark-read-btn {
  background: var(--tech-gradient-primary);
  color: white;
  border: none;
  padding: var(--tech-space-2) var(--tech-space-4);
  border-radius: var(--tech-radius-md);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: var(--tech-transition-base);
}

.mark-read-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--tech-shadow-glow);
}

/* ============================================
   工单列表 - Tech Ticket List
   ============================================ */
.ticket-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--tech-space-4);
  min-height: 200px;
}

.ticket-list::-webkit-scrollbar {
  width: 6px;
}

.ticket-list::-webkit-scrollbar-track {
  background: transparent;
}

.ticket-list::-webkit-scrollbar-thumb {
  background: var(--tech-border);
  border-radius: var(--tech-radius-full);
}

.ticket-list::-webkit-scrollbar-thumb:hover {
  background: var(--tech-border-light);
}

.ticket-priority-bar {
  height: 4px;
  width: 100%;
  position: relative;
  overflow: hidden;
}

.ticket-priority-bar::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.ticket-content {
  padding: var(--tech-space-5);
}

.ticket-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 var(--tech-space-3) 0;
  color: var(--tech-text-primary);
  line-height: 1.4;
}

.ticket-preview {
  font-size: 0.875rem;
  color: var(--tech-text-secondary);
  margin: 0 0 var(--tech-space-4) 0;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ticket-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--tech-space-3);
  font-size: 0.75rem;
}

.ticket-department {
  color: var(--tech-text-muted);
  display: flex;
  align-items: center;
  gap: var(--tech-space-1);
}

.ticket-department::before {
  content: '🏢';
}

.ticket-category {
  background: rgba(59, 130, 246, 0.15);
  color: var(--tech-primary-400);
  padding: var(--tech-space-1) var(--tech-space-3);
  border-radius: var(--tech-radius-full);
  font-weight: 500;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.ticket-time {
  color: var(--tech-text-muted);
  display: flex;
  align-items: center;
  gap: var(--tech-space-1);
}

.ticket-time::before {
  content: '🕐';
}

.ticket-quick-actions {
  position: absolute;
  top: var(--tech-space-3);
  right: var(--tech-space-3);
  display: flex;
  gap: var(--tech-space-2);
  opacity: 0;
  transition: var(--tech-transition-base);
}

.ticket-card:hover .ticket-quick-actions {
  opacity: 1;
}

.quick-action-btn {
  background: rgba(30, 41, 59, 0.9);
  color: var(--tech-text-secondary);
  border: 1px solid var(--tech-border);
  padding: var(--tech-space-2);
  border-radius: var(--tech-radius-md);
  cursor: pointer;
  transition: var(--tech-transition-base);
  font-size: 0.875rem;
  backdrop-filter: blur(4px);
}

.quick-action-btn:hover {
  background: var(--tech-gradient-primary);
  color: white;
  border-color: transparent;
  transform: translateY(-2px);
  box-shadow: var(--tech-shadow-glow);
}

/* 右侧处理台 */
.ticket-processing {
  width: 47%;
  background-color: var(--agent-bg-primary);
  overflow-y: auto;
  padding: var(--spacing-lg);
}

.no-ticket-selected {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--agent-text-secondary);
  font-size: 1.125rem;
}

.processing-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

/* 工单摘要区 */
.ticket-summary {
  background-color: var(--agent-bg-secondary);
  border-radius: var(--border-radius);
  padding: var(--spacing-lg);
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-md);
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.user-avatar-small {
  width: 40px;
  height: 40px;
  border-radius: 50%;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.user-name {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.user-department {
  font-size: 0.875rem;
  color: var(--agent-text-secondary);
}

.ticket-priority {
  display: flex;
  align-items: center;
}

.priority-badge {
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 16px;
  font-size: 0.875rem;
  font-weight: 600;
}

.ticket-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0 0 var(--spacing-md) 0;
  color: var(--agent-text-primary);
}

.ticket-description {
  font-size: 0.875rem;
  color: var(--agent-text-secondary);
  line-height: 1.5;
  margin: 0;
}

/* ============================================
   AI作战面板 - Enhanced AI Panel
   ============================================ */
.ai-panel {
  background: linear-gradient(180deg, #1a1f2e 0%, #0f1419 100%);
  border: 1px solid var(--tech-border);
  border-radius: var(--tech-radius-xl);
  padding: var(--tech-space-6);
  color: var(--tech-text-primary);
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

/* 顶部标题分隔线 */
.ai-panel h3 {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0 0 var(--tech-space-5) 0;
  color: var(--tech-text-primary);
  display: flex;
  align-items: center;
  gap: var(--tech-space-3);
  padding-bottom: var(--tech-space-4);
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
}

.ai-panel h3::before {
  content: '🤖';
  font-size: 1.5rem;
  filter: drop-shadow(0 0 8px rgba(67, 97, 238, 0.5));
}

/* 智能回复建议区域 */
.ai-suggestion {
  margin-bottom: var(--tech-space-6);
  position: relative;
}

.ai-suggestion h4 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 var(--tech-space-4) 0;
  color: var(--tech-text-primary);
  display: flex;
  align-items: center;
  gap: var(--tech-space-2);
}

/* 黄色灯泡图标 */
.ai-suggestion h4::before {
  content: '💡';
  font-size: 1.125rem;
  filter: drop-shadow(0 0 6px rgba(255, 209, 102, 0.6));
}

/* 生成智能回复按钮 - 品牌主色 #4361EE */
.generate-suggestion-btn {
  background: linear-gradient(135deg, #4361EE 0%, #3651d4 100%);
  color: white;
  border: none;
  padding: var(--tech-space-3) var(--tech-space-6);
  border-radius: var(--tech-radius-lg);
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: inline-flex;
  align-items: center;
  gap: var(--tech-space-2);
  box-shadow: 0 4px 14px rgba(67, 97, 238, 0.4);
  position: relative;
  overflow: hidden;
}

/* 按钮悬停效果 */
.generate-suggestion-btn:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 6px 20px rgba(67, 97, 238, 0.5);
  background: linear-gradient(135deg, #4d6bf0 0%, #4361EE 100%);
}

/* 按钮点击动画 */
.generate-suggestion-btn:active:not(:disabled) {
  transform: translateY(0) scale(0.98);
}

/* 按钮焦点样式 - 键盘导航 */
.generate-suggestion-btn:focus-visible {
  outline: 2px solid #FFD166;
  outline-offset: 2px;
}

/* 按钮禁用状态 */
.generate-suggestion-btn:disabled {
  background: linear-gradient(135deg, #475569 0%, #334155 100%);
  color: var(--tech-text-muted);
  cursor: not-allowed;
  opacity: 0.7;
  box-shadow: none;
}



/* 刷新按钮 */
.refresh-btn-container {
  position: absolute;
  bottom: 0;
  right: 0;
  margin-bottom: var(--tech-space-4);
}

.refresh-suggestion-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  padding: var(--tech-space-2) var(--tech-space-4);
  border-radius: var(--tech-radius-md);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: var(--tech-space-2);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.refresh-suggestion-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}

.refresh-suggestion-btn:focus-visible {
  outline: 2px solid #FFD166;
  outline-offset: 2px;
}

/* 建议输入框 */
.suggestion-input {
  width: 100%;
  padding: var(--tech-space-4);
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: var(--tech-radius-lg);
  background: rgba(15, 23, 42, 0.8);
  color: var(--tech-text-primary);
  font-family: inherit;
  font-size: 0.9375rem;
  line-height: 1.7;
  margin-bottom: var(--tech-space-4);
  resize: vertical;
  min-height: 140px;
  transition: all 0.2s ease;
}

.suggestion-input:focus {
  outline: none;
  border-color: #4361EE;
  box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.15);
}

.suggestion-item {
  margin-bottom: var(--tech-space-4);
  background: rgba(67, 97, 238, 0.08);
  border: 1px solid rgba(67, 97, 238, 0.25);
  border-radius: var(--tech-radius-lg);
  padding: var(--tech-space-4);
  transition: all 0.3s ease;
}

.suggestion-item:hover {
  background: rgba(67, 97, 238, 0.12);
  border-color: rgba(67, 97, 238, 0.4);
  transform: translateX(4px);
}

/* 加载状态 */
.loading-suggestions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--tech-space-3);
  padding: var(--tech-space-8);
  background: rgba(15, 23, 42, 0.6);
  border-radius: var(--tech-radius-lg);
  border: 1px dashed rgba(148, 163, 184, 0.3);
  color: var(--tech-text-secondary);
}

/* 空状态提示 */
.no-suggestions {
  padding: var(--tech-space-8);
  background: rgba(30, 41, 59, 0.4);
  border-radius: var(--tech-radius-lg);
  border: 1px dashed rgba(148, 163, 184, 0.3);
  text-align: center;
  color: var(--tech-text-muted);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--tech-space-3);
}

.no-suggestions::before {
  content: '📝';
  font-size: 2rem;
  opacity: 0.5;
}

/* 采纳按钮 */
.adopt-btn {
  background: linear-gradient(135deg, #4361EE 0%, #3651d4 100%);
  color: white;
  border: none;
  padding: var(--tech-space-3) var(--tech-space-6);
  border-radius: var(--tech-radius-lg);
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: var(--tech-space-2);
  box-shadow: 0 4px 14px rgba(67, 97, 238, 0.3);
}

.adopt-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(67, 97, 238, 0.4);
}

.adopt-btn:focus-visible {
  outline: 2px solid #FFD166;
  outline-offset: 2px;
}

.adopt-btn::before {
  content: '✓';
}

/* 字段提取结果区域 - 卡片样式 */
.field-extraction {
  margin-bottom: var(--tech-space-6);
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: var(--tech-radius-lg);
  padding: var(--tech-space-5);
}

.field-extraction h4 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 var(--tech-space-4) 0;
  color: var(--tech-text-primary);
  display: flex;
  align-items: center;
  gap: var(--tech-space-2);
}

/* 字段提取图标 - 亮色 #FFD166 */
.field-extraction h4::before {
  content: '🏷️';
  color: #FFD166;
  filter: drop-shadow(0 0 4px rgba(255, 209, 102, 0.4));
}

.extracted-fields {
  display: flex;
  flex-wrap: wrap;
  gap: var(--tech-space-3);
}

.field-tag {
  background: rgba(67, 97, 238, 0.15);
  color: #e0e7ff;
  padding: var(--tech-space-2) var(--tech-space-3);
  border-radius: var(--tech-radius-full);
  font-size: 0.875rem;
  border: 1px solid rgba(67, 97, 238, 0.3);
  transition: all 0.2s ease;
}

.field-tag:hover {
  background: rgba(67, 97, 238, 0.25);
  transform: translateY(-1px);
}

.field-tag.placeholder {
  background: rgba(148, 163, 184, 0.1);
  color: var(--tech-text-muted);
  border-style: dashed;
}

/* 相关知识片段区域 - 卡片样式 */
.related-knowledge {
  margin-bottom: var(--tech-space-6);
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: var(--tech-radius-lg);
  padding: var(--tech-space-5);
}

.related-knowledge h4 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 var(--tech-space-4) 0;
  color: var(--tech-text-primary);
  display: flex;
  align-items: center;
  gap: var(--tech-space-2);
}

/* 知识片段图标 - 亮色 #FFD166 */
.related-knowledge h4::before {
  content: '📚';
  color: #FFD166;
  filter: drop-shadow(0 0 4px rgba(255, 209, 102, 0.4));
}

.knowledge-list {
  display: flex;
  flex-direction: column;
  gap: var(--tech-space-3);
}

.knowledge-item {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.15);
  border-radius: var(--tech-radius-md);
  padding: var(--tech-space-4);
  transition: all 0.2s ease;
}

.knowledge-item:hover {
  border-color: rgba(67, 97, 238, 0.3);
  background: rgba(15, 23, 42, 0.8);
}

.knowledge-content {
  color: var(--tech-text-secondary);
  font-size: 0.875rem;
  line-height: 1.6;
  margin: 0 0 var(--tech-space-2) 0;
}

.knowledge-source {
  color: #FFD166;
  font-size: 0.75rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: var(--tech-space-1);
}

.knowledge-source::before {
  content: '📎';
}

/* 友好空状态 - 暂无相关知识片段 */
.no-knowledge {
  padding: var(--tech-space-8);
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.6) 100%);
  border-radius: var(--tech-radius-lg);
  border: 1px dashed rgba(148, 163, 184, 0.3);
  text-align: center;
  color: var(--tech-text-secondary);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--tech-space-3);
}

.no-knowledge::before {
  content: '📭';
  font-size: 2.5rem;
  opacity: 0.8;
  margin-bottom: var(--tech-space-2);
  filter: drop-shadow(0 0 8px rgba(255, 209, 102, 0.3));
}

.no-knowledge p {
  font-size: 0.9375rem;
  line-height: 1.5;
  color: var(--tech-text-secondary);
}

/* 响应式适配 */
@media (max-width: 768px) {
  .ai-panel {
    padding: var(--tech-space-4);
  }
  
  .ai-panel h3 {
    font-size: 1.125rem;
  }
  
  .generate-suggestion-btn {
    width: 100%;
    justify-content: center;
  }
  
  .field-extraction,
  .related-knowledge {
    padding: var(--tech-space-4);
  }
  
  .extracted-fields {
    gap: var(--tech-space-2);
  }
  
  .field-tag {
    font-size: 0.8125rem;
  }
}

/* 高对比度模式支持 */
@media (prefers-contrast: high) {
  .generate-suggestion-btn {
    border: 2px solid white;
  }
  
  .field-tag {
    border-width: 2px;
  }
  
  .suggestion-input:focus {
    outline-width: 3px;
  }
}

/* 减少动画偏好支持 */
@media (prefers-reduced-motion: reduce) {
  .generate-suggestion-btn,
  .adopt-btn,
  .refresh-suggestion-btn,
  .field-tag,
  .suggestion-item {
    transition: none;
  }
  
  .generate-suggestion-btn:hover:not(:disabled) {
    transform: none;
  }
}

.knowledge-item {
  background-color: white;
  padding: var(--spacing-md);
  border-radius: var(--border-radius);
  border: 1px solid var(--employee-border);
  max-height: 200px;
  overflow-y: auto;
}

.knowledge-content {
  font-size: 0.875rem;
  font-weight: 500;
  margin: 0 0 var(--spacing-xs) 0;
  color: #333333;
  line-height: 1.4;
  white-space: pre-wrap;
}

.knowledge-source {
  font-size: 0.75rem;
  color: #666666;
}

.no-knowledge {
  background-color: white;
  padding: var(--spacing-md);
  border-radius: var(--border-radius);
  border: 1px solid var(--employee-border);
  text-align: center;
  color: #666666;
  font-size: 0.875rem;
}

/* 操作工作区 */
.action-workspace {
  background-color: var(--agent-bg-secondary);
  border-radius: var(--border-radius);
  padding: var(--spacing-lg);
}

.action-workspace h3 {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0 0 var(--spacing-lg) 0;
}

.reply-section {
  margin-bottom: var(--spacing-lg);
}

.reply-input {
  width: 100%;
  padding: var(--spacing-md);
  border: 1px solid var(--agent-border);
  border-radius: var(--border-radius);
  background-color: var(--agent-bg-primary);
  color: var(--agent-text-primary);
  font-family: inherit;
  font-size: 0.875rem;
  line-height: 1.5;
  margin-bottom: var(--spacing-md);
  resize: vertical;
  min-height: 120px;
}

.quick-replies {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.quick-reply-btn {
  background-color: var(--agent-bg-primary);
  color: var(--agent-text-primary);
  border: 1px solid var(--agent-border);
  padding: 0.25rem 0.75rem;
  border-radius: var(--border-radius);
  font-size: 0.75rem;
  cursor: pointer;
  transition: var(--transition);
}

.quick-reply-btn:hover {
  background-color: var(--employee-accent);
  color: white;
  border-color: var(--employee-accent);
}

.attachment-section {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.attachment-btn {
  background-color: var(--agent-bg-primary);
  color: var(--agent-text-primary);
  border: 1px solid var(--agent-border);
  padding: 0.5rem 1rem;
  border-radius: var(--border-radius);
  font-size: 0.875rem;
  cursor: pointer;
  transition: var(--transition);
}

.attachment-btn:hover {
  background-color: var(--agent-bg-light);
}

.quality-check-btn {
  background-color: var(--agent-bg-primary);
  color: var(--agent-text-primary);
  border: 1px solid var(--agent-border);
  padding: 0.5rem 1rem;
  border-radius: var(--border-radius);
  font-size: 0.875rem;
  cursor: pointer;
  transition: var(--transition);
}

.quality-check-btn:hover {
  background-color: var(--agent-bg-light);
}

/* 知识库上传按钮样式 */
.knowledge-actions {
  margin: var(--spacing-md) 0;
  text-align: center;
}

.upload-knowledge-btn {
  background-color: var(--employee-accent);
  color: white;
  border: none;
  padding: var(--spacing-sm) var(--spacing-lg);
  border-radius: var(--border-radius);
  font-size: 0.875rem;
  cursor: pointer;
  transition: var(--transition);
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.upload-knowledge-btn:hover {
  background-color: #36a0a8;
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.main-actions {
  display: flex;
  gap: var(--spacing-md);
  justify-content: flex-end;
}

.transfer-btn {
  background-color: var(--agent-bg-primary);
  color: var(--agent-text-primary);
  border: 1px solid var(--agent-border);
  padding: 0.5rem 1.5rem;
  border-radius: var(--border-radius);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition);
}

.transfer-btn:hover {
  background-color: var(--agent-bg-light);
}

.send-close-btn {
  background-color: var(--employee-accent);
  color: white;
  border: none;
  padding: 0.5rem 1.5rem;
  border-radius: var(--border-radius);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition);
}

.send-close-btn:hover {
  transform: scale(1.02);
  box-shadow: var(--shadow-md);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .nav-sidebar {
    width: 20%;
  }
  
  .ticket-pool {
    width: 33%;
  }
  
  .ticket-processing {
    width: 47%;
  }
}

@media (max-width: 992px) {
  .nav-sidebar {
    width: 25%;
  }
  
  .ticket-pool {
    width: 35%;
  }
  
  .ticket-processing {
    width: 40%;
  }
}

@media (max-width: 768px) {
  .agent-main {
    flex-direction: column;
  }
  
  .nav-sidebar {
    width: 100%;
    height: 60px;
    overflow-x: auto;
    overflow-y: hidden;
  }
  
  .sidebar-nav {
    display: flex;
    padding: 0;
  }
  
  .nav-item {
    white-space: nowrap;
    border-left: none;
    border-bottom: 3px solid transparent;
  }
  
  .nav-item.active {
    border-left: none;
    border-bottom-color: var(--employee-accent);
  }
  
  .ticket-pool {
    width: 100%;
    height: 300px;
  }
  
  .ticket-processing {
    width: 100%;
    flex: 1;
  }
}

/* 拖拽上传区域样式 */
.upload-area {
  background-color: var(--agent-bg-secondary);
  border: 2px dashed var(--agent-border);
  border-radius: var(--border-radius);
  padding: var(--spacing-xl);
  margin-bottom: var(--spacing-lg);
  text-align: center;
  transition: var(--transition);
  cursor: pointer;
}

.upload-area:hover {
  border-color: var(--employee-accent);
  background-color: rgba(67, 183, 194, 0.05);
}

.upload-area.dragging {
  border-color: var(--employee-accent);
  background-color: rgba(67, 183, 194, 0.1);
  transform: scale(1.01);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-md);
}

.upload-icon {
  font-size: 2.5rem;
  color: var(--agent-text-secondary);
  transition: var(--transition);
}

.upload-area:hover .upload-icon,
.upload-area.dragging .upload-icon {
  color: var(--employee-accent);
}

.upload-content h3 {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
  color: var(--agent-text-primary);
}

.upload-content p {
  font-size: 0.875rem;
  color: var(--agent-text-secondary);
  margin: 0;
}

/* 响应式设计 - 拖拽上传区域 */
@media (max-width: 768px) {
  .upload-area {
    padding: var(--spacing-lg);
  }
  
  .upload-icon {
    font-size: 2rem;
  }
  
  .upload-content h3 {
    font-size: 1rem;
  }
}
/* 质检预览卡片样式 */
.quality-preview-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.quality-preview-card {
  background-color: var(--agent-bg-secondary);
  border-radius: var(--border-radius);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.quality-preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--agent-border);
}

.quality-preview-header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: var(--agent-text-primary);
}

.close-btn {
  background: transparent;
  border: none;
  font-size: 1.5rem;
  color: var(--agent-text-secondary);
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 50%;
  transition: var(--transition);
}

.close-btn:hover {
  background-color: var(--agent-bg-primary);
  color: var(--agent-text-primary);
}

.quality-preview-content {
  padding: var(--spacing-lg);
}

.preview-section {
  margin-bottom: var(--spacing-lg);
}

.preview-section h4 {
  margin: 0 0 var(--spacing-md) 0;
  font-size: 1rem;
  color: var(--agent-text-secondary);
  font-weight: 500;
}

.preview-score {
  font-size: 2rem;
  font-weight: 600;
  color: var(--employee-accent);
  margin-bottom: var(--spacing-md);
}

.preview-user-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.preview-user {
  font-weight: 500;
  color: var(--agent-text-primary);
}

.preview-department {
  color: var(--agent-text-secondary);
  font-size: 0.875rem;
}

.preview-content,
.preview-response {
  margin: 0;
  color: var(--agent-text-primary);
  line-height: 1.5;
  white-space: pre-wrap;
}

.preview-response {
  min-height: 100px;
  padding: var(--spacing-md);
  background-color: var(--agent-bg-primary);
  border-radius: var(--border-radius);
}

.quality-preview-footer {
  padding: var(--spacing-lg);
  border-top: 1px solid var(--agent-border);
  display: flex;
  justify-content: flex-end;
}

.confirm-btn {
  background-color: var(--employee-accent);
  color: white;
  border: none;
  padding: var(--spacing-md) var(--spacing-xl);
  border-radius: var(--border-radius);
  cursor: pointer;
  transition: var(--transition);
  font-size: 1rem;
}

.confirm-btn:hover {
  background-color: var(--employee-accent-dark);
}

/* 响应式调整 */
@media (max-width: 768px) {
  .quality-preview-card {
    width: 95%;
    margin: var(--spacing-md);
  }
  
  .quality-preview-header,
  .quality-preview-content,
  .quality-preview-footer {
    padding: var(--spacing-md);
  }
}

/* ============================================
   全局动画效果 - Global Animations
   ============================================ */

/* 淡入动画 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 滑入动画 */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* 缩放动画 */
@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* 旋转动画 */
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 闪烁动画 */
@keyframes blink {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* 弹跳动画 */
@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}

/* 应用动画类 */
.animate-fade-in {
  animation: fadeIn 0.3s ease-out;
}

.animate-slide-in {
  animation: slideIn 0.3s ease-out;
}

.animate-scale-in {
  animation: scaleIn 0.2s ease-out;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

.animate-blink {
  animation: blink 1.5s ease-in-out infinite;
}

.animate-bounce {
  animation: bounce 1s ease-in-out infinite;
}

/* ============================================
   响应式适配 - Responsive Design
   ============================================ */
@media (max-width: 1400px) {
  .dashboard-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 1200px) {
  .agent-header {
    padding: var(--tech-space-3) var(--tech-space-6);
  }
  
  .app-title {
    font-size: 1.25rem;
  }
  
  .nav-sidebar {
    width: 220px;
  }
  
  .dashboard-cards {
    gap: var(--tech-space-4);
  }
  
  .card-value {
    font-size: 1.75rem;
  }
}

@media (max-width: 992px) {
  .agent-view {
    font-size: 14px;
  }
  
  .header-right {
    gap: var(--tech-space-4);
  }
  
  .status-switcher {
    display: none;
  }
  
  .nav-sidebar {
    width: 180px;
  }
  
  .dashboard-cards {
    grid-template-columns: 1fr;
  }
  
  .ticket-pool {
    width: 40%;
  }
  
  .ticket-processing {
    width: 45%;
  }
}

@media (max-width: 768px) {
  .agent-header {
    padding: var(--tech-space-3);
    flex-wrap: wrap;
    gap: var(--tech-space-3);
  }
  
  .header-left {
    gap: var(--tech-space-2);
  }
  
  .logo {
    width: 32px;
    height: 32px;
    font-size: 1.25rem;
  }
  
  .app-title {
    font-size: 1.125rem;
  }
  
  .header-right {
    width: 100%;
    justify-content: space-between;
  }
  
  .pending-count {
    order: -1;
  }
  
  .main-container {
    flex-direction: column;
  }
  
  .nav-sidebar {
    width: 100%;
    height: auto;
    flex-direction: row;
    padding: var(--tech-space-3);
    border-right: none;
    border-bottom: 1px solid var(--tech-border);
    overflow-x: auto;
  }
  
  .nav-item {
    white-space: nowrap;
    padding: var(--tech-space-2) var(--tech-space-4);
  }
  
  .nav-item::before {
    display: none;
  }
  
  .content-area {
    flex-direction: column;
  }
  
  .ticket-pool,
  .ticket-processing {
    width: 100%;
    height: 50%;
  }
  
  .dashboard-right-view {
    padding: var(--tech-space-4);
  }
  
  .dashboard-cards {
    grid-template-columns: 1fr;
    gap: var(--tech-space-4);
  }
  
  .notification-dropdown {
    width: 280px;
    right: -20px;
  }
}

@media (max-width: 480px) {
  .agent-view {
    font-size: 13px;
  }
  
  .app-title {
    font-size: 1rem;
  }
  
  .card-value {
    font-size: 1.5rem;
  }
  
  .dashboard-card {
    padding: var(--tech-space-4);
  }
  
  .ai-panel {
    padding: var(--tech-space-4);
  }
  
  .suggestion-input {
    min-height: 100px;
  }
}

/* 减少动画偏好 */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* ============================================
   赛博朋克加载弹窗 - Cyberpunk Loading Modal
   ============================================ */

.cyber-loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(2, 8, 38, 0.9);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.cyber-loading-modal {
  position: relative;
  background: linear-gradient(135deg, rgba(17, 24, 39, 0.98) 0%, rgba(31, 41, 55, 0.95) 100%);
  border: 2px solid var(--neon-cyan);
  border-radius: 1rem;
  padding: 2.5rem 3rem;
  min-width: 320px;
  box-shadow: 
    0 0 40px rgba(6, 182, 212, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  animation: modalPulse 2s ease-in-out infinite;
  overflow: hidden;
}

@keyframes modalPulse {
  0%, 100% { 
    box-shadow: 0 0 40px rgba(6, 182, 212, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  }
  50% { 
    box-shadow: 0 0 60px rgba(6, 182, 212, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  }
}

/* 角落装饰 */
.cyber-corner {
  position: absolute;
  width: 20px;
  height: 20px;
  border: 2px solid var(--neon-cyan);
  opacity: 0.6;
}

.cyber-corner.top-left {
  top: 10px;
  left: 10px;
  border-right: none;
  border-bottom: none;
}

.cyber-corner.top-right {
  top: 10px;
  right: 10px;
  border-left: none;
  border-bottom: none;
}

.cyber-corner.bottom-left {
  bottom: 10px;
  left: 10px;
  border-right: none;
  border-top: none;
}

.cyber-corner.bottom-right {
  bottom: 10px;
  right: 10px;
  border-left: none;
  border-top: none;
}

/* 扫描线效果 */
.cyber-scan-line {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--neon-cyan), transparent);
  animation: scanLine 2s linear infinite;
  opacity: 0.6;
}

@keyframes scanLine {
  0% { transform: translateY(0); }
  100% { transform: translateY(200px); }
}

.cyber-loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  position: relative;
  z-index: 1;
}

/* 赛博朋克旋转器 */
.cyber-spinner {
  position: relative;
  width: 80px;
  height: 80px;
}

.spinner-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border: 3px solid transparent;
  border-top-color: var(--neon-cyan);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner-ring:nth-child(1) {
  width: 80px;
  height: 80px;
  animation-duration: 1s;
  border-top-color: var(--neon-cyan);
  box-shadow: 0 0 20px rgba(6, 182, 212, 0.5);
}

.spinner-ring:nth-child(2) {
  width: 60px;
  height: 60px;
  animation-duration: 0.8s;
  animation-direction: reverse;
  border-top-color: var(--neon-purple);
  box-shadow: 0 0 15px rgba(168, 85, 247, 0.5);
}

.spinner-ring:nth-child(3) {
  width: 40px;
  height: 40px;
  animation-duration: 0.6s;
  border-top-color: var(--neon-pink);
  box-shadow: 0 0 10px rgba(236, 72, 153, 0.5);
}

@keyframes spin {
  0% { transform: translate(-50%, -50%) rotate(0deg); }
  100% { transform: translate(-50%, -50%) rotate(360deg); }
}

/* 加载文本 */
.cyber-loading-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.loading-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: white;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  text-shadow: 0 0 20px rgba(6, 182, 212, 0.8);
  animation: textGlow 1.5s ease-in-out infinite alternate;
}

@keyframes textGlow {
  from { text-shadow: 0 0 20px rgba(6, 182, 212, 0.8); }
  to { text-shadow: 0 0 30px rgba(6, 182, 212, 1), 0 0 40px rgba(168, 85, 247, 0.5); }
}

.loading-subtitle {
  font-size: 0.875rem;
  color: var(--text-secondary);
  text-align: center;
  max-width: 280px;
  line-height: 1.5;
}

/* 进度条 */
.cyber-loading-progress {
  width: 100%;
  position: relative;
}

.progress-bar {
  height: 4px;
  background: rgba(75, 85, 99, 0.3);
  border-radius: 2px;
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--neon-cyan), var(--neon-purple), var(--neon-pink));
  background-size: 200% 100%;
  border-radius: 2px;
  animation: progressMove 1.5s ease-in-out infinite, gradientShift 2s linear infinite;
  box-shadow: 0 0 10px rgba(6, 182, 212, 0.5);
}

@keyframes progressMove {
  0% { width: 0%; margin-left: 0%; }
  50% { width: 50%; margin-left: 25%; }
  100% { width: 0%; margin-left: 100%; }
}

@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  100% { background-position: 200% 50%; }
}

/* 网格背景 */
.progress-grid {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(90deg, rgba(6, 182, 212, 0.1) 1px, transparent 1px);
  background-size: 20px 100%;
  pointer-events: none;
}

/* 响应式适配 */
@media (max-width: 480px) {
  .cyber-loading-modal {
    padding: 2rem;
    min-width: 280px;
    margin: 1rem;
  }
  
  .cyber-spinner {
    width: 60px;
    height: 60px;
  }
  
  .spinner-ring:nth-child(1) {
    width: 60px;
    height: 60px;
  }
  
  .spinner-ring:nth-child(2) {
    width: 45px;
    height: 45px;
  }
  
  .spinner-ring:nth-child(3) {
    width: 30px;
    height: 30px;
  }
  
  .loading-title {
    font-size: 1.1rem;
  }
}
</style>