<template>
  <div class="forecast-business-advice bg-white dark:bg-slate-800 rounded-lg p-6">
    <div class="ai-header border-b-2 border-slate-100 dark:border-slate-700 pb-4 mb-6">
      <div class="ai-badge">
        <svg
          class="ai-icon"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M12 2L2 7L12 12L22 7L12 2Z"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <path
            d="M2 17L12 22L22 17"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <path
            d="M2 12L12 17L22 12"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        <span class="ai-text">Daglige anbefalinger fra din personlige AI-Rådgiver</span>
      </div>
    </div>

    <div v-if="advice && advice.length > 0" class="advice-content text-slate-800 dark:text-slate-200">
      <div v-html="renderedMarkdown" class="markdown-body prose dark:prose-invert max-w-none"></div>
    </div>
    <div v-else class="no-advice text-center text-slate-500 dark:text-slate-400 py-8">
      <p>Ingen anbefalinger tilgængelige</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { marked } from 'marked'
import { computed } from 'vue'
import type { ForecastBusinessAdvice } from '~/types/forecast-business-advice'

const props = defineProps<{
  advice: ForecastBusinessAdvice[]
}>()

const renderedMarkdown = computed(() => {
  if (!props.advice || props.advice.length === 0) return ''
  const text = props.advice[0].response_text
  return marked(text)
})
</script>

<style scoped>
.ai-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  animation: pulse-subtle 3s ease-in-out infinite;
}

.ai-icon {
  width: 1.25rem;
  height: 1.25rem;
  animation: float 3s ease-in-out infinite;
}

.ai-text {
  letter-spacing: 0.025em;
}

@keyframes pulse-subtle {
  0%,
  100% {
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  }
  50% {
    box-shadow: 0 4px 16px rgba(102, 126, 234, 0.5);
  }
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-2px);
  }
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  font-weight: 600;
}

.markdown-body :deep(h1) {
  font-size: 1.75rem;
}

.markdown-body :deep(h2) {
  font-size: 1.5rem;
}

.markdown-body :deep(h3) {
  font-size: 1.25rem;
}

.markdown-body :deep(p) {
  margin-bottom: 1rem;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin-left: 1.5rem;
  margin-bottom: 1rem;
}

.markdown-body :deep(li) {
  margin-bottom: 0.5rem;
}

.markdown-body :deep(strong) {
  font-weight: 600;
}

.markdown-body :deep(code) {
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
}

.markdown-body :deep(pre) {
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
  margin-bottom: 1rem;
}
</style>
