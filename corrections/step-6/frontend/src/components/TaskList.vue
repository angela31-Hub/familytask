<script setup>
const props = defineProps({
  tasks: Array,
  members: { type: Array, default: () => [] }
})
const emit = defineEmits(['toggle', 'remove'])

function memberName(id) {
  const m = props.members.find(m => m.id === id)
  return m ? m.name : ''
}
</script>

<template>
  <ul>
    <li v-for="t in tasks" :key="t.id" :class="{ done: t.done }">
      <input type="checkbox" :checked="t.done" @change="emit('toggle', t)" />
      <span>{{ t.title }}</span>
      <span class="who" v-if="memberName(t.member_id)">👤 {{ memberName(t.member_id) }}</span>
      <button class="trash" @click="emit('remove', t)">🗑</button>
    </li>
    <li v-if="tasks.length === 0" class="hint">Aucune tâche pour l'instant.</li>
  </ul>
</template>
