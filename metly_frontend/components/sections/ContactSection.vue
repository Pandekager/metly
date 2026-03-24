<template>
  <section id="contact" class="py-24 bg-white dark:bg-slate-900">
    <div class="max-w-4xl mx-auto px-6 text-center">
      <h2 class="text-4xl md:text-5xl font-bold text-slate-900 dark:text-slate-100 mb-6">
        Kan vi hjælpe jer?
      </h2>
      <p class="text-xl text-slate-600 dark:text-slate-400 mb-12 max-w-2xl mx-auto">
        Vi hjælper webshops med at træffe bedre beslutninger baseret på data - helt automatisk. Kontakt os for at høre mere.
      </p>

      <div class="bg-gradient-to-br from-metly-50 to-blue-50 dark:from-slate-800 dark:to-slate-700 rounded-3xl p-12 shadow-xl border border-metly-100 dark:border-slate-600">
        <div class="max-w-md mx-auto space-y-6">
          <a
            href="mailto:hej@metly.dk?subject=Forespørgsel%20om%20tilbud"
            class="btn-primary block text-center"
          >
            Send os en e-mail
          </a>
          <p class="text-slate-600 dark:text-slate-300">
            Eller skriv til os på
            <a href="mailto:hej@metly.dk" class="text-metly-600 hover:text-metly-700 font-medium">
              hej@metly.dk
            </a>
          </p>
        </div>

        <div class="mt-12 pt-8 border-t border-metly-200 dark:border-slate-600 grid md:grid-cols-3 gap-8 text-left">
          <div>
            <div class="flex items-center space-x-3 mb-2">
              <MapPinIcon class="w-5 h-5 text-metly-600" />
              <h4 class="font-semibold text-slate-900 dark:text-slate-100">Lokation</h4>
            </div>
            <p class="text-slate-600 dark:text-slate-400">Aarhus, Danmark</p>
          </div>
          <div>
            <div class="flex items-center space-x-3 mb-2">
              <ShieldCheckIcon class="w-5 h-5 text-metly-600" />
              <h4 class="font-semibold text-slate-900 dark:text-slate-100">Sikkerhed</h4>
            </div>
            <p class="text-slate-600 dark:text-slate-400">GDPR kompliant • EU hosting</p>
          </div>
          <div>
            <div class="flex items-center space-x-3 mb-2">
              <ChatBubbleLeftRightIcon class="w-5 h-5 text-metly-600" />
              <h4 class="font-semibold text-slate-900 dark:text-slate-100">Svar tid</h4>
            </div>
            <p class="text-slate-600 dark:text-slate-400">Typisk inden for 24 timer</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import {
  MapPinIcon,
  ShieldCheckIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/vue/24/outline'
</script>
