import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { PAYMENT_STATUSES } from '../mocks/paymentMock.js'
import * as paymentService from '../services/paymentService.js'

// src/stores: Centralized payment state for payment management workflows.
// The store remains a thin state layer and delegates payment operations to paymentService.
//
// TODO:
// - Replace mock-backed service calls with FastAPI-backed service calls in Milestone 3.
// - Keep filtering, receipt generation, and reminder workflows behind paymentService.

export const usePaymentStore = defineStore('payment', () => {
  const payments = ref([])
  const selectedPayment = ref(null)
  const receipts = ref([])
  const pendingPayments = ref([])
  const selectedReceipt = ref(null)
  const selectedReminder = ref(null)

  const paymentFilters = ref({
    search: '',
    month: '',
    status: '',
  })

  const isLoading = ref(false)
  const error = ref(null)

  const paymentCount = computed(() => payments.value.length)

  const paidPayments = computed(() => {
    return payments.value.filter(
      (payment) => payment.status === PAYMENT_STATUSES.PAID,
    )
  })

  const unpaidPayments = computed(() => {
    return payments.value.filter(
      (payment) => payment.status === PAYMENT_STATUSES.UNPAID,
    )
  })

  const paidPaymentCount = computed(() => paidPayments.value.length)
  const unpaidPaymentCount = computed(() => unpaidPayments.value.length)

  const totalCollectedAmount = computed(() => {
    return paidPayments.value.reduce((total, payment) => {
      return total + Number(payment.amount || 0)
    }, 0)
  })

  const totalPendingAmount = computed(() => {
    return unpaidPayments.value.reduce((total, payment) => {
      return total + Number(payment.amount || 0)
    }, 0)
  })

  const availableMonths = computed(() => {
    return [...new Set(payments.value.map((payment) => payment.month))]
      .filter(Boolean)
      .sort((firstMonth, secondMonth) => secondMonth.localeCompare(firstMonth))
  })

  const hasActivePaymentFilters = computed(() => {
    return Object.values(paymentFilters.value).some((value) => Boolean(value))
  })

  const errorMessage = computed(() => {
    return error.value?.response?.data?.message || error.value?.message || ''
  })

  function getResponseData(response) {
    return response?.data || {}
  }

  function syncPaymentList(response) {
    const data = getResponseData(response)

    if (Array.isArray(data.payments)) {
      payments.value = data.payments
    }
  }

  function syncSelectedPayment(response) {
    const data = getResponseData(response)

    if (data.payment) {
      selectedPayment.value = data.payment
    }
  }

  async function runPaymentServiceRequest(serviceRequest) {
    isLoading.value = true
    error.value = null

    try {
      return await serviceRequest()
    } catch (requestError) {
      error.value = requestError
      throw requestError
    } finally {
      isLoading.value = false
    }
  }

  async function fetchPayments(filters = paymentFilters.value) {
    const response = await runPaymentServiceRequest(() =>
      paymentService.getPayments({ ...filters }),
    )

    syncPaymentList(response)

    return response
  }

  async function fetchPaymentById(paymentId) {
    const response = await runPaymentServiceRequest(() =>
      paymentService.getPaymentById(paymentId),
    )

    syncSelectedPayment(response)

    return response
  }

  async function createPayment(paymentPayload) {
    const response = await runPaymentServiceRequest(() =>
      paymentService.createPayment(paymentPayload),
    )

    syncPaymentList(response)
    syncSelectedPayment(response)

    return response
  }

  async function updatePaymentStatus(paymentId, statusPayload) {
    const response = await runPaymentServiceRequest(() =>
      paymentService.updatePaymentStatus(paymentId, statusPayload),
    )

    syncPaymentList(response)
    syncSelectedPayment(response)

    return response
  }

  async function fetchPaymentHistory(filters = paymentFilters.value) {
    const response = await runPaymentServiceRequest(() =>
      paymentService.getPaymentHistory({ ...filters }),
    )

    syncPaymentList(response)

    return response
  }

  async function fetchPendingPayments(filters = paymentFilters.value) {
    const response = await runPaymentServiceRequest(() =>
      paymentService.getPendingPayments({ ...filters }),
    )

    const data = getResponseData(response)
    pendingPayments.value = Array.isArray(data.payments) ? data.payments : []

    return response
  }

  async function fetchReceipts(filters = paymentFilters.value) {
    const response = await runPaymentServiceRequest(() =>
      paymentService.getReceipts({ ...filters }),
    )

    const data = getResponseData(response)
    receipts.value = Array.isArray(data.receipts) ? data.receipts : []

    return response
  }

  async function generateReceipt(paymentId) {
    const response = await runPaymentServiceRequest(() =>
      paymentService.generateReceipt(paymentId),
    )

    const data = getResponseData(response)

    selectedReceipt.value = data.receipt || null
    syncSelectedPayment(response)

    return response
  }

  async function generateWhatsAppReminder(paymentId, reminderPayload = {}) {
    const response = await runPaymentServiceRequest(() =>
      paymentService.generateWhatsAppReminder(paymentId, reminderPayload),
    )

    const data = getResponseData(response)

    selectedReminder.value = data.reminder || null
    syncSelectedPayment(response)

    return response
  }

  function updatePaymentFilter(filterName, value) {
    if (!(filterName in paymentFilters.value)) return

    paymentFilters.value = {
      ...paymentFilters.value,
      [filterName]: value,
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
      search: '',
      month: '',
      status: '',
    }
  }

  function clearSelectedPayment() {
    selectedPayment.value = null
  }

  function clearSelectedReceipt() {
    selectedReceipt.value = null
  }

  function clearSelectedReminder() {
    selectedReminder.value = null
  }

  function clearError() {
    error.value = null
  }

  return {
    payments,
    selectedPayment,
    receipts,
    pendingPayments,
    selectedReceipt,
    selectedReminder,
    paymentFilters,
    isLoading,
    error,

    paymentCount,
    paidPayments,
    unpaidPayments,
    paidPaymentCount,
    unpaidPaymentCount,
    totalCollectedAmount,
    totalPendingAmount,
    availableMonths,
    hasActivePaymentFilters,
    errorMessage,

    fetchPayments,
    fetchPaymentById,
    createPayment,
    updatePaymentStatus,
    fetchPaymentHistory,
    fetchPendingPayments,
    fetchReceipts,
    generateReceipt,
    generateWhatsAppReminder,

    updatePaymentFilter,
    setPaymentFilters,
    resetPaymentFilters,
    clearSelectedPayment,
    clearSelectedReceipt,
    clearSelectedReminder,
    clearError,
  }
})