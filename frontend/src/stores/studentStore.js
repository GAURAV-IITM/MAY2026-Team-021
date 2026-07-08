import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as studentService from '../services/studentService'

// src/stores: Centralized Student Management state for Milestone 2.
// Pages and components should interact with this store instead of importing mocks directly.
export const useStudentStore = defineStore('student', () => {
  const students = ref([])
  const selectedStudent = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  const studentCount = computed(() => students.value.length)
  const activeStudentCount = computed(
    () => students.value.filter((student) => student.status === 'active').length,
  )
  const inactiveStudentCount = computed(
    () => students.value.filter((student) => student.status === 'inactive').length,
  )

  function getErrorMessage(requestError) {
    return (
      requestError?.response?.data?.message ||
      requestError?.message ||
      'An unexpected student service error occurred.'
    )
  }

  async function runStudentServiceRequest(serviceRequest) {
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

  function replaceStudentInList(updatedStudent) {
    const studentIndex = students.value.findIndex(
      (student) => student.id === updatedStudent.id,
    )

    if (studentIndex === -1) {
      students.value.push(updatedStudent)
      return
    }

    students.value.splice(studentIndex, 1, updatedStudent)
  }

  async function fetchStudents() {
    const response = await runStudentServiceRequest(() =>
      studentService.getStudents(),
    )

    students.value = response.data

    return response
  }

  async function fetchStudentById(studentId) {
    const response = await runStudentServiceRequest(() =>
      studentService.getStudentById(studentId),
    )

    selectedStudent.value = response.data

    return response
  }

  async function createStudent(studentData) {
    const response = await runStudentServiceRequest(() =>
      studentService.createStudent(studentData),
    )

    students.value.push(response.data)
    selectedStudent.value = response.data

    return response
  }

  async function updateStudent(studentId, studentData) {
    const response = await runStudentServiceRequest(() =>
      studentService.updateStudent(studentId, studentData),
    )

    replaceStudentInList(response.data)

    if (selectedStudent.value?.id === String(studentId)) {
      selectedStudent.value = response.data
    }

    return response
  }

  async function deactivateStudent(studentId) {
    const response = await runStudentServiceRequest(() =>
      studentService.deactivateStudent(studentId),
    )

    replaceStudentInList(response.data)

    if (selectedStudent.value?.id === String(studentId)) {
      selectedStudent.value = response.data
    }

    return response
  }

  function clearSelectedStudent() {
    selectedStudent.value = null
  }

  function clearError() {
    error.value = null
  }

  return {
    students,
    selectedStudent,
    isLoading,
    error,

    studentCount,
    activeStudentCount,
    inactiveStudentCount,

    errorMessage: computed(() => (error.value ? getErrorMessage(error.value) : '')),

    fetchStudents,
    fetchStudentById,
    createStudent,
    updateStudent,
    deactivateStudent,
    clearSelectedStudent,
    clearError,
  }
})