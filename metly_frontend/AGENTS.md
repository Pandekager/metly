# Metly Frontend - Agent Guidelines

## Build, Lint, and Test Commands

### Core Commands
- `pnpm dev` - Start development server on http://localhost:3000
- `pnpm build` - Build for production
- `pnpm preview` - Preview production build
- `pnpm postinstall` - Run `nuxt prepare` after installation

### Testing
This project currently has no formal test suite. When adding tests:
- Use Vitest for unit tests
- Use Playwright for E2E tests
- Test files should be placed alongside source files with `.test.ts` or `.spec.ts` suffix

### Linting and Formatting
- No explicit linting configured yet
- Consider adding ESLint and Prettier for code consistency
- Use TypeScript compiler for type checking

## Code Style Guidelines

### File Structure
```
components/
  ├── charts/           # Chart components
  ├── sections/         # Page sections
  ├── layout/           # Layout components (Navbar, Footer)
  └── [ComponentName].vue

pages/
  ├── index.vue         # Landing page
  ├── login.vue         # Login page
  └── home.vue          # Dashboard

composables/                   # Vue composables
utils/                         # Utility functions
stores/                        # Pinia stores
```

### Vue Component Conventions
- Use `<script setup lang="ts">` syntax
- Export composables with camelCase names
- Use `computed()` for derived values
- Use `ref()` for reactive state
- Use `onMounted()` for lifecycle hooks

```vue
<template>
  <div class="component-class">
    <!-- Template content -->
  </div>
</template>

<script setup lang="ts">
// Import statements
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'pinia'

// Component logic
const someValue = ref<string>('')
const computedValue = computed(() => someValue.value.toUpperCase())

onMounted(() => {
  // Initialization logic
})
</script>
```

### TypeScript Conventions
- Use strict TypeScript configuration
- Prefer explicit return types for functions
- Use interfaces for object shapes
- Use enums for fixed sets of values
- Avoid `any` type - use `unknown` or proper typing

```typescript
// Good
interface User {
  id: string
  email: string
  name: string
}

// Good
type Theme = 'light' | 'dark' | 'system'

// Avoid
const data: any = getUserData()
```

### Import Organization
1. Vue imports first
2. Nuxt/nuxt-related imports second
3. Third-party libraries third
4. Local imports last

```typescript
// Vue imports
import { ref, computed, onMounted } from 'vue'

// Nuxt imports
import { useRoute, useRouter } from 'nuxt'

// Third-party
import Chart from 'chart.js'

// Local
import { useAuthStore } from '~/stores/auth'
import { formatDate } from '~/utils/date'
```

### Naming Conventions
- **Components**: PascalCase (e.g., `ForecastChart.vue`, `HeroSection.vue`)
- **Composables**: camelCase with `use` prefix (e.g., `useTheme.ts`, `useAuth.ts`)
- **Stores**: camelCase (e.g., `auth.ts`, `user.ts`)
- **Utilities**: camelCase (e.g., `date.ts`, `format.ts`)
- **Variables**: camelCase
- **Constants**: UPPER_SNAKE_CASE
- **CSS Classes**: kebab-case with Tailwind prefixes

### Error Handling
- Use try-catch blocks for async operations
- Log errors with context
- Provide user-friendly error messages
- Handle loading states appropriately

```typescript
const handleAction = async () => {
  try {
    await $fetch('/api/endpoint', { method: 'POST' })
  } catch (error) {
    console.error('Action failed:', error)
    // Show user-friendly message
  }
}
```

### Tailwind CSS Conventions
- Use Tailwind classes for all styling
- Follow the design system colors defined in `tailwind.config.js`
- Use semantic class names for components
- Maintain responsive design with mobile-first approach

```vue
<div class="bg-white dark:bg-slate-900 p-6 rounded-lg shadow-md">
  <h2 class="text-2xl font-semibold text-slate-900 dark:text-slate-100 mb-4">
    Component Title
  </h2>
</div>
```

### State Management (Pinia)
- Use stores for shared state
- Keep store logic minimal and focused
- Use actions for state mutations
- Use getters for computed state

```typescript
// stores/auth.ts
export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  
  const isLoggedIn = computed(() => user.value !== null)
  
  const login = async (credentials: LoginCredentials) => {
    // Login logic
  }
  
  return { user, isLoggedIn, login }
})
```

### API Integration
- Use `$fetch` for API calls
- Handle loading and error states
- Use environment variables for API endpoints
- Include proper error handling

```typescript
const fetchData = async () => {
  try {
    const response = await $fetch('/api/data')
    return response
  } catch (error) {
    console.error('API call failed:', error)
    throw error
  }
}
```

### Performance Guidelines
- Use `v-if` over `v-show` for expensive components
- Implement proper loading states
- Use `computed()` for expensive derived values
- Lazy load components when appropriate
- Optimize images with `@nuxt/image`

### Accessibility
- Use semantic HTML elements
- Provide proper ARIA labels
- Ensure keyboard navigation
- Use proper color contrast ratios
- Test with screen readers

### Git Conventions
- Use conventional commit messages
- Keep commits focused and atomic
- Include proper descriptions
- Use feature branches for new functionality

### Environment Variables
- Use `.env.example` as template
- Never commit `.env` files
- Use runtimeConfig for Nuxt variables
- Keep sensitive data out of client-side code

### Browser Support
- Target modern browsers (ES2020+)
- Use polyfills for older browser support
- Test in Chrome, Firefox, Safari, Edge
- Ensure responsive design works on mobile devices

## Development Workflow

1. Create feature branch from main
2. Implement changes following style guidelines
3. Test locally with `pnpm dev`
4. Build with `pnpm build` to verify
5. Commit changes with descriptive messages
6. Create pull request for review

## Notes

- This is a Nuxt 4 project using Vue 3
- Primary styling is Tailwind CSS
- State management uses Pinia
- Charts use Chart.js + vue-chartjs
- Authentication uses JWT tokens
- The app supports both light and dark themes