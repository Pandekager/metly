<template>
    <div class="customer-behavior-container">
        <div class="summary-cards">
            <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Unikke kunder
                </h3>
                <p class="text-2xl font-bold text-slate-900 dark:text-slate-100">
                    {{ formatNumber(data?.total_customers ?? 0) }}
                </p>
            </div>
            <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Retention
                </h3>
                <p class="text-2xl font-bold" :class="retentionClass">
                    {{ data?.retention_rate ?? 0 }}%
                </p>
            </div>
            <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Gns. kunde-LTV
                </h3>
                <p class="text-2xl font-bold text-slate-900 dark:text-slate-100">
                    {{ formatCurrency(data?.avg_customer_lifetime_value ?? 0) }}
                </p>
            </div>
            <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Samlet omsætning
                </h3>
                <p class="text-2xl font-bold text-slate-900 dark:text-slate-100">
                    {{ formatCurrency(data?.total_revenue ?? 0) }}
                </p>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            <div class="frequency-section">
                <h4 class="text-lg font-semibold mb-4 text-slate-900 dark:text-slate-100">
                    Købsfrekvens
                </h4>
                <div class="frequency-list">
                    <div
                        class="frequency-item p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 mb-3"
                    >
                        <div class="flex justify-between items-center mb-2">
                            <span class="font-medium text-slate-900 dark:text-slate-100">Engangskøbere</span>
                            <span class="text-sm text-slate-600 dark:text-slate-400">
                                {{ formatNumber(purchaseFrequency.one_time) }} ({{ purchaseFrequency.one_time_pct }}%)
                            </span>
                        </div>
                        <div class="w-full bg-slate-200 dark:bg-slate-600 rounded-full h-2">
                            <div
                                class="h-2 rounded-full bg-amber-500"
                                :style="{ width: purchaseFrequency.one_time_pct + '%' }"
                            ></div>
                        </div>
                    </div>
                    <div
                        class="frequency-item p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 mb-3"
                    >
                        <div class="flex justify-between items-center mb-2">
                            <span class="font-medium text-slate-900 dark:text-slate-100">Regelmæssige (2-3 ordrer)</span>
                            <span class="text-sm text-slate-600 dark:text-slate-400">
                                {{ formatNumber(purchaseFrequency.regular) }} ({{ purchaseFrequency.regular_pct }}%)
                            </span>
                        </div>
                        <div class="w-full bg-slate-200 dark:bg-slate-600 rounded-full h-2">
                            <div
                                class="h-2 rounded-full bg-blue-500"
                                :style="{ width: purchaseFrequency.regular_pct + '%' }"
                            ></div>
                        </div>
                    </div>
                    <div
                        class="frequency-item p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 mb-3"
                    >
                        <div class="flex justify-between items-center mb-2">
                            <span class="font-medium text-slate-900 dark:text-slate-100">Faste (4+ ordrer)</span>
                            <span class="text-sm text-slate-600 dark:text-slate-400">
                                {{ formatNumber(purchaseFrequency.frequent) }} ({{ purchaseFrequency.frequent_pct }}%)
                            </span>
                        </div>
                        <div class="w-full bg-slate-200 dark:bg-slate-600 rounded-full h-2">
                            <div
                                class="h-2 rounded-full bg-emerald-500"
                                :style="{ width: purchaseFrequency.frequent_pct + '%' }"
                            ></div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="returning-section">
                <h4 class="text-lg font-semibold mb-4 text-slate-900 dark:text-slate-100">
                    Tilbagevendende kunder
                </h4>
                <div class="returning-stats p-6 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                    <div class="text-center">
                        <p class="text-5xl font-bold" :class="retentionClass">
                            {{ data?.returning_customers ?? 0 }}
                        </p>
                        <p class="text-lg text-slate-600 dark:text-slate-400 mt-2">
                            kunder har bestilt mere end én gang
                        </p>
                    </div>
                    <div class="mt-6 text-center">
                        <p class="text-3xl font-semibold text-slate-900 dark:text-slate-100">
                            {{ formatCurrency(data?.avg_customer_lifetime_value ?? 0) }}
                        </p>
                        <p class="text-sm text-slate-600 dark:text-slate-400">
                            gennemsnitlig livstidsværdi per kunde
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <div class="trend-section mt-6">
            <h4 class="text-lg font-semibold mb-4 text-slate-900 dark:text-slate-100">
                Kundekohorter over tid
            </h4>
            <div class="chart-wrapper">
                <Bar
                    v-if="monthlyCohorts.length > 0"
                    :key="isDark ? 'dark' : 'light'"
                    :data="chartData"
                    :options="chartOptions"
                />
                <div v-else class="empty-state">
                    <p class="text-slate-500 dark:text-slate-400">
                        Ingen kohortedata tilgængelig
                    </p>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted } from "vue";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
} from "chart.js";
import { Bar } from "vue-chartjs";

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
);

interface PurchaseFrequency {
    one_time: number;
    one_time_pct: number;
    regular: number;
    regular_pct: number;
    frequent: number;
    frequent_pct: number;
}

interface MonthlyCohort {
    month: string;
    new_customers: number;
    returning_customers: number;
    retention_rate: number;
    total_revenue: number;
}

interface CustomerBehaviorResponse {
    total_customers: number;
    returning_customers: number;
    retention_rate: number;
    avg_customer_lifetime_value: number;
    total_revenue: number;
    purchase_frequency: PurchaseFrequency;
    monthly_cohorts: MonthlyCohort[];
}

const { isDark } = useTheme();

const props = defineProps<{
  dateRange?: { start: string; end: string }
}>();

const data = ref<CustomerBehaviorResponse | null>(null);
const loading = ref(false);

const loadData = async () => {
  loading.value = true;
  try {
    const params = new URLSearchParams();
    if (props.dateRange) {
      params.set('start_date', props.dateRange.start);
      params.set('end_date', props.dateRange.end);
    }
    const query = params.toString();
    const url = query ? `/api/customer_behavior_analysis?${query}` : '/api/customer_behavior_analysis';
    const result = await $fetch<CustomerBehaviorResponse>(url);
    data.value = result;
  } catch (error) {
    console.error('Failed to load customer behavior data:', error);
    data.value = null;
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadData();
});

watch(
  () => props.dateRange,
  () => {
    loadData();
  },
  { deep: true }
);

const purchaseFrequency = computed(() => data.value?.purchase_frequency ?? {
    one_time: 0,
    one_time_pct: 0,
    regular: 0,
    regular_pct: 0,
    frequent: 0,
    frequent_pct: 0,
});

const monthlyCohorts = computed(() => data.value?.monthly_cohorts ?? []);

const retentionClass = computed(() => {
    const rate = data.value?.retention_rate ?? 0;
    if (rate > 50) return "text-emerald-600 dark:text-emerald-400";
    if (rate > 25) return "text-blue-600 dark:text-blue-400";
    if (rate > 10) return "text-amber-600 dark:text-amber-400";
    return "text-rose-600 dark:text-rose-400";
});

const formatNumber = (value: number): string => {
    return new Intl.NumberFormat("da-DK").format(value);
};

const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat("da-DK", {
        style: "currency",
        currency: "DKK",
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    }).format(value);
};

const chartData = computed(() => {
    if (!monthlyCohorts.value.length) {
        return { labels: [], datasets: [] };
    }

    return {
        labels: monthlyCohorts.value.map(d => d.month),
        datasets: [
            {
                label: "Nye kunder",
                data: monthlyCohorts.value.map(d => d.new_customers),
                backgroundColor: "rgba(59, 130, 246, 0.7)",
                borderColor: "rgba(59, 130, 246, 1)",
                borderWidth: 1,
            },
            {
                label: "Tilbagevendende",
                data: monthlyCohorts.value.map(d => d.returning_customers),
                backgroundColor: "rgba(16, 185, 129, 0.7)",
                borderColor: "rgba(16, 185, 129, 1)",
                borderWidth: 1,
            },
        ],
    };
});

const chartOptions = computed(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            display: true,
            position: "top" as const,
            labels: {
                color: isDark.value ? "#e2e8f0" : "#334155",
            },
        },
        tooltip: {
            backgroundColor: isDark.value ? "#1e293b" : "#ffffff",
            titleColor: isDark.value ? "#e2e8f0" : "#1e293b",
            bodyColor: isDark.value ? "#cbd5e1" : "#475569",
        },
    },
    scales: {
        y: {
            beginAtZero: true,
            grid: {
                color: isDark.value ? "#334155" : "#e2e8f0",
            },
            ticks: {
                color: isDark.value ? "#e2e8f0" : "#334155",
            },
        },
        x: {
            grid: {
                color: isDark.value ? "#334155" : "#e2e8f0",
            },
            ticks: {
                color: isDark.value ? "#e2e8f0" : "#334155",
            },
        },
    },
}));
</script>

<style scoped>
.customer-behavior-container {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
}

.summary-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
}

.summary-card {
    text-align: center;
}

.grid {
    display: grid;
}

.lg\:grid-cols-2 {
    grid-template-columns: repeat(2, 1fr);
}

@media (max-width: 1024px) {
    .lg\:grid-cols-2 {
        grid-template-columns: 1fr;
    }
}

.frequency-list,
.returning-stats {
    display: flex;
    flex-direction: column;
}

.chart-wrapper {
    width: 100%;
    height: 300px;
    padding: 16px;
    background: white;
    dark: bg-slate-800;
    border-radius: 12px;
}

.empty-state {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
}
</style>