<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiFetch } from './api'

const route = useRoute()
const router = useRouter()
const member = ref(null)
const hasToken = ref(false)

async function loadCurrentMember() {
  const token = localStorage.getItem('token')
  hasToken.value = Boolean(token)
  member.value = null

  if (!token) return

  try {
    const response = await apiFetch('/api/me')
    if (!response.ok) {
      localStorage.removeItem('token')
      hasToken.value = false
      return
    }
    member.value = await response.json()
  } catch {
    // Le garde de navigation protège toujours les pages privées si le serveur est indisponible.
  }
}

async function logout() {
  try {
    await apiFetch('/api/logout', { method: 'POST' })
  } finally {
    // La déconnexion locale reste garantie, même si le serveur ne répond pas.
    localStorage.removeItem('token')
    hasToken.value = false
    member.value = null
    await router.push('/login')
  }
}

watch(() => route.path, loadCurrentMember, { immediate: true })
</script>

<template>
  <div class="app-shell">
  <header class="app-header">
    <div class="topbar">
      <RouterLink class="brand" to="/tasks"><span class="brand-mark">F</span><span>FamilyTask</span></RouterLink>
      <div v-if="hasToken" class="member-bar">
        <span v-if="member" class="welcome"><span class="avatar avatar-small">{{ member.name.charAt(0).toUpperCase() }}</span><span>Bonjour {{ member.name }}</span></span>
        <button class="logout-button" type="button" aria-label="Se déconnecter" @click="logout">Sortir</button>
      </div>
    </div>
  </header>
  <RouterView />
  <nav v-if="hasToken" class="bottom-tabs" aria-label="Navigation principale">
    <RouterLink to="/tasks">Tâches</RouterLink>
    <RouterLink to="/assistant">Assistant</RouterLink>
    <RouterLink v-if="member?.is_admin" to="/family">Famille</RouterLink>
  </nav>
  </div>
</template>
