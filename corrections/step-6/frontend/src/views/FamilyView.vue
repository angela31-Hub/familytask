<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import TaskList from '../components/TaskList.vue'
import { API, authHeaders, getMe } from '../api.js'

const router = useRouter()
const me = getMe()
const members = ref([])
const familyTasks = ref([])
const liens = ref([])

const nName = ref('')
const nEmail = ref('')
const nPass = ref('')
const nLien = ref('')
const nAdmin = ref(false)
const msg = ref('')
const newLien = ref('')

async function refresh() {
  members.value = await (await fetch(`${API}/api/members`, { headers: authHeaders() })).json()
  familyTasks.value = await (await fetch(`${API}/api/tasks/famille`, { headers: authHeaders() })).json()
  liens.value = await (await fetch(`${API}/api/liens`, { headers: authHeaders() })).json()
  if (!nLien.value && liens.value.length) nLien.value = liens.value[0]
}
async function createAccount() {
  msg.value = ''
  if (!nName.value.trim() || !nEmail.value.trim() || !nPass.value) { msg.value = 'Prénom, email et mot de passe requis.'; return }
  const q = new URLSearchParams({ name: nName.value.trim(), email: nEmail.value.trim(), password: nPass.value, lien: nLien.value, is_admin: nAdmin.value })
  const r = await fetch(`${API}/api/members?${q}`, { method: 'POST', headers: authHeaders() })
  if (!r.ok) { const d = await r.json().catch(() => ({})); msg.value = d.detail || 'Erreur.'; return }
  nName.value = ''; nEmail.value = ''; nPass.value = ''; nAdmin.value = false
  await refresh()
}
async function addLien() {
  if (!newLien.value.trim()) return
  const q = new URLSearchParams({ label: newLien.value.trim() })
  liens.value = await (await fetch(`${API}/api/liens?${q}`, { method: 'POST', headers: authHeaders() })).json()
  nLien.value = newLien.value.trim(); newLien.value = ''
}
async function removeMember(m) {
  if (!confirm(`Supprimer le compte de ${m.name} et ses tâches ?`)) return
  const r = await fetch(`${API}/api/members/${m.id}`, { method: 'DELETE', headers: authHeaders() })
  if (!r.ok) { const d = await r.json().catch(() => ({})); alert(d.detail || 'Suppression impossible.') }
  await refresh()
}
async function toggle(t) { await fetch(`${API}/api/tasks/${t.id}`, { method: 'PATCH', headers: authHeaders() }); await refresh() }
async function remove(t) { await fetch(`${API}/api/tasks/${t.id}`, { method: 'DELETE', headers: authHeaders() }); await refresh() }
function initials(n) { return n.slice(0, 2).toUpperCase() }
onMounted(refresh)
</script>

<template>
  <div class="view">
    <button class="primary block" @click="router.push('/taches')">Aller à mes tâches →</button>

    <div class="card">
      <h3>Créer un compte</h3>
      <div class="row"><input v-model="nName" placeholder="Prénom (ex : Léa)" /></div>
      <div class="row"><input v-model="nEmail" type="email" placeholder="Email (ex : lea@durand.fr)" /></div>
      <div class="row"><input v-model="nPass" type="password" placeholder="Mot de passe" /></div>
      <div class="row">
        <select v-model="nLien"><option v-for="l in liens" :key="l" :value="l">{{ l }}</option></select>
        <label class="check"><input type="checkbox" v-model="nAdmin" /> admin</label>
      </div>
      <button class="primary block" @click="createAccount">Créer le compte</button>
      <p class="err" v-if="msg">{{ msg }}</p>
      <div class="row addlien">
        <input v-model="newLien" placeholder="Ajouter un lien (ex : belle-mère)" @keyup.enter="addLien" />
        <button class="ghost" @click="addLien">+ lien</button>
      </div>
    </div>

    <div class="card">
      <h3>Membres de la famille</h3>
      <div class="mlist">
        <div v-for="m in members" :key="m.id" class="mrow">
          <span class="avatar sm">{{ initials(m.name) }}</span>
          <span class="mname">{{ m.name }}</span>
          <span class="who">{{ m.lien }}</span>
          <span class="badge" v-if="m.is_admin">admin</span>
          <button v-if="m.id !== me.id" class="trash" @click="removeMember(m)" title="Supprimer">🗑</button>
        </div>
      </div>
    </div>

    <div class="card">
      <h3>Toutes les tâches de la famille</h3>
      <TaskList :tasks="familyTasks" :members="members" @toggle="toggle" @remove="remove" />
    </div>
  </div>
</template>
