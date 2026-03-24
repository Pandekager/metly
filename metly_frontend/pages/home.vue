<template>
    <div class="min-h-screen bg-slate-50 dark:bg-slate-900">
        <Navbar />
        <main class="pt-24 pb-12 px-6">
            <div class="max-w-7xl mx-auto">
                <div
                    class="bg-white dark:bg-slate-800 rounded-3xl shadow-xl border border-slate-100 dark:border-slate-700 overflow-hidden"
                >
                    <div class="p-8 border-b border-slate-100 dark:border-slate-700">
                        <div>
                            <h1 class="text-3xl font-bold text-slate-900 dark:text-slate-100">
                                {{
                                    isDemoUser
                                        ? "Demo-webshop: Alt til golf"
                                        : "Velkommen tilbage!"
                                }}
                            </h1>
                            <p
                                v-if="shopifyNotice"
                                :class="[
                                    'mt-3 inline-flex rounded-full px-4 py-2 text-sm font-medium',
                                    shopifyNotice.type === 'success'
                                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200'
                                        : 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
                                ]"
                            >
                                {{ shopifyNotice.message }}
                            </p>
                        </div>
                    </div>

                    <div class="p-6">
                        <div class="flex flex-wrap gap-2 mb-8">
                            <button
                                v-for="tab in tabs"
                                :key="tab.id"
                                @click="activeTab = tab.id"
                                :class="[
                                    'px-6 py-3 rounded-lg font-medium transition-all',
                                    activeTab === tab.id
                                        ? 'bg-metly-600 text-white shadow-md'
                                        : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-600',
                                ]"
                            >
                                {{ tab.label }}
                            </button>
                        </div>

                        <div
                            v-if="loading"
                            class="flex items-center justify-center py-12"
                        >
                            <svg
                                class="animate-spin h-8 w-8 text-metly-600"
                                xmlns="http://www.w3.org/2000/svg"
                                fill="none"
                                viewBox="0 0 24 24"
                            >
                                <circle
                                    class="opacity-25"
                                    cx="12"
                                    cy="12"
                                    r="10"
                                    stroke="currentColor"
                                    stroke-width="4"
                                ></circle>
                                <path
                                    class="opacity-75"
                                    fill="currentColor"
                                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                ></path>
                            </svg>
                        </div>

                        <div
                            v-else-if="activeTab === 'ordrer'"
                            class="space-y-6"
                        >
                            <ChartsForecastChart
                                v-if="forecasts && forecasts.length > 0"
                                :forecasts="forecasts"
                            />
                            <AIBusinessAdvice
                                v-if="advice && advice.length > 0"
                                :advice="advice"
                            />
                            <div
                                v-if="!forecasts?.length && !advice?.length"
                                class="text-center py-12"
                            >
                                <p class="text-slate-500 dark:text-slate-400">
                                    Ingen data tilgængelig endnu
                                </p>
                            </div>
                        </div>

                        <div
                            v-else-if="activeTab === 'kunder'"
                            class="space-y-6"
                        >
                            <div v-if="!analyticsData?.length" class="text-center py-12">
                                <p class="text-slate-500 dark:text-slate-400">
                                    Ingen kundedata tilgængelig
                                </p>
                            </div>
                            <template v-else>
                                <CustomerAnalyticsChart :data="analyticsData" />
                                <ClientOnly>
                                    <template #fallback>
                                        <div class="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6 h-96 flex items-center justify-center">
                                            <p class="text-slate-500 dark:text-slate-400">Indlæser kort...</p>
                                        </div>
                                    </template>
                                    <CustomerMap :data="analyticsData" />
                                </ClientOnly>
                            </template>
                        </div>

                        <div
                            v-else-if="activeTab === 'produkter'"
                            class="text-center py-12"
                        >
                            <p class="text-slate-500 dark:text-slate-400">
                                Produkter data er under udvikling
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </main>
        <Footer />
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from "vue";
import type { Forecast } from "~/types/forecast";
import type { ForecastBusinessAdvice } from "~/types/forecast-business-advice";
import CustomerAnalyticsChart from "~/components/charts/CustomerAnalyticsChart.vue";
import CustomerMap from "~/components/maps/CustomerMap.vue";

interface CityAnalytics {
  city: string
  customer_count: number
  revenue: number
  latitude: number
  longitude: number
}

definePageMeta({
    middleware: "require-auth",
});

useHead({
    title: "Dashboard - Metly",
    meta: [
        {
            name: "description",
            content: "Dit Metly dashboard med prognoser og anbefalinger",
        },
    ],
});

const authStore = useAuthStore();
const route = useRoute();
const isDemoUser = computed(() => authStore.user?.email === "demo@metly.dk");

const tabs = [
    { id: "ordrer", label: "Ordrer" },
    { id: "kunder", label: "Kunder" },
    { id: "produkter", label: "Produkter" },
];

const activeTab = ref("ordrer");
const loading = ref(false);
const forecasts = ref<Forecast[] | null>(null);
const advice = ref<ForecastBusinessAdvice[] | null>(null);
const analyticsData = ref<CityAnalytics[] | null>(null);

const shopifyNotice = computed(() => {
  if (route.query.shopify === 'connected') {
    const shop = typeof route.query.shop === 'string' ? route.query.shop : 'din butik'
    return {
      type: 'success' as const,
      message: `Shopify er forbundet til ${shop}.`
    }
  }

  if (route.query.shopify === 'error') {
    return {
      type: 'error' as const,
      message: 'Shopify-forbindelsen fejlede. Prøv igen og kontroller at appens redirect URL matcher denne side.'
    }
  }

  return null
})

const fetchForecasts = async () => {
    try {
        forecasts.value = await $fetch<Forecast[]>("/api/forecasts");
    } catch (error) {
        console.error("Failed to fetch forecasts:", error);
    }
};

const fetchAdvice = async () => {
  try {
    const data = await $fetch("/api/forecast_business_advice");
    advice.value = Array.isArray(data) ? data : [data];
  } catch (error) {
    console.error("Failed to fetch advice:", error);
  }
};

const fetchAnalytics = async () => {
  console.log("fetchAnalytics called");
  try {
    console.log("Fetching /api/customer_analytics...");
    const result = await $fetch<{data: CityAnalytics[]} | CityAnalytics[]>("/api/customer_analytics");
    analyticsData.value = (result as any).data || result;
    console.log("Analytics fetched:", JSON.stringify(analyticsData.value));
  } catch (error: any) {
    console.error("Failed to fetch analytics:", error?.message || error);
    analyticsData.value = [];
  }
};

onMounted(() => {
  loading.value = true;
  Promise.all([fetchForecasts(), fetchAdvice()]).finally(() => {
    loading.value = false;
  });
  
  // Fetch analytics if kunder tab is active
  if (activeTab.value === 'kunder') {
    fetchAnalytics();
  }
});

// Watch for tab changes to fetch analytics
watch(activeTab, (newTab) => {
  console.log("Tab changed to:", newTab, "analyticsData:", analyticsData.value);
  if (newTab === 'kunder') {
    if (!analyticsData.value || analyticsData.value.length === 0) {
      fetchAnalytics();
    }
  }
});
</script>
