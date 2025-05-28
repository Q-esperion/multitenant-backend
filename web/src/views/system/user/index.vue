<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives, watch, computed } from 'vue'
import {
  NButton,
  NCheckbox,
  NCheckboxGroup,
  NForm,
  NFormItem,
  NImage,
  NInput,
  NSpace,
  NSwitch,
  NTag,
  NPopconfirm,
  NLayout,
  NLayoutSider,
  NLayoutContent,
  NTreeSelect,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'

import { formatDate, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
// import { loginTypeMap, loginTypeOptions } from '@/constant/data'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'
import { useUserStore } from '@/store'

defineOptions({ name: '用户管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')

const {
  modalVisible,
  modalTitle,
  modalAction,
  modalLoading,
  handleSave,
  modalForm,
  modalFormRef,
  handleEdit,
  handleDelete,
  handleAdd,
} = useCRUD({
  name: '用户',
  initForm: {},
  doCreate: api.createUser,
  doUpdate: api.updateUser,
  doDelete: api.deleteUser,
  refresh: () => $table.value?.handleSearch(),
})

const roleOption = ref([])
const deptOption = ref([])

const userStore = useUserStore()
console.log('userStore初始化状态:', {
  user: userStore.user,
  token: userStore.token,
  userId: userStore.userId
})

const isSuperuser = computed(() => {
  const isSuper = userStore.userInfo?.is_superuser ?? false
  console.log('当前用户信息:', userStore.userInfo)
  console.log('是否为超级管理员:', isSuper)
  return isSuper
})

onMounted(async () => {
  console.log('组件挂载 - 开始加载数据')
  try {
    // 确保用户信息已加载
    if (!userStore.user) {
      console.log('用户信息未加载，尝试获取用户信息')
      const userInfo = await userStore.getUserInfo()
      console.log('getUserInfo返回结果:', userInfo)
    }
    console.log('用户信息加载完成:', userStore.user)
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
  
  $table.value?.handleSearch()
  api.getRoleList({ page: 1, page_size: 9999 }).then((res) => {
    console.log('角色列表加载完成:', res.data)
    roleOption.value = res.data
  })
  api.getDepts().then((res) => {
    console.log('部门列表加载完成:', res.value)
    deptOption.value = res.value
  })
})

// 监听租户变化，更新部门选项
watch(() => modalForm.tenant_id, async (newTenantId) => {
  if (newTenantId) {
    // 从对应租户获取部门列表
    const res = await api.getTenantDepts({ tenant_id: newTenantId })
    deptOption.value = res.data
  } else {
    deptOption.value = []
  }
  // 清空已选部门
  modalForm.dept_id = null
})

const columns = computed(() => {
  console.log('计算表格列 - 是否为超级管理员:', isSuperuser.value)
  const baseColumns = [
    {
      title: '名称',
      key: 'username',
      width: 60,
      align: 'center',
      ellipsis: { tooltip: true },
    },
    {
      title: '租户',
      key: 'tenant_name',
      align: 'center',
      width: 40,
      ellipsis: { tooltip: true },
    },
    {
      title: '用户角色',
      key: 'role',
      width: 60,
      align: 'center',
      render(row) {
        const roles = row.roles ?? []
        const group = []
        for (let i = 0; i < roles.length; i++)
          group.push(
            h(NTag, { type: 'info', style: { margin: '2px 3px' } }, { default: () => roles[i].name })
          )
        return h('span', group)
      },
    },
    {
      title: '上次登录时间',
      key: 'last_login',
      align: 'center',
      width: 80,
      ellipsis: { tooltip: true },
      render(row) {
        return h(
          NButton,
          { size: 'small', type: 'text', ghost: true },
          {
            default: () => (row.last_login !== null ? formatDate(row.last_login) : null),
            icon: renderIcon('mdi:update', { size: 16 }),
          }
        )
      },
    },
    {
      title: '禁用',
      key: 'is_active',
      width: 50,
      align: 'center',
      render(row) {
        return h(NSwitch, {
          size: 'small',
          rubberBand: false,
          value: row.is_active,
          loading: !!row.publishing,
          checkedValue: false,
          uncheckedValue: true,
          onUpdateValue: () => handleUpdateDisable(row),
        })
      },
    },
    {
      title: '操作',
      key: 'actions',
      width: 80,
      align: 'center',
      fixed: 'right',
      render(row) {
        return [
          withDirectives(
            h(
              NButton,
              {
                size: 'small',
                type: 'primary',
                style: 'margin-right: 8px;',
                onClick: () => {
                  handleEdit(row)
                  modalForm.value.dept_id = row.dept?.id
                  modalForm.value.role_ids = row.roles.map((e) => (e = e.id))
                  delete modalForm.value.dept
                },
              },
              {
                default: () => '编辑',
                icon: renderIcon('material-symbols:edit', { size: 16 }),
              }
            ),
            [[vPermission, 'post/api/v1/user/update']]
          ),
          h(
            NPopconfirm,
            {
              onPositiveClick: () => handleDelete({ user_id: row.id }, false),
              onNegativeClick: () => {},
            },
            {
              trigger: () =>
                withDirectives(
                  h(
                    NButton,
                    {
                      size: 'small',
                      type: 'error',
                      style: 'margin-right: 8px;',
                    },
                    {
                      default: () => '删除',
                      icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
                    }
                  ),
                  [[vPermission, 'delete/api/v1/user/delete']]
                ),
              default: () => h('div', {}, '确定删除该用户吗?'),
            }
          ),
          !row.is_superuser && h(
            NPopconfirm,
            {
              onPositiveClick: async () => {
                try {
                  await api.resetPassword({ user_id: row.id });
                  $message.success('密码已成功重置为123456');
                  await $table.value?.handleSearch();
                } catch (error) {
                  $message.error('重置密码失败: ' + error.message);
                }
              },
              onNegativeClick: () => {},
            },
            {
              trigger: () =>
                withDirectives(
                  h(
                    NButton,
                    {
                      size: 'small',
                      type: 'warning',
                      style: 'margin-right: 8px;',
                    },
                    {
                      default: () => '重置密码',
                      icon: renderIcon('material-symbols:lock-reset', { size: 16 }),
                    }
                  ),
                  [[vPermission, 'post/api/v1/user/reset_password']]
                ),
              default: () => h('div', {}, '确定重置用户密码为123456吗?'),
            }
          ),
        ]
      },
    },
  ]

  // 如果不是超级管理员，添加部门列
  if (!isSuperuser.value) {
    console.log('非超级管理员，添加部门列')
    baseColumns.splice(3, 0, {
      title: '部门',
      key: 'dept.name',
      align: 'center',
      width: 40,
      ellipsis: { tooltip: true },
    })
  }

  console.log('最终表格列配置:', baseColumns)
  return baseColumns
})

// 修改用户禁用状态
async function handleUpdateDisable(row) {
  if (!row.id) return
  const userStore = useUserStore()
  if (userStore.userId === row.id) {
    $message.error('当前登录用户不可禁用！')
    return
  }
  row.publishing = true
  row.is_active = row.is_active === false ? true : false
  row.publishing = false
  const role_ids = []
  row.roles.forEach((e) => {
    role_ids.push(e.id)
  })
  row.role_ids = role_ids
  row.dept_id = row.dept?.id
  try {
    await api.updateUser(row)
    $message?.success(row.is_active ? '已取消禁用该用户' : '已禁用该用户')
    $table.value?.handleSearch()
  } catch (err) {
    // 有异常恢复原来的状态
    row.is_active = row.is_active === false ? true : false
  } finally {
    row.publishing = false
  }
}

let lastClickedNodeId = null

const nodeProps = ({ option }) => {
  return {
    onClick() {
      if (lastClickedNodeId === option.id) {
        $table.value?.handleSearch()
        lastClickedNodeId = null
      } else {
        api.getUserList({ dept_id: option.id }).then((res) => {
          $table.value.tableData = res.data
          lastClickedNodeId = option.id
        })
      }
    },
  }
}

const validateAddUser = {
  username: [
    {
      required: true,
      message: '请输入名称',
      trigger: ['input', 'blur'],
    },
  ],
  email: [
    {
      required: true,
      message: '请输入邮箱地址',
      trigger: ['input', 'change'],
    },
    {
      trigger: ['blur'],
      validator: (rule, value, callback) => {
        const re = /^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$/
        if (!re.test(modalForm.value.email)) {
          callback('邮箱格式错误')
          return
        }
        callback()
      },
    },
  ],
  password: [
    {
      required: true,
      message: '请输入密码',
      trigger: ['input', 'blur', 'change'],
    },
  ],
  confirmPassword: [
    {
      required: true,
      message: '请再次输入密码',
      trigger: ['input'],
    },
    {
      trigger: ['blur'],
      validator: (rule, value, callback) => {
        if (value !== modalForm.value.password) {
          callback('两次密码输入不一致')
          return
        }
        callback()
      },
    },
  ],
  roles: [
    {
      type: 'array',
      required: true,
      message: '请至少选择一个角色',
      trigger: ['blur', 'change'],
    },
  ],
}

const formItems = computed(() => {
  console.log('计算表单项 - 是否为超级管理员:', isSuperuser.value)
  const baseItems = [
    {
      label: '用户名称',
      path: 'username',
      component: 'NInput',
      props: {
        clearable: true,
        placeholder: '请输入用户名称'
      }
    },
    {
      label: '邮箱',
      path: 'email',
      component: 'NInput',
      props: {
        clearable: true,
        placeholder: '请输入邮箱'
      }
    },
    {
      label: '密码',
      path: 'password',
      component: 'NInput',
      props: {
        showPasswordOn: 'mousedown',
        type: 'password',
        clearable: true,
        placeholder: '请输入密码'
      }
    },
    {
      label: '确认密码',
      path: 'confirmPassword',
      component: 'NInput',
      props: {
        showPasswordOn: 'mousedown',
        type: 'password',
        clearable: true,
        placeholder: '请确认密码'
      }
    },
    {
      label: '角色',
      path: 'role_ids',
      component: 'NCheckboxGroup',
      props: {
        options: roleOption,
        value: modalForm.role_ids,
        onChange: (value) => {
          modalForm.role_ids = value
        }
      }
    },
    {
      label: '超级用户',
      path: 'is_superuser',
      component: 'NSwitch',
      props: {
        size: 'small',
        checkedValue: true,
        uncheckedValue: false,
        value: modalForm.is_superuser
      }
    },
    {
      label: '禁用',
      path: 'is_active',
      component: 'NSwitch',
      props: {
        size: 'small',
        checkedValue: false,
        uncheckedValue: true,
        value: modalForm.is_active
      }
    },
  ]

  if (!isSuperuser.value) {
    console.log('非超级管理员，添加部门选择字段')
    baseItems.push({
      label: '部门',
      path: 'dept_id',
      component: 'NTreeSelect',
      props: {
        options: deptOption,
        keyField: 'id',
        labelField: 'name',
        placeholder: '请选择部门',
        clearable: true,
        defaultExpandAll: true,
        disabled: !modalForm.tenant_id
      }
    })
  }

  console.log('最终表单项配置:', baseItems)
  return baseItems
})
</script>

<template>
  <NLayout has-sider wh-full>
    <!-- 如果不是超级管理员，显示部门树 -->
    <NLayoutSider
      v-if="!isSuperuser"
      bordered
      content-style="padding: 24px;"
      :collapsed-width="0"
      :width="240"
      show-trigger="arrow-circle"
    >
      <h1>部门列表</h1>
      <br />
      <NTree
        block-line
        :data="deptOption"
        key-field="id"
        label-field="name"
        default-expand-all
        :node-props="nodeProps"
      >
      </NTree>
    </NLayoutSider>
    <NLayoutContent>
      <CommonPage show-footer title="用户列表">
        <template #action>
          <NButton v-permission="'post/api/v1/user/create'" type="primary" @click="handleAdd">
            <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建用户
          </NButton>
        </template>
        <!-- 表格 -->
        <CrudTable
          ref="$table"
          v-model:query-items="queryItems"
          :columns="columns"
          :get-data="async (params) => {
            console.log('获取用户列表参数:', params)
            const res = await api.getUserList(params)
            console.log('用户列表数据:', res)
            return res
          }"
        >
          <template #queryBar>
            <QueryBarItem label="名称" :label-width="40">
              <NInput
                v-model:value="queryItems.username"
                clearable
                type="text"
                placeholder="请输入用户名称"
                @keypress.enter="$table?.handleSearch()"
              />
            </QueryBarItem>
            <QueryBarItem label="邮箱" :label-width="40">
              <NInput
                v-model:value="queryItems.email"
                clearable
                type="text"
                placeholder="请输入邮箱"
                @keypress.enter="$table?.handleSearch()"
              />
            </QueryBarItem>
          </template>
        </CrudTable>

        <!-- 新增/编辑 弹窗 -->
        <CrudModal
          v-model:visible="modalVisible"
          :title="modalTitle"
          :loading="modalLoading"
          @save="handleSave"
        >
          <NForm
            ref="modalFormRef"
            label-placement="left"
            label-align="left"
            :label-width="80"
            :model="modalForm"
            :rules="validateAddUser"
          >
            <NFormItem label="用户名称" path="username">
              <NInput v-model:value="modalForm.username" clearable placeholder="请输入用户名称" />
            </NFormItem>
            <NFormItem label="邮箱" path="email">
              <NInput v-model:value="modalForm.email" clearable placeholder="请输入邮箱" />
            </NFormItem>
            <NFormItem v-if="modalAction === 'add'" label="密码" path="password">
              <NInput
                v-model:value="modalForm.password"
                show-password-on="mousedown"
                type="password"
                clearable
                placeholder="请输入密码"
              />
            </NFormItem>
            <NFormItem v-if="modalAction === 'add'" label="确认密码" path="confirmPassword">
              <NInput
                v-model:value="modalForm.confirmPassword"
                show-password-on="mousedown"
                type="password"
                clearable
                placeholder="请确认密码"
              />
            </NFormItem>
            <NFormItem label="角色" path="role_ids">
              <NCheckboxGroup v-model:value="modalForm.role_ids">
                <NSpace item-style="display: flex;">
                  <NCheckbox
                    v-for="item in roleOption"
                    :key="item.id"
                    :value="item.id"
                    :label="item.name"
                  />
                </NSpace>
              </NCheckboxGroup>
            </NFormItem>
            <NFormItem label="超级用户" path="is_superuser">
              <NSwitch
                v-model:value="modalForm.is_superuser"
                size="small"
                :checked-value="true"
                :unchecked-value="false"
              ></NSwitch>
            </NFormItem>
            <NFormItem label="禁用" path="is_active">
              <NSwitch
                v-model:value="modalForm.is_active"
                :checked-value="false"
                :unchecked-value="true"
                :default-value="true"
              />
            </NFormItem>
            <!-- 如果不是超级管理员，显示部门字段 -->
            <NFormItem v-if="!isSuperuser" label="部门" path="dept_id">
              <NTreeSelect
                v-model:value="modalForm.dept_id"
                :options="deptOption"
                key-field="id"
                label-field="name"
                placeholder="请选择部门"
                clearable
                default-expand-all
                :disabled="!modalForm.tenant_id"
              ></NTreeSelect>
            </NFormItem>
          </NForm>
        </CrudModal>
      </CommonPage>
    </NLayoutContent>
  </NLayout>
  <!-- 业务页面 -->
</template>
