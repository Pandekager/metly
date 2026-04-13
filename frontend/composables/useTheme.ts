type Theme = 'light' | 'dark' | 'system'

export const useTheme = () => {
  const preference = ref<Theme>('system')
  const systemDark = ref(false)
  
  // Computed value for actual theme (resolved)
  const theme = computed<Exclude<Theme, 'system'>>(() => {
    if (preference.value === 'system') {
      return systemDark.value ? 'dark' : 'light'
    }
    return preference.value
  })
  
  const isDark = computed(() => theme.value === 'dark')
  const isLight = computed(() => theme.value === 'light')
  const isSystem = computed(() => preference.value === 'system')
  
  // Apply theme to document
  const applyTheme = () => {
    if (import.meta.client) {
      const html = document.documentElement
      if (isDark.value) {
        html.classList.add('dark')
      } else {
        html.classList.remove('dark')
      }
    }
  }
  
  // Set theme preference
  const setTheme = (newTheme: Theme) => {
    preference.value = newTheme
    if (import.meta.client) {
      localStorage.setItem('theme-preference', newTheme)
    }
    applyTheme()
  }
  
  // Cycle through themes
  const toggleTheme = () => {
    const themes: Theme[] = ['system', 'light', 'dark']
    const currentIndex = themes.indexOf(preference.value)
    const nextIndex = (currentIndex + 1) % themes.length
    setTheme(themes[nextIndex])
  }
  
  // Initialize on client side
  onMounted(() => {
    if (import.meta.client) {
      // Check system preference
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      systemDark.value = mediaQuery.matches
      
      // Listen for system changes
      mediaQuery.addEventListener('change', (e) => {
        systemDark.value = e.matches
        applyTheme()
      })
      
      // Load saved preference
      const saved = localStorage.getItem('theme-preference') as Theme | null
      if (saved && ['light', 'dark', 'system'].includes(saved)) {
        preference.value = saved
      }
      
      applyTheme()
    }
  })
  
  return {
    theme,
    preference,
    toggleTheme,
    setTheme,
    isDark,
    isLight,
    isSystem
  }
}