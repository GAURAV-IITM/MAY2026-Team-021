import AdminLayout from '../layouts/AdminLayout.vue'

import AdminDashboard from '../pages/admin/Dashboard.vue'
import AdminStudents from '../pages/admin/Students.vue'
import AdminStudentDetails from '../pages/admin/StudentDetails.vue'
import AdminSeatRequests from '../pages/admin/SeatRequests.vue'
import AdminAddStudent from '../pages/admin/AddStudent.vue'
import AdminEditStudent from '../pages/admin/EditStudent.vue'
import AdminSeatManagement from '../pages/admin/SeatManagement.vue'
import AdminSeatAvailability from '../pages/admin/SeatAvailability.vue'
import AdminShiftManagement from '../pages/admin/ShiftManagement.vue'
import AdminPayments from '../pages/admin/Payments.vue'
import AdminReceipts from '../pages/admin/Receipts.vue'
const AdminReports = () => import('../pages/admin/Reports.vue')
const AdminAnnouncements = () => import('../pages/admin/Announcements.vue')
const AdminSettings = () => import('../pages/admin/Settings.vue')

// Admin route module.
// TODO: Attach admin guards after authentication and permissions are implemented.
const adminRoutes = [
  {
    path: '/admin',
    component: AdminLayout,
    meta: { title: 'Admin', role: 'admin', requiresAuth: true },
    children: [
      {
        path: '',
        redirect: { name: 'adminDashboard' },
        meta: { title: 'Admin', role: 'admin', requiresAuth: true },
      },
      {
        path: 'dashboard',
        name: 'adminDashboard',
        component: AdminDashboard,
        meta: { title: 'Dashboard', role: 'admin', requiresAuth: true },
      },
      {
        path: 'students',
        name: 'adminStudents',
        component: AdminStudents,
        meta: { title: 'Students', role: 'admin', requiresAuth: true },
      },
      {
        path: 'seat-requests',
        name: 'adminSeatRequests',
        component: AdminSeatRequests,
        meta: { title: 'Seat Requests', role: 'admin', requiresAuth: true },
      },
      {
        path: 'students/add',
        name: 'adminAddStudent',
        component: AdminAddStudent,
        meta: { title: 'Add Student', role: 'admin', requiresAuth: true },
      },
      {
        path: 'students/:studentId',
        name: 'adminStudentDetails',
        component: AdminStudentDetails,
        meta: { title: 'Student Details', role: 'admin', requiresAuth: true },
      },
      {
        path: 'students/:studentId/edit',
        name: 'adminEditStudent',
        component: AdminEditStudent,
        meta: { title: 'Edit Student', role: 'admin', requiresAuth: true },
      },
      {
        path: 'seat-management',
        name: 'adminSeatManagement',
        component: AdminSeatManagement,
        meta: { title: 'Seat Management', role: 'admin', requiresAuth: true },
      },
      {
        path: 'seats/map',
        name: 'adminSeatMap',
        component: AdminSeatAvailability,
        meta: { title: 'Seat Map', role: 'admin', requiresAuth: true },
      },
      {
        path: 'shift-management',
        name: 'adminShiftManagement',
        component: AdminShiftManagement,
        meta: { title: 'Shift Management', role: 'admin', requiresAuth: true },
      },
      {
        path: 'payments',
        name: 'adminPayments',
        component: AdminPayments,
        meta: { title: 'Payments', role: 'admin', requiresAuth: true },
      },
      {
        path: 'receipts',
        name: 'adminReceipts',
        component: AdminReceipts,
        meta: { title: 'Receipts', role: 'admin', requiresAuth: true },
      },
      {
        path: 'reports',
        name: 'adminReports',
        component: AdminReports,
        meta: { title: 'Reports & Analytics', role: 'admin', requiresAuth: true },
      },
      {
        path: 'announcements',
        name: 'adminAnnouncements',
        component: AdminAnnouncements,
        meta: { title: 'Announcements', role: 'admin', requiresAuth: true },
      },
      {
        path: 'settings',
        name: 'adminSettings',
        component: AdminSettings,
        meta: { title: 'Settings', role: 'admin', requiresAuth: true },
      },
    ],
  },
]

export default adminRoutes
