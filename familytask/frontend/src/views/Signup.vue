<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch } from '../api'

const router = useRouter()
const form = ref({ family: '', name: '', lien: '', email: '', password: '' })
const errorMessage = ref('')
const isSubmitting = ref(false)

async function submitSignup() {
  errorMessage.value = ''
  isSubmitting.value = true

  try {
    const response = await apiFetch('/api/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value)
    })
    const data = await response.json()

    if (!response.ok) {
      errorMessage.value = data.detail || 'Impossible de créer la famille.'
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
    <section class="auth-card signup-card">
      <div class="auth-intro">
        <span class="eyebrow">NOUVEAU DÉPART</span>
        <span class="auth-glyph">✦</span>
        <h2>Créer ton cercle.</h2>
        <p>Le quotidien de la famille, au même endroit.</p>
      </div>

      <form @submit.prevent="submitSignup">
        <p v-if="errorMessage" class="error-message" role="alert">{{ errorMessage }}</p>
        <label>
          Nom de famille
          <input v-model.trim="form.family" type="text" required autocomplete="family-name">
        </label>
        <label>
          Prénom
          <input v-model.trim="form.name" type="text" required autocomplete="given-name">
        </label>
        <label>
          Lien de parenté
          <input v-model.trim="form.lien" type="text" placeholder="Mère, père, enfant..." required>
        </label>
        <label>
          Email
          <input v-model.trim="form.email" type="email" required autocomplete="email">
        </label>
        <label>
          Mot de passe
          <input v-model="form.password" type="password" required minlength="4" autocomplete="new-password">
        </label>
        <button class="primary-action" type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? 'Création...' : 'Créer la famille' }}
        </button>
      </form>
      <p class="auth-switch">Déjà un compte ? <RouterLink class="link" to="/login">Se connecter</RouterLink></p>
    </section>
  </main>
</template>
