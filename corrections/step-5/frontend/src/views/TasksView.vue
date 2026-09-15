<script setup>
import { ref, onMounted, computed } from 'vue'
import TaskList from '../components/TaskList.vue'
import { API, authHeaders, getMe } from '../api.js'

const me = getMe()
const tasks = ref([])
const members = ref([])
const newTitle = ref('')
const assignTo = ref(null)
const isAdmin = computed(() => me && me.is_admin)

async function refresh() {
  tasks.value = await (await fetch(`${API}/api/tasks`, { headers: authHeaders() })).json()
  members.value = await (await fetch(`${API}/api/members`, { headers: authHeaders() })).json()
}
async function addTask() {
  if (!newTitle.value.trim()) return
  const q = new URLSearchParams({ title: newTitle.value })
  if (isAdmin.value && assignTo.value) q.append('member_id', assignTo.value)
  await fetch(`${API}/api/tasks?${q}`, { method: 'POST', headers: authHeaders() })
  newTitle.value = ''
  await refresh()
}
async function toggle(t) { await fetch(`${API}/api/tasks/${t.id}`, { method: 'PATCH', headers: authHeaders() }); await refresh() }
async function remove(t) { await fetch(`${API}/api/tasks/${t.id}`, { method: 'DELETE', headers: authHeaders() }); await refresh() }
onMounted(refresh)
</script>

<template>
  <div class="view">
    <div class="hello">Bonjour <strong>{{ me?.name }}</strong> 👋</div>

    <div class="card add">
      <div class="row">
        <input v-model="newTitle" placeholder="Nouvelle tâche…" @keyup.enter="addTask" />
        <button class="primary square" @click="addTask">＋</button>
      </div>
      <select v-if="isAdmin" v-model="assignTo" class="assign">
        <option :value="null">Pour moi</option>
        <option v-for="m in members.filter(x => x.id !== me.id)" :key="m.id" :value="m.id">Pour {{ m.name }}</option>
      </select>
    </div>

    <div class="card">
      <h3>Mes tâches</h3>
      <TaskList :tasks="tasks" :members="members" @toggle="toggle" @remove="remove" />
    </div>
  </div>
</template>
