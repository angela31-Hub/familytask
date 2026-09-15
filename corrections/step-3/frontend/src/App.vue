<script setup>
import { ref } from 'vue'
import TaskList from './components/TaskList.vue'

// Données locales (pas encore de base de données) — juste pour construire l'interface.
const tasks = ref([
  { id: 1, title: 'Sortir les poubelles', done: false },
  { id: 2, title: 'Faire les courses', done: true },
])
const newTitle = ref('')
let nextId = 3

function addTask() {
  if (!newTitle.value.trim()) return
  tasks.value.push({ id: nextId++, title: newTitle.value, done: false })
  newTitle.value = ''
}
function toggle(t) { t.done = !t.done }
function remove(t) { tasks.value = tasks.value.filter(x => x.id !== t.id) }
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
      <h2>Les tâches</h2>
      <TaskList :tasks="tasks" @toggle="toggle" @remove="remove" />
    </div>
  </main>
</template>
