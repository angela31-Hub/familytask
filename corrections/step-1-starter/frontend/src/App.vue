<script setup>
import { ref, onMounted } from 'vue'

const status = ref('...')
onMounted(async () => {
  try {
    const r = await fetch('/api/health')
    status.value = (await r.json()).status
  } catch (e) {
    status.value = 'back pas encore prêt'
  }
})
</script>

<template>
  <header><h1>🏠 FamilyTask</h1></header>
  <main>
    <div class="card">
      <h2>Bienvenue ! 🎉</h2>
      <p>Ton environnement fonctionne : le front (Vue) tourne sur le port 5173.</p>
      <p class="hint">Réponse du back : <strong>{{ status }}</strong></p>
    </div>
  </main>
</template>
