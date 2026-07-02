import { createRouter, createWebHistory } from 'vue-router'

import AuthLayout from '../layouts/AuthLayout.vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import StudentLayout from '../layouts/StudentLayout.vue'
import SuperAdminLayout from '../layouts/SuperAdminLayout.vue'

import Login from '../pages/auth/Login.vue'
import RegisterLibrary from '../pages/auth/RegisterLibrary.vue'
import ForgotPassword from '../pages/auth/ForgotPassword.vue'

import AdminDashboard from '../pages/admin/Dashboard.vue'
import AdminStudents from '../pages/admin/Students.vue'
import AdminStudentDetails from '../pages/admin/StudentDetails.vue'
import AdminAddStudent from '../pages/admin/AddStudent.vue'
import AdminEditStudent from '../pages/admin/EditStudent.vue'
import AdminSeatManagement from '../pages/admin/SeatManagement.vue'
import AdminPayments from '../pages/admin/Payments.vue'
import AdminReports from '../pages/admin/Reports.vue'
import AdminAnnouncements from '../pages/admin/Announcements.vue'
import AdminSettings from '../pages/admin/Settings.vue'

import StudentDashboard from '../pages/student/Dashboard.vue'
import StudentMySeat from '../pages/student/MySeat.vue'
import StudentFees from '../pages/student/Fees.vue'
import StudentReceipts from '../pages/student/Receipts.vue'
import StudentRequests from '../pages/student/Requests.vue'
import StudentAnnouncements from '../pages/student/Announcements.vue'
import StudentProfile from '../pages/student/Profile.vue'

import SuperAdminDashboard from '../pages/superadmin/Dashboard.vue'
import SuperAdminLibraries from '../pages/superadmin/Libraries.vue'
import SuperAdminOwners from '../pages/superadmin/Owners.vue'
import SuperAdminSubscriptions from '../pages/superadmin/Subscriptions.vue'
import SuperAdminAnalytics from '../pages/superadmin/Analytics.vue'
import SuperAdminSettings from '../pages/superadmin/Settings.vue'

import NotFound from '../pages/shared/NotFound.vue'

// src/router: Central route definitions and future navigation guards.
// TODO: Add authentication, role, and tenant guards after auth APIs are implemented.
const routes = [
  {
    path: '/',
    component: AuthLayout,
    children: [
      { path: '', redirect: { name: 'login' } },
      { path: 'login', name: 'login', component: Login },
      { path: 'register-library', name: 'registerLibrary', component: RegisterLibrary },
      { path: 'forgot-password', name: 'forgotPassword', component: ForgotPassword },
    ],
  },
  {
    path: '/admin',
    component: AdminLayout,
    children: [
      { path: '', redirect: { name: 'adminDashboard' } },
      { path: 'dashboard', name: 'adminDashboard', component: AdminDashboard },
      { path: 'students', name: 'adminStudents', component: AdminStudents },
      { path: 'students/add', name: 'adminAddStudent', component: AdminAddStudent },
      { path: 'students/:studentId', name: 'adminStudentDetails', component: AdminStudentDetails },
      { path: 'students/:studentId/edit', name: 'adminEditStudent', component: AdminEditStudent },
      { path: 'seat-management', name: 'adminSeatManagement', component: AdminSeatManagement },
      { path: 'payments', name: 'adminPayments', component: AdminPayments },
      { path: 'reports', name: 'adminReports', component: AdminReports },
      { path: 'announcements', name: 'adminAnnouncements', component: AdminAnnouncements },
      { path: 'settings', name: 'adminSettings', component: AdminSettings },
    ],
  },
  {
    path: '/student',
    component: StudentLayout,
    children: [
      { path: '', redirect: { name: 'studentDashboard' } },
      { path: 'dashboard', name: 'studentDashboard', component: StudentDashboard },
      { path: 'my-seat', name: 'studentMySeat', component: StudentMySeat },
      { path: 'fees', name: 'studentFees', component: StudentFees },
      { path: 'receipts', name: 'studentReceipts', component: StudentReceipts },
      { path: 'requests', name: 'studentRequests', component: StudentRequests },
      { path: 'announcements', name: 'studentAnnouncements', component: StudentAnnouncements },
      { path: 'profile', name: 'studentProfile', component: StudentProfile },
    ],
  },
  {
    path: '/superadmin',
    component: SuperAdminLayout,
    children: [
      { path: '', redirect: { name: 'superAdminDashboard' } },
      { path: 'dashboard', name: 'superAdminDashboard', component: SuperAdminDashboard },
      { path: 'libraries', name: 'superAdminLibraries', component: SuperAdminLibraries },
      { path: 'owners', name: 'superAdminOwners', component: SuperAdminOwners },
      {
        path: 'subscriptions',
        name: 'superAdminSubscriptions',
        component: SuperAdminSubscriptions,
      },
      { path: 'analytics', name: 'superAdminAnalytics', component: SuperAdminAnalytics },
      { path: 'settings', name: 'superAdminSettings', component: SuperAdminSettings },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'notFound',
    component: NotFound,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
