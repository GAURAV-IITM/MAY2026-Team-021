import StudentLayout from '../layouts/StudentLayout.vue'

import StudentDashboard from '../pages/student/Dashboard.vue'
import StudentMySeat from '../pages/student/MySeat.vue'
import StudentFees from '../pages/student/Fees.vue'
import StudentReceipts from '../pages/student/Receipts.vue'
import StudentRequests from '../pages/student/Requests.vue'
import StudentAnnouncements from '../pages/student/Announcements.vue'
import StudentProfile from '../pages/student/Profile.vue'

// Student route module.
// TODO: Attach student guards after authentication and permissions are implemented.
const studentRoutes = [
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
]

export default studentRoutes
