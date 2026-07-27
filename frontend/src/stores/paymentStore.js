import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { PAYMENT_STATUSES } from '../constants/payment.js'
import * as paymentService from '../services/paymentService.js'
import * as receiptService from '../services/receiptMockService.js'

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
  const summary = ref(emptySummary())
  const pagination = ref(emptyPagination())
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
  const error = ref(null)
  let latestListRequest = 0

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

  async function fetchReceipts(filters = {}) {
    isLoading.value = true
    error.value = null
    try {
      const response = await receiptService.getReceipts(filters)
      receipts.value = response.data.receipts || []
      return response
    } catch (requestError) {
      error.value = requestError
      throw requestError
    } finally {
      isLoading.value = false
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

  function clearSelectedPayment() {
    selectedPayment.value = null
  }

  function clearError() {
    error.value = null
  }

  return {
    payments,
    selectedPayment,
    receipts,
    summary,
    pagination,
    paymentFilters,
    isLoading,
    error,
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
    fetchPayments,
    fetchPaymentHistory,
    fetchReceipts,
    generateMonthlyPayments,
    recordPayment,
    updatePaymentFilter,
    setPaymentFilters,
    resetPaymentFilters,
    clearSelectedPayment,
    clearError,
  }
})
