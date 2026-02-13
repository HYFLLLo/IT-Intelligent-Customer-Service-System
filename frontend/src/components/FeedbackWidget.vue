<template>
  <div class="feedback-widget-container">
    <!-- 反馈窗口 -->
    <transition name="feedback-slide">
      <div v-if="showFeedback && !feedbackSubmitted" class="feedback-panel cyber-feedback-panel">
        <div class="feedback-glow-border"></div>
        <div class="feedback-grid-bg"></div>
        
        <!-- 初始反馈选项 -->
        <div v-if="!showDetailPanel" class="feedback-options">
          <p class="feedback-title">这个回答对您有帮助吗？</p>
          <div class="feedback-buttons">
            <button 
              class="feedback-btn cyber-btn-satisfied"
              :class="{ active: selectedType === 'satisfied' }"
              @click="handleSatisfied"
            >
              <span class="btn-glow"></span>
              <svg class="feedback-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path class="icon-path" d="M12 21C16.9706 21 21 16.9706 21 12C21 7.02944 16.9706 3 12 3C7.02944 3 3 7.02944 3 12C3 16.9706 7.02944 21 12 21Z" stroke="currentColor" stroke-width="2"/>
                <path class="icon-path" d="M8 14C8 14 9.5 16 12 16C14.5 16 16 14 16 14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path class="icon-path" d="M9 9H9.01" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
                <path class="icon-path" d="M15 9H15.01" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
              </svg>
              <span class="btn-label">满意</span>
            </button>
            
            <button 
              class="feedback-btn cyber-btn-dissatisfied"
              :class="{ active: selectedType === 'dissatisfied' }"
              @click="handleDissatisfied"
            >
              <span class="btn-glow"></span>
              <svg class="feedback-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path class="icon-path" d="M12 21C16.9706 21 21 16.9706 21 12C21 7.02944 16.9706 3 12 3C7.02944 3 3 7.02944 3 12C3 16.9706 7.02944 21 12 21Z" stroke="currentColor" stroke-width="2"/>
                <path class="icon-path" d="M8 16C8 16 9.5 14 12 14C14.5 14 16 16 16 16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path class="icon-path" d="M9 9H9.01" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
                <path class="icon-path" d="M15 9H15.01" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
              </svg>
              <span class="btn-label">不满意</span>
            </button>
          </div>
        </div>
        
        <!-- 不满意详情面板 -->
        <transition name="detail-expand">
          <div v-if="showDetailPanel" class="detail-panel">
            <div class="detail-header">
              <span class="detail-title">请告诉我们原因</span>
              <button class="close-btn" @click="closeDetailPanel">×</button>
            </div>
            
            <div class="issue-options">
              <label class="option-item cyber-checkbox">
                <input type="checkbox" v-model="selectedIssues" value="inaccurate">
                <span class="checkmark"></span>
                <span class="option-label">回答不准确</span>
              </label>
              <label class="option-item cyber-checkbox">
                <input type="checkbox" v-model="selectedIssues" value="misunderstood">
                <span class="checkmark"></span>
                <span class="option-label">未理解问题</span>
              </label>
              <label class="option-item cyber-checkbox">
                <input type="checkbox" v-model="selectedIssues" value="slow">
                <span class="checkmark"></span>
                <span class="option-label">响应太慢</span>
              </label>
            </div>
            
            <div class="description-area">
              <label class="description-label">详细描述（选填）：</label>
              <textarea 
                v-model="detailedDescription"
                class="cyber-textarea"
                placeholder="请详细描述您遇到的问题..."
                rows="3"
              ></textarea>
            </div>
            
            <div class="detail-actions">
              <button class="cyber-btn-cancel" @click="closeDetailPanel">取消</button>
              <button 
                class="cyber-btn-submit"
                :disabled="!canSubmit"
                :class="{ loading: isSubmitting }"
                @click="submitFeedback"
              >
                <span v-if="isSubmitting" class="btn-spinner"></span>
                <span v-else>提交</span>
              </button>
            </div>
          </div>
        </transition>
        
        <!-- 感谢信息 -->
        <transition name="fade">
          <div v-if="showThanks" class="thanks-message">
            <div class="thanks-icon">✓</div>
            <p>感谢您的参与，我们会继续努力</p>
          </div>
        </transition>
      </div>
    </transition>
    
    <!-- 小型反馈入口（5秒后显示） -->
    <transition name="fade">
      <div 
        v-if="showMiniEntry && feedbackSubmitted" 
        class="mini-feedback-entry"
        @click="reopenFeedback"
      >
        <svg class="mini-icon" viewBox="0 0 24 24" fill="none">
          <path d="M12 21C16.9706 21 21 16.9706 21 12C21 7.02944 16.9706 3 12 3C7.02944 3 3 7.02944 3 12C3 16.9706 7.02944 21 12 21Z" stroke="currentColor" stroke-width="2"/>
          <path d="M8 14H16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { analytics } from '@/analytics'
import { BusinessEventType, UserRole } from '@/analytics/types'

const props = defineProps({
  sessionId: {
    type: String,
    required: true
  },
  questionText: {
    type: String,
    default: ''
  },
  answerText: {
    type: String,
    default: ''
  },
  answerGeneratedAt: {
    type: String,
    default: ''
  }
})

// 状态
const showFeedback = ref(false)
const showDetailPanel = ref(false)
const selectedType = ref('')
const selectedIssues = ref([])
const detailedDescription = ref('')
const isSubmitting = ref(false)
const feedbackSubmitted = ref(false)
const showThanks = ref(false)
const showMiniEntry = ref(false)
const submitStartTime = ref(null)

// 防抖定时器
let debounceTimer = null
let miniEntryTimer = null
let thanksTimer = null

// 计算属性
const canSubmit = computed(() => {
  return selectedIssues.value.length > 0 && !isSubmitting.value
})

// 检查是否已经显示过反馈
const checkFeedbackStatus = async () => {
  try {
    const response = await fetch(`http://localhost:8000/api/v1/feedback/session/${props.sessionId}/check`)
    if (response.ok) {
      const data = await response.json()
      if (!data.feedback_shown && !data.feedback_submitted) {
        // 延迟显示反馈窗口，确保用户已经阅读完回答
        setTimeout(() => {
          showFeedback.value = true
          markSessionShown()
        }, 1000)
      }
    } else {
      // API返回错误，但仍显示反馈窗口（降级处理）
      setTimeout(() => {
        showFeedback.value = true
      }, 1000)
    }
  } catch (error) {
    console.error('检查反馈状态失败:', error)
    // API调用失败，但仍显示反馈窗口（降级处理）
    setTimeout(() => {
      showFeedback.value = true
    }, 1000)
  }
}

// 标记会话已显示
const markSessionShown = async () => {
  try {
    await fetch(`http://localhost:8000/api/v1/feedback/session/${props.sessionId}/mark-shown`, {
      method: 'POST'
    })
  } catch (error) {
    console.error('标记会话失败:', error)
  }
}

// 处理满意
const handleSatisfied = async () => {
  selectedType.value = 'satisfied'
  submitStartTime.value = Date.now()
  
  // 显示感谢信息
  showThanks.value = true
  
  // 提交反馈
  await submitFeedbackData()
  
  // 2-3秒后关闭
  thanksTimer = setTimeout(() => {
    showFeedback.value = false
    feedbackSubmitted.value = true
    showThanks.value = false
    
    // 5秒后显示小型入口
    miniEntryTimer = setTimeout(() => {
      showMiniEntry.value = true
      // 5秒后消失
      setTimeout(() => {
        showMiniEntry.value = false
      }, 5000)
    }, 5000)
  }, 2500)
}

// 处理不满意
const handleDissatisfied = () => {
  selectedType.value = 'dissatisfied'
  submitStartTime.value = Date.now()
  showDetailPanel.value = true
}

// 关闭详情面板
const closeDetailPanel = () => {
  showDetailPanel.value = false
  selectedType.value = ''
  selectedIssues.value = []
  detailedDescription.value = ''
}

// 提交反馈
const submitFeedback = async () => {
  if (!canSubmit.value) return
  
  isSubmitting.value = true
  await submitFeedbackData()
  isSubmitting.value = false
  
  // 显示成功提示
  showDetailPanel.value = false
  showThanks.value = true
  
  // 2秒后关闭
  thanksTimer = setTimeout(() => {
    showFeedback.value = false
    feedbackSubmitted.value = true
    showThanks.value = false
  }, 2000)
}

// 提交反馈数据
const submitFeedbackData = async () => {
  // 验证 feedback_type 不为空
  if (!selectedType.value) {
    console.error('反馈类型不能为空')
    return
  }

  const submitDuration = submitStartTime.value ? Date.now() - submitStartTime.value : null

  const feedbackData = {
    session_id: props.sessionId,
    feedback_type: selectedType.value,
    question_text: props.questionText,
    answer_text: props.answerText,
    issue_options: selectedIssues.value.length > 0 ? selectedIssues.value : null,
    detailed_description: detailedDescription.value || null,
    device_info: navigator.userAgent,
    browser_info: navigator.appName + ' ' + navigator.appVersion,
    answer_generated_at: props.answerGeneratedAt,
    submit_duration_ms: submitDuration
  }

  console.log('提交反馈数据:', feedbackData)

  // 上报评价回复埋点
  analytics.track(BusinessEventType.RATE_RESPONSE, {
    ratingId: props.sessionId,
    ticketId: props.sessionId,
    ratingScore: selectedType.value === 'satisfied' ? 5 : 1,
    replyContentLength: props.answerText ? props.answerText.length : 0,
    hasReply: !!props.answerText,
    userRole: UserRole.EMPLOYEE
  })

  try {
    const response = await fetch('http://localhost:8000/api/v1/feedback/submit', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(feedbackData)
    })

    if (!response.ok) {
      throw new Error('提交失败')
    }

    console.log('反馈提交成功')
  } catch (error) {
    console.error('提交反馈失败:', error)
    // 重试机制
    retrySubmit(feedbackData, 3)
  }
}

// 重试提交
const retrySubmit = async (data, retries) => {
  if (retries <= 0) return
  
  const delay = [1000, 3000, 5000][3 - retries] || 5000
  
  setTimeout(async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/feedback/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      })
      
      if (!response.ok) {
        throw new Error('重试失败')
      }
      
      console.log('反馈重试提交成功')
    } catch (error) {
      console.error(`第${4-retries}次重试失败:`, error)
      retrySubmit(data, retries - 1)
    }
  }, delay)
}

// 重新打开反馈
const reopenFeedback = () => {
  showFeedback.value = true
  feedbackSubmitted.value = false
  selectedType.value = ''
  selectedIssues.value = []
  detailedDescription.value = ''
}

onMounted(() => {
  // 防抖检查
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    checkFeedbackStatus()
  }, 300)
})

onUnmounted(() => {
  if (debounceTimer) clearTimeout(debounceTimer)
  if (miniEntryTimer) clearTimeout(miniEntryTimer)
  if (thanksTimer) clearTimeout(thanksTimer)
})
</script>

<style scoped>
/* 反馈组件容器 */
.feedback-widget-container {
  position: relative;
  width: 100%;
}

/* 赛博朋克反馈面板 */
.cyber-feedback-panel {
  position: relative;
  background: linear-gradient(135deg, rgba(17, 24, 39, 0.98) 0%, rgba(31, 41, 55, 0.95) 100%);
  border: 1px solid rgba(6, 182, 212, 0.5);
  border-radius: 8px;
  padding: 16px;
  margin-top: 12px;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.3),
    0 0 20px rgba(6, 182, 212, 0.1);
  overflow: hidden;
}

.feedback-glow-border {
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

.feedback-grid-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: 
    linear-gradient(90deg, rgba(6, 182, 212, 0.03) 1px, transparent 1px),
    linear-gradient(rgba(6, 182, 212, 0.03) 1px, transparent 1px);
  background-size: 20px 20px;
  pointer-events: none;
}

/* 反馈选项区域 */
.feedback-options {
  position: relative;
  z-index: 1;
  text-align: center;
}

.feedback-title {
  margin: 0 0 16px 0;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.feedback-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
}

/* 反馈按钮 */
.feedback-btn {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: linear-gradient(135deg, rgba(31, 41, 55, 0.9) 0%, rgba(55, 65, 81, 0.8) 100%);
  border: 1px solid rgba(6, 182, 212, 0.3);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  overflow: hidden;
}

.feedback-btn:hover {
  transform: scale(1.05);
  border-color: var(--neon-cyan);
  box-shadow: 0 0 20px rgba(6, 182, 212, 0.3);
}

.feedback-btn.active {
  transform: scale(1.1);
}

.cyber-btn-satisfied.active {
  border-color: var(--neon-cyan);
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.2) 0%, rgba(6, 182, 212, 0.1) 100%);
  box-shadow: 0 0 30px rgba(6, 182, 212, 0.4);
}

.cyber-btn-dissatisfied.active {
  border-color: var(--neon-pink);
  background: linear-gradient(135deg, rgba(236, 72, 153, 0.2) 0%, rgba(236, 72, 153, 0.1) 100%);
  box-shadow: 0 0 30px rgba(236, 72, 153, 0.4);
}

.btn-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  background: radial-gradient(circle, rgba(6, 182, 212, 0.4) 0%, transparent 70%);
  transform: translate(-50%, -50%);
  transition: all 0.3s ease;
  border-radius: 50%;
}

.feedback-btn:hover .btn-glow {
  width: 100px;
  height: 100px;
}

.feedback-icon {
  width: 40px;
  height: 40px;
  color: var(--text-secondary);
  transition: all 0.3s ease;
}

.feedback-btn:hover .feedback-icon {
  color: var(--neon-cyan);
}

.feedback-btn.active .feedback-icon {
  color: var(--neon-cyan);
}

.cyber-btn-dissatisfied.active .feedback-icon {
  color: var(--neon-pink);
}

.icon-path {
  transition: all 0.3s ease;
}

.btn-label {
  font-size: 0.8rem;
  color: var(--text-secondary);
  transition: all 0.3s ease;
}

.feedback-btn:hover .btn-label,
.feedback-btn.active .btn-label {
  color: white;
}

/* 详情面板 */
.detail-panel {
  position: relative;
  z-index: 1;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(6, 182, 212, 0.2);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.detail-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--neon-cyan);
  text-shadow: 0 0 10px rgba(6, 182, 212, 0.3);
}

.close-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.5);
  border-radius: 4px;
  color: var(--neon-pink);
  cursor: pointer;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: rgba(239, 68, 68, 0.4);
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.4);
}

/* 问题选项 */
.issue-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.cyber-checkbox {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.cyber-checkbox:hover {
  background: rgba(6, 182, 212, 0.1);
}

.cyber-checkbox input {
  display: none;
}

.checkmark {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(6, 182, 212, 0.5);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.cyber-checkbox input:checked + .checkmark {
  background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple));
  border-color: var(--neon-cyan);
  box-shadow: 0 0 10px rgba(6, 182, 212, 0.5);
}

.checkmark::after {
  content: '✓';
  color: white;
  font-size: 12px;
  opacity: 0;
  transform: scale(0);
  transition: all 0.2s ease;
}

.cyber-checkbox input:checked + .checkmark::after {
  opacity: 1;
  transform: scale(1);
}

.option-label {
  font-size: 0.85rem;
  color: var(--text-secondary);
  transition: all 0.3s ease;
}

.cyber-checkbox:hover .option-label,
.cyber-checkbox input:checked ~ .option-label {
  color: white;
}

/* 描述区域 */
.description-area {
  margin-bottom: 16px;
}

.description-label {
  display: block;
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.cyber-textarea {
  width: 100%;
  min-height: 60px;
  padding: 10px;
  background: rgba(17, 24, 39, 0.8);
  border: 1px solid rgba(6, 182, 212, 0.3);
  border-radius: 6px;
  color: white;
  font-size: 0.85rem;
  resize: vertical;
  transition: all 0.3s ease;
}

.cyber-textarea:focus {
  outline: none;
  border-color: var(--neon-cyan);
  box-shadow: 0 0 15px rgba(6, 182, 212, 0.2);
}

.cyber-textarea::placeholder {
  color: rgba(156, 163, 175, 0.5);
}

/* 详情操作按钮 */
.detail-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.cyber-btn-cancel {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid rgba(156, 163, 175, 0.5);
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cyber-btn-cancel:hover {
  border-color: var(--neon-pink);
  color: var(--neon-pink);
  box-shadow: 0 0 10px rgba(236, 72, 153, 0.2);
}

.cyber-btn-submit {
  position: relative;
  padding: 8px 20px;
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

.cyber-btn-submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(6, 182, 212, 0.4);
}

.cyber-btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.cyber-btn-submit.loading {
  pointer-events: none;
}

.btn-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 感谢信息 */
.thanks-message {
  text-align: center;
  padding: 20px;
}

.thanks-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple));
  border-radius: 50%;
  font-size: 24px;
  color: white;
  box-shadow: 0 0 20px rgba(6, 182, 212, 0.5);
  animation: thanksPulse 0.5s ease;
}

@keyframes thanksPulse {
  0% { transform: scale(0); }
  50% { transform: scale(1.2); }
  100% { transform: scale(1); }
}

.thanks-message p {
  margin: 0;
  font-size: 0.9rem;
  color: var(--neon-cyan);
  text-shadow: 0 0 10px rgba(6, 182, 212, 0.3);
}

/* 小型反馈入口 */
.mini-feedback-entry {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(168, 85, 247, 0.2));
  border: 1px solid rgba(6, 182, 212, 0.5);
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 0 15px rgba(6, 182, 212, 0.3);
  z-index: 100;
}

.mini-feedback-entry:hover {
  transform: scale(1.1);
  box-shadow: 0 0 25px rgba(6, 182, 212, 0.5);
}

.mini-icon {
  width: 20px;
  height: 20px;
  color: var(--neon-cyan);
}

/* 过渡动画 */
.feedback-slide-enter-active,
.feedback-slide-leave-active {
  transition: all 0.3s ease;
}

.feedback-slide-enter-from,
.feedback-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.detail-expand-enter-active {
  transition: all 0.3s ease;
}

.detail-expand-leave-active {
  transition: all 0.2s ease;
}

.detail-expand-enter-from,
.detail-expand-leave-to {
  opacity: 0;
  max-height: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
