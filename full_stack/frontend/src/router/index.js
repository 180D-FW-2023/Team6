import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/lessons',
      name: 'lessons',
      component: () => import('../views/LessonsView.vue')
    },
    {
      path: '/testing',
      name: 'testing',
      component: () => import('../views/TestingView.vue')
    }
  ]
})

export default router
