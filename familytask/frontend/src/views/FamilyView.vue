<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch } from '../api'

const router = useRouter()
const currentMember = ref(null)
const members = ref([])
const liens = ref([])
const familyTasks = ref([])
const errorMessage = ref('')
const isLoading = ref(true)
const isSubmitting = ref(false)
const isAddingLien = ref(false)
const newLienName = ref('')
const memberForm = ref({ name: '', lien: '', email: '', password: '', is_admin: false })

const tasksWithOwner = computed(() => familyTasks.value.map((task) => ({
  ...task,
  owner: members.value.find(member => member.id === task.member_id)
})))

async function loadFamily() {
  const responses = await Promise.all([
    apiFetch('/api/me'),
    apiFetch('/api/members'),
    apiFetch('/api/liens'),
    apiFetch('/api/tasks/famille')
  ])

  if (responses.some(response => response.status === 401)) {
    localStorage.removeItem('token')
    await router.push('/login')
    return
  }
  if (responses.some(response => !response.ok)) {
    throw new Error('Impossible de charger les données de la famille.')
  }

  currentMember.value = await responses[0].json()
  members.value = await responses[1].json()
  liens.value = await responses[2].json()
  familyTasks.value = await responses[3].json()
}

async function addMember() {
  errorMessage.value = ''
  isSubmitting.value = true

  try {
    const response = await apiFetch('/api/members', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(memberForm.value)
    })
    const data = await response.json()
    if (!response.ok) {
      errorMessage.value = data.detail || 'Impossible de créer ce membre.'
      return
    }

    members.value.push(data)
    memberForm.value = { name: '', lien: '', email: '', password: '', is_admin: false }
  } catch {
    errorMessage.value = 'Le serveur est indisponible. Réessaie dans un instant.'
  } finally {
    isSubmitting.value = false
  }
}

async function addLien() {
  const name = newLienName.value.trim()
  if (!name) return

  errorMessage.value = ''
  isAddingLien.value = true
  try {
    const response = await apiFetch('/api/liens', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    })
    const data = await response.json()
    if (!response.ok) {
      errorMessage.value = data.detail || 'Impossible d’ajouter ce lien.'
      return
    }

    liens.value.push(data)
    memberForm.value.lien = data.name
    newLienName.value = ''
  } catch {
    errorMessage.value = 'Le serveur est indisponible. Réessaie dans un instant.'
  } finally {
    isAddingLien.value = false
  }
}

async function deleteMember(member) {
  if (member.id === currentMember.value?.id) return
  if (!window.confirm(`Supprimer le compte de ${member.name} et ses tâches ?`)) return

  errorMessage.value = ''
  try {
    const response = await apiFetch(`/api/members/${member.id}`, { method: 'DELETE' })
    const data = await response.json()
    if (!response.ok) {
      errorMessage.value = data.detail || 'Impossible de supprimer ce membre.'
      return
    }

    members.value = members.value.filter(item => item.id !== member.id)
    familyTasks.value = familyTasks.value.filter(task => task.member_id !== member.id)
  } catch {
    errorMessage.value = 'Le serveur est indisponible. Réessaie dans un instant.'
  }
}

onMounted(async () => {
  try {
    await loadFamily()
    if (!currentMember.value?.is_admin) await router.push('/tasks')
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <main>
    <section class="card">
      <div class="page-heading">
        <h2>Ma famille</h2>
        <p>Gère les membres, les liens et les tâches de la famille.</p>
      </div>

      <p v-if="errorMessage" class="error-message" role="alert">{{ errorMessage }}</p>
      <p v-if="isLoading" class="hint">Chargement de la famille...</p>
      <div v-else class="family-grid">
        <section>
          <h3>Membres</h3>
          <ul class="member-list">
            <li v-for="member in members" :key="member.id" class="member-row">
              <div class="member-details">
                <strong class="member-name-line">
                  <span class="avatar" :class="`avatar-${member.id % 5}`">{{ member.name.charAt(0).toUpperCase() }}</span>
                  <span>{{ member.name }}</span>
                  <span v-if="member.is_admin" class="admin-badge">admin</span>
                </strong>
                <span class="member-meta">{{ member.lien }} · {{ member.email }}</span>
              </div>
              <button
                v-if="member.id !== currentMember?.id"
                class="danger-button"
                type="button"
                @click="deleteMember(member)"
              >Supprimer</button>
            </li>
          </ul>
        </section>

        <form class="family-form" @submit.prevent="addMember">
          <h3>Ajouter un membre</h3>
          <label>
            Prénom
            <input v-model.trim="memberForm.name" type="text" required>
          </label>
          <label>
            Lien de parenté
            <select v-model="memberForm.lien" required>
              <option disabled value="">Choisir un lien</option>
              <option v-for="lien in liens" :key="lien.id" :value="lien.name">{{ lien.name }}</option>
            </select>
          </label>
          <label>
            Email
            <input v-model.trim="memberForm.email" type="email" required>
          </label>
          <label>
            Mot de passe
            <input v-model="memberForm.password" type="password" minlength="4" required>
          </label>
          <label class="checkbox-label">
            <input v-model="memberForm.is_admin" type="checkbox">
            Administrateur
          </label>
          <button type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? 'Ajout...' : 'Ajouter le membre' }}
          </button>
        </form>

        <form class="family-form" @submit.prevent="addLien">
          <h3>Ajouter un lien de parenté</h3>
          <label>
            Nouveau lien
            <input v-model.trim="newLienName" type="text" placeholder="Oncle, cousine..." required>
          </label>
          <button type="submit" :disabled="isAddingLien">
            {{ isAddingLien ? 'Ajout...' : 'Ajouter le lien' }}
          </button>
        </form>

        <section>
          <h3>Tâches de la famille</h3>
          <p v-if="tasksWithOwner.length === 0" class="empty-message">Aucune tâche dans la famille.</p>
          <ul v-else class="family-task-list">
            <li v-for="task in tasksWithOwner" :key="task.id">
              <strong :class="{ completed: task.done }">{{ task.title }}</strong>
              <span class="task-owner">Responsable : {{ task.owner?.name || 'Membre supprimé' }}</span>
            </li>
          </ul>
        </section>
      </div>
    </section>
  </main>
</template>
