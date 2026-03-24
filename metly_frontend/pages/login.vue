<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800">
    <Navbar />
    <main class="min-h-screen flex items-center justify-center px-6 pt-20">
      <div class="w-full max-w-md">
        <div class="bg-white dark:bg-slate-800 rounded-3xl shadow-2xl p-8 border border-slate-100 dark:border-slate-700 animate-slide-up">
          <div class="text-center mb-8">
            <div class="w-16 h-16 bg-gradient-to-br from-metly-500 to-metly-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <span class="text-white font-display text-3xl">M</span>
            </div>
            <h1 class="text-3xl font-bold text-slate-900 dark:text-slate-100">Velkommen tilbage</h1>
            <p class="text-slate-600 dark:text-slate-400 mt-2">Log ind for at fortsætte</p>
          </div>

          <form @submit.prevent="handleLogin" class="space-y-6">
            <div>
              <label for="email" class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                E-mail
              </label>
              <input
                id="email"
                v-model="email"
                type="email"
                placeholder="dig@eksempel.dk"
                required
                autocomplete="email"
                class="input-field"
              />
            </div>

            <div>
              <label for="password" class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Adgangskode
              </label>
              <input
                id="password"
                v-model="password"
                type="password"
                placeholder="••••••••"
                required
                autocomplete="current-password"
                class="input-field"
              />
            </div>

            <button
              type="submit"
              :disabled="loading"
              class="w-full btn-primary"
            >
              <span v-if="loading" class="flex items-center justify-center">
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Logger ind...
              </span>
              <span v-else>Log ind</span>
            </button>

            <p v-if="error" class="text-red-600 dark:text-red-400 text-center text-sm">
              {{ error }}
            </p>

            <p class="text-center text-sm text-slate-600 dark:text-slate-400">
              Har du ikke en konto endnu?
              <NuxtLink to="/signup" class="font-semibold text-metly-600 hover:text-metly-700 dark:text-metly-400">
                Opret konto
              </NuxtLink>
            </p>
          </form>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

definePageMeta({
  layout: false
})

useHead({
  title: 'Login - Metly',
  meta: [
    { name: 'description', content: 'Login til din Metly konto' }
  ]
})

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await $fetch('/api/auth/login', {
      method: 'POST',
      body: {
        email: email.value,
        password: password.value
      }
    })

    if (response.success) {
      authStore.setUser(response.user)
      await router.push('/home')
    }
  } catch (e: any) {
    error.value = e?.data?.message || e?.message || 'Forkert e-mail eller adgangskode'
  } finally {
    loading.value = false
  }
}
</script>
