<script setup>
import { ref, onMounted } from 'vue'
import TaskList from './components/TaskList.vue'

const status = ref('...')
const tasks = ref([]) // Stocke les tâches chargées depuis l'API.
const newTitle = ref('') // Stocke le titre saisi dans le formulaire.

async function loadTasks() { // Recharge la liste des tâches depuis l'API.
  const response = await fetch('/api/tasks') // Demande toutes les tâches au back-end.
  if (!response.ok) throw new Error('Impossible de charger les tâches') // Signale une erreur HTTP.
  tasks.value = await response.json() // Remplace les données locales par la réponse du serveur.
}

async function addTask() { // Ajoute une nouvelle tâche dans la base de données.
  const title = newTitle.value.trim() // Nettoie le titre saisi par l'utilisateur.
  if (!title) return // Ignore l'envoi si le titre est vide.
  const response = await fetch('/api/tasks', { // Appelle l'API de création.
    method: 'POST', // Utilise la méthode HTTP POST.
    headers: { 'Content-Type': 'application/json' }, // Indique que le corps est au format JSON.
    body: JSON.stringify({ title }) // Envoie le titre au back-end.
  })
  if (!response.ok) throw new Error('Impossible d’ajouter la tâche') // Signale une erreur HTTP.
  newTitle.value = '' // Vide le champ après une création réussie.
  await loadTasks() // Recharge la liste depuis la base de données.
}

async function toggleTask(taskToToggle) { // Bascule l'état d'une tâche dans la base.
  const response = await fetch(`/api/tasks/${taskToToggle.id}`, { method: 'PATCH' }) // Appelle l'API de basculement.
  if (!response.ok) throw new Error('Impossible de modifier la tâche') // Signale une erreur HTTP.
  await loadTasks() // Recharge la liste après la modification.
}

async function removeTask(taskToRemove) { // Supprime une tâche de la base de données.
  const response = await fetch(`/api/tasks/${taskToRemove.id}`, { method: 'DELETE' }) // Appelle l'API de suppression.
  if (!response.ok) throw new Error('Impossible de supprimer la tâche') // Signale une erreur HTTP.
  await loadTasks() // Recharge la liste après la suppression.
}

onMounted(async () => {
  try {
    const healthResponse = await fetch('/api/health') // Vérifie que le back-end répond.
    status.value = (await healthResponse.json()).status // Affiche l'état du back-end.
    await loadTasks() // Charge les tâches au démarrage de l'application.
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
      <form @submit.prevent="addTask">
        <input v-model="newTitle" type="text" placeholder="Nouvelle tâche" aria-label="Titre de la tâche">
        <button type="submit">Ajouter</button>
      </form>
      <TaskList :tasks="tasks" @toggle="toggleTask" @remove="removeTask" />
    </div>
  </main>
</template>git add 
