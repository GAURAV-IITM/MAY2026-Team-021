import AdminLayout from '../layouts/AdminLayout.vue'

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
        path: 'payments',
        name: 'adminPayments',
        component: AdminPayments,
        meta: { title: 'Payments', role: 'admin', requiresAuth: true },
      },
      {
        path: 'reports',
        name: 'adminReports',
        component: AdminReports,
        meta: { title: 'Reports', role: 'admin', requiresAuth: true },
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
