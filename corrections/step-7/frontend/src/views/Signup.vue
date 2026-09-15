<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { API, setToken, setMe } from '../api.js'

const router = useRouter()
const family = ref('')
const name = ref('')
const lien = ref('mère')
const email = ref('')
const password = ref('')
const error = ref('')
const LIENS = ['mère', 'père', 'fille', 'fils', 'frère', 'sœur', 'grand-mère', 'grand-père', 'oncle', 'tante']

async function submit() {
  error.value = ''
  if (!family.value.trim() || !name.value.trim() || !email.value.trim() || !password.value) {
    error.value = 'Remplis tous les champs.'; return
  }
  const q = new URLSearchParams({
    email: email.value.trim(), password: password.value,
    name: name.value.trim(), family: family.value.trim(), lien: lien.value,
  })
  const r = await fetch(`${API}/api/signup?${q}`, { method: 'POST' })
  if (!r.ok) {
    const d = await r.json().catch(() => ({}))
    error.value = d.detail || 'Impossible de créer le compte.'; return
  }
  const data = await r.json()
  setToken(data.token); setMe(data)
  router.push('/famille')
}
</script>

<template>
  <div class="auth">
    <div class="hero">
      <div class="logo">🏠</div>
      <h1>Créer ma famille</h1>
      <p>Tu seras l'<strong>admin</strong> : tu créeras ensuite les comptes de tes proches.</p>
    </div>

    <div class="panel">
      <h2>Nouveau compte</h2>
      <label>Nom de la famille</label>
      <input v-model="family" placeholder="ex : Durand" />
      <label>Ton prénom</label>
      <input v-model="name" placeholder="ex : Maman" />
      <label>Ton lien de parenté</label>
      <select v-model="lien"><option v-for="l in LIENS" :key="l" :value="l">{{ l }}</option></select>
      <label>Email</label>
      <input v-model="email" type="email" autocomplete="email" placeholder="ex : maman@durand.fr" />
      <label>Mot de passe</label>
      <input v-model="password" type="password" autocomplete="new-password" placeholder="••••••" @keyup.enter="submit" />
      <button class="primary block" @click="submit">Créer ma famille</button>
      <p class="err" v-if="error">{{ error }}</p>
      <p class="switch">Déjà un compte ? <router-link to="/login">Se connecter</router-link></p>
    </div>
  </div>
</template>
