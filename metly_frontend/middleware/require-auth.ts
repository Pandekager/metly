export default defineNuxtRouteMiddleware(async (to) => {
  const authStore = useAuthStore()

  if (to.path === '/login' || to.path === '/signup') {
    return
  }

  if (!authStore.isLoggedIn) {
    try {
      const auth = await $fetch<{ authenticated: boolean; user: { id: string; email: string } | null }>('/api/auth/check')
      if (auth.authenticated && auth.user) {
        authStore.setUser(auth.user)
        return
      }
    } catch {
      authStore.logout()
    }

    return navigateTo('/login')
  }
})
