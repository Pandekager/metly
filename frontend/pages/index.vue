<template>
  <div class="min-h-screen">
    <Navbar />
    <main>
      <SectionsHeroSection />
      <SectionsFeaturesSection />
      <SectionsAboutSection />
      <SectionsContactSection />
    </main>
    <Footer />
  </div>
</template>

<script setup lang="ts">
useHead({
  title: "Metly - Fra data til handling",
  meta: [
    {
      name: "description",
      content:
        "Metly hjælper webshops med at træffe bedre beslutninger baseret på data - helt automatisk.",
    },
  ],
});
</script>
