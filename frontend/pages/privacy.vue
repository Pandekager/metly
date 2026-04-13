<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-900">
    <Navbar />
    <main class="pt-24 pb-16 px-6">
      <div class="max-w-4xl mx-auto bg-white dark:bg-slate-800 rounded-3xl shadow-xl border border-slate-100 dark:border-slate-700 p-8 md:p-12">
        <h1 class="text-3xl font-bold text-slate-900 dark:text-slate-100">Privatlivspolitik</h1>
        <div class="mt-8 space-y-8 text-slate-700 dark:text-slate-300 leading-7">
          <section>
            <h2 class="text-xl font-semibold text-slate-900 dark:text-slate-100">Hvilke data Metly behandler</h2>
            <p>Metly behandler ordre-, produkt- og kundedata fra den webshop, som en merchant forbinder til platformen. Formålet er at levere salgsprognoser, kundeindsigter, produktanalyse og operationelle anbefalinger til den pågældende merchant.</p>
          </section>
          <section>
            <h2 class="text-xl font-semibold text-slate-900 dark:text-slate-100">Dataminimering</h2>
            <p>Metly begrænser behandlingen til de datafelter, der er nødvendige for analysefunktionerne. For Shopify-kilder gemmer Metly som udgangspunkt ikke kundens navn, e-mail eller gadeadresse, når disse ikke er nødvendige for at levere produktet.</p>
          </section>
          <section>
            <h2 class="text-xl font-semibold text-slate-900 dark:text-slate-100">Formål og begrænsning</h2>
            <p>Data bruges kun til at levere Metlys analyse- og forecastfunktioner til merchanten. Data sælges ikke videre og bruges ikke til annoncering, profilering på tværs af merchants eller andre formål uden for produktleverancen.</p>
          </section>
          <section>
            <h2 class="text-xl font-semibold text-slate-900 dark:text-slate-100">Opbevaring og sletning</h2>
            <p>Direkte kundeidentifikatorer som navn, adresse og e-mail pseudonymiseres automatisk efter en fast retentionperiode, medmindre kortere opbevaring kræves. Merchants kan kontakte Metly for sletning af konto- og kundedata.</p>
          </section>
          <section>
            <h2 class="text-xl font-semibold text-slate-900 dark:text-slate-100">Sikkerhed</h2>
            <p>Metly beskytter data under overførsel via TLS og begrænser adgang til data til de systemer og medarbejdere, der er nødvendige for drift og support.</p>
          </section>
        </div>
      </div>
    </main>
    <Footer />
  </div>
</template>

<script setup lang="ts">
useHead({
  title: 'Privatlivspolitik - Metly',
})
</script>
