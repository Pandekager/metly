const devTunnelUrl = process.env.NUXT_DEV_TUNNEL_URL || process.env.DEV_TUNNEL_URL
const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000'
const allowedHosts = ['.ngrok-free.dev']

let viteServerConfig: Record<string, any> = {
  allowedHosts
}

if (devTunnelUrl) {
  const tunnel = new URL(devTunnelUrl)
  const isSecure = tunnel.protocol === 'https:'
  const clientPort = tunnel.port
    ? Number(tunnel.port)
    : (isSecure ? 443 : 80)

  viteServerConfig = {
    ...viteServerConfig,
    origin: devTunnelUrl,
    hmr: {
      protocol: isSecure ? 'wss' : 'ws',
      host: tunnel.hostname,
      clientPort,
    }
  }
}

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  runtimeConfig: {
    jwtSecret: process.env.JWT_SECRET,
    public: {
      apiBase: process.env.API_BASE || `http://127.0.0.1:8000/api`
    }
  },

  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt',
    '@nuxtjs/google-fonts',
    '@nuxt/image',
  ],

  vite: {
    server: viteServerConfig,
    optimizeDeps: {
      exclude: []
    }
  },

  googleFonts: {
    families: {
      Montserrat: [300, 400, 500, 600, 700],
      'Leckerli One': true,
    },
    display: 'swap',
  },

  colorMode: {
    classSuffix: '',
    storageKey: 'nuxt-color-mode'
  },

  app: {
    head: {
      htmlAttrs: {
        lang: 'da'
      },
      meta: [
        { name: 'viewport', content: 'width=device-width, initial-scale=1.0' },
        { name: 'description', content: 'Metly hjælper webshops med at træffe bedre beslutninger baseret på data - helt automatisk.' },
        { name: 'og:title', content: 'Metly - Fra data til handling' },
        { name: 'og:description', content: 'Metly hjælper webshops med at træffe bedre beslutninger baseret på data.' },
        { name: 'og:type', content: 'website' },
        { name: 'og:image', content: '/og-image.png' },
        { name: 'og:url', content: 'https://metly.dk/' },
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
        { rel: 'apple-touch-icon', href: '/favicon.ico' },
      ],
    }
  }
})