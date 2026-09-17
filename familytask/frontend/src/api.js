// Centralise les appels API et ajoute automatiquement le token de session.
// Une chaîne vide conserve les URLs relatives lorsque l'application tourne en local.
let API_URL = import.meta.env.VITE_API_URL || ''
if (API_URL && !API_URL.startsWith('http')) API_URL = `https://${API_URL}`
API_URL = API_URL.replace(/\/$/, '')

export function apiFetch(url, options = {}) {
  const headers = new Headers(options.headers || {})
  const token = localStorage.getItem('token')

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  return fetch(`${API_URL}${url}`, { ...options, headers })
}
