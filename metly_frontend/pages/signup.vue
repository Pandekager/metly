<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800">
    <Navbar />
    <main class="min-h-screen flex items-center justify-center px-6 py-24">
      <div class="w-full max-w-2xl">
        <div class="bg-white dark:bg-slate-800 rounded-3xl shadow-2xl p-8 border border-slate-100 dark:border-slate-700 animate-slide-up">
          <div class="mb-8">
            <div class="w-16 h-16 bg-gradient-to-br from-metly-500 to-metly-700 rounded-2xl flex items-center justify-center mb-4">
              <span class="text-white font-display text-3xl">M</span>
            </div>
            <h1 class="text-3xl font-bold text-slate-900 dark:text-slate-100">Opret din Metly-konto</h1>
            <p class="mt-2 text-slate-600 dark:text-slate-400">
              Vælg din webshop-platform nu. Integration kan forbindes bagefter fra dashboardet.
            </p>
          </div>

          <form class="space-y-6" @submit.prevent="handleSignup">
            <div class="grid gap-6 sm:grid-cols-2">
              <div class="sm:col-span-2">
                <label for="email" class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  E-mail
                </label>
                <input
                  id="email"
                  v-model="email"
                  type="email"
                  required
                  autocomplete="email"
                  placeholder="dig@eksempel.dk"
                  class="input-field"
                />
              </div>

              <div class="sm:col-span-2">
                <label class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Hvilken webshop har du?
                </label>
                <div class="grid gap-3 sm:grid-cols-3">
                  <button
                    v-for="option in platformOptions"
                    :key="option.value"
                    type="button"
                    :class="[
                      'rounded-2xl border p-4 text-left transition-all',
                      platform === option.value
                        ? 'border-metly-600 bg-metly-50 text-slate-900 shadow-md dark:border-metly-400 dark:bg-slate-700'
                        : 'border-slate-200 bg-white text-slate-700 hover:border-slate-300 dark:border-slate-700 dark:bg-slate-900/40 dark:text-slate-300',
                    ]"
                    @click="platform = option.value"
                  >
                    <p class="font-semibold">{{ option.label }}</p>
                    <p class="mt-1 text-sm opacity-80">{{ option.description }}</p>
                  </button>
                </div>
              </div>

              <div v-if="platform === 'shopify'" class="sm:col-span-2">
                <label for="shopify-shop" class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Shopify butik
                </label>
                <input
                  id="shopify-shop"
                  v-model="shopifyShop"
                  type="text"
                  required
                  placeholder="din-butik.myshopify.com eller Shopify admin-link"
                  class="input-field"
                />
                <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
                  Når du opretter brugeren, sender vi dig direkte videre til Shopify for at godkende forbindelsen.
                </p>
              </div>

              <div class="sm:col-span-2">
                <label for="password" class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Adgangskode
                </label>
                <input
                  id="password"
                  v-model="password"
                  type="password"
                  required
                  minlength="8"
                  autocomplete="new-password"
                  placeholder="Mindst 8 tegn"
                  class="input-field"
                />
              </div>
            </div>

            <button
              type="submit"
              :disabled="loading || !platform || (platform === 'shopify' && !shopifyShop.trim())"
              class="w-full btn-primary"
            >
              <span v-if="loading" class="flex items-center justify-center">
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {{ platform === 'shopify' ? 'Opretter konto og forbinder Shopify...' : 'Opretter konto...' }}
              </span>
              <span v-else>{{ platform === 'shopify' ? 'Opret konto og forbind Shopify' : 'Opret konto' }}</span>
            </button>

            <p v-if="error" class="text-sm text-center text-red-600 dark:text-red-400">
              {{ error }}
            </p>

            <p class="text-center text-sm text-slate-600 dark:text-slate-400">
              Har du allerede en konto?
              <NuxtLink to="/login" class="font-semibold text-metly-600 hover:text-metly-700 dark:text-metly-400">
                Log ind
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
  title: 'Opret konto - Metly',
  meta: [
    { name: 'description', content: 'Opret en Metly konto og vælg din webshop-platform' }
  ]
})

const router = useRouter()
const authStore = useAuthStore()

const platformOptions = [
  {
    value: 'shopify',
    label: 'Shopify',
    description: 'For Shopify-butikker med OAuth-forbindelse.'
  },
  {
    value: 'dandomain',
    label: 'DanDomain',
    description: 'Moderne DanDomain webshop.'
  },
  {
    value: 'dandomain classic',
    label: 'DanDomain Classic',
    description: 'Klassisk DanDomain installation.'
  }
] as const

const email = ref('')
const password = ref('')
const platform = ref<(typeof platformOptions)[number]['value'] | ''>('')
const shopifyShop = ref('')
const loading = ref(false)
const error = ref('')

const handleSignup = async () => {
  loading.value = true
  error.value = ''

  if (platform.value === 'shopify' && !shopifyShop.value.trim()) {
    error.value = 'Indtast din Shopify butik'
    loading.value = false
    return
  }

  try {
    const response = await $fetch('/api/auth/register', {
      method: 'POST',
      body: {
        email: email.value,
        password: password.value,
        platform: platform.value
      }
    })

    if (response.success) {
      authStore.setUser(response.user)
      if (platform.value === 'shopify') {
        window.location.href = `/api/integrations/shopify/install?shop=${encodeURIComponent(shopifyShop.value.trim())}`
        return
      }

      await router.push('/home')
    }
  } catch (e: any) {
    error.value = e?.data?.message || e?.message || 'Kunne ikke oprette konto'
  } finally {
    loading.value = false
  }
}
</script>
