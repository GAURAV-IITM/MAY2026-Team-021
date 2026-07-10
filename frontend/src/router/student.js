import StudentLayout from '../layouts/StudentLayout.vue'

import StudentDashboard from '../pages/student/Dashboard.vue'
import StudentMySeat from '../pages/student/MySeat.vue'
import StudentFees from '../pages/student/Fees.vue'
import StudentRequests from '../pages/student/Requests.vue'
import StudentAnnouncements from '../pages/student/Announcements.vue'
import StudentProfile from '../pages/student/Profile.vue'

// Student route module.
// TODO: Attach student guards after authentication and permissions are implemented.
const studentRoutes = [
  {
    path: '/student',
    component: StudentLayout,
    meta: { title: 'Student', role: 'student', requiresAuth: true },
    children: [
      {
        path: '',
        redirect: { name: 'studentDashboard' },
        meta: { title: 'Student', role: 'student', requiresAuth: true },
      },
      {
        path: 'dashboard',
        name: 'studentDashboard',
        component: StudentDashboard,
        meta: { title: 'Dashboard', role: 'student', requiresAuth: true },
      },
      {
        path: 'my-seat',
        name: 'studentMySeat',
        component: StudentMySeat,
        meta: { title: 'My Seat', role: 'student', requiresAuth: true },
      },
      {
        path: 'fees',
        name: 'studentFees',
        component: StudentFees,
        meta: { title: 'Fees', role: 'student', requiresAuth: true },
      },
      {
        path: 'requests',
        name: 'studentRequests',
        component: StudentRequests,
        meta: { title: 'Requests', role: 'student', requiresAuth: true },
      },
      {
        path: 'announcements',
        name: 'studentAnnouncements',
        component: StudentAnnouncements,
        meta: { title: 'Announcements', role: 'student', requiresAuth: true },
      },
      {
        path: 'profile',
        name: 'studentProfile',
        component: StudentProfile,
        meta: { title: 'Profile', role: 'student', requiresAuth: true },
      },
    ],
  },
]

export default studentRoutes
