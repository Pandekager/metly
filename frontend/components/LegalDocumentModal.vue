<template>
  <div
    v-if="document"
    class="fixed inset-0 z-[70] flex items-center justify-center bg-slate-950/60 px-4"
    @click.self="$emit('close')"
  >
    <div class="w-full max-w-2xl rounded-3xl bg-white p-8 shadow-2xl dark:bg-slate-800">
      <div class="flex items-start justify-between gap-4">
        <div>
          <h2 class="text-2xl font-bold text-slate-900 dark:text-slate-100">
            {{ document.title }}
          </h2>
          <p class="mt-2 text-sm text-slate-500 dark:text-slate-400">
            {{ document.subtitle }}
          </p>
        </div>
        <button
          type="button"
          class="text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
          @click="$emit('close')"
        >
          Luk
        </button>
      </div>
      <div class="mt-6 max-h-[60vh] space-y-6 overflow-y-auto pr-2 text-sm leading-7 text-slate-700 dark:text-slate-300">
        <section
          v-for="section in document.sections"
          :key="section.title"
        >
          <h3 class="text-base font-semibold text-slate-900 dark:text-slate-100">
            {{ section.title }}
          </h3>
          <p class="mt-2 whitespace-pre-line">
            {{ section.body }}
          </p>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { LegalDocumentContent } from '~/composables/useLegalDocuments'

defineProps<{
  document: LegalDocumentContent | null
}>()

defineEmits<{
  close: []
}>()
</script>
