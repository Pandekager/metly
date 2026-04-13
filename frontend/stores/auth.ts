import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    isLoggedIn: false,
    user: null as { id: string; email: string } | null,
  }),

  actions: {
    setLoggedIn(value: boolean) {
      this.isLoggedIn = value
    },

    setUser(user: { id: string; email: string }) {
      this.user = user
      this.isLoggedIn = true
    },

    logout() {
      this.isLoggedIn = false
      this.user = null
    },
  },
})
