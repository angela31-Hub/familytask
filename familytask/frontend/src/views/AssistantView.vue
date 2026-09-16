<script setup>
import ChatAssistant from '../components/ChatAssistant.vue'

function notifyTasksUpdated() {
  window.dispatchEvent(new Event('tasks-updated'))
}
</script>

<template>
  <main>
    <section class="card assistant-card">
      <div class="page-heading">
        <span class="eyebrow">FAMILYTASK</span>
        <h2>Assistant familial</h2>
        <p>Ajoutez une tâche naturellement, par écrit ou à la voix.</p>
      </div>
      <ChatAssistant @tasks-updated="notifyTasksUpdated" />
    </section>
  </main>
</template>
