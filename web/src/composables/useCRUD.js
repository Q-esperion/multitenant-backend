import { isNullOrWhitespace } from '@/utils'

const ACTIONS = {
  view: '查看',
  edit: '编辑',
  add: '新增',
}

export default function ({ name, initForm = {}, doCreate, doDelete, doUpdate, refresh, beforeEdit }) {
  const modalVisible = ref(false)
  const modalAction = ref('')
  const modalTitle = computed(() => ACTIONS[modalAction.value] + name)
  const modalLoading = ref(false)
  const modalFormRef = ref(null)
  const modalForm = ref({ ...initForm })

  /** 新增 */
  function handleAdd() {
    modalAction.value = 'add'
    modalVisible.value = true
    modalForm.value = { ...initForm }
  }

  /** 修改 */
  function handleEdit(row) {
    modalAction.value = 'edit'
    modalVisible.value = true
    // 如果有beforeEdit钩子，先处理数据
    if (beforeEdit) {
      modalForm.value = beforeEdit(row)
    } else {
      modalForm.value = { ...row }
    }
  }

  /** 查看 */
  function handleView(row) {
    modalAction.value = 'view'
    modalVisible.value = true
    modalForm.value = { ...row }
  }

  /** 保存 */
  function handleSave(...callbacks) {
    console.log('handleSave 被调用:', {
      action: modalAction.value,
      formData: modalForm.value,
      formRef: modalFormRef.value
    })

    if (!['edit', 'add'].includes(modalAction.value)) {
      console.log('无效的操作类型:', modalAction.value)
      modalVisible.value = false
      return
    }
    
    modalFormRef.value?.validate(async (err) => {
      if (err) {
        console.error('表单验证失败:', err)
        return
      }
      console.log('表单验证通过，准备调用API')
      
      const actions = {
        add: {
          api: () => doCreate(modalForm.value),
          cb: () => {
            callbacks.forEach((callback) => callback && callback())
          },
          msg: () => $message.success('新增成功'),
        },
        edit: {
          api: () => doUpdate(modalForm.value),
          cb: () => {
            callbacks.forEach((callback) => callback && callback())
          },
          msg: () => $message.success('编辑成功'),
        },
      }
      const action = actions[modalAction.value]

      try {
        modalLoading.value = true
        console.log('开始调用API:', modalAction.value)
        const data = await action.api()
        console.log('API调用成功:', data)
        action.cb()
        action.msg()
        modalLoading.value = modalVisible.value = false
        data && refresh(data)
      } catch (error) {
        console.error('API调用失败:', error)
        modalLoading.value = false
        $message.error(error.message || '操作失败')
      }
    })
  }

  /** 删除 */
  async function handleDelete(params = {}) {
    if (isNullOrWhitespace(params)) return
    try {
      modalLoading.value = true
      const data = await doDelete(params)
      $message.success('删除成功')
      modalLoading.value = false
      refresh(data)
    } catch (error) {
      modalLoading.value = false
    }
  }

  return {
    modalVisible,
    modalAction,
    modalTitle,
    modalLoading,
    handleAdd,
    handleDelete,
    handleEdit,
    handleView,
    handleSave,
    modalForm,
    modalFormRef,
  }
}
