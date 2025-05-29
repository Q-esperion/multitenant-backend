<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NPopconfirm,
  NDatePicker,
  NSelect,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'
import TheIcon from '@/components/icon/TheIcon.vue'

import { renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'
import { format } from 'date-fns' 

defineOptions({ name: '租户管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')

const {
  modalVisible,
  modalTitle,
  modalLoading,
  handleSave,
  modalForm,
  modalFormRef,
  handleEdit,
  handleDelete,
  handleAdd,
} = useCRUD({
  name: '租户',
  initForm: { status: 'active' },
  doCreate: (form) => api.createTenant(formatTenantForm(form)),
  doUpdate: (form) => api.updateTenant(formatTenantForm(form)),
  doDelete: (form) => api.deleteTenant(formatTenantForm(form)),
  refresh: () => $table.value?.handleSearch(),
  beforeEdit: (row) => {
    const form = { ...row }
    console.log('【beforeEdit】原始 row:', row)
    console.log('【beforeEdit】row.expire_date:', row.expire_date)
    console.log('【beforeEdit】row.expire_date 类型:', typeof row.expire_date)

    if (form.expire_date) {
      try {
        // 如果已经是时间戳格式，直接使用
        if (typeof form.expire_date === 'number') {
          form.expire_date = form.expire_date
        } else {
          // 尝试转换为时间戳
          const date = new Date(form.expire_date)
          if (!isNaN(date.getTime())) {
            form.expire_date = date.getTime()
          } else {
            form.expire_date = null
          }
        }
      } catch (error) {
        console.error('【beforeEdit】日期转换失败', error)
        form.expire_date = null
      }
    }

    console.log('【beforeEdit】最终返回 form:', form)
    return form
  }
})

// 租户状态选项
const statusOptions = [
  { label: '激活', value: 'active' },
  { label: '禁用', value: 'inactive' },
  { label: '暂停', value: 'suspended' },
]

onMounted(() => {
  $table.value?.handleSearch()
})

function formatTenantForm(form) {
  console.log('formatTenantForm 输入:', form)
  const data = { ...form }
  if (data.expire_date) {
    try {
      // 如果是时间戳，转换为日期字符串
      if (typeof data.expire_date === 'number') {
        const date = new Date(data.expire_date)
        if (!isNaN(date.getTime())) {
          data.expire_date = format(date, 'yyyy-MM-dd')
        } else {
          data.expire_date = null
        }
      } else {
        // 如果是日期对象或字符串，直接格式化
        const date = new Date(data.expire_date)
        if (!isNaN(date.getTime())) {
          data.expire_date = format(date, 'yyyy-MM-dd')
        } else {
          data.expire_date = null
        }
      }
    } catch (error) {
      console.error('日期格式化错误:', error)
      data.expire_date = null
    }
  }
  return data
}

const tenantRules = {
  name: [
    {
      required: true,
      message: '请输入租户名称',
      trigger: ['input', 'blur', 'change'],
    },
  ],
  // max_users: [
  //   {
  //     required: false,
  //     message: '请输入最大用户数',
  //     trigger: ['input', 'blur', 'change'],
  //   },
  // ],
  // expire_date: [
  //   {
  //     required: false,
  //     message: '请选择到期时间',
  //     trigger: ['blur', 'change'],
  //   },
  // ],
}

const columns = [
  {
    title: '租户名称',
    key: 'name',
    width: 'auto',
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '描述',
    key: 'description',
    align: 'center',
    width: 'auto',
    ellipsis: { tooltip: true },
  },
  {
    title: '最大用户数',
    key: 'max_users',
    align: 'center',
    width: 100,
  },
  {
    title: '到期时间',
    key: 'expire_date',
    align: 'center',
    width: 160,
    render(row) {
      console.log('渲染到期时间:', row.expire_date)
      if (!row.expire_date) return '-'
      try {
        // 如果已经是字符串格式，直接返回
        if (typeof row.expire_date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(row.expire_date)) {
          return row.expire_date
        }
        const date = new Date(row.expire_date)
        if (isNaN(date.getTime())) {
          console.log('无效的日期值，返回 -')
          return '-'
        }
        console.log('转换后的日期对象:', date)
        return format(date, 'yyyy-MM-dd')
      } catch (error) {
        console.error('日期渲染错误:', error)
        return '-'
      }
    }
  },
  {
    title: '状态',
    key: 'status',
    align: 'center',
    width: 100,
    render(row) {
      const statusMap = {
        active: { type: 'success', text: '激活' },
        inactive: { type: 'error', text: '禁用' },
        suspended: { type: 'warning', text: '暂停' },
      }
      const status = statusMap[row.status] || { type: 'default', text: row.status }
      return h('span', { style: { color: status.type === 'success' ? '#18a058' : status.type === 'error' ? '#d03050' : '#f0a020' } }, status.text)
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
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
              onClick: () => handleEdit(row),
            },
            {
              default: () => '编辑',
              icon: renderIcon('material-symbols:edit', { size: 16 }),
            }
          ),
          [[vPermission, 'put/api/v1/tenant/update']]
        ),
        h(
          NPopconfirm,
          {
            onPositiveClick: () => handleDelete({ tenant_id: row.id }, false),
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
                [[vPermission, 'delete/api/v1/tenant/delete']]
              ),
            default: () => h('div', {}, '确定删除该租户吗?'),
          }
        ),
      ]
    },
  },
]
</script>

<template>
  <CommonPage show-footer title="租户列表">
    <template #action>
      <NButton v-permission="'post/api/v1/tenant/create'" type="primary" @click="handleAdd">
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建租户
      </NButton>
    </template>
    <!-- 表格 -->
    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getTenantList"
    >
      <template #queryBar>
        <QueryBarItem label="租户名称" :label-width="80">
          <NInput
            v-model:value="queryItems.name"
            clearable
            type="text"
            placeholder="请输入租户名称"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
        <QueryBarItem label="状态" :label-width="80">
          <NSelect
            v-model:value="queryItems.status"
            :options="statusOptions"
            clearable
            placeholder="请选择状态"
            @update:value="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <!-- 新增/编辑 弹窗 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      @Save="handleSave"
    >
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="80"
        :model="modalForm"
        :rules="tenantRules"
      >
        <NFormItem label="租户名称" path="name">
          <NInput v-model:value="modalForm.name" clearable placeholder="请输入租户名称" />
        </NFormItem>
        <NFormItem label="描述" path="description">
          <NInput
            v-model:value="modalForm.description"
            type="textarea"
            clearable
            placeholder="请输入租户描述"
            @update:value="(val) => {
              modalForm.description = val || null
            }"
          />
        </NFormItem>
        <NFormItem label="最大用户数" path="max_users">
          <NInputNumber
            v-model:value="modalForm.max_users"
            :min="1"
            :default-value="100"
            clearable
            placeholder="请输入最大用户数"
            @update:value="(val) => {
              modalForm.max_users = val || null
            }"
          />
        </NFormItem>
        <NFormItem label="到期时间" path="expire_date">
          <NDatePicker
            v-model:value="modalForm.expire_date"
            type="date"
            clearable
            :default-value="null"
            placeholder="请选择到期时间"
            value-format="timestamp"
          />
        </NFormItem>
        <NFormItem label="状态" path="status">
          <NSelect
            v-model:value="modalForm.status"
            :options="statusOptions"
            clearable
            placeholder="请选择状态"
          />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>