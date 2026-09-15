<script setup>
import { ref } from 'vue'
import { API, authHeaders } from '../api.js'

const emit = defineEmits(['changed'])

const chat = ref([])
const chatInput = ref('')
const loading = ref(false)

async function ask() {
  if (!chatInput.value.trim() || loading.value) return
  const message = chatInput.value
  chat.value.push({ role: 'me', text: message })
  chatInput.value = ''
  loading.value = true
  try {
    const q = new URLSearchParams({ message })
    const res = await (await fetch(`${API}/api/assistant?${q}`, { method: 'POST', headers: authHeaders() })).json()
    chat.value.push({ role: 'bot', text: res.reply })
    emit('changed')
  } catch (e) {
    chat.value.push({ role: 'bot', text: "Désolé, l'assistant n'a pas pu répondre." })
  } finally {
    loading.value = false
  }
}

// --- Dictée vocale (option "à la voix") ---
const SR = window.SpeechRecognition || window.webkitSpeechRecognition
const voiceSupported = !!SR
const listening = ref(false)
let recognition = null

function toggleVoice() {
  if (!voiceSupported) return
  if (listening.value) { recognition && recognition.stop(); return }
  recognition = new SR()
  recognition.lang = 'fr-FR'
  recognition.interimResults = true
  recognition.continuous = false
  listening.value = true
  recognition.onresult = (e) => {
    chatInput.value = Array.from(e.results).map(r => r[0].transcript).join('')
  }
  recognition.onerror = () => { listening.value = false }
  recognition.onend = () => {
    listening.value = false
    if (chatInput.value.trim()) ask()
  }
  recognition.start()
}
</script>

<template>
  <div>
    <div class="chat" v-if="chat.length || loading">
      <div v-for="(m, i) in chat" :key="i" class="msg" :class="m.role">{{ m.text }}</div>
      <div v-if="loading" class="msg bot">…</div>
    </div>
    <div class="row">
      <input v-model="chatInput" placeholder="Écris ou dicte une tâche…" @keyup.enter="ask" />
      <button v-if="voiceSupported" class="mic" :class="{ live: listening }"
              :title="listening ? 'Écoute…' : 'Dicter à la voix'" @click="toggleVoice">
        {{ listening ? '🔴' : '🎤' }}
      </button>
      <button class="primary" @click="ask">Envoyer</button>
    </div>
    <p v-if="!voiceSupported" class="hint">🎤 La dictée vocale marche sur Chrome et Edge.</p>
  </div>
</template>
