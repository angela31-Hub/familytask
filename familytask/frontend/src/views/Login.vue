<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch } from '../api'

const router = useRouter()
const email = ref('')
const password = ref('')
const errorMessage = ref('')
const isSubmitting = ref(false)

async function submitLogin() {
  errorMessage.value = ''
  isSubmitting.value = true

  try {
    const response = await apiFetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.value, password: password.value })
    })
    const data = await response.json()

    if (!response.ok) {
      errorMessage.value = data.detail || 'Email ou mot de passe incorrect.'
      return
    }

    localStorage.setItem('token', data.token)
    await router.push('/tasks')
  } catch {
    errorMessage.value = 'Le serveur est indisponible. Réessaie dans un instant.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-card">
      <div class="auth-intro">
        <span class="eyebrow">ESPACE FAMILLE</span>
        <span class="auth-glyph">↗</span>
        <h2>Ravi de te revoir.</h2>
        <p>Retrouve les tâches de ta famille, simplement.</p>
      </div>

      <form @submit.prevent="submitLogin">
        <p v-if="errorMessage" class="error-message" role="alert">{{ errorMessage }}</p>
        <label>
          Email
          <input v-model.trim="email" type="email" required autocomplete="email">
        </label>
        <label>
          Mot de passe
          <input v-model="password" type="password" required autocomplete="current-password">
        </label>
        <button class="primary-action" type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? 'Connexion...' : 'Se connecter' }}
        </button>
      </form>
      <p class="auth-switch">Pas encore de compte ? <RouterLink class="link" to="/signup">Créer ma famille</RouterLink></p>
    </section>
  </main>
</template>
