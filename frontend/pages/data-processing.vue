<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-900">
    <Navbar />
    <main class="pt-24 pb-16 px-6">
      <div class="max-w-4xl mx-auto bg-white dark:bg-slate-800 rounded-3xl shadow-xl border border-slate-100 dark:border-slate-700 p-8 md:p-12">
        <h1 class="text-3xl font-bold text-slate-900 dark:text-slate-100">Databehandlerbetingelser</h1>
        <div class="mt-8 space-y-8 text-slate-700 dark:text-slate-300 leading-7">
          <section>
            <h2 class="text-xl font-semibold text-slate-900 dark:text-slate-100">Rollefordeling</h2>
            <p>Merchanten er dataansvarlig for kundedata i den tilknyttede webshop. Metly er databehandler og behandler alene data efter merchantens instruks for at levere analyse, forecasting og forretningsindsigter.</p>
          </section>
          <section>
            <h2 class="text-xl font-semibold text-slate-900 dark:text-slate-100">Instruks og formål</h2>
            <p>Metly behandler kun data til de formål, der er nødvendige for at levere dashboards, prognoser, kundeanalyser og anbefalinger. Metly må ikke bruge data til egne marketingformål eller dele data mellem merchants.</p>
          </section>
          <section>
            <h2 class="text-xl font-semibold text-slate-900 dark:text-slate-100">Underdatabehandlere og sikkerhed</h2>
            <p>Metly anvender kun tekniske underleverandører, der er nødvendige for drift, hosting og sikkerhed. Data overføres krypteret i transit, og direkte personhenførbare felter reduceres eller pseudonymiseres efter retentionregler.</p>
          </section>
          <section>
            <h2 class="text-xl font-semibold text-slate-900 dark:text-slate-100">Sletning og ophør</h2>
            <p>Når samarbejdet ophører, eller hvis Shopify-onboarding fejler under signup-flowet, sletter Metly brugerens konto og relaterede data i systemet. Merchants kan desuden anmode om sletning af importerede data.</p>
          </section>
        </div>
      </div>
    </main>
    <Footer />
  </div>
</template>

<script setup lang="ts">
useHead({
  title: 'Databehandlerbetingelser - Metly',
})
</script>
