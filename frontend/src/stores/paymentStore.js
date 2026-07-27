import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { PAYMENT_STATUSES } from '../constants/payment.js'
import * as paymentService from '../services/paymentService.js'

function currentMonth() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

function emptySummary() {
  return {
    totalRecords: 0,
    unpaidCount: 0,
    partiallyPaidCount: 0,
    paidCount: 0,
    totalBilledAmount: 0,
    totalCollectedAmount: 0,
    totalPendingAmount: 0,
  }
}

function emptyPagination() {
  return {
    page: 1,
    pageSize: 10,
    totalItems: 0,
    totalPages: 0,
  }
}

export const usePaymentStore = defineStore('payment', () => {
  const payments = ref([])
  const selectedPayment = ref(null)
  const receipts = ref([])
  const selectedReceipt = ref(null)
  const selectedReminder = ref(null)
  const summary = ref(emptySummary())
  const pagination = ref(emptyPagination())
  const receiptPagination = ref(emptyPagination())
  const paymentFilters = ref({
    search: '',
    month: currentMonth(),
    status: '',
    page: 1,
    pageSize: 10,
    sortBy: 'month',
    sortOrder: 'desc',
  })
  const isLoading = ref(false)
  const isReceiptLoading = ref(false)
  const isReceiptPreviewLoading = ref(false)
  const isReceiptDownloading = ref(false)
  const isReminderSubmitting = ref(false)
  const error = ref(null)
  const receiptError = ref(null)
  const reminderError = ref(null)
  const receiptFilters = ref({
    search: '',
    billingMonth: '',
    paymentMethod: '',
    status: '',
    page: 1,
    pageSize: 10,
    sortBy: 'issuedAt',
    sortOrder: 'desc',
  })
  let latestListRequest = 0
  let latestReceiptListRequest = 0
  let latestReceiptPreviewRequest = 0

  const paymentCount = computed(() => summary.value.totalRecords)
  const paidPaymentCount = computed(() => summary.value.paidCount)
  const unpaidPaymentCount = computed(() => summary.value.unpaidCount)
  const partiallyPaidPaymentCount = computed(
    () => summary.value.partiallyPaidCount,
  )
  const totalCollectedAmount = computed(
    () => Number(summary.value.totalCollectedAmount || 0),
  )
  const totalPendingAmount = computed(
    () => Number(summary.value.totalPendingAmount || 0),
  )
  const totalBilledAmount = computed(
    () => Number(summary.value.totalBilledAmount || 0),
  )
  const paidPayments = computed(() =>
    payments.value.filter(
      (payment) => payment.status === PAYMENT_STATUSES.PAID,
    ),
  )
  const unpaidPayments = computed(() =>
    payments.value.filter(
      (payment) => payment.status === PAYMENT_STATUSES.UNPAID,
    ),
  )
  const availableMonths = computed(() => {
    const months = []
    const cursor = new Date()
    cursor.setDate(1)
    for (let index = 0; index < 24; index += 1) {
      months.push(
        `${cursor.getFullYear()}-${String(cursor.getMonth() + 1).padStart(2, '0')}`,
      )
      cursor.setMonth(cursor.getMonth() - 1)
    }
    if (
      paymentFilters.value.month &&
      !months.includes(paymentFilters.value.month)
    ) {
      months.unshift(paymentFilters.value.month)
    }
    return months
  })
  const hasActivePaymentFilters = computed(() => {
    return Boolean(
      paymentFilters.value.search ||
      paymentFilters.value.status ||
      paymentFilters.value.month !== currentMonth(),
    )
  })
  const errorMessage = computed(() => {
    return (
      error.value?.response?.data?.error?.message ||
      error.value?.response?.data?.message ||
      error.value?.message ||
      ''
    )
  })
  const receiptErrorMessage = computed(() => {
    return (
      receiptError.value?.response?.data?.error?.message ||
      receiptError.value?.response?.data?.message ||
      receiptError.value?.message ||
      ''
    )
  })
  const reminderErrorMessage = computed(() => {
    return (
      reminderError.value?.response?.data?.error?.message ||
      reminderError.value?.response?.data?.message ||
      reminderError.value?.message ||
      ''
    )
  })

  function syncListResponse(response) {
    payments.value = response?.data?.payments || []
    pagination.value = response?.meta || emptyPagination()
    summary.value = response?.summary || emptySummary()
  }

  async function fetchPayments(filters = paymentFilters.value) {
    const requestNumber = ++latestListRequest
    isLoading.value = true
    error.value = null

    try {
      const response = await paymentService.getPayments({ ...filters })
      if (requestNumber === latestListRequest) {
        syncListResponse(response)
      }
      return response
    } catch (requestError) {
      if (requestNumber === latestListRequest) {
        error.value = requestError
      }
      throw requestError
    } finally {
      if (requestNumber === latestListRequest) {
        isLoading.value = false
      }
    }
  }

  async function generateMonthlyPayments(month) {
    isLoading.value = true
    error.value = null
    try {
      const response = await paymentService.generateMonthlyPayments(month)
      await fetchPayments()
      return response
    } catch (requestError) {
      error.value = requestError
      throw requestError
    } finally {
      isLoading.value = false
    }
  }

  async function recordPayment(paymentId, payload) {
    isLoading.value = true
    error.value = null
    try {
      const response = await paymentService.recordPayment(paymentId, payload)
      selectedPayment.value = response.data.payment
      selectedReceipt.value = response.data.receipt
      if (receipts.value.length || receiptPagination.value.totalItems) {
        const existingIndex = receipts.value.findIndex(
          (receipt) => receipt.id === response.data.receipt.id,
        )
        if (existingIndex >= 0) {
          receipts.value.splice(existingIndex, 1, response.data.receipt)
        } else {
          receipts.value.unshift(response.data.receipt)
          receiptPagination.value = {
            ...receiptPagination.value,
            totalItems: receiptPagination.value.totalItems + 1,
          }
        }
      }
      await fetchPayments()
      return response
    } catch (requestError) {
      error.value = requestError
      throw requestError
    } finally {
      isLoading.value = false
    }
  }

  async function fetchPaymentHistory(filters = paymentFilters.value) {
    return fetchPayments({ ...filters, month: filters.month || '' })
  }

  async function fetchReceipts(filters = receiptFilters.value) {
    const requestNumber = ++latestReceiptListRequest
    isReceiptLoading.value = true
    receiptError.value = null
    try {
      const response = await paymentService.getReceipts({ ...filters })
      if (requestNumber === latestReceiptListRequest) {
        receipts.value = response.data.receipts || []
        receiptPagination.value = response.meta || emptyPagination()
      }
      return response
    } catch (requestError) {
      if (requestNumber === latestReceiptListRequest) {
        receiptError.value = requestError
      }
      throw requestError
    } finally {
      if (requestNumber === latestReceiptListRequest) {
        isReceiptLoading.value = false
      }
    }
  }

  async function fetchReceiptDetail(receiptId) {
    const requestNumber = ++latestReceiptPreviewRequest
    selectedReceipt.value = null
    isReceiptPreviewLoading.value = true
    receiptError.value = null
    try {
      const response = await paymentService.getReceipt(receiptId)
      if (requestNumber === latestReceiptPreviewRequest) {
        selectedReceipt.value = response.data
      }
      return response
    } catch (requestError) {
      if (requestNumber === latestReceiptPreviewRequest) {
        receiptError.value = requestError
      }
      throw requestError
    } finally {
      if (requestNumber === latestReceiptPreviewRequest) {
        isReceiptPreviewLoading.value = false
      }
    }
  }

  async function downloadReceipt(receiptId) {
    isReceiptDownloading.value = true
    receiptError.value = null
    try {
      return await paymentService.downloadReceipt(receiptId)
    } catch (requestError) {
      receiptError.value = requestError
      throw requestError
    } finally {
      isReceiptDownloading.value = false
    }
  }

  async function createWhatsAppReminder(paymentId, payload = {}) {
    if (isReminderSubmitting.value) return null
    isReminderSubmitting.value = true
    reminderError.value = null
    selectedReminder.value = null
    try {
      const response = await paymentService.createWhatsAppReminder(
        paymentId,
        payload,
      )
      selectedReminder.value = response.data
      return response
    } catch (requestError) {
      reminderError.value = requestError
      throw requestError
    } finally {
      isReminderSubmitting.value = false
    }
  }

  function updatePaymentFilter(filterName, value) {
    if (!(filterName in paymentFilters.value)) return
    paymentFilters.value = {
      ...paymentFilters.value,
      [filterName]: value,
      page: filterName === 'page' ? value : 1,
    }
  }

  function setPaymentFilters(filters = {}) {
    paymentFilters.value = {
      ...paymentFilters.value,
      ...filters,
    }
  }

  function resetPaymentFilters() {
    paymentFilters.value = {
      ...paymentFilters.value,
      search: '',
      month: currentMonth(),
      status: '',
      page: 1,
    }
  }

  function updateReceiptFilter(filterName, value) {
    if (!(filterName in receiptFilters.value)) return
    receiptFilters.value = {
      ...receiptFilters.value,
      [filterName]: value,
      page: filterName === 'page' ? value : 1,
    }
  }

  function setReceiptFilters(filters = {}) {
    receiptFilters.value = {
      ...receiptFilters.value,
      ...filters,
    }
  }

  function resetReceiptFilters() {
    receiptFilters.value = {
      ...receiptFilters.value,
      search: '',
      billingMonth: '',
      paymentMethod: '',
      status: '',
      page: 1,
    }
  }

  function clearSelectedPayment() {
    selectedPayment.value = null
  }

  function clearSelectedReceipt() {
    latestReceiptPreviewRequest += 1
    selectedReceipt.value = null
    isReceiptPreviewLoading.value = false
  }

  function clearSelectedReminder() {
    selectedReminder.value = null
    reminderError.value = null
  }

  function clearError() {
    error.value = null
    reminderError.value = null
  }

  return {
    payments,
    selectedPayment,
    receipts,
    selectedReceipt,
    selectedReminder,
    summary,
    pagination,
    receiptPagination,
    paymentFilters,
    receiptFilters,
    isLoading,
    isReceiptLoading,
    isReceiptPreviewLoading,
    isReceiptDownloading,
    isReminderSubmitting,
    error,
    receiptError,
    reminderError,
    paymentCount,
    paidPayments,
    unpaidPayments,
    paidPaymentCount,
    unpaidPaymentCount,
    partiallyPaidPaymentCount,
    totalCollectedAmount,
    totalPendingAmount,
    totalBilledAmount,
    availableMonths,
    hasActivePaymentFilters,
    errorMessage,
    receiptErrorMessage,
    reminderErrorMessage,
    fetchPayments,
    fetchPaymentHistory,
    fetchReceipts,
    fetchReceiptDetail,
    downloadReceipt,
    createWhatsAppReminder,
    generateMonthlyPayments,
    recordPayment,
    updatePaymentFilter,
    setPaymentFilters,
    resetPaymentFilters,
    updateReceiptFilter,
    setReceiptFilters,
    resetReceiptFilters,
    clearSelectedPayment,
    clearSelectedReceipt,
    clearSelectedReminder,
    clearError,
  }
})
