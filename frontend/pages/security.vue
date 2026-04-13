<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-900">
    <Navbar />
    <main class="pt-24 pb-16 px-6">
      <div class="max-w-4xl mx-auto bg-white dark:bg-slate-800 rounded-3xl shadow-xl border border-slate-100 dark:border-slate-700 p-8 md:p-12">
        <h1 class="text-3xl font-bold text-slate-900 dark:text-slate-100">Sikkerhed og databeskyttelse</h1>
        <div class="mt-8 space-y-8 text-slate-700 dark:text-slate-300 leading-7">
          <section>
            <h2 class="text-xl font-semibold text-slate-900 dark:text-slate-100">Kryptering i transit</h2>
            <p>Metly anvender HTTPS/TLS til overførsel mellem browser, frontend, backend og eksterne integrationskilder som Shopify.</p>
          </section>
          <section>
            <h2 class="text-xl font-semibold text-slate-900 dark:text-slate-100">Adgangsbegrænsning</h2>
            <p>Data er logisk adskilt per merchant via bruger-id, og applikationen returnerer kun data for den autentificerede merchant.</p>
          </section>
          <section>
            <h2 class="text-xl font-semibold text-slate-900 dark:text-slate-100">Retention</h2>
            <p>Metly kører automatiske retentionregler som en del af backend-jobbet. Direkte kundeidentifikatorer pseudonymiseres efter en konfigurerbar periode, så de ikke gemmes længere end nødvendigt.</p>
          </section>
          <section>
            <h2 class="text-xl font-semibold text-slate-900 dark:text-slate-100">Automatiserede anbefalinger</h2>
            <p>Metly genererer forecast og forretningsanbefalinger som beslutningsstøtte til merchanten. Metly træffer ikke automatiske beslutninger med juridiske eller tilsvarende væsentlige virkninger for kundernes rettigheder.</p>
          </section>
        </div>
      </div>
    </main>
    <Footer />
  </div>
</template>

<script setup lang="ts">
useHead({
  title: 'Sikkerhed - Metly',
})
</script>
