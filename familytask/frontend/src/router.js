import { createRouter, createWebHistory } from 'vue-router'
import Login from './views/Login.vue'
import Signup from './views/Signup.vue'
import TasksView from './views/TasksView.vue'
import FamilyView from './views/FamilyView.vue'
import AssistantView from './views/AssistantView.vue'
import { apiFetch } from './api'

const routes = [
  { path: '/', redirect: '/tasks' },
  { path: '/login', component: Login },
  { path: '/signup', component: Signup },
  { path: '/tasks', component: TasksView, meta: { requiresAuth: true } },
  { path: '/assistant', component: AssistantView, meta: { requiresAuth: true } },
  { path: '/family', component: FamilyView, meta: { requiresAuth: true, requiresAdmin: true } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to) => {
  // Redirige toute page privée vers la connexion si aucun token n'est enregistré.
  if (to.meta.requiresAuth && !localStorage.getItem('token')) {
    return { path: '/login' }
  }

  if (to.meta.requiresAdmin) {
    // Vérifie côté routeur que la page famille est réservée aux administrateurs.
    const response = await apiFetch('/api/me')
    if (response.status === 401) {
      localStorage.removeItem('token')
      return { path: '/login' }
    }
    if (!response.ok || !(await response.json()).is_admin) return { path: '/tasks' }
  }

  // Évite de laisser un utilisateur déjà connecté revenir aux formulaires publics.
  if ((to.path === '/login' || to.path === '/signup') && localStorage.getItem('token')) {
    return { path: '/tasks' }
  }
})

export default router
