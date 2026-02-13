<template>
  <div class="admin-container">
    <!-- 顶部导航栏 -->
    <header class="admin-header">
      <div class="logo">
        <h1>IT智能客服系统 - 管理端</h1>
      </div>
      <div class="user-info">
        <span>管理员</span>
        <el-button type="primary" size="small">退出登录</el-button>
      </div>
    </header>

    <!-- 左侧导航菜单 -->
    <aside class="admin-sidebar">
      <el-menu
        :default-active="activeTab"
        class="admin-menu"
        @select="handleMenuSelect"
      >
        <el-menu-item index="dashboard">
          <el-icon><data-analysis /></el-icon>
          <span>数据看板</span>
        </el-menu-item>
        <el-menu-item index="knowledge">
          <el-icon><reading /></el-icon>
          <span>知识库管理</span>
        </el-menu-item>
        <el-menu-item index="users">
          <el-icon><users /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="quality">
          <el-icon><check /></el-icon>
          <span>质检规则设置</span>
        </el-menu-item>
      </el-menu>
    </aside>

    <!-- 主内容区域 -->
    <main class="admin-main">
      <!-- 数据看板 -->
      <div v-if="activeTab === 'dashboard'" class="dashboard-section">
        <h2>系统数据看板</h2>
        <div class="dashboard-stats">
          <el-card shadow="hover" class="stat-card">
            <template #header>
              <div class="card-header">
                <span>总工单数</span>
                <el-icon><ticket /></el-icon>
              </div>
            </template>
            <div class="stat-value">{{ dashboardStats.total_tickets || 0 }}</div>
          </el-card>
          <el-card shadow="hover" class="stat-card">
            <template #header>
              <div class="card-header">
                <span>开放工单</span>
                <el-icon><timer /></el-icon>
              </div>
            </template>
            <div class="stat-value">{{ dashboardStats.open_tickets || 0 }}</div>
          </el-card>
          <el-card shadow="hover" class="stat-card">
            <template #header>
              <div class="card-header">
                <span>已解决工单</span>
                <el-icon><success /></el-icon>
              </div>
            </template>
            <div class="stat-value">{{ dashboardStats.resolved_tickets || 0 }}</div>
          </el-card>
          <el-card shadow="hover" class="stat-card">
            <template #header>
              <div class="card-header">
                <span>已关闭工单</span>
                <el-icon><close /></el-icon>
              </div>
            </template>
            <div class="stat-value">{{ dashboardStats.closed_tickets || 0 }}</div>
          </el-card>
        </div>

        <div class="dashboard-charts">
          <el-card shadow="hover" class="chart-card">
            <template #header>
              <div class="card-header">
                <span>客服绩效</span>
              </div>
            </template>
            <div class="chart-content">
              <el-table :data="dashboardStats.agent_performance || []" style="width: 100%">
                <el-table-column prop="agent_name" label="客服姓名" width="180" />
                <el-table-column prop="assigned_tickets" label="分配工单" width="120" />
                <el-table-column prop="resolved_tickets" label="已解决工单" width="120" />
                <el-table-column prop="resolution_rate" label="解决率" width="120">
                  <template #default="scope">
                    {{ (scope.row.resolution_rate * 100).toFixed(2) }}%
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-card>
          <el-card shadow="hover" class="chart-card">
            <template #header>
              <div class="card-header">
                <span>分类分布</span>
              </div>
            </template>
            <div class="chart-content">
              <el-table :data="dashboardStats.category_distribution || []" style="width: 100%">
                <el-table-column prop="category" label="分类名称" width="180" />
                <el-table-column prop="count" label="工单数量" width="120" />
              </el-table>
            </div>
          </el-card>
        </div>
      </div>

      <!-- 知识库管理 -->
      <div v-if="activeTab === 'knowledge'" class="knowledge-section">
        <div class="section-header">
          <h2>知识库管理</h2>
          <el-button type="primary" @click="openKnowledgeDialog">
            <el-icon><plus /></el-icon>
            添加知识库
          </el-button>
        </div>
        <el-table :data="knowledgeList" style="width: 100%">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="title" label="标题" />
          <el-table-column prop="category" label="分类" width="120" />
          <el-table-column prop="is_active" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
                {{ scope.row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180" />
          <el-table-column label="操作" width="200">
            <template #default="scope">
              <el-button size="small" @click="editKnowledge(scope.row)">
                <el-icon><edit /></el-icon>
                编辑
              </el-button>
              <el-button size="small" type="danger" @click="deleteKnowledge(scope.row.id)">
                <el-icon><delete /></el-icon>
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 用户管理 -->
      <div v-if="activeTab === 'users'" class="users-section">
        <div class="section-header">
          <h2>用户管理</h2>
          <el-button type="primary" @click="openUserDialog">
            <el-icon><plus /></el-icon>
            添加用户
          </el-button>
        </div>
        <el-table :data="userList" style="width: 100%">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="email" label="邮箱" />
          <el-table-column prop="role" label="角色" width="120">
            <template #default="scope">
              <el-tag :type="getRoleType(scope.row.role)">
                {{ scope.row.role }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="department" label="部门" width="120" />
          <el-table-column prop="created_at" label="创建时间" width="180" />
          <el-table-column label="操作" width="200">
            <template #default="scope">
              <el-button size="small" @click="editUser(scope.row)">
                <el-icon><edit /></el-icon>
                编辑
              </el-button>
              <el-button size="small" type="danger" @click="deleteUser(scope.row.id)">
                <el-icon><delete /></el-icon>
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 质检规则设置 -->
      <div v-if="activeTab === 'quality'" class="quality-section">
        <div class="section-header">
          <h2>质检规则设置</h2>
          <el-button type="primary" @click="openQualityDialog">
            <el-icon><plus /></el-icon>
            添加规则
          </el-button>
        </div>
        <el-table :data="qualityRules" style="width: 100%">
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="name" label="规则名称" />
          <el-table-column prop="description" label="描述" />
          <el-table-column prop="weight" label="权重" width="100" />
          <el-table-column prop="is_active" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
                {{ scope.row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200">
            <template #default="scope">
              <el-button size="small" @click="editQualityRule(scope.row)">
                <el-icon><edit /></el-icon>
                编辑
              </el-button>
              <el-button size="small" type="danger" @click="deleteQualityRule(scope.row.id)">
                <el-icon><delete /></el-icon>
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </main>

    <!-- 知识库编辑对话框 -->
    <el-dialog
      v-model="knowledgeDialogVisible"
      :title="knowledgeDialogTitle"
      width="50%"
    >
      <el-form :model="knowledgeForm" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="knowledgeForm.title" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="knowledgeForm.content"
            type="textarea"
            :rows="4"
          />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="knowledgeForm.category" />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="knowledgeForm.tags" placeholder="逗号分隔" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="knowledgeForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="knowledgeDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveKnowledge">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { 
  DataAnalysis, Reading, Users, Check, Plus, Edit, Delete, 
  Ticket, Timer, Success, Close
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// 响应式数据
const activeTab = ref('dashboard')
const dashboardStats = ref({
  total_tickets: 0,
  open_tickets: 0,
  resolved_tickets: 0,
  closed_tickets: 0,
  agent_performance: [],
  category_distribution: []
})
const knowledgeList = ref([])
const userList = ref([])
const qualityRules = ref([])
const isLoading = ref(false)

// 对话框状态
const knowledgeDialogVisible = ref(false)
const knowledgeDialogTitle = ref('添加知识库')
const knowledgeForm = ref({
  id: 0,
  title: '',
  content: '',
  category: '',
  tags: '',
  is_active: true
})

// API基础URL
const API_BASE_URL = 'http://localhost:8000/api/v1/admin'

// 方法
const handleMenuSelect = (key: string) => {
  activeTab.value = key
  // 切换标签时加载对应数据
  if (key === 'dashboard') {
    loadDashboardStats()
  } else if (key === 'knowledge') {
    loadKnowledgeList()
  } else if (key === 'users') {
    loadUserList()
  } else if (key === 'quality') {
    loadQualityRules()
  }
}

const loadDashboardStats = async () => {
  isLoading.value = true
  try {
    const response = await fetch(`${API_BASE_URL}/dashboard`)
    if (response.ok) {
      const data = await response.json()
      dashboardStats.value = data
    } else {
      ElMessage.error('获取仪表盘数据失败')
    }
  } catch (error) {
    ElMessage.error('网络连接失败，请检查您的网络设置')
  } finally {
    isLoading.value = false
  }
}

const loadKnowledgeList = async () => {
  isLoading.value = true
  try {
    const response = await fetch(`${API_BASE_URL}/knowledge`)
    if (response.ok) {
      const data = await response.json()
      knowledgeList.value = data
    } else {
      ElMessage.error('获取知识库列表失败')
    }
  } catch (error) {
    ElMessage.error('网络连接失败，请检查您的网络设置')
  } finally {
    isLoading.value = false
  }
}

const loadUserList = async () => {
  isLoading.value = true
  try {
    const response = await fetch(`${API_BASE_URL}/users`)
    if (response.ok) {
      const data = await response.json()
      userList.value = data
    } else {
      ElMessage.error('获取用户列表失败')
    }
  } catch (error) {
    ElMessage.error('网络连接失败，请检查您的网络设置')
  } finally {
    isLoading.value = false
  }
}

const loadQualityRules = async () => {
  isLoading.value = true
  try {
    const response = await fetch(`${API_BASE_URL}/quality-rules`)
    if (response.ok) {
      const data = await response.json()
      qualityRules.value = data
    } else {
      ElMessage.error('获取质检规则列表失败')
    }
  } catch (error) {
    ElMessage.error('网络连接失败，请检查您的网络设置')
  } finally {
    isLoading.value = false
  }
}

const getRoleType = (role: string) => {
  switch (role) {
    case 'admin':
      return 'danger'
    case 'agent':
      return 'primary'
    case 'user':
      return 'info'
    default:
      return 'default'
  }
}

const openKnowledgeDialog = () => {
  knowledgeDialogTitle.value = '添加知识库'
  knowledgeForm.value = {
    id: 0,
    title: '',
    content: '',
    category: '',
    tags: '',
    is_active: true
  }
  knowledgeDialogVisible.value = true
}

const editKnowledge = (row: any) => {
  knowledgeDialogTitle.value = '编辑知识库'
  knowledgeForm.value = {
    ...row,
    tags: Array.isArray(row.tags) ? row.tags.join(',') : ''
  }
  knowledgeDialogVisible.value = true
}

const saveKnowledge = async () => {
  isLoading.value = true
  try {
    // 准备数据
    const tagsArray = knowledgeForm.value.tags ? knowledgeForm.value.tags.split(',').map(tag => tag.trim()) : []
    const knowledgeData = {
      title: knowledgeForm.value.title,
      content: knowledgeForm.value.content,
      category: knowledgeForm.value.category,
      tags: tagsArray,
      is_active: knowledgeForm.value.is_active
    }

    let response
    if (knowledgeForm.value.id) {
      // 更新知识库
      response = await fetch(`${API_BASE_URL}/knowledge/${knowledgeForm.value.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(knowledgeData)
      })
    } else {
      // 创建知识库
      response = await fetch(`${API_BASE_URL}/knowledge`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(knowledgeData)
      })
    }

    if (response.ok) {
      ElMessage.success(knowledgeForm.value.id ? '知识库更新成功' : '知识库创建成功')
      knowledgeDialogVisible.value = false
      await loadKnowledgeList()
    } else {
      ElMessage.error('操作失败，请稍后再试')
    }
  } catch (error) {
    ElMessage.error('网络连接失败，请检查您的网络设置')
  } finally {
    isLoading.value = false
  }
}

const deleteKnowledge = async (id: number) => {
  try {
    const response = await fetch(`${API_BASE_URL}/knowledge/${id}`, {
      method: 'DELETE'
    })

    if (response.ok) {
      ElMessage.success('知识库删除成功')
      await loadKnowledgeList()
    } else {
      ElMessage.error('删除失败，请稍后再试')
    }
  } catch (error) {
    ElMessage.error('网络连接失败，请检查您的网络设置')
  }
}

const openUserDialog = () => {
  // 实现用户添加对话框
}

const editUser = (row: any) => {
  // 实现用户编辑
}

const deleteUser = (id: number) => {
  // 实现用户删除
}

const openQualityDialog = () => {
  // 实现质检规则添加对话框
}

const editQualityRule = (row: any) => {
  // 实现质检规则编辑
}

const deleteQualityRule = (id: number) => {
  // 实现质检规则删除
}

// 生命周期
onMounted(() => {
  loadDashboardStats()
})
</script>

<style scoped>
.admin-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f7fa;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 60px;
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.logo h1 {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  margin: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.admin-sidebar {
  width: 200px;
  height: calc(100vh - 60px);
  background-color: #fff;
  border-right: 1px solid #e4e7ed;
  position: fixed;
  left: 0;
  top: 60px;
  z-index: 10;
}

.admin-menu {
  height: 100%;
  border-right: none;
}

.admin-main {
  flex: 1;
  margin-left: 200px;
  padding: 20px;
  overflow-y: auto;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h2 {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  margin: 0;
}

.dashboard-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  text-align: center;
  margin-top: 20px;
}

.dashboard-charts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
}

.chart-card {
  height: 300px;
}

.chart-content {
  height: calc(100% - 40px);
  overflow: auto;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .admin-sidebar {
    width: 100%;
    height: auto;
    position: relative;
    top: 0;
  }
  
  .admin-main {
    margin-left: 0;
    margin-top: 60px;
  }
  
  .dashboard-stats {
    grid-template-columns: 1fr;
  }
  
  .dashboard-charts {
    grid-template-columns: 1fr;
  }
}
</style>