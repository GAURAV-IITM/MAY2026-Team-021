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
]

export default adminRoutes
