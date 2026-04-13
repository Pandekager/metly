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
          <div
            v-else-if="currentRoute === 'home'"
            ref="menuRoot"
            class="relative"
          >
            <button
              type="button"
              class="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:border-slate-300 hover:text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-slate-600 dark:hover:text-white"
              @click="toggleMenu"
            >
              Konto
              <svg
                class="h-4 w-4 transition-transform"
                :class="{ 'rotate-180': menuOpen }"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <path
                  fill-rule="evenodd"
                  d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
                  clip-rule="evenodd"
                />
              </svg>
            </button>

            <div
              v-if="menuOpen"
              class="absolute right-0 mt-3 w-56 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-800"
            >
              <button
                type="button"
                class="block w-full px-4 py-3 text-left text-sm text-slate-700 transition-colors hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-700/60"
                @click="handleLogout"
              >
                Log ud
              </button>
              <button
                type="button"
                :disabled="deletingAccount"
                class="block w-full px-4 py-3 text-left text-sm text-red-600 transition-colors hover:bg-red-50 disabled:opacity-60 dark:text-red-300 dark:hover:bg-red-950/40"
                @click="handleDeleteAccount"
              >
                {{ deletingAccount ? 'Sletter konto...' : 'Slet konto' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const deletingAccount = ref(false)
const menuOpen = ref(false)
const menuRoot = ref<HTMLElement | null>(null)

const currentRoute = computed(() => {
  if (route.path === '/login') return 'login'
  if (route.path === '/signup') return 'signup'
  if (route.path === '/home') return 'home'
  return 'index'
})

const isDemoUser = computed(() => {
  return authStore.user?.email === 'demo@metly.dk'
})

const handleDocumentClick = (event: MouseEvent) => {
  if (!menuRoot.value) return
  if (!menuRoot.value.contains(event.target as Node)) {
    menuOpen.value = false
  }
}

const toggleMenu = () => {
  menuOpen.value = !menuOpen.value
}

const handleLogout = async () => {
  menuOpen.value = false
  try {
    await $fetch('/api/auth/logout', { method: 'POST' })
  } catch (error) {
    console.error('Logout error:', error)
  }
  authStore.logout()
  await router.push('/')
}

const handleDeleteAccount = async () => {
  if (deletingAccount.value) return

  const confirmed = window.confirm(
    'Vil du slette din konto? Alle data for denne bruger bliver slettet permanent.'
  )

  if (!confirmed) return

  deletingAccount.value = true
  menuOpen.value = false

  try {
    await $fetch('/api/auth/account', { method: 'DELETE' })
    authStore.logout()
    await router.push('/signup?deleted=1')
  } catch (error: any) {
    console.error('Delete account error:', error)
    window.alert(error?.data?.message || error?.message || 'Kunne ikke slette kontoen.')
  } finally {
    deletingAccount.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleDocumentClick)
})
</script>
