<template>
  <nav class="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-slate-900/80 backdrop-blur-lg border-b border-slate-200/50 dark:border-slate-700/50">
    <div class="max-w-7xl mx-auto px-6 py-4">
      <div class="flex items-center justify-between">
        <NuxtLink to="/" class="flex items-center">
          <img src="/images/logo.png" alt="Metly" class="h-8 object-contain" />
        </NuxtLink>

        <div v-if="currentRoute === 'index'" class="hidden md:flex items-center space-x-8">
          <a href="#hero" class="text-slate-600 dark:text-slate-300 hover:text-metly-600 dark:hover:text-metly-400 transition-colors">Hjem</a>
          <a href="#features" class="text-slate-600 dark:text-slate-300 hover:text-metly-600 dark:hover:text-metly-400 transition-colors">Features</a>
          <a href="#about" class="text-slate-600 dark:text-slate-300 hover:text-metly-600 dark:hover:text-metly-400 transition-colors">Om os</a>
          <a href="#contact" class="text-slate-600 dark:text-slate-300 hover:text-metly-600 dark:hover:text-metly-400 transition-colors">Kontakt</a>
        </div>

        <div class="flex items-center gap-2">
          <ThemeToggle />
          <NuxtLink
            v-if="currentRoute === 'index'"
            to="/login"
            class="btn-primary"
          >
            Log ind
          </NuxtLink>
          <NuxtLink
            v-else-if="currentRoute === 'login' || currentRoute === 'signup'"
            to="/"
            class="btn-secondary"
          >
            Tilbage til forsiden
          </NuxtLink>
          <NuxtLink
            v-else-if="currentRoute === 'home' && isDemoUser"
            to="/"
            class="btn-secondary"
          >
            Tilbage til forsiden
          </NuxtLink>
          <button
            v-else-if="currentRoute === 'home'"
            @click="handleLogout"
            class="text-slate-600 dark:text-slate-300 hover:text-red-600 dark:hover:text-red-400 transition-colors font-medium"
          >
            Log ud
          </button>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const currentRoute = computed(() => {
  if (route.path === '/login') return 'login'
  if (route.path === '/signup') return 'signup'
  if (route.path === '/home') return 'home'
  return 'index'
})

const isDemoUser = computed(() => {
  return authStore.user?.email === 'demo@metly.dk'
})

const handleLogout = async () => {
  try {
    await $fetch('/api/auth/logout', { method: 'POST' })
  } catch (error) {
    console.error('Logout error:', error)
  }
  authStore.logout()
  await router.push('/')
}
</script>
