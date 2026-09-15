import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Sommes-nous dans un codespace ? La variable CODESPACES est fournie par GitHub
// et transmise au conteneur par docker-compose.yml.
const enCodespace = !!process.env.CODESPACES

export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    port: 5173,

    // En codespace, le site n'est plus servi sur "localhost" mais sur une
    // adresse du type https://mon-codespace-5173.app.github.dev.
    // Vite bloque par défaut les domaines qu'il ne connaît pas : on l'autorise.
    allowedHosts: ['.app.github.dev', '.github.dev', 'localhost'],

    // Le rechargement automatique de la page (HMR) passe par le proxy HTTPS de
    // GitHub, qui écoute sur le port 443 — pas sur 5173. En local, on garde le
    // comportement par défaut.
    hmr: enCodespace ? { clientPort: 443 } : true,

    // Le front appelle /api/... et Vite transmet la requête au back-end.
    proxy: { '/api': { target: 'http://backend:8000', changeOrigin: true } }
  }
})
