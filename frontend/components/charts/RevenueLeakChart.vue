<template>
    <div class="revenue-leak-chart-container">
        <div class="summary-cards">
            <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Samlet omsætning
                </h3>
                <p class="text-2xl font-bold text-slate-900 dark:text-slate-100">
                    {{ formatCurrency(totalRevenue) }}
                </p>
            </div>
            <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Samlet ordrer
                </h3>
                <p class="text-2xl font-bold text-slate-900 dark:text-slate-100">
                    {{ formatNumber(orderCount) }}
                </p>
            </div>
            <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Lækage
                </h3>
                <p class="text-2xl font-bold" :class="leakClass">
                    {{ totalLeakPct.toFixed(1) }}%
                </p>
            </div>
        </div>

        <div v-if="redFlags.length > 0" class="red-flags mt-6">
            <div
                v-for="flag in redFlags"
                :key="flag.key"
                class="flag-item p-4 mb-3 rounded-lg flex items-center gap-3"
                :class="flag.class"
            >
                <span class="text-xl">{{ flag.icon }}</span>
                <div>
                    <p class="font-semibold">{{ flag.title }}</p>
                    <p class="text-sm">{{ flag.description }}</p>
                </div>
            </div>
        </div>

        <div class="chart-wrapper">
            <Bar
                v-if="leakByMonth.length > 0"
                :key="isDark ? 'dark' : 'light'"
                :data="chartData"
                :options="chartOptions"
            />
            <div v-else class="empty-state">
                <p class="empty-text text-slate-500 dark:text-slate-400">
                    Ingen indtægtslækage-data tilgængelig
                </p>
            </div>
        </div>

        <div v-if="leakByStatus.length > 0" class="status-breakdown mt-6">
            <h4 class="text-lg font-semibold mb-3 text-slate-900 dark:text-slate-100">
                Fordeling efter status
            </h4>
            <div class="status-list flex flex-wrap gap-3">
                <div
                    v-for="item in leakByStatus"
                    :key="item.status"
                    class="status-item p-3 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800"
                >
                    <p class="font-medium text-slate-900 dark:text-slate-100 capitalize">
                        {{ formatStatus(item.status) }}
                    </p>
                    <p class="text-sm text-slate-600 dark:text-slate-400">
                        {{ item.count }} ordrer · {{ formatCurrency(item.revenue) }}
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

interface LeakByStatus {
    status: string;
    count: number;
    revenue: number;
}

interface LeakByMonth {
    month: string;
    total_orders: number;
    total_revenue: number;
    failed: number;
    cancelled: number;
    refunded: number;
}

interface RevenueLeakResponse {
    order_count: number;
    total_revenue: number;
    failed_payment_count: number;
    failed_payment_revenue: number;
    failed_payment_pct: number;
    cancelled_count: number;
    cancelled_revenue: number;
    cancelled_pct: number;
    refunded_count: number;
    refunded_revenue: number;
    refunded_pct: number;
    total_leak_count: number;
    total_leak_revenue: number;
    total_leak_pct: number;
    leak_by_status: LeakByStatus[];
    leak_by_month: LeakByMonth[];
}

const { isDark } = useTheme();

const props = defineProps<{
  dateRange?: { start: string; end: string }
}>();

const leakData = ref<RevenueLeakResponse | null>(null);
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
    const url = query ? `/api/revenue_leak_analysis?${query}` : '/api/revenue_leak_analysis';
    const result = await $fetch<RevenueLeakResponse>(url);
    leakData.value = result;
  } catch (error) {
    console.error('Failed to load revenue leak data:', error);
    leakData.value = null;
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

const orderCount = computed(() => leakData.value?.order_count ?? 0);
const totalRevenue = computed(() => leakData.value?.total_revenue ?? 0);
const totalLeakPct = computed(() => leakData.value?.total_leak_pct ?? 0);
const leakByStatus = computed(() => leakData.value?.leak_by_status ?? []);
const leakByMonth = computed(() => leakData.value?.leak_by_month ?? []);

const failedPaymentPct = computed(() => leakData.value?.failed_payment_pct ?? 0);
const cancelledPct = computed(() => leakData.value?.cancelled_pct ?? 0);
const refundedPct = computed(() => leakData.value?.refunded_pct ?? 0);

const leakClass = computed(() => {
    if (totalLeakPct.value > 20) return "text-rose-600 dark:text-rose-400";
    if (totalLeakPct.value > 10) return "text-amber-600 dark:text-amber-400";
    return "text-emerald-600 dark:text-emerald-400";
});

interface RedFlag {
    key: string;
    icon: string;
    title: string;
    description: string;
    class: string;
}

const redFlags = computed<RedFlag[]>(() => {
    const flags: RedFlag[] = [];

    if (failedPaymentPct.value > 5) {
        flags.push({
            key: "failed-payments",
            icon: "💳",
            title: "Høj betalingsfejl-rate",
            description: `${failedPaymentPct.value.toFixed(1)}% af ordrer har fejlende betalinger`,
            class: "bg-rose-100 dark:bg-rose-900/30 text-rose-800 dark:text-rose-200"
        });
    }

    if (cancelledPct.value > 10) {
        flags.push({
            key: "high-cancellations",
            icon: "❌",
            title: "Høj annulleringsrate",
            description: `${cancelledPct.value.toFixed(1)}% af ordrer bliver annulleret`,
            class: "bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-200"
        });
    }

    if (refundedPct.value > 15) {
        flags.push({
            key: "high-refunds",
            icon: "↩️",
            title: "Høj refunderingsrate",
            description: `${refundedPct.value.toFixed(1)}% af ordrer bliver refunderet`,
            class: "bg-rose-100 dark:bg-rose-900/30 text-rose-800 dark:text-rose-200"
        });
    }

    return flags;
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

const formatStatus = (status: string): string => {
    const statusMap: Record<string, string> = {
        "payment_failed": "Betaling fejlede",
        "failed": "Fejlede",
        "declined": "Afvist",
        "cancelled": "Annulleret",
        "canceled": "Annulleret",
        "refunded": "Refunderet"
    };
    return statusMap[status.toLowerCase()] || status;
};

const chartData = computed(() => {
    if (leakByMonth.value.length === 0) {
        return { labels: [], datasets: [] };
    }

    return {
        labels: leakByMonth.value.map(d => d.month),
        datasets: [
            {
                label: "Fejlende betaling",
                data: leakByMonth.value.map(d => d.failed),
                backgroundColor: "rgba(220, 38, 38, 0.8)",
                borderColor: "rgba(220, 38, 38, 1)",
                borderWidth: 1,
            },
            {
                label: "Annulleret",
                data: leakByMonth.value.map(d => d.cancelled),
                backgroundColor: "rgba(217, 119, 6, 0.8)",
                borderColor: "rgba(217, 119, 6, 1)",
                borderWidth: 1,
            },
            {
                label: "Refunderet",
                data: leakByMonth.value.map(d => d.refunded),
                backgroundColor: "rgba(37, 99, 235, 0.8)",
                borderColor: "rgba(37, 99, 235, 1)",
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
            borderColor: isDark.value ? "#475569" : "#e2e8f0",
            borderWidth: 1,
        },
    },
    scales: {
        y: {
            beginAtZero: true,
            stacked: true,
            grid: {
                color: isDark.value ? "#334155" : "#e2e8f0",
            },
            ticks: {
                color: isDark.value ? "#e2e8f0" : "#334155",
            },
            title: {
                display: true,
                text: "Antal ordrer",
                color: isDark.value ? "#e2e8f0" : "#334155",
            },
        },
        x: {
            stacked: true,
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
.revenue-leak-chart-container {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
}

.summary-cards {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    margin-bottom: 24px;
}

.summary-card {
    flex: 1;
    min-width: 140px;
}

.red-flags {
    margin-bottom: 24px;
}

.flag-item {
    border-left: 4px solid;
}

.status-breakdown {
    margin-top: 24px;
}

.status-list {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
}

.status-item {
    min-width: 150px;
}

.chart-wrapper {
    width: 100%;
    max-width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1.5rem;
    border-radius: 12px;
    min-height: 350px;
    position: relative;
    overflow: hidden;
}

.chart-wrapper canvas {
    max-width: 100% !important;
    height: auto !important;
}

.empty-state {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    font-size: 16px;
}

.empty-text {
    margin: 0;
}

@media (max-width: 768px) {
    .summary-cards {
        flex-direction: column;
    }

    .summary-card {
        min-width: 100%;
    }

    .chart-wrapper {
        padding: 1rem;
        min-height: 300px;
    }
}

@media (max-width: 640px) {
    .chart-wrapper {
        padding: 0.5rem;
        min-height: 250px;
    }
}
</style>
