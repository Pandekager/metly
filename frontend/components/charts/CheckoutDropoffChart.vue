<template>
    <div class="checkout-dropoff-container">
        <div class="summary-cards">
            <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Checkout-sessions
                </h3>
                <p class="text-2xl font-bold text-slate-900 dark:text-slate-100">
                    {{ formatNumber(checkoutData?.total_checkout_sessions ?? 0) }}
                </p>
            </div>
            <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Gennemførte
                </h3>
                <p class="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                    {{ formatNumber(checkoutData?.completed_orders ?? 0) }}
                </p>
            </div>
            <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Opgivne
                </h3>
                <p class="text-2xl font-bold" :class="abandonmentClass">
                    {{ formatNumber(checkoutData?.abandoned_checkouts ?? 0) }}
                </p>
            </div>
            <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Tabt omsætning
                </h3>
                <p class="text-2xl font-bold text-rose-600 dark:text-rose-400">
                    {{ formatCurrency(checkoutData?.lost_revenue ?? 0) }}
                </p>
            </div>
        </div>

        <div v-if="abandonmentRate > 10" class="red-flags mt-6">
            <div class="flag-item p-4 rounded-lg flex items-center gap-3 bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-200">
                <span class="text-xl">⚠️</span>
                <div>
                    <p class="font-semibold">Høj opgivelsesrate</p>
                    <p class="text-sm">{{ abandonmentRate.toFixed(1) }}% af kunder fuldfører ikke deres køb</p>
                </div>
            </div>
        </div>

        <div class="funnel-section mt-6">
            <h4 class="text-lg font-semibold mb-4 text-slate-900 dark:text-slate-100">
                Checkout-tragt
            </h4>
            <div class="funnel-chart">
                <div
                    v-for="(stage, index) in funnelStages"
                    :key="stage.stage"
                    class="funnel-stage"
                >
                    <div class="funnel-bar-wrapper">
                        <div
                            class="funnel-bar"
                            :style="{ width: stage.percentage + '%' }"
                            :class="index === funnelStages.length - 1 ? 'completed' : 'dropping'"
                        >
                            <span class="funnel-label">{{ stage.stage }}</span>
                            <span class="funnel-count">{{ formatNumber(stage.entered) }}</span>
                        </div>
                    </div>
                    <div v-if="stage.dropOff > 0" class="drop-off-indicator">
                        <span class="drop-arrow">↓</span>
                        <span class="drop-count">{{ stage.dropOff.toFixed(0) }} ({{ stage.dropOffRate.toFixed(1) }}%)</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            <div class="reasons-section">
                <h4 class="text-lg font-semibold mb-4 text-slate-900 dark:text-slate-100">
                    Opgivelsesårsager
                </h4>
                <div class="reasons-list">
                    <div
                        v-for="reason in abandonReasons"
                        :key="reason.reason"
                        class="reason-item p-3 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800"
                    >
                        <div class="flex justify-between items-center mb-2">
                            <span class="font-medium text-slate-900 dark:text-slate-100">{{ reason.reason }}</span>
                            <span class="text-sm text-slate-600 dark:text-slate-400">{{ reason.count }}</span>
                        </div>
                        <div class="w-full bg-slate-200 dark:bg-slate-600 rounded-full h-2">
                            <div
                                class="bg-rose-500 h-2 rounded-full"
                                :style="{ width: reason.percentage + '%' }"
                            ></div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="trend-section">
                <h4 class="text-lg font-semibold mb-4 text-slate-900 dark:text-slate-100">
                    Tendens over tid
                </h4>
                <div class="chart-wrapper">
                    <Line
                        v-if="monthlyTrend.length > 0"
                        :key="isDark ? 'dark' : 'light'"
                        :data="trendChartData"
                        :options="trendChartOptions"
                    />
                    <div v-else class="empty-state">
                        <p class="text-slate-500 dark:text-slate-400">
                            Ingen tendensdata tilgængelig
                        </p>
                    </div>
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
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
} from "chart.js";
import { Line } from "vue-chartjs";

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

interface FunnelStage {
    stage: string;
    entered_count: number;
    completed_count: number;
    drop_off_count: number;
    drop_off_rate: number;
}

interface MonthlyTrend {
    month: string;
    checkout_count: number;
    completion_count: number;
    abandonment_rate: number;
}

interface AbandonReason {
    reason: string;
    count: number;
    percentage: number;
    estimated_lost_revenue: number;
}

interface CheckoutDropoffResponse {
    total_checkout_sessions: number;
    completed_orders: number;
    abandoned_checkouts: number;
    abandonment_rate: number;
    lost_revenue: number;
    funnel_stages: FunnelStage[];
    dropoff_by_month: MonthlyTrend[];
    abandon_reasons: AbandonReason[];
}

const { isDark } = useTheme();

const props = defineProps<{
  dateRange?: { start: string; end: string }
}>();

const checkoutData = ref<CheckoutDropoffResponse | null>(null);
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
    const url = query ? `/api/checkout_dropoff_analysis?${query}` : '/api/checkout_dropoff_analysis';
    const result = await $fetch<CheckoutDropoffResponse>(url);
    checkoutData.value = result;
  } catch (error) {
    console.error('Failed to load checkout dropoff data:', error);
    checkoutData.value = null;
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

const abandonmentRate = computed(() => checkoutData.value?.abandonment_rate ?? 0);

const abandonmentClass = computed(() => {
    if (abandonmentRate.value > 50) return "text-rose-600 dark:text-rose-400";
    if (abandonmentRate.value > 25) return "text-amber-600 dark:text-amber-400";
    return "text-slate-600 dark:text-slate-400";
});

const funnelStages = computed(() => {
    if (!checkoutData.value?.funnel_stages?.length) return [];
    
    const maxEntered = Math.max(...checkoutData.value.funnel_stages.map(s => s.entered_count));
    return checkoutData.value.funnel_stages.map(stage => ({
        stage: stage.stage,
        entered: stage.entered_count,
        completed: stage.completed_count,
        dropOff: stage.entered_count - stage.completed_count,
        percentage: maxEntered > 0 ? (stage.entered_count / maxEntered) * 100 : 0,
        dropOffRate: stage.drop_off_rate,
    }));
});

const abandonReasons = computed(() => {
    return checkoutData.value?.abandon_reasons ?? [];
});

const monthlyTrend = computed(() => {
    return checkoutData.value?.dropoff_by_month ?? [];
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

const trendChartData = computed(() => {
    if (!monthlyTrend.value.length) {
        return { labels: [], datasets: [] };
    }

    return {
        labels: monthlyTrend.value.map(d => d.month),
        datasets: [
            {
                label: "Checkout-sessions",
                data: monthlyTrend.value.map(d => d.checkout_count),
                borderColor: "rgba(59, 130, 246, 1)",
                backgroundColor: "rgba(59, 130, 246, 0.1)",
                fill: true,
                tension: 0.3,
            },
            {
                label: "Gennemførte",
                data: monthlyTrend.value.map(d => d.completion_count),
                borderColor: "rgba(16, 185, 129, 1)",
                backgroundColor: "rgba(16, 185, 129, 0.1)",
                fill: true,
                tension: 0.3,
            },
        ],
    };
});

const trendChartOptions = computed(() => ({
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
.checkout-dropoff-container {
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

.red-flags {
    margin-bottom: 24px;
}

.flag-item {
    border-left: 4px solid;
}

.funnel-section {
    background: white;
    dark: bg-slate-800;
    padding: 20px;
    border-radius: 12px;
}

.funnel-chart {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.funnel-stage {
    display: flex;
    flex-direction: column;
    align-items: center;
}

.funnel-bar-wrapper {
    width: 100%;
    display: flex;
    justify-content: center;
}

.funnel-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-radius: 8px;
    transition: width 0.3s ease;
    min-width: 200px;
    max-width: 600px;
}

.funnel-bar.dropping {
    background: linear-gradient(90deg, rgba(239, 68, 68, 0.3), rgba(239, 68, 68, 0.1));
    border: 1px solid rgba(239, 68, 68, 0.5);
}

.funnel-bar.completed {
    background: linear-gradient(90deg, rgba(16, 185, 129, 0.3), rgba(16, 185, 129, 0.1));
    border: 1px solid rgba(16, 185, 129, 0.5);
}

.funnel-label {
    font-weight: 500;
    color: #1e293b;
}

.dark .funnel-label {
    color: #f1f5f9;
}

.funnel-count {
    font-weight: 600;
    color: #475569;
}

.dark .funnel-count {
    color: #94a3b8;
}

.drop-off-indicator {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: #dc2626;
    margin-top: 4px;
}

.drop-arrow {
    font-weight: bold;
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

.reasons-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.chart-wrapper {
    width: 100%;
    height: 250px;
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
