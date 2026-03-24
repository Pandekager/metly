<template>
  <footer class="bg-white dark:bg-slate-900 border-t border-slate-200/50 dark:border-slate-700/50 py-16">
    <div class="max-w-7xl mx-auto px-6">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-12 mb-12">
        <div class="md:col-span-1">
          <div class="mb-4">
            <img src="/images/logo.png" alt="Metly" class="h-8 object-contain" />
          </div>
          <p class="text-slate-600 dark:text-slate-400 leading-relaxed">
            Fra data til handling. Metly hjælper webshops med at træffe bedre beslutninger baseret på data - helt automatisk.
          </p>
        </div>

        <div>
          <h4 class="text-slate-900 dark:text-slate-100 font-semibold mb-4">Links</h4>
          <ul class="space-y-2">
            <li><NuxtLink to="/" class="text-slate-600 dark:text-slate-400 hover:text-metly-600 dark:hover:text-metly-400 transition-colors">Hjem</NuxtLink></li>
            <li><NuxtLink to="/#features" class="text-slate-600 dark:text-slate-400 hover:text-metly-600 dark:hover:text-metly-400 transition-colors">Features</NuxtLink></li>
            <li><NuxtLink to="/#about" class="text-slate-600 dark:text-slate-400 hover:text-metly-600 dark:hover:text-metly-400 transition-colors">Om os</NuxtLink></li>
            <li><NuxtLink to="/#contact" class="text-slate-600 dark:text-slate-400 hover:text-metly-600 dark:hover:text-metly-400 transition-colors">Kontakt</NuxtLink></li>
          </ul>
        </div>

        <div>
          <h4 class="text-slate-900 dark:text-slate-100 font-semibold mb-4">Kontakt</h4>
          <ul class="space-y-2">
            <li>
              <a href="mailto:hej@metly.dk" class="text-slate-600 dark:text-slate-400 hover:text-metly-600 dark:hover:text-metly-400 transition-colors">
                hej@metly.dk
              </a>
            </li>
            <li class="text-slate-600 dark:text-slate-400">Aarhus, Danmark</li>
          </ul>
        </div>
      </div>

      <div class="border-t border-slate-200 dark:border-slate-700 pt-8 text-center">
        <p class="text-slate-600 dark:text-slate-400">&copy; {{ currentYear }} Metly. Alle rettigheder forbeholdes.</p>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
const currentYear = computed(() => new Date().getFullYear())
</script>
