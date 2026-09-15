<script setup>
import { ref, onMounted } from 'vue'
import TaskList from './components/TaskList.vue'

// Les tâches viennent maintenant du back (elles sont sauvegardées en base).
const tasks = ref([])
const newTitle = ref('')

async function refresh() {
  tasks.value = await (await fetch('/api/tasks')).json()
}
async function addTask() {
  if (!newTitle.value.trim()) return
  await fetch(`/api/tasks?${new URLSearchParams({ title: newTitle.value })}`, { method: 'POST' })
  newTitle.value = ''
  await refresh()
}
async function toggle(t) {
  await fetch(`/api/tasks/${t.id}`, { method: 'PATCH' })
  await refresh()
}
async function remove(t) {
  await fetch(`/api/tasks/${t.id}`, { method: 'DELETE' })
  await refresh()
}
onMounted(refresh)
</script>

<template>
  <header><h1>🏠 FamilyTask</h1></header>
  <main>
    <div class="card">
      <h2>Nouvelle tâche</h2>
      <div class="row">
        <input v-model="newTitle" placeholder="Ex: Sortir les poubelles" @keyup.enter="addTask" />
        <button @click="addTask">Ajouter</button>
      </div>
    </div>
    <div class="card">
      <h2>Les tâches (sauvegardées)</h2>
      <TaskList :tasks="tasks" @toggle="toggle" @remove="remove" />
    </div>
  </main>
</template>
