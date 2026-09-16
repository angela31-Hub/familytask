<script setup>
import { onBeforeUnmount, ref } from 'vue'
import { apiFetch } from '../api'

const emit = defineEmits(['tasks-updated'])

const messages = ref([
  { id: 0, role: 'assistant', content: 'Bonjour. Quelle tâche dois-je ajouter ?' },
])
const messageDraft = ref('')
const isSending = ref(false)
const isListening = ref(false)
const errorMessage = ref('')
let recognition = null

function addMessage(role, content) {
  messages.value.push({ id: Date.now() + messages.value.length, role, content })
}

async function sendMessage() {
  const message = messageDraft.value.trim()
  if (!message || isSending.value) return

  addMessage('user', message)
  messageDraft.value = ''
  errorMessage.value = ''
  isSending.value = true

  try {
    const response = await apiFetch(`/api/assistant?message=${encodeURIComponent(message)}`, {
      method: 'POST',
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || 'Le service de l’assistant est indisponible.')

    addMessage('assistant', data.reply || 'Je n’ai pas de réponse à afficher.')
    if (data.tool_call?.name === 'ajouter_tache') emit('tasks-updated')
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    isSending.value = false
  }
}

function toggleVoiceInput() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!SpeechRecognition) {
    errorMessage.value = 'La dictée vocale n’est pas disponible dans ce navigateur.'
    return
  }

  if (isListening.value) {
    recognition?.stop()
    return
  }

  recognition = new SpeechRecognition()
  recognition.lang = 'fr-FR'
  recognition.interimResults = false
  recognition.continuous = false
  recognition.onstart = () => { isListening.value = true }
  recognition.onresult = event => {
    messageDraft.value = event.results[0][0].transcript
  }
  recognition.onerror = () => {
    errorMessage.value = 'La dictée vocale n’a pas pu démarrer.'
  }
  recognition.onend = () => { isListening.value = false }
  recognition.start()
}

onBeforeUnmount(() => {
  recognition?.stop()
})
</script>

<template>
  <section class="assistant-panel" aria-label="Assistant familial">
    <div class="assistant-messages" aria-live="polite">
      <p
        v-for="message in messages"
        :key="message.id"
        class="assistant-message"
        :class="`assistant-message-${message.role}`"
      >
        {{ message.content }}
      </p>
      <p v-if="isSending" class="assistant-message assistant-message-assistant assistant-pending">
        Je réfléchis...
      </p>
    </div>

    <p v-if="errorMessage" class="error-message" role="alert">{{ errorMessage }}</p>

    <form class="assistant-form" @submit.prevent="sendMessage">
      <label class="sr-only" for="assistant-message">Votre message</label>
      <input
        id="assistant-message"
        v-model="messageDraft"
        type="text"
        placeholder="Ex. Ajoute la vaisselle pour Léa"
        autocomplete="off"
        :disabled="isSending"
      >
      <button
        class="voice-button"
        type="button"
        :aria-label="isListening ? 'Arrêter la dictée' : 'Dicter un message'"
        :aria-pressed="isListening"
        :disabled="isSending"
        @click="toggleVoiceInput"
      >
        <span aria-hidden="true">🎙</span>
      </button>
      <button class="send-button" type="submit" :disabled="isSending || !messageDraft.trim()">
        Envoyer
      </button>
    </form>
  </section>
</template>
