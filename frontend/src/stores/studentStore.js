import { defineStore } from 'pinia'

// src/stores: Pinia state containers for shared frontend state.
export const useStudentStore = defineStore('student', {
  state: () => ({
    students: [],
    selectedStudent: null,
    isLoading: false,
    error: null,
  }),
  getters: {
    studentCount: (state) => state.students.length,
  },
  actions: {
    async fetchStudents() {
      // TODO: Connect to studentService.getStudents after mock contract is ready.
    },
    async fetchStudentById() {
      // TODO: Connect to studentService.getStudentById after mock contract is ready.
    },
    async createStudent() {
      // TODO: Connect to studentService.createStudent after CRUD requirements are approved.
    },
    async updateStudent() {
      // TODO: Connect to studentService.updateStudent after CRUD requirements are approved.
    },
  },
})
