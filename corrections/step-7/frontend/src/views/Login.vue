<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { API, setToken, setMe } from '../api.js'

const router = useRouter()
const email = ref('')
const password = ref('')
const error = ref('')

async function connect() {
  error.value = ''
  if (!email.value.trim() || !password.value) { error.value = 'Email et mot de passe requis.'; return }
  const q = new URLSearchParams({ email: email.value.trim(), password: password.value })
  const r = await fetch(`${API}/api/login?${q}`, { method: 'POST' })
  if (!r.ok) { error.value = 'Email ou mot de passe incorrect.'; return }
  const data = await r.json()
  setToken(data.token); setMe(data)
  router.push('/taches')
}
</script>

<template>
  <div class="auth">
    <div class="hero">
      <div class="logo">🏠</div>
      <h1>FamilyTask</h1>
      <p>Les tâches de toute la famille, au même endroit.</p>
    </div>

    <div class="panel">
      <h2>Se connecter</h2>
      <label>Email</label>
      <input v-model="email" type="email" autocomplete="email" placeholder="ex : maman@durand.fr" @keyup.enter="connect" />
      <label>Mot de passe</label>
      <input v-model="password" type="password" autocomplete="current-password" placeholder="••••••" @keyup.enter="connect" />
      <button class="primary block" @click="connect">Se connecter</button>
      <p class="err" v-if="error">{{ error }}</p>
      <p class="switch">Pas encore de compte ? <router-link to="/signup">Créer ma famille</router-link></p>
    </div>
  </div>
</template>
