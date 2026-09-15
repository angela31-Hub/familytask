<script setup>
defineProps({
  tasks: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['toggle', 'remove'])
</script>

<template>
  <p v-if="tasks.length === 0" class="empty-message">
    Tout est fait, bravo ! 🎉
  </p>
  <ul v-else>
    <li v-for="task in tasks" :key="task.id">
      <label>
        <input
          type="checkbox"
          :checked="task.done"
          @change="emit('toggle', task)"
        >
        <span :class="{ completed: task.done }">{{ task.title }}</span>
      </label>
      <button
        type="button"
        aria-label="Supprimer la tâche"
        title="Supprimer"
        @click="emit('remove', task)"
      >🗑</button>
    </li>
  </ul>
</template>