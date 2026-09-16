// Centralise les appels API et ajoute automatiquement le token de session.
// Une chaîne vide conserve les URLs relatives lorsque l'application tourne en local.
const API_URL = import.meta.env.VITE_API_URL || ''

export function apiFetch(url, options = {}) {
  const headers = new Headers(options.headers || {})
  const token = localStorage.getItem('token')

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  return fetch(`${API_URL}${url}`, { ...options, headers })
}
