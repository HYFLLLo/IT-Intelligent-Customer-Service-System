<script setup lang="ts">
import { ref, onMounted } from 'vue'
import FeedbackWidget from '../components/FeedbackWidget.vue'
import { analytics } from '@/analytics'
import { BusinessEventType, UserRole } from '@/analytics/types'

// 生成真实的时间戳
const getRealTimestamp = (hoursOffset = 0) => {
  const date = new Date()
  date.setHours(date.getHours() + hoursOffset)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()
  const isYesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000).toDateString() === date.toDateString()
  
  if (isToday) {
    return `今天 ${date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`
  } else if (isYesterday) {
    return `昨天 ${date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`
  } else {
    return date.toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  }
}

const getTimeOnly = (hoursOffset = 0) => {
  const date = new Date()
  date.setHours(date.getHours() + hoursOffset)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 状态管理
const messages = ref([
  {
    id: 1,
    type: 'system',
    content: '你好！我是IT智能助手，有什么可以帮你的吗？',
    timestamp: getTimeOnly(0),
    source: 'IT手册V3.2',
    confidence: 0.95
  }
])

// 通知管理
const notifications = ref([])
const showNotifications = ref(false)
const selectedNotification = ref(null)
const showNotificationDetail = ref(false)
const isLoadingNotifications = ref(false)

const conversations = ref([
  {
    id: 1,
    title: '如何重置密码？',
    timestamp: getRealTimestamp(-2),
    isActive: false,
    messages: [
      {
        id: 1,
        type: 'user',
        content: '如何重置密码？',
        timestamp: getTimeOnly(-2)
      },
      {
        id: 2,
        type: 'system',
        content: '要重置密码，请按照以下步骤操作：\n1. 访问公司内网的密码重置页面\n2. 输入您的用户名和邮箱\n3. 点击"发送验证码"按钮\n4. 输入收到的验证码\n5. 设置新密码并确认\n6. 点击"确认重置"按钮',
        timestamp: getTimeOnly(-2),
        source: 'IT手册V3.2',
        confidence: 0.95
      }
    ]
  },
  {
    id: 2,
    title: '打印机连接问题',
    timestamp: getRealTimestamp(-25),
    isActive: false,
    messages: [
      {
        id: 1,
        type: 'user',
        content: '我的打印机无法连接到电脑',
        timestamp: getTimeOnly(-25)
      },
      {
        id: 2,
        type: 'system',
        content: '打印机连接问题可能由以下原因引起：\n1.  USB连接线松动或损坏\n2.  打印机驱动程序过时\n3.  打印机服务未启动\n4.  网络连接问题（如果是网络打印机）\n\n建议您先检查USB连接线，然后尝试重新安装打印机驱动程序。',
        timestamp: getTimeOnly(-25),
        source: 'IT故障排查指南',
        confidence: 0.90
      }
    ]
  },
  {
    id: 3,
    title: 'Office安装失败',
    timestamp: getRealTimestamp(-33),
    isActive: false,
    messages: [
      {
        id: 1,
        type: 'user',
        content: 'Office安装失败，提示错误代码30088',
        timestamp: getTimeOnly(-33)
      },
      {
        id: 2,
        type: 'system',
        content: '错误代码30088通常表示Office安装过程中遇到了网络问题。\n\n建议您：\n1. 检查网络连接是否稳定\n2. 暂时禁用防火墙和杀毒软件\n3. 使用Office部署工具进行安装\n4. 清理之前的Office安装残留\n\n如果问题仍然存在，请联系IT支持团队获取进一步帮助。',
        timestamp: getTimeOnly(-33),
        source: 'Office安装指南',
        confidence: 0.85
      }
    ]
  }
])

const inputMessage = ref('')
const isLoading = ref(false)
const hotQuestions = [
  '如何重置密码？',
  'Office安装失败怎么办？',
  'WiFi连接不上？'
]
const suggestedTags = ref(['网络', '软件', '账号'])

// 添加工单相关状态
const showCreateTicket = ref(false)
const ticketTitle = ref('')
const ticketDescription = ref('')
const ticketPriority = ref('medium')
const ticketUser = ref('')
const ticketDepartment = ref('')

// 方法
const sendMessage = async () => {
  if (!inputMessage.value.trim()) return

  // 记录提交问题埋点
  const submitStartTime = Date.now()
  const questionContent = inputMessage.value

  // 添加用户消息
  const userMessage = {
    id: Date.now(),
    type: 'user',
    content: inputMessage.value,
    timestamp: new Date().toLocaleTimeString()
  }
  messages.value.push(userMessage)

  // 清空输入
  const message = inputMessage.value
  inputMessage.value = ''
  
  // 添加AI消息占位符
  const aiMessageId = Date.now() + 1
  const aiMessage = {
    id: aiMessageId,
    type: 'system',
    content: '',
    timestamp: new Date().toLocaleTimeString(),
    source: '知识库',
    confidence: 0.0,
    isStreaming: true
  }
  messages.value.push(aiMessage)
  
  // 获取当前活动会话
  let activeConversation = conversations.value.find(conv => conv.isActive)
  
  // 如果没有活动会话，自动创建一个新会话
  if (!activeConversation) {
    // 生成新会话ID
    const newId = Math.max(...conversations.value.map(conv => conv.id), 0) + 1
    
    // 取消所有会话的激活状态
    conversations.value.forEach(conv => {
      conv.isActive = false
    })
    
    // 创建新会话
    const questionTitle = message.trim().substring(0, 30)
    activeConversation = {
      id: newId,
      title: questionTitle,
      timestamp: getRealTimestamp(0),
      isActive: true,
      messages: [
        {
          ...userMessage,
          timestamp: getTimeOnly(0)
        },
        {
          ...aiMessage,
          timestamp: getTimeOnly(0)
        }
      ]
    }
    
    // 添加新会话到列表
    conversations.value.unshift(activeConversation)
  } else {
    // 确保会话有messages数组
    if (!activeConversation.messages) {
      activeConversation.messages = []
    }
    // 如果是新会话且是第一次发送用户消息，更新会话标题为用户的问题
    if (activeConversation.title === '新会话') {
      // 截取问题的前30个字符作为会话标题
      const questionTitle = message.trim().substring(0, 30)
      activeConversation.title = questionTitle
      // 更新会话时间戳为当前时间
      activeConversation.timestamp = getRealTimestamp(0)
    }
    // 添加用户消息到会话历史
    activeConversation.messages.push({
      ...userMessage,
      timestamp: getTimeOnly(0)
    })
    // 添加AI消息占位符到会话历史（稍后会更新）
    activeConversation.messages.push({
      ...aiMessage,
      timestamp: getTimeOnly(0)
    })
  }
  
  // 调用后端API获取AI回复（流式）
    isLoading.value = true
    try {
      const response = await fetch('http://localhost:8000/api/v1/employee/question/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json; charset=utf-8',
          'Accept': 'application/json; charset=utf-8'
        },
        body: JSON.stringify({
          question: message
        })
      })
    
    if (response.ok) {
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let completeAnswer = ''
      let confidence = 0.0
      let suggestion = ''
      let buffer = ''  // 用于处理跨chunk的不完整数据
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value, { stream: true })
        buffer += chunk
        
        // 处理SSE格式 - 按行分割
        const lines = buffer.split('\n')
        // 保留最后一行（可能不完整）
        buffer = lines.pop() || ''
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.substring(6).trim()
            if (data) {
              try {
                const jsonData = JSON.parse(data)
                
                if (jsonData.error) {
                  // 错误处理
                  aiMessage.content = `抱歉，处理过程中发生错误：${jsonData.error}`
                  aiMessage.isStreaming = false
                  messages.value = [...messages.value]
                } else if (jsonData.end) {
                  // 流式结束
                  confidence = jsonData.confidence
                  suggestion = jsonData.suggestion
                } else if (jsonData.text) {
                  // 普通文本块
                  completeAnswer += jsonData.text
                  aiMessage.content = completeAnswer
                  messages.value = [...messages.value]
                }
              } catch (e) {
                // JSON解析失败，忽略
                console.error('JSON解析失败:', e, data)
              }
            }
          }
        }
      }
      
      // 处理缓冲区中剩余的数据
      if (buffer.startsWith('data: ')) {
        const data = buffer.substring(6).trim()
        if (data) {
          try {
            const jsonData = JSON.parse(data)
            if (jsonData.text) {
              completeAnswer += jsonData.text
              aiMessage.content = completeAnswer
            } else if (jsonData.end) {
              confidence = jsonData.confidence
              suggestion = jsonData.suggestion
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
      
      // 完成流式传输
      aiMessage.isStreaming = false
      aiMessage.confidence = confidence
      aiMessage.suggestion = suggestion
      // 强制触发响应式更新
      messages.value = [...messages.value]

      // 上报提交问题埋点
      analytics.track(BusinessEventType.SUBMIT_QUESTION, {
        questionId: String(aiMessageId),
        questionType: 'text',
        questionSummary: questionContent.substring(0, 50),
        questionLength: questionContent.length,
        hasAttachment: false,
        submitDuration: Date.now() - submitStartTime,
        userRole: UserRole.EMPLOYEE
      })
      
      // 更新会话历史中的AI消息
      const activeConversation = conversations.value.find(conv => conv.isActive)
      if (activeConversation && activeConversation.messages) {
        // 找到会话历史中的AI消息占位符
        const aiMessageInHistory = activeConversation.messages.find(msg => msg.id === aiMessageId)
        if (aiMessageInHistory) {
          // 更新AI消息内容
          aiMessageInHistory.content = aiMessage.content
          aiMessageInHistory.confidence = aiMessage.confidence
          aiMessageInHistory.suggestion = aiMessage.suggestion
          aiMessageInHistory.isStreaming = false
          aiMessageInHistory.source = aiMessage.source
        }
      }
    } else {
      // 回退到普通请求
      const fallbackResponse = await fetch('http://localhost:8000/api/v1/employee/question', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json; charset=utf-8',
          'Accept': 'application/json; charset=utf-8'
        },
        body: JSON.stringify({
          question: message
        })
      })
      
      if (fallbackResponse.ok) {
        const data = await fallbackResponse.json()
        aiMessage.content = data.answer
        aiMessage.confidence = data.confidence
        aiMessage.suggestion = data.suggestion
      } else {
        aiMessage.content = '抱歉，AI服务暂时不可用，请稍后再试。'
        aiMessage.source = '系统'
      }
      aiMessage.isStreaming = false
      
      // 更新会话历史中的AI消息
      const activeConversation = conversations.value.find(conv => conv.isActive)
      if (activeConversation && activeConversation.messages) {
        // 找到会话历史中的AI消息占位符
        const aiMessageInHistory = activeConversation.messages.find(msg => msg.id === aiMessageId)
        if (aiMessageInHistory) {
          // 更新AI消息内容
          aiMessageInHistory.content = aiMessage.content
          aiMessageInHistory.confidence = aiMessage.confidence
          aiMessageInHistory.suggestion = aiMessage.suggestion
          aiMessageInHistory.isStreaming = false
          aiMessageInHistory.source = aiMessage.source
        }
      }
    }
  } catch (error) {
    console.error('流式请求错误:', error)
    // 回退到普通请求
    try {
      const fallbackResponse = await fetch('http://localhost:8000/api/v1/employee/question', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json; charset=utf-8',
          'Accept': 'application/json; charset=utf-8'
        },
        body: JSON.stringify({
          question: message
        })
      })
      
      if (fallbackResponse.ok) {
        const data = await fallbackResponse.json()
        aiMessage.content = data.answer
        aiMessage.confidence = data.confidence
        aiMessage.suggestion = data.suggestion
      } else {
        aiMessage.content = '抱歉，AI服务暂时不可用，请稍后再试。'
        aiMessage.source = '系统'
      }
    } catch (fallbackError) {
      aiMessage.content = '网络连接失败，请检查您的网络设置。'
      aiMessage.source = '系统'
    } finally {
      aiMessage.isStreaming = false
      
      // 更新会话历史中的AI消息
      const activeConversation = conversations.value.find(conv => conv.isActive)
      if (activeConversation && activeConversation.messages) {
        // 找到会话历史中的AI消息占位符
        const aiMessageInHistory = activeConversation.messages.find(msg => msg.id === aiMessageId)
        if (aiMessageInHistory) {
          // 更新AI消息内容
          aiMessageInHistory.content = aiMessage.content
          aiMessageInHistory.confidence = aiMessage.confidence
          aiMessageInHistory.suggestion = aiMessage.suggestion
          aiMessageInHistory.isStreaming = false
          aiMessageInHistory.source = aiMessage.source
        }
      }
    }
  } finally {
    isLoading.value = false
  }
}

const selectConversation = (conversationId) => {
  // 切换会话状态
  conversations.value.forEach(conv => {
    conv.isActive = conv.id === conversationId
  })
  
  // 加载会话历史消息
  const selectedConversation = conversations.value.find(conv => conv.id === conversationId)
  if (selectedConversation && selectedConversation.messages) {
    // 清空当前消息
    messages.value = []
    // 添加会话历史消息
    selectedConversation.messages.forEach(msg => {
      messages.value.push({
        ...msg,
        // 确保消息有完整的时间戳格式
        timestamp: msg.timestamp
      })
    })
  }
}

const deleteConversation = (conversationId, event) => {
  event.stopPropagation()
  conversations.value = conversations.value.filter(conv => conv.id !== conversationId)
}

const createNewConversation = () => {
  // 生成新会话ID
  const newId = Math.max(...conversations.value.map(conv => conv.id), 0) + 1
  
  // 取消所有会话的激活状态
  conversations.value.forEach(conv => {
    conv.isActive = false
  })
  
  // 创建新会话
  const newConversation = {
    id: newId,
    title: '新会话',
    timestamp: getRealTimestamp(0),
    isActive: true,
    messages: [
      {
        id: 1,
        type: 'system',
        content: '你好！我是IT智能助手，有什么可以帮你的吗？',
        timestamp: getTimeOnly(0),
        source: 'IT手册V3.2',
        confidence: 0.95
      }
    ]
  }
  
  // 添加新会话到列表
  conversations.value.unshift(newConversation)
  
  // 加载新会话的消息
  messages.value = []
  newConversation.messages.forEach(msg => {
    messages.value.push({
      ...msg,
      timestamp: msg.timestamp
    })
  })
}

const selectHotQuestion = (question) => {
  inputMessage.value = question
}

const selectTag = (tag) => {
  inputMessage.value += ` ${tag}`
}

const toggleCreateTicket = () => {
  showCreateTicket.value = !showCreateTicket.value
}

const createTicket = async () => {
  if (!ticketTitle.value.trim() || !ticketDescription.value.trim() || !ticketUser.value.trim() || !ticketDepartment.value.trim()) {
    alert('请填写工单标题、详细描述、姓名和部门')
    return
  }

  // 记录创建工单开始时间
  const createStartTime = Date.now()

  isLoading.value = true
  try {
    const response = await fetch('http://localhost:8000/api/v1/employee/ticket', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json; charset=utf-8'
      },
      body: JSON.stringify({
        title: ticketTitle.value,
        description: ticketDescription.value,
        priority: ticketPriority.value,
        user: ticketUser.value,
        department: ticketDepartment.value,
        category: 'technical' // 默认分类为技术问题
      })
    })

    if (response.ok) {
      const data = await response.json()
      const systemMessage = {
        id: Date.now(),
        type: 'system',
        content: `已为您创建工单，工单ID: ${data.id}，将有客服人员尽快回复您。`,
        timestamp: new Date().toLocaleTimeString(),
        source: '系统',
        confidence: 1.0
      }
      messages.value.push(systemMessage)

      // 上报创建工单埋点
      analytics.track(BusinessEventType.CREATE_TICKET, {
        ticketId: String(data.id),
        ticketTitle: ticketTitle.value,
        priority: ticketPriority.value,
        department: ticketDepartment.value,
        descriptionLength: ticketDescription.value.length,
        createStartTime: createStartTime,
        createEndTime: Date.now(),
        duration: Date.now() - createStartTime,
        userRole: UserRole.EMPLOYEE
      })

      // 重置表单
      ticketTitle.value = ''
      ticketDescription.value = ''
      ticketPriority.value = 'medium'
      ticketUser.value = ''
      ticketDepartment.value = ''
      showCreateTicket.value = false
    } else {
      const errorMessage = {
        id: Date.now(),
        type: 'system',
        content: '创建工单失败，请稍后再试。',
        timestamp: new Date().toLocaleTimeString(),
        source: '系统',
        confidence: 1.0
      }
      messages.value.push(errorMessage)
    }
  } catch (error) {
    const errorMessage = {
      id: Date.now(),
      type: 'system',
      content: '网络连接失败，请检查您的网络设置。',
      timestamp: new Date().toLocaleTimeString(),
      source: '系统',
      confidence: 1.0
    }
    messages.value.push(errorMessage)
  } finally {
    isLoading.value = false
  }
}

// 获取指定AI消息对应的问题文本
const getQuestionForMessage = (messageId: number) => {
  // 找到当前AI消息的索引
  const messageIndex = messages.value.findIndex(msg => msg.id === messageId)
  if (messageIndex <= 0) return ''

  // 向前查找最近的用户消息
  for (let i = messageIndex - 1; i >= 0; i--) {
    if (messages.value[i].type === 'user') {
      return messages.value[i].content
    }
  }
  return ''
}

const transferToAgent = async () => {
  // 调用后端API创建工单
  isLoading.value = true
  
  // 记录创建工单开始时间（用于埋点）
  const createStartTime = Date.now()
  
  try {
    // 获取最近的对话内容作为工单描述
    const recentMessages = messages.value
      .filter(msg => msg.type === 'user' || msg.type === 'system')
      .map(msg => `${msg.type === 'user' ? '用户' : 'AI'}: ${msg.content}`)
      .join('\n')
    
    // 这里可以添加默认的用户信息，或者从其他地方获取
    const defaultUser = ticketUser.value || '用户'
    const defaultDepartment = ticketDepartment.value || '未知部门'
    
    const response = await fetch('http://localhost:8000/api/v1/employee/ticket', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json; charset=utf-8'
      },
      body: JSON.stringify({
        title: '人工客服请求',
        description: recentMessages,
        priority: 'medium',
        user: defaultUser,
        department: defaultDepartment,
        source: 'transferred'  // 标记为转人工创建的工单
      })
    })
    
    if (response.ok) {
      const data = await response.json()
      
      // 上报创建工单埋点（转工单方式）
      analytics.track(BusinessEventType.CREATE_TICKET, {
        ticketId: String(data.id),
        ticketTitle: '人工客服请求',
        priority: 'medium',
        department: defaultDepartment,
        descriptionLength: recentMessages.length,
        createStartTime: createStartTime,
        createEndTime: Date.now(),
        duration: Date.now() - createStartTime,
        source: 'transferred',
        userRole: UserRole.EMPLOYEE
      })
      
      const systemMessage = {
        id: Date.now(),
        type: 'system',
        content: `已为您创建工单，工单ID: ${data.id}，将有客服人员尽快回复您。`,
        timestamp: new Date().toLocaleTimeString(),
        source: '系统',
        confidence: 1.0
      }
      messages.value.push(systemMessage)
    } else {
      const errorMessage = {
        id: Date.now(),
        type: 'system',
        content: '创建工单失败，请稍后再试。',
        timestamp: new Date().toLocaleTimeString(),
        source: '系统',
        confidence: 1.0
      }
      messages.value.push(errorMessage)
    }
  } catch (error) {
    const errorMessage = {
      id: Date.now(),
      type: 'system',
      content: '网络连接失败，请检查您的网络设置。',
      timestamp: new Date().toLocaleTimeString(),
      source: '系统',
      confidence: 1.0
    }
    messages.value.push(errorMessage)
  } finally {
    isLoading.value = false
  }
}

const uploadImage = () => {
  // 模拟上传图片
  alert('上传功能开发中...')
}

// 通知相关方法
const toggleNotifications = () => {
  // 切换通知列表显示状态
  showNotifications.value = !showNotifications.value
  showNotificationDetail.value = false
}

const showNotificationList = () => {
  showNotifications.value = true
  showNotificationDetail.value = false
}

const viewNotificationDetail = (notification) => {
  selectedNotification.value = notification
  showNotificationDetail.value = true
  showNotifications.value = false
}

const closeNotificationDetail = () => {
  showNotificationDetail.value = false
  selectedNotification.value = null
}

const getUnreadCount = () => {
  return notifications.value.filter(n => !n.isRead).length
}

// 获取通知列表
const fetchNotifications = async () => {
  try {
    isLoadingNotifications.value = true
    const response = await fetch('http://localhost:8000/api/v1/employee/notifications', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json; charset=utf-8'
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      // 转换通知数据，添加时间戳和report字段
      notifications.value = data.map(notification => {
        // 转换score为5分制
        const score = notification.score ? notification.score / 10 : 0
        
        // 使用后端返回的完整报告数据（如果有）
        let reportData = notification.report_data
        
        // 如果没有完整的报告数据，则使用基础数据构建
        if (!reportData) {
          reportData = {
            id: notification.report_id,
            ticketId: notification.ticket_id,
            title: notification.title.replace('质检报告：', ''),
            content: notification.content || '工单内容暂无',
            response: notification.response || '处理结果暂无',
            score: score,
            user: '未知用户',
            department: '未知部门',
            createdAt: notification.created_at,
            scoreDetails: [
              { name: '响应速度', score: 18, maxScore: 20, description: '响应及时' },
              { name: '解决方案', score: 22, maxScore: 25, description: '方案合理' },
              { name: '沟通态度', score: 19, maxScore: 20, description: '态度友好' },
              { name: '专业性', score: 18, maxScore: 20, description: '专业准确' },
              { name: '跟进处理', score: 14, maxScore: 15, description: '跟进及时' }
            ],
            comments: [],
            suggestions: []
          }
        }
        
        return {
          ...notification,
          timestamp: formatTimestamp(notification.created_at),
          report: reportData
        }
      })
    } else {
      console.error('获取通知列表失败:', response.status)
      // 如果获取通知失败，使用模拟数据
      notifications.value = [
        {
          id: 1,
          type: 'quality_report',
          title: '质检报告：业务系统登錄时出现错误',
          content: '用户无法登錄业务系统，提示密码错误，但用户确认密码正确。',
          response: '已为您重置密码，请使用新密码登錄系统。',
          timestamp: formatTimestamp(new Date().toISOString()),
          isRead: false,
          report: {
            id: 1,
            ticket_id: 1,
            title: '业务系统登錄时出现错误',
            content: '用户无法登錄业务系统，提示密码错误，但用户确认密码正确。',
            response: '已为您重置密码，请使用新密码登錄系统。',
            score: 4.0,
            evaluator: '系统',
            department: '质检部门',
            evaluation_time: formatTimestamp(new Date().toISOString()),
            issues: [],
            suggestions: []
          }
        }
      ]
    }
  } catch (error) {
    console.error('获取通知列表时发生错误:', error)
    // 如果获取通知失败，使用模拟数据
    notifications.value = [
      {
        id: 1,
        type: 'quality_report',
        title: '质检报告：业务系统登錄时出现错误',
        content: '用户无法登錄业务系统，提示密码错误，但用户确认密码正确。',
        response: '已为您重置密码，请使用新密码登錄系统。',
        timestamp: formatTimestamp(new Date().toISOString()),
        isRead: false,
        report: {
          id: 1,
          ticket_id: 1,
          title: '业务系统登錄时出现错误',
          content: '用户无法登錄业务系统，提示密码错误，但用户确认密码正确。',
          response: '已为您重置密码，请使用新密码登錄系统。',
          score: 4.0,
          evaluator: '系统',
          department: '质检部门',
          evaluation_time: formatTimestamp(new Date().toISOString()),
          issues: [],
          suggestions: []
        }
      }
    ]
  } finally {
    isLoadingNotifications.value = false
  }
}

// 标记通知为已读
const markNotificationAsRead = async (notificationId) => {
  try {
    const response = await fetch(`http://localhost:8000/api/v1/employee/notifications/${notificationId}/read`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (response.ok) {
      // 更新本地通知状态
      const notification = notifications.value.find(n => n.id === notificationId)
      if (notification) {
        notification.isRead = true
      }
    } else {
      console.error('标记通知为已读失败:', response.status)
    }
  } catch (error) {
    console.error('标记通知为已读时发生错误:', error)
  }
}

// 格式化时间戳
const formatTimestamp = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()
  const isYesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000).toDateString() === date.toDateString()
  
  if (isToday) {
    return `今天 ${date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`
  } else if (isYesterday) {
    return `昨天 ${date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}`
  } else {
    return date.toLocaleString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  }
}

// 获取评分样式类
const getScoreClass = (score) => {
  if (score >= 4.5) return 'excellent'
  if (score >= 3.5) return 'good'
  if (score >= 2.5) return 'average'
  return 'poor'
}

// 初始化
onMounted(() => {
  // 获取通知列表
  fetchNotifications()
  
  // 设置定期获取通知，每30秒更新一次
  setInterval(fetchNotifications, 30000)
})

// 格式化系统消息，支持标题、列表等结构化内容
const formatSystemMessage = (content) => {
  if (!content) return ''
  
  // 处理标题（# 标题）
  content = content.replace(/^# (.*$)/gm, '<h2 class="system-title">$1</h2>')
  content = content.replace(/^## (.*$)/gm, '<h3 class="system-subtitle">$1</h3>')
  
  // 处理有序列表（1. 项）
  content = content.replace(/^(\d+)\.\s+(.*$)/gm, '<li class="system-list-item">$2</li>')
  
  // 处理无序列表（- 项）
  content = content.replace(/^-\s+(.*$)/gm, '<li class="system-list-item">$1</li>')
  
  // 处理代码块（```代码```）
  content = content.replace(/```(.*?)```/gs, '<pre class="system-code"><code>$1</code></pre>')
  
  // 处理粗体（**文本**）
  content = content.replace(/\*\*(.*?)\*\*/g, '<strong class="system-bold">$1</strong>')
  
  // 处理段落
  content = content.split('\n\n').map(paragraph => {
    // 如果段落不是标题或列表，包装为段落
    if (!paragraph.match(/^<(h2|h3|ul|ol|pre)/)) {
      // 检查是否包含列表项
      if (paragraph.match(/<li class="system-list-item">/)) {
        return '<ol class="system-list">' + paragraph + '</ol>'
      }
      return '<p class="system-paragraph">' + paragraph + '</p>'
    }
    return paragraph
  }).join('')
  
  return content
}
</script>

<template>
  <div class="employee-view">
    <!-- 顶部导航栏 -->
    <header class="employee-header">
      <div class="header-left">
        <div class="logo">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <circle cx="16" cy="16" r="14" fill="#43B7C2" opacity="0.1"/>
            <path d="M10 16C10 13.7909 11.7909 12 14 12H18C20.2091 12 22 13.7909 22 16V19C22 21.2091 20.2091 23 18 23H14C11.7909 23 10 21.2091 10 19V16Z" fill="#43B7C2"/>
            <path d="M16 8V10" stroke="#43B7C2" stroke-width="3" stroke-linecap="round"/>
            <path d="M8 16H10" stroke="#43B7C2" stroke-width="3" stroke-linecap="round"/>
            <path d="M22 16H24" stroke="#43B7C2" stroke-width="3" stroke-linecap="round"/>
            <path d="M16 22V24" stroke="#43B7C2" stroke-width="3" stroke-linecap="round"/>
          </svg>
        </div>
        <h1 class="app-title">IT智能助手</h1>
      </div>
      <div class="header-right">
        <div class="notification-icon" @click="toggleNotifications">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M12 22C13.1 22 14 21.1 14 20H10C10 21.1 10.9 22 12 22Z" fill="currentColor"/>
            <path d="M19 15V10C19 5.58 15.42 2 11 2S3 5.58 3 10V15L1 17V18H23V17L21 15Z" fill="currentColor"/>
          </svg>
          <span v-if="getUnreadCount() > 0" class="notification-badge">{{ getUnreadCount() }}</span>
        </div>
      </div>
    </header>

    <!-- 通知列表弹窗 -->
    <div v-if="showNotifications" class="notification-list-popup">
      <div class="notification-list-header">
        <h3>通知列表 ({{ notifications.length }})</h3>
        <button class="close-button" @click="showNotifications = false">✕</button>
      </div>
      <div class="notification-list-content">
        <div v-if="notifications.length === 0" class="no-notifications">
          <p>暂无通知</p>
        </div>
        <div 
          v-for="notification in notifications" 
          :key="notification.id"
          class="notification-item"
          :class="{ unread: !notification.isRead }"
          @click="viewNotificationDetail(notification); markNotificationAsRead(notification.id); notification.isRead = true"
        >
          <div class="notification-item-icon">📋</div>
          <div class="notification-item-content">
            <h4 class="notification-item-title">{{ notification.title }}</h4>
            <p class="notification-item-time">{{ notification.timestamp }}</p>
          </div>
          <div v-if="!notification.isRead" class="notification-item-unread"></div>
        </div>
      </div>
    </div>

    <!-- 独立的质检报告详情卡片 -->
    <div v-if="showNotificationDetail && selectedNotification" class="quality-report-card">
      <div class="quality-report-header">
        <h3>质检报告详情</h3>
        <button class="close-button" @click="closeNotificationDetail">✕</button>
      </div>
      <div class="quality-report-content">
        <div v-if="selectedNotification.type === 'quality_report' && selectedNotification.report" class="quality-report-detail">
          <!-- 报告头部信息 -->
          <div class="report-header">
            <h4>{{ selectedNotification.report.title }}</h4>
            <div class="report-meta">
              <span class="report-user">{{ selectedNotification.report.user }} - {{ selectedNotification.report.department }}</span>
              <span class="report-time">{{ formatTimestamp(selectedNotification.report.createdAt) }}</span>
            </div>
          </div>
          
          <!-- 总评分展示 -->
          <div class="report-total-score">
            <div class="total-score-value" :class="getScoreClass(selectedNotification.report.score)">
              {{ selectedNotification.report.score }}
            </div>
            <div class="total-score-label">综合评分</div>
            <div class="total-score-stars">
              <span v-for="n in 5" :key="n" class="star" :class="{ 'filled': n <= Math.round(selectedNotification.report.score) }">★</span>
            </div>
          </div>
          
          <!-- 详细评分项 -->
          <div class="report-score-details" v-if="selectedNotification.report.scoreDetails">
            <h4 class="score-details-title">📊 评分详情</h4>
            <div class="score-items">
              <div v-for="(item, index) in selectedNotification.report.scoreDetails" :key="index" class="score-item">
                <div class="score-item-header">
                  <span class="score-item-name">{{ item.name }}</span>
                  <span class="score-item-value">{{ item.score.toFixed(2) }} / {{ item.maxScore }}</span>
                </div>
                <div class="score-item-bar">
                  <div class="score-item-progress" :style="{ width: (item.score / item.maxScore * 100) + '%' }"></div>
                </div>
                <div class="score-item-percentage">{{ (item.score / item.maxScore * 100).toFixed(0) }}%</div>
              </div>
            </div>
          </div>
          
          <!-- 报告内容 -->
          <div class="report-body">
            <div class="report-section">
              <h4>📝 问题描述</h4>
              <div class="report-content-box">{{ selectedNotification.report.content }}</div>
            </div>
            <div class="report-section">
              <h4>💬 工程师回复</h4>
              <div class="report-content-box" :class="{ 'empty': !selectedNotification.report.response }">
                {{ selectedNotification.report.response || '暂无工程师回复' }}
              </div>
            </div>
          </div>
          
        </div>
      </div>
    </div>

    <!-- 中央对话画布 -->
    <main class="employee-main">
      <!-- 左侧历史会话 -->
      <aside class="conversation-sidebar">
        <div class="sidebar-header">
          <h2 class="sidebar-title">历史会话</h2>
          <button class="new-conversation-btn" @click="createNewConversation" title="新建会话">
            ➕
          </button>
        </div>
        <div class="conversation-list">
          <div 
            v-for="conversation in conversations" 
            :key="conversation.id"
            class="conversation-item"
            :class="{ active: conversation.isActive }"
            @click="selectConversation(conversation.id)"
          >
            <div class="conversation-content">
              <h3 class="conversation-title">{{ conversation.title }}</h3>
              <p class="conversation-time">{{ conversation.timestamp }}</p>
            </div>
            <button 
              class="delete-conversation"
              @click="deleteConversation(conversation.id, $event)"
              title="删除会话"
            >
              🗑️
            </button>
          </div>
        </div>
      </aside>

      <!-- 右侧主对话区 -->
      <section class="chat-area">
        <div class="messages-container">
          <div 
            v-for="message in messages" 
            :key="message.id"
            class="message"
            :class="message.type"
          >
            <div class="message-content">
              <div v-if="message.isStreaming" class="streaming-container">
                <span>{{ message.content }}</span>
                <span class="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </span>
              </div>
              <div v-else class="rich-content">
                <!-- 富文本渲染，支持换行、标题、列表等 -->
                <template v-if="message.type === 'system'">
                  <div class="system-message-body">
                    <!-- 处理结构化内容，支持标题、列表等 -->
                    <div v-html="formatSystemMessage(message.content)"></div>
                  </div>
                </template>
                <template v-else>
                  {{ message.content }}
                </template>
              </div>
              
              <div v-if="message.type === 'system' && !message.isStreaming" class="message-meta">
                <span class="message-source">📚 来源：{{ message.source }}</span>
                <span v-if="message.confidence" class="message-confidence">
                  {{ message.confidence > 0.7 ? '✅ 高置信度' : '⚠️ 低置信度' }}
                </span>
                <!-- 只有AI回复的消息才显示转工单按钮，工单创建等系统消息不显示 -->
                <button
                  v-if="message.source !== '系统' || (message.content && !message.content.includes('已为您创建工单'))"
                  class="btn-transfer-small"
                  @click="transferToAgent"
                  title="转成工单"
                >
                  👤 转工单
                </button>
                <div v-if="message.confidence < 0.7" class="low-confidence">
                  <p class="confidence-message">💡 {{ message.suggestion || '建议补充更多信息，或点击【转工单】获取专属支持' }}</p>
                  <div class="confidence-buttons">
                    <button class="btn-secondary" @click="transferToAgent">转工单</button>
                    <button class="btn-primary">补充信息</button>
                  </div>
                </div>
              </div>
              <!-- 用户反馈组件 - 只在AI回复消息且不是系统消息时显示 -->
              <FeedbackWidget
                v-if="message.type === 'system' && !message.isStreaming && message.source !== '系统' && !message.content.includes('已为您创建工单')"
                :session-id="'session_' + message.id"
                :question-text="getQuestionForMessage(message.id)"
                :answer-text="message.content"
                :answer-generated-at="new Date().toISOString()"
              />
            </div>
            <div class="message-time">{{ message.timestamp }}</div>
          </div>
        </div>

        <!-- 底部输入区 -->
        <div class="input-area">
          <!-- 预置问题按钮 -->
          <div class="preset-questions">
            <span class="preset-label">常见问题：</span>
            <button 
              v-for="(question, index) in hotQuestions" 
              :key="index"
              class="preset-btn"
              @click="selectHotQuestion(question)"
            >
              {{ question }}
            </button>
          </div>
          <div class="suggested-tags" v-if="inputMessage">
            <span 
              v-for="(tag, index) in suggestedTags" 
              :key="index"
              class="tag"
              @click="selectTag(tag)"
            >
              {{ tag }}
            </span>
          </div>
          <div class="input-container">
            <div class="input-wrapper">
              <input
                v-model="inputMessage"
                type="text"
                placeholder="例如：如何重置密码？Office安装失败？"
                class="message-input"
                @keyup.enter="sendMessage"
              />
            </div>
            <button class="input-button" @click="toggleCreateTicket" title="添加工单">
              🎫
            </button>
            <button class="send-button" @click="sendMessage">
              发送
            </button>
          </div>
          
          <!-- 添加工单表单 -->
          <div v-if="showCreateTicket" class="create-ticket-form">
            <h3>📝 添加工单</h3>
            <div class="form-group">
              <label for="ticket-title">工单标题</label>
              <input
                v-model="ticketTitle"
                type="text"
                id="ticket-title"
                placeholder="请输入工单标题"
                class="ticket-input"
              />
            </div>
            <div class="form-group">
              <label for="ticket-description">详细描述</label>
              <textarea
                v-model="ticketDescription"
                id="ticket-description"
                placeholder="请详细描述您遇到的问题..."
                class="ticket-textarea"
                rows="4"
              ></textarea>
            </div>
            <div class="form-group">
              <label for="ticket-user">姓名</label>
              <input
                v-model="ticketUser"
                type="text"
                id="ticket-user"
                placeholder="请输入您的姓名"
                class="ticket-input"
              />
            </div>
            <div class="form-group">
              <label for="ticket-department">部门</label>
              <input
                v-model="ticketDepartment"
                type="text"
                id="ticket-department"
                placeholder="请输入您的部门"
                class="ticket-input"
              />
            </div>
            <div class="form-group">
              <label for="ticket-priority">优先级</label>
              <select
                v-model="ticketPriority"
                id="ticket-priority"
                class="ticket-select"
              >
                <option value="low">低</option>
                <option value="medium">中</option>
                <option value="high">高</option>
                <option value="emergency">紧急</option>
              </select>
            </div>
            <div class="form-actions">
              <button class="btn-secondary" @click="toggleCreateTicket">取消</button>
              <button class="btn-primary" @click="createTicket" :disabled="isLoading">
                {{ isLoading ? '提交中...' : '提交工单' }}
              </button>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
/* ============================================
   赛博朋克设计系统 - Cyberpunk Design System
   ============================================ */

/* CSS 变量定义 */
.employee-view {
  /* 霓虹色系 - Neon Colors */
  --neon-purple: #a855f7;
  --neon-pink: #ec4899;
  --neon-blue: #3b82f6;
  --neon-cyan: #06b6d4;
  --neon-green: #10b981;
  --neon-yellow: #f59e0b;
  --neon-red: #ef4444;

  /* 霓虹渐变 */
  --gradient-purple-pink: linear-gradient(135deg, #a855f7 0%, #ec4899 100%);
  --gradient-blue-cyan: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
  --gradient-cyan-green: linear-gradient(135deg, #06b6d4 0%, #10b981 100%);
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
  --neon-border-cyan: 2px solid var(--neon-cyan);
  --neon-border-purple: 2px solid var(--neon-purple);

  /* 霓虹发光 */
  --glow-cyan: 0 0 10px rgba(6, 182, 212, 0.5), 0 0 20px rgba(6, 182, 212, 0.3), 0 0 30px rgba(6, 182, 212, 0.2);
  --glow-purple: 0 0 10px rgba(168, 85, 247, 0.5), 0 0 20px rgba(168, 85, 247, 0.3), 0 0 30px rgba(168, 85, 247, 0.2);
  --glow-pink: 0 0 10px rgba(236, 72, 153, 0.5), 0 0 20px rgba(236, 72, 153, 0.3), 0 0 30px rgba(236, 72, 153, 0.2);

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

  /* 布局 */
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-deepest);
  font-family: var(--font-sans);
  position: relative;
  overflow: hidden;
}

/* 背景动画效果 */
.employee-view::before {
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

.employee-view::after {
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

/* ============================================
   顶部导航栏 - Cyberpunk Header
   ============================================ */
.employee-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4) var(--space-6);
  background: rgba(17, 24, 39, 0.9);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-cyan);
  position: relative;
  z-index: 50;
  box-shadow: var(--shadow-md);
}

.employee-header::before {
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

@keyframes rainbowBorder {
  0% {
    background-position: 0% 50%;
  }
  100% {
    background-position: 200% 50%;
  }
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.logo {
  width: 40px;
  height: 40px;
  background: var(--gradient-blue-cyan);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--glow-cyan);
  transition: var(--transition-base);
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

@keyframes hologramScan {
  0% {
    left: -100%;
  }
  50%, 100% {
    left: 100%;
  }
}

.logo:hover {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 0 30px rgba(6, 182, 212, 0.5);
}

.logo svg {
  filter: drop-shadow(0 0 8px rgba(6, 182, 212, 0.8));
  z-index: 1;
}

.app-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: 0.05em;
  font-family: var(--font-sans);
  text-shadow: 0 0 10px var(--neon-cyan);
  position: relative;
}

.app-title::after {
  content: attr(data-text);
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  color: var(--neon-pink);
  opacity: 0;
  animation: glitchText 3s infinite;
  clip-path: polygon(0 0, 100% 0, 100% 35%, 0 35%);
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

/* 通知图标 - 赛博朋克风格 */
.notification-icon {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: var(--transition-base);
  background: var(--bg-card);
  border: 1px solid var(--border-cyan);
  color: var(--neon-cyan);
}

.notification-icon::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: inherit;
  border: 1px solid var(--neon-cyan);
  opacity: 0;
  transition: var(--transition-base);
}

.notification-icon:hover {
  background: var(--bg-elevated);
  color: var(--text-primary);
  box-shadow: var(--glow-cyan);
  transform: translateY(-2px);
}

.notification-icon:hover::before {
  opacity: 1;
  animation: pulseBorder 1s ease-out;
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

.notification-icon svg {
  width: 20px;
  height: 20px;
  filter: drop-shadow(0 0 5px var(--neon-cyan));
}

.notification-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 20px;
  height: 20px;
  background: var(--gradient-purple-pink);
  color: white;
  font-size: 0.6875rem;
  font-weight: 700;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 var(--space-1);
  box-shadow: var(--glow-pink);
  animation: badgePulse 2s ease-in-out infinite;
  border: 1px solid var(--neon-pink);
}

@keyframes badgePulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: var(--glow-pink);
  }
  50% {
    transform: scale(1.15);
    box-shadow: 0 0 25px rgba(236, 72, 153, 0.6);
  }
}

/* 用户头像 - 赛博朋克风格 */
.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: var(--transition-base);
  background: var(--bg-card);
  border: 1px solid var(--border-purple);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.user-avatar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, transparent, rgba(168, 85, 247, 0.2), transparent);
  animation: hologramScan 4s ease-in-out infinite;
}

.user-avatar:hover {
  border-color: var(--neon-purple);
  box-shadow: var(--glow-purple);
  transform: translateY(-2px);
}

.user-avatar svg {
  color: var(--text-primary);
  filter: drop-shadow(0 0 5px var(--neon-purple));
}

/* ============================================
   中央对话画布 - Cyberpunk Main Layout
   ============================================ */
.employee-main {
  display: flex;
  flex: 1;
  overflow: hidden;
  position: relative;
}

/* ============================================
   左侧历史会话 - Cyberpunk Sidebar
   ============================================ */
.conversation-sidebar {
  width: 280px;
  background: var(--bg-card);
  border-right: 1px solid var(--border-cyan);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  backdrop-filter: blur(10px);
  box-shadow: var(--shadow-md);
  position: relative;
}

.conversation-sidebar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(180deg, var(--gradient-blue-cyan), transparent);
  opacity: 0.1;
  pointer-events: none;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4) var(--space-4);
  border-bottom: 1px solid var(--border-cyan);
  background: var(--bg-elevated);
}

.sidebar-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--neon-cyan);
  margin: 0;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  text-shadow: 0 0 10px rgba(6, 182, 212, 0.5);
}

.new-conversation-btn {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: var(--transition-base);
  background: transparent;
  color: var(--neon-cyan);
  border: 2px solid var(--neon-cyan);
  font-size: 1.25rem;
  font-weight: 600;
  position: relative;
  overflow: hidden;
}

.new-conversation-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: var(--gradient-blue-cyan);
  transition: var(--transition-base);
  z-index: -1;
}

.new-conversation-btn:hover {
  color: var(--text-primary);
  box-shadow: var(--glow-cyan);
  transform: translateY(-2px) scale(1.1);
}

.new-conversation-btn:hover::before {
  left: 0;
}

.new-conversation-btn:active {
  transform: translateY(0) scale(1);
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-3);
  position: relative;
}

.conversation-list::-webkit-scrollbar {
  width: 4px;
}

.conversation-list::-webkit-scrollbar-track {
  background: transparent;
}

.conversation-list::-webkit-scrollbar-thumb {
  background: var(--gradient-blue-cyan);
  border-radius: var(--radius-full);
}

.conversation-list::-webkit-scrollbar-thumb:hover {
  background: var(--neon-cyan);
  box-shadow: var(--glow-cyan);
}

/* 会话项 - 赛博朋克风格 */
.conversation-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: var(--space-3);
  margin-bottom: var(--space-2);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: var(--transition-base);
  background: var(--bg-surface);
  border: 1px solid transparent;
  position: relative;
  overflow: hidden;
}

.conversation-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 3px;
  height: 100%;
  background: var(--gradient-blue-cyan);
  opacity: 0;
  transition: var(--transition-base);
}

.conversation-item:hover {
  background: var(--bg-elevated);
  border-color: var(--border-cyan);
  transform: translateX(4px);
  box-shadow: var(--shadow-glow);
}

.conversation-item:hover::before {
  opacity: 1;
}

.conversation-item.active {
  background: var(--bg-elevated);
  border: 1px solid var(--neon-cyan);
  box-shadow: var(--glow-cyan), inset 0 0 20px rgba(6, 182, 212, 0.1);
}

.conversation-item.active::before {
  opacity: 1;
}

.conversation-content {
  flex: 1;
  min-width: 0;
  padding-right: var(--space-2);
}

.conversation-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0 0 var(--space-1) 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
  letter-spacing: 0.02em;
}

.conversation-item:hover .conversation-title,
.conversation-item.active .conversation-title {
  color: var(--neon-cyan);
  text-shadow: 0 0 10px rgba(6, 182, 212, 0.5);
}

.conversation-time {
  font-size: 0.7rem;
  color: var(--text-muted);
  margin: 0;
  font-family: var(--font-mono);
}

.conversation-item.active .conversation-time {
  color: var(--neon-cyan);
}

/* 删除按钮 - 赛博朋克风格 */
.delete-conversation {
  background: none;
  border: none;
  font-size: 1rem;
  cursor: pointer;
  opacity: 0;
  transition: var(--transition-base);
  padding: var(--space-1);
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  position: relative;
  z-index: 2;
}

.conversation-item:hover .delete-conversation {
  opacity: 1;
}

.delete-conversation:hover {
  background: var(--gradient-purple-pink);
  color: white;
  box-shadow: var(--glow-pink);
  transform: scale(1.1);
}

/* ============================================
   右侧主对话区 - Cyberpunk Chat Area
   ============================================ */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--hologram-bg);
  position: relative;
}

.chat-area::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at 20% 80%, rgba(168, 85, 247, 0.05) 0%, transparent 50%);
  pointer-events: none;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6) var(--space-8);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  position: relative;
}

.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-track {
  background: transparent;
}

.messages-container::-webkit-scrollbar-thumb {
  background: var(--gradient-blue-cyan);
  border-radius: var(--radius-full);
  border: 1px solid var(--border-cyan);
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: var(--neon-cyan);
  box-shadow: var(--glow-cyan);
}

/* ============================================
   消息气泡 - Cyberpunk Message Bubbles
   ============================================ */
.message {
  display: flex;
  flex-direction: column;
  max-width: 75%;
  animation: cyberSlideIn 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  position: relative;
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

.message.system {
  align-self: flex-start;
}

.message.user {
  align-self: flex-end;
}

.message-content {
  padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-lg);
  line-height: 1.7;
  font-size: 0.9375rem;
  transition: var(--transition-base);
  position: relative;
  overflow: hidden;
}

/* AI 消息样式 - 全息效果 */
.message.system .message-content {
  background: var(--bg-card);
  color: var(--text-primary);
  border: 1px solid var(--border-cyan);
  box-shadow: var(--shadow-md);
  backdrop-filter: blur(10px);
}

.message.system .message-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, transparent, rgba(6, 182, 212, 0.1), transparent);
  animation: hologramScan 4s ease-in-out infinite;
  pointer-events: none;
}

.message.system .message-content:hover {
  border-color: var(--neon-cyan);
  box-shadow: var(--glow-cyan), inset 0 0 20px rgba(6, 182, 212, 0.1);
  transform: translateY(-2px);
}

/* 用户消息样式 - 霓虹风格 */
.message.user .message-content {
  background: var(--gradient-blue-cyan);
  color: white;
  border: 1px solid var(--neon-cyan);
  box-shadow: var(--glow-cyan);
}

.message.user .message-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  animation: hologramScan 3s ease-in-out infinite;
  pointer-events: none;
}

.message.user .message-content:hover {
  background: var(--gradient-blue-cyan);
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 0 30px rgba(6, 182, 212, 0.5);
}

/* ============================================
   消息元数据 - Cyberpunk Message Meta
   ============================================ */
.message-meta {
  margin-top: var(--space-3);
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
  padding-left: var(--space-2);
}

.message-source {
  color: var(--neon-cyan);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
  background: var(--bg-surface);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-cyan);
  transition: var(--transition-base);
  font-family: var(--font-mono);
  text-transform: uppercase;
  font-size: 0.65rem;
  letter-spacing: 0.05em;
}

.message-source:hover {
  color: var(--text-primary);
  background: var(--bg-elevated);
  border-color: var(--neon-cyan);
  box-shadow: var(--glow-cyan);
  transform: translateY(-1px);
}

.message-confidence {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-md);
  font-weight: 500;
  font-family: var(--font-mono);
  text-transform: uppercase;
  font-size: 0.65rem;
  letter-spacing: 0.05em;
}

.message-confidence.high {
  background: rgba(16, 185, 129, 0.1);
  color: var(--neon-green);
  border: 1px solid var(--neon-green);
}

.message-confidence.low {
  background: rgba(245, 158, 11, 0.1);
  color: var(--neon-yellow);
  border: 1px solid var(--neon-yellow);
}

.low-confidence {
  margin-top: var(--space-3);
  padding: var(--space-4);
  background: rgba(245, 158, 11, 0.1);
  border-radius: var(--radius-lg);
  border: 1px solid var(--neon-yellow);
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.2);
}

.confidence-message {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin: 0 0 var(--space-3) 0;
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.confidence-buttons {
  display: flex;
  gap: var(--space-3);
}

/* ============================================
   按钮系统 - Cyberpunk Button System
   ============================================ */
.btn-primary {
  background: transparent;
  color: var(--neon-cyan);
  border: 2px solid var(--neon-cyan);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-lg);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition-base);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  position: relative;
  overflow: hidden;
}

.btn-primary::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: var(--gradient-blue-cyan);
  transition: var(--transition-base);
  z-index: -1;
}

.btn-primary:hover {
  color: white;
  border-color: var(--neon-cyan);
  box-shadow: var(--glow-cyan);
  transform: translateY(-2px);
}

.btn-primary:hover::before {
  left: 0;
}

.btn-primary:active {
  transform: translateY(0);
}

.btn-secondary {
  background: var(--bg-surface);
  color: var(--text-secondary);
  border: 1px solid var(--border-cyan);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-lg);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition-base);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.btn-secondary:hover {
  background: var(--bg-elevated);
  border-color: var(--neon-cyan);
  color: var(--neon-cyan);
  box-shadow: var(--shadow-glow);
  transform: translateY(-2px);
}

.btn-transfer-small {
  background: transparent;
  color: var(--text-muted);
  border: 1px solid var(--border-cyan);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-md);
  font-size: 0.7rem;
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition-base);
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  text-transform: uppercase;
  letter-spacing: 0.03em;
  font-family: var(--font-mono);
}

.btn-transfer-small:hover {
  background: var(--gradient-blue-cyan);
  color: white;
  border-color: transparent;
  box-shadow: var(--glow-cyan);
  transform: translateY(-2px) scale(1.05);
}

.message-time {
  font-size: 0.7rem;
  color: var(--text-muted);
  margin-top: var(--space-2);
  align-self: flex-end;
  padding-right: var(--space-2);
  font-family: var(--font-mono);
}

/* ============================================
   加载动画 - Cyberpunk Loading Animation
   ============================================ */
.loading-message {
  align-self: flex-start;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-5);
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border-cyan);
  backdrop-filter: blur(10px);
}

.typing-indicator {
  display: flex;
  gap: var(--space-1);
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--gradient-blue-cyan);
  border-radius: var(--radius-full);
  animation: cyberBounce 1.4s infinite ease-in-out both;
  box-shadow: 0 0 8px var(--neon-cyan);
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes cyberBounce {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* ============================================
   底部输入区 - Cyberpunk Input Area
   ============================================ */
.input-area {
  padding: var(--space-4) var(--space-6);
  background: var(--bg-card);
  border-top: 1px solid var(--border-cyan);
  backdrop-filter: blur(10px);
  position: relative;
}

.input-area::before {
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

/* 预置问题按钮 - 赛博朋克风格 */
.preset-questions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border-cyan);
}

.preset-label {
  font-size: 0.8rem;
  color: var(--neon-cyan);
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.preset-btn {
  padding: var(--space-2) var(--space-3);
  background: transparent;
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-md);
  font-size: 0.75rem;
  color: var(--neon-cyan);
  cursor: pointer;
  transition: var(--transition-base);
  white-space: nowrap;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  position: relative;
  overflow: hidden;
}

.preset-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: var(--gradient-blue-cyan);
  transition: var(--transition-base);
  z-index: -1;
}

.preset-btn:hover {
  color: white;
  border-color: transparent;
  box-shadow: var(--glow-cyan);
  transform: translateY(-2px);
}

.preset-btn:hover::before {
  left: 0;
}

.suggested-tags {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
  flex-wrap: wrap;
}

.tag {
  padding: var(--space-1) var(--space-3);
  background: transparent;
  border: 1px solid var(--border-purple);
  border-radius: var(--radius-full);
  font-size: 0.7rem;
  color: var(--neon-purple);
  cursor: pointer;
  transition: var(--transition-base);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  position: relative;
  overflow: hidden;
}

.tag::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: var(--gradient-purple-pink);
  transition: var(--transition-base);
  z-index: -1;
}

.tag:hover {
  color: white;
  border-color: transparent;
  box-shadow: var(--glow-purple);
  transform: translateY(-2px) scale(1.05);
}

.tag:hover::before {
  left: 0;
}

/* 输入容器 - 赛博朋克风格 */
.input-container {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  position: relative;
  background: var(--bg-dark);
  padding: var(--space-2);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-cyan);
  transition: var(--transition-base);
}

.input-container::before {
  content: '';
  position: absolute;
  top: -1px;
  left: -1px;
  right: -1px;
  bottom: -1px;
  border-radius: inherit;
  border: 1px solid var(--border-cyan);
  opacity: 0;
  transition: var(--transition-base);
}

.input-container:focus-within {
  border-color: var(--neon-cyan);
  box-shadow: var(--glow-cyan);
  transform: scale(1.01);
}

.input-container:focus-within::before {
  opacity: 1;
  animation: pulseBorder 1s ease-out;
}

.input-wrapper {
  flex: 1;
  position: relative;
}

.message-input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  border: none;
  background: transparent;
  font-size: 0.9375rem;
  color: var(--text-primary);
  transition: var(--transition-base);
  font-family: var(--font-sans);
  letter-spacing: 0.02em;
}

.message-input::placeholder {
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.message-input:focus {
  outline: none;
}

/* 输入按钮 - 赛博朋克风格 */
.input-button {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: var(--transition-base);
  font-size: 1.25rem;
  background: transparent;
  border: 1px solid var(--border-cyan);
  color: var(--neon-cyan);
  position: relative;
  overflow: hidden;
}

.input-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, transparent, rgba(6, 182, 212, 0.2), transparent);
  transition: var(--transition-base);
}

.input-button:hover {
  background: var(--bg-elevated);
  color: var(--text-primary);
  border-color: var(--neon-cyan);
  box-shadow: var(--shadow-glow);
  transform: translateY(-2px);
}

.input-button:hover::before {
  background: var(--gradient-blue-cyan);
}

/* 发送按钮 - 赛博朋克风格 */
.send-button {
  background: transparent;
  color: var(--neon-cyan);
  border: 2px solid var(--neon-cyan);
  padding: 0 var(--space-5);
  height: 44px;
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: var(--transition-base);
  font-weight: 600;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  position: relative;
  overflow: hidden;
}

.send-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: var(--gradient-blue-cyan);
  transition: var(--transition-base);
  z-index: -1;
}

.send-button:hover {
  color: white;
  border-color: var(--neon-cyan);
  box-shadow: var(--glow-cyan);
  transform: translateY(-2px) scale(1.05);
}

.send-button:hover::before {
  left: 0;
}

.send-button:active {
  transform: translateY(0) scale(1);
}

/* ============================================
   响应式设计 - Cyberpunk Responsive
   ============================================ */
@media (max-width: 1024px) {
  .conversation-sidebar {
    width: 260px;
  }

  .messages-container {
    padding: var(--space-5) var(--space-6);
  }

  .input-area {
    padding: var(--space-4) var(--space-6);
  }
}

@media (max-width: 768px) {
  .employee-view {
    --space-8: 1.5rem;
    --space-6: 1rem;
    --space-5: 0.875rem;
  }

  .employee-header {
    padding: var(--space-3) var(--space-4);
  }

  .header-left h1 {
    font-size: 1.125rem;
  }

  .conversation-sidebar {
    width: 100%;
    position: absolute;
    z-index: 100;
    transform: translateX(-100%);
    transition: transform 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  }

  .conversation-sidebar.open {
    transform: translateX(0);
  }

  .message {
    max-width: 90%;
  }

  .messages-container {
    padding: var(--space-4);
  }

  .input-area {
    padding: var(--space-4);
  }

  .preset-questions {
    gap: var(--space-2);
  }

  .preset-btn {
    padding: var(--space-1) var(--space-3);
    font-size: 0.7rem;
  }

  .send-button {
    padding: 0 var(--space-4);
  }

  .send-button span {
    display: none;
  }
}

@media (max-width: 480px) {
  .employee-view {
    --space-8: 1rem;
    --space-6: 0.75rem;
    --space-5: 0.75rem;
    --space-4: 0.625rem;
  }

  .header-left h1 {
    font-size: 1rem;
  }

  .message-content {
    font-size: 0.875rem;
    padding: var(--space-3);
  }

  .input-container {
    gap: var(--space-2);
  }

  .input-button {
    width: 40px;
    height: 40px;
  }

  .send-button {
    width: 44px;
    height: 44px;
    padding: 0;
    justify-content: center;
  }
}

/* ============================================
   流式传输样式 - Cyberpunk Streaming Styles
   ============================================ */
.streaming-container {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2);
}

/* ============================================
   富文本样式 - Cyberpunk Rich Content
   ============================================ */
.rich-content {
  line-height: 1.8;
  color: var(--text-secondary);
}

.rich-content p {
  margin: 0 0 var(--space-3) 0;
}

.rich-content p:last-child {
  margin-bottom: 0;
}

.rich-content strong {
  color: var(--neon-purple);
  font-weight: 600;
  text-shadow: 0 0 10px rgba(168, 85, 247, 0.5);
}

.rich-content code {
  background: var(--bg-dark);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-cyan);
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.875em;
  color: var(--neon-cyan);
  box-shadow: 0 0 8px rgba(6, 182, 212, 0.3);
}

.system-message-body {
  margin-bottom: var(--space-3);
}

/* ============================================
   系统消息结构化样式 - Cyberpunk System Message
   ============================================ */
.system-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--neon-cyan);
  margin: 0 0 var(--space-4) 0;
  padding: 0;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  text-shadow: 0 0 15px rgba(6, 182, 212, 0.5);
}

.system-subtitle {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--neon-purple);
  margin: var(--space-4) 0 var(--space-3) 0;
  padding: 0;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  text-shadow: 0 0 12px rgba(168, 85, 247, 0.4);
}

.system-paragraph {
  margin: 0 0 var(--space-4) 0;
  padding: 0;
  color: var(--text-secondary);
  line-height: 1.8;
}

.system-list {
  margin: 0 0 var(--space-4) 0;
  padding-left: var(--space-6);
  color: var(--text-secondary);
}

.system-list-item {
  margin: 0 0 var(--space-2) 0;
  padding: 0;
  line-height: 1.7;
  position: relative;
}

.system-list-item::marker {
  color: var(--neon-cyan);
}

.system-code {
  background: var(--bg-deepest);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  margin: 0 0 var(--space-4) 0;
  overflow-x: auto;
  font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
  font-size: 0.875rem;
  color: var(--neon-green);
  border: 1px solid var(--neon-green);
  box-shadow: var(--shadow-glow);
  box-shadow: 0 0 15px rgba(16, 185, 129, 0.3);
}

.system-bold {
  font-weight: 600;
  color: var(--neon-purple);
}

/* ============================================
   淡入动画 - Cyberpunk Fade Animations
   ============================================ */
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

@keyframes fadeInScale {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* ============================================
   添加工单表单样式 - Cyberpunk Create Ticket Form
   ============================================ */
.create-ticket-form {
  margin-top: var(--space-4);
  padding: var(--space-5);
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-cyan);
  animation: fadeInScale 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: var(--shadow-lg);
  max-height: calc(100vh - 300px);
  overflow-y: auto;
  overflow-x: hidden;
  backdrop-filter: blur(10px);
  position: relative;
}

.create-ticket-form::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--gradient-rainbow);
  background-size: 200% 100%;
  animation: rainbowBorder 3s linear infinite;
}

.create-ticket-form::-webkit-scrollbar {
  width: 6px;
}

.create-ticket-form::-webkit-scrollbar-track {
  background: transparent;
}

.create-ticket-form::-webkit-scrollbar-thumb {
  background: var(--gradient-blue-cyan);
  border-radius: var(--radius-full);
  border: 1px solid var(--border-cyan);
}

.create-ticket-form::-webkit-scrollbar-thumb:hover {
  background: var(--neon-cyan);
  box-shadow: var(--glow-cyan);
}

.create-ticket-form h3 {
  margin: 0 0 var(--space-4) 0;
  color: var(--neon-cyan);
  font-size: 1.125rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  text-shadow: 0 0 15px rgba(6, 182, 212, 0.5);
}

.form-group {
  margin-bottom: var(--space-4);
}

.form-group label {
  display: block;
  margin-bottom: var(--space-2);
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--neon-cyan);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.ticket-input,
.ticket-textarea,
.ticket-select {
  width: 100%;
  padding: var(--space-3);
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-lg);
  font-size: 0.9375rem;
  transition: var(--transition-base);
  box-sizing: border-box;
  background: var(--bg-dark);
  color: var(--text-primary);
  font-family: var(--font-sans);
  letter-spacing: 0.02em;
}

/* 防止浏览器自动填充时背景变白 */
.ticket-input:-webkit-autofill,
.ticket-input:-webkit-autofill:hover,
.ticket-input:-webkit-autofill:focus,
.ticket-input:-webkit-autofill:active {
  -webkit-box-shadow: 0 0 0 30px var(--bg-dark) inset !important;
  -webkit-text-fill-color: var(--text-primary) !important;
  transition: background-color 5000s ease-in-out 0s;
}

.ticket-input:focus,
.ticket-textarea:focus,
.ticket-select:focus {
  outline: none;
  border-color: var(--neon-cyan);
  box-shadow: var(--glow-cyan);
}

.ticket-textarea {
  resize: vertical;
  min-height: 120px;
  line-height: 1.7;
}

.form-actions {
  display: flex;
  gap: var(--space-3);
  justify-content: flex-end;
  margin-top: var(--space-5);
  padding-top: var(--space-4);
  border-top: 1px solid var(--border-cyan);
}

/* ============================================
   通知相关样式 - Cyberpunk Notifications
   ============================================ */
.notification-icon {
  background: var(--bg-card);
  border: 1px solid var(--border-cyan);
}

.notification-badge {
  animation: badgePulse 2s ease-in-out infinite;
}

/* ============================================
   通知列表弹窗 - Cyberpunk Notification Popup
   ============================================ */
.notification-list-popup {
  position: fixed;
  top: 80px;
  right: var(--space-6);
  width: 380px;
  background: var(--bg-card);
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-lg);
  z-index: 1001;
  max-height: 500px;
  overflow: hidden;
  animation: cyberSlideIn 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  backdrop-filter: blur(12px);
}

@keyframes cyberSlideIn {
  0% {
    opacity: 0;
    transform: translateX(30px) scale(0.9);
  }
  100% {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
}

.notification-list-popup::before {
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

.notification-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--border-cyan);
  background: var(--bg-elevated);
}

.notification-list-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--neon-cyan);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  text-shadow: 0 0 10px rgba(6, 182, 212, 0.5);
}

.notification-list-content {
  padding: var(--space-3);
  max-height: 400px;
  overflow-y: auto;
}

.notification-list-content::-webkit-scrollbar {
  width: 6px;
}

.notification-list-content::-webkit-scrollbar-thumb {
  background: var(--gradient-blue-cyan);
  border-radius: var(--radius-full);
}

.no-notifications {
  text-align: center;
  padding: var(--space-8);
  color: var(--text-muted);
}

.notification-item {
  display: flex;
  align-items: flex-start;
  padding: var(--space-4);
  margin-bottom: var(--space-3);
  background: var(--bg-surface);
  border-radius: var(--radius-xl);
  cursor: pointer;
  transition: var(--transition-base);
  border: 1px solid transparent;
}

.notification-item:hover {
  background: var(--bg-elevated);
  border-color: var(--border-cyan);
  transform: translateX(4px);
  box-shadow: var(--shadow-glow);
}

.notification-item.unread {
  background: var(--bg-elevated);
  border-left: 3px solid var(--neon-cyan);
  box-shadow: inset 0 0 20px rgba(6, 182, 212, 0.1);
}

.notification-item-icon {
  font-size: 1.5rem;
  margin-right: var(--space-3);
  flex-shrink: 0;
  filter: drop-shadow(0 0 8px var(--neon-cyan));
}

.notification-item-content {
  flex: 1;
  min-width: 0;
}

.notification-item-title {
  margin: 0 0 var(--space-1) 0;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-secondary);
  line-height: 1.5;
}

.notification-item-time {
  margin: 0;
  font-size: 0.7rem;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.notification-item-unread {
  width: 8px;
  height: 8px;
  background: var(--gradient-blue-cyan);
  border-radius: var(--radius-full);
  flex-shrink: 0;
  margin-top: var(--space-1);
  box-shadow: 0 0 8px var(--neon-cyan);
}

/* ============================================
   质检报告卡片 - Cyberpunk Quality Report Card
   ============================================ */
.quality-report-card {
  position: fixed;
  top: 100px;
  right: var(--space-6);
  width: 480px;
  background: var(--bg-card);
  border: 1px solid var(--border-cyan);
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-lg);
  z-index: 1000;
  max-height: 600px;
  overflow: hidden;
  animation: cyberSlideIn 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  backdrop-filter: blur(12px);
}

.quality-report-card::before {
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

.quality-report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--border-cyan);
  background: var(--bg-elevated);
}

.quality-report-header h3 {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--neon-green);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  text-shadow: 0 0 15px rgba(16, 185, 129, 0.5);
}

.quality-report-content {
  padding: var(--space-5);
  max-height: 500px;
  overflow-y: auto;
}

.quality-report-detail {
  background: var(--bg-surface);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
  border: 1px solid var(--border-cyan);
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--border-cyan);
}

.report-header h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-secondary);
}

.report-score {
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  color: white;
  font-weight: 700;
  font-size: 0.9375rem;
  background: var(--gradient-cyan-green);
  box-shadow: var(--glow-cyan);
  border: 1px solid var(--neon-cyan);
}

.report-info {
  margin-bottom: var(--space-4);
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.report-info p {
  margin: 0 0 var(--space-2) 0;
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.report-content {
  margin-bottom: var(--space-4);
}

.report-content h5 {
  margin: 0 0 var(--space-3) 0;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--neon-purple);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.report-content p {
  margin: 0 0 var(--space-4) 0;
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.7;
  background: var(--bg-dark);
  padding: var(--space-3);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-purple);
}

.report-issues,
.report-suggestions {
  margin-bottom: var(--space-4);
}

.report-issues h5,
.report-suggestions h5 {
  margin: 0 0 var(--space-3) 0;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--neon-yellow);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.report-issues ul,
.report-suggestions ul {
  margin: 0;
  padding-left: var(--space-6);
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.report-issues li,
.report-suggestions li {
  margin: 0 0 var(--space-2) 0;
  line-height: 1.7;
  position: relative;
}

/* ============================================
   动画效果 - Cyberpunk Animations
   ============================================ */
@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ============================================
   响应式调整 - Cyberpunk Mobile Responsive
   ============================================ */
@media (max-width: 768px) {
  .quality-report-card {
    width: calc(100% - var(--space-8));
    right: var(--space-4);
    left: var(--space-4);
    top: 80px;
  }

  .notification-list-popup {
    width: calc(100% - var(--space-8));
    right: var(--space-4);
    left: var(--space-4);
  }

  .create-ticket-form {
    padding: var(--space-4);
    max-height: calc(100vh - 200px);
    margin-top: var(--space-3);
  }

  .form-actions {
    flex-direction: column;
    gap: var(--space-2);
  }

  .form-actions button {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .quality-report-card,
  .notification-list-popup {
    width: calc(100% - var(--space-4));
    right: var(--space-2);
    left: var(--space-2);
    border-radius: var(--radius-xl);
  }

  .create-ticket-form {
    padding: var(--space-3);
    max-height: calc(100vh - 150px);
    border-radius: var(--radius-lg);
  }

  .create-ticket-form h3 {
    font-size: 1rem;
  }

  .form-group {
    margin-bottom: var(--space-3);
  }
}

/* 质检报告详情样式 */
.quality-report-detail {
  padding: 1rem;
}

.report-header {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border-color);
}

.report-header h4 {
  font-size: 1.25rem;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
}

.report-meta {
  display: flex;
  gap: 1rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.report-total-score {
  text-align: center;
  padding: 1.5rem;
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
  border-radius: 0.75rem;
  margin-bottom: 1.5rem;
  border: 1px solid var(--border-cyan);
}

.total-score-value {
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.total-score-value.excellent {
  color: #10b981;
  text-shadow: 0 0 20px rgba(16, 185, 129, 0.5);
}

.total-score-value.good {
  color: #3b82f6;
  text-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
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
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.total-score-stars {
  display: flex;
  justify-content: center;
  gap: 0.25rem;
}

.total-score-stars .star {
  font-size: 1.25rem;
  color: #4b5563;
}

.total-score-stars .star.filled {
  color: #fbbf24;
  text-shadow: 0 0 10px rgba(251, 191, 36, 0.5);
}

.report-score-details {
  margin-bottom: 1.5rem;
}

.score-details-title {
  font-size: 1rem;
  color: var(--text-primary);
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.score-items {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.score-item {
  background: rgba(31, 41, 55, 0.5);
  padding: 0.75rem;
  border-radius: 0.5rem;
  border: 1px solid var(--border-color);
}

.score-item-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.score-item-name {
  font-weight: 500;
  color: var(--text-primary);
}

.score-item-value {
  color: var(--neon-cyan);
  font-weight: 600;
}

.score-item-bar {
  height: 6px;
  background: rgba(75, 85, 99, 0.5);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.25rem;
}

.score-item-progress {
  height: 100%;
  background: linear-gradient(90deg, var(--neon-cyan) 0%, var(--neon-purple) 100%);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.score-item-percentage {
  font-size: 0.75rem;
  color: var(--text-muted);
  text-align: right;
}

.report-body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.report-section {
  background: rgba(31, 41, 55, 0.5);
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid var(--border-color);
}

.report-section h4 {
  font-size: 0.9375rem;
  color: var(--text-primary);
  margin: 0 0 0.75rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.report-content-box {
  background: rgba(17, 24, 39, 0.8);
  padding: 1rem;
  border-radius: 0.375rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
  line-height: 1.6;
  white-space: pre-wrap;
}

.report-content-box.empty {
  color: var(--text-muted);
  font-style: italic;
}

.report-content-box ul {
  margin: 0;
  padding-left: 1.5rem;
}

.report-content-box li {
  margin-bottom: 0.5rem;
}

.report-content-box li:last-child {
  margin-bottom: 0;
}
</style>
