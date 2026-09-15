<script setup>
import { useRoute, useRouter } from 'vue-router'
import { isLogged, getMe, logout as apiLogout } from './api.js'

const route = useRoute()
const router = useRouter()

async function logout() { await apiLogout(); router.push('/login') }
</script>

<template>
  <div class="phone">
    <header class="appbar" v-if="isLogged() && route.meta.nav">
      <div class="brand">🏠 FamilyTask</div>
      <button class="link" @click="logout">Se déconnecter</button>
    </header>

    <main class="screen"><router-view /></main>

    <nav class="tabbar" v-if="isLogged() && route.meta.nav">
      <router-link to="/taches" class="tab"><span class="ico">✅</span>Tâches</router-link>
      <router-link v-if="getMe() && getMe().is_admin" to="/famille" class="tab"><span class="ico">👨‍👩‍👧</span>Famille</router-link>
    </nav>
  </div>
</template>
