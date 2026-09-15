// Adresse du back. En local : vide (le proxy Vite gère /api).
export const API = ''

// --- Session : jeton + membre connecté (gardés en localStorage) ---
let token = localStorage.getItem('token') || ''

export function setToken(t) {
  token = t || ''
  if (t) localStorage.setItem('token', t)
  else localStorage.removeItem('token')
}
export function authHeaders() {
  return token ? { Authorization: 'Bearer ' + token } : {}
}
export function isLogged() { return !!token }

export function setMe(m) {
  if (m) localStorage.setItem('me', JSON.stringify(m))
  else localStorage.removeItem('me')
}
export function getMe() {
  try { return JSON.parse(localStorage.getItem('me') || 'null') } catch (e) { return null }
}
export async function logout() {
  // On prévient d'abord le serveur (il invalide le jeton), puis on nettoie
  // le navigateur. Le `catch` garantit qu'on se déconnecte quand même si
  // le réseau est coupé : mieux vaut sortir que rester bloqué·e.
  try {
    await fetch(API + '/api/logout', { method: 'POST', headers: authHeaders() })
  } catch (e) {
    console.warn('Serveur injoignable, déconnexion locale seulement.')
  }
  setToken(''); setMe(null)
}
