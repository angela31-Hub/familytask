<script setup>
// Ce composant ne connaît que les tâches.
// Il ne les modifie JAMAIS lui-même : il prévient le parent (emit), et le parent décide.
defineProps({
  tasks: Array,
})
const emit = defineEmits(['toggle', 'remove'])
</script>

<template>
  <ul>
    <li v-for="t in tasks" :key="t.id" :class="{ done: t.done }">
      <input type="checkbox" :checked="t.done" @change="emit('toggle', t)" />
      <span>{{ t.title }}</span>
      <button class="trash" @click="emit('remove', t)">🗑</button>
    </li>
    <li v-if="tasks.length === 0" class="hint">Aucune tâche pour l'instant. 🎉</li>
  </ul>
</template>
