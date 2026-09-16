<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import TaskList from '../components/TaskList.vue'
import { apiFetch } from '../api'

const router = useRouter()
const tasks = ref([])
const currentMember = ref(null)
const familyMembers = ref([])
const selectedMemberId = ref('')
const newTitle = ref('')
const errorMessage = ref('')
const isLoading = ref(true)

async function loadTasks() {
  const response = await apiFetch('/api/tasks')
  if (response.status === 401) {
    localStorage.removeItem('token')
    await router.push('/login')
    return
  }
  if (!response.ok) throw new Error('Impossible de charger les tâches.')
  tasks.value = await response.json()
}

async function loadCurrentMember() {
  const response = await apiFetch('/api/me')
  if (response.status === 401) {
    localStorage.removeItem('token')
    await router.push('/login')
    return
  }
  if (!response.ok) throw new Error('Impossible de charger le membre connecté.')
  currentMember.value = await response.json()
}

async function loadFamilyMembers() {
  const response = await apiFetch('/api/members')
  if (!response.ok) throw new Error('Impossible de charger les membres de la famille.')
  familyMembers.value = (await response.json()).filter(
    member => member.id !== currentMember.value.id
  )
}

async function addTask() {
  const title = newTitle.value.trim()
  if (!title) return

  const taskData = { title }
  if (selectedMemberId.value) taskData.member_id = Number(selectedMemberId.value)

  const response = await apiFetch('/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(taskData)
  })
  if (!response.ok) throw new Error('Impossible d’ajouter la tâche.')
  newTitle.value = ''
  selectedMemberId.value = ''
  await loadTasks()
}

async function toggleTask(taskToToggle) {
  const response = await apiFetch(`/api/tasks/${taskToToggle.id}`, {
    method: 'PATCH',
  })
  if (!response.ok) throw new Error('Impossible de modifier la tâche.')
  await loadTasks()
}

async function removeTask(taskToRemove) {
  const response = await apiFetch(`/api/tasks/${taskToRemove.id}`, {
    method: 'DELETE',
  })
  if (!response.ok) throw new Error('Impossible de supprimer la tâche.')
  await loadTasks()
}

async function logout() {
  try {
    await apiFetch('/api/logout', { method: 'POST' })
  } finally {
    localStorage.removeItem('token')
    await router.push('/login')
  }
}

onMounted(async () => {
  try {
    await loadCurrentMember()
    if (currentMember.value?.is_admin) await loadFamilyMembers()
    await loadTasks()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    isLoading.value = false
  }
})

onMounted(() => window.addEventListener('tasks-updated', loadTasks))
onBeforeUnmount(() => window.removeEventListener('tasks-updated', loadTasks))
</script>

<template>
  <main>
    <section class="card">
      <div class="tasks-toolbar">
        <div class="page-heading">
          <h2>Les tâches d’hier</h2>
          <p>Organisez la journée de toute la famille.</p>
        </div>
        <button type="button" @click="logout">Déconnexion</button>
      </div>

      <p v-if="errorMessage" class="error-message" role="alert">{{ errorMessage }}</p>
      <p v-if="isLoading" class="hint">Chargement des tâches...</p>
      <template v-else>
        <form class="task-form" @submit.prevent="addTask">
          <div class="task-fields">
            <label>
              Nouvelle tâche
              <input v-model="newTitle" type="text" placeholder="Ex. Préparer le dîner" aria-label="Titre de la tâche">
            </label>
            <label v-if="currentMember?.is_admin">
              Pour qui ?
              <select v-model="selectedMemberId">
                <option value="">Pour moi</option>
                <option v-for="member in familyMembers" :key="member.id" :value="member.id">
                  {{ member.name }} ({{ member.lien }})
                </option>
              </select>
            </label>
          </div>
          <button type="submit">Ajouter</button>
        </form>
        <TaskList :tasks="tasks" @toggle="toggleTask" @remove="removeTask" />
      </template>
    </section>
  </main>
</template>
