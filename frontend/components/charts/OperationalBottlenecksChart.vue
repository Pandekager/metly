<template>
    <div class="operational-bottlenecks-container">
        <div class="Summary-cards">
            <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Samlet ordrer
                </h3>
                <p class="text-2xl font-bold text-slate-900 dark:text-slate-100">
                    {{ formatNumber(data?.total_orders ?? 0) }}
                </p>
            </div>
            <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Gns. behandlingstid
                </h3>
                <p class="text-2xl font-bold text-slate-900 dark:text-slate-100">
                    {{ formatHours(data?.avg_processing_time_hours ?? 0) }}
                </p>
            </div>
            <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Gns. leveringstid
                </h3>
                <p class="text-2xl font-bold text-slate-900 dark:text-slate-100">
                    {{ formatHours(data?.avg_fulfillment_time_hours ?? 0) }}
                </p>
            </div>
            <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Forsinkede ordrer
                </h3>
                <p class="text-2xl font-bold" :class="delayRateClass">
                    {{ data?.delay_rate ?? 0 }}%
                </p>
            </div>
        </div>

        <div v-if="(data?.delay_rate ?? 0) > 15" class="red-flags mt-6">
            <div class="flag-item p-4 rounded-lg flex items-center gap-3 bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-200">
                <span class="text-xl">⚠️</span>
                <div>
                    <p class="font-semibold">Høj forsinkelsesrate</p>
                    <p class="text-sm">{{ data?.delay_rate }}% af ordrer har forsinkelser i leveringen</p>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            <div class="bottleneck-stages-section">
                <h4 class="text-lg font-semibold mb-4 text-slate-900 dark:text-slate-100">
                    Flaskehalse i processen
                </h4>
                <div class="stages-list">
                    <div
                        v-for="stage in bottleneckStages"
                        :key="stage.stage"
                        class="stage-item p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 mb-3"
                    >
                        <div class="flex justify-between items-center mb-2">
                            <span class="font-medium text-slate-900 dark:text-slate-100">{{ stage.stage }}</span>
                            <span class="text-sm text-slate-600 dark:text-slate-400">
                                {{ formatNumber(stage.orders_count) }} ordrer
                            </span>
                        </div>
                        <div class="flex items-center gap-4 text-sm">
                            <span class="text-slate-600 dark:text-slate-400">
                                Gns: {{ formatHours(stage.avg_duration_hours) }}
                            </span>
                            <span v-if="stage.delay_rate > 10" class="text-rose-600 dark:text-rose-400">
                                {{ stage.delay_rate }}% forsinket
                            </span>
                        </div>
                        <div class="w-full bg-slate-200 dark:bg-slate-600 rounded-full h-2 mt-2">
                            <div
                                class="h-2 rounded-full"
                                :class="stage.delay_rate > 20 ? 'bg-rose-500' : stage.delay_rate > 10 ? 'bg-amber-500' : 'bg-emerald-500'"
                                :style="{ width: Math.min(stage.delay_rate, 100) + '%' }"
                            ></div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="carrier-metrics-section">
                <h4 class="text-lg font-semibold mb-4 text-slate-900 dark:text-slate-100">
                    Carrier-præstation
                </h4>
                <div class="carriers-list">
                    <div
                        v-for="carrier in carrierMetrics"
                        :key="carrier.carrier"
                        class="carrier-item p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 mb-3"
                    >
                        <div class="flex justify-between items-center mb-2">
                            <span class="font-medium text-slate-900 dark:text-slate-100">{{ carrier.carrier }}</span>
                            <span class="text-sm text-slate-600 dark:text-slate-400">
                                {{ formatNumber(carrier.total_orders) }} ordrer
                            </span>
                        </div>
                        <div class="flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
                            <span>Gns. {{ carrier.avg_delivery_days }} dage</span>
                            <span :class="carrier.on_time_rate > 90 ? 'text-emerald-600' : 'text-amber-600'">
                                {{ carrier.on_time_rate }}% til tiden
                            </span>
                        </div>
                    </div>
                    <div v-if="!carrierMetrics.length" class="text-center py-8 text-slate-500">
                        Ingen carrier-data tilgængelig
                    </div>
                </div>
            </div>
        </div>

        <div class="trend-section mt-6">
            <h4 class="text-lg font-semibold mb-4 text-slate-900 dark:text-slate-100">
                Tendens over tid
            </h4>
            <div class="chart-wrapper">
                <Bar
                    v-if="monthlyTrends.length > 0"
                    :key="isDark ? 'dark' : 'light'"
                    :data="chartData"
                    :options="chartOptions"
                />
                <div v-else class="empty-state">
                    <p class="text-slate-500 dark:text-slate-400">
                        Ingen tendensdata tilgængelig
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

interface CarrierMetrics {
    carrier: string;
    total_orders: number;
    avg_delivery_days: number;
    on_time_rate: number;
    delayed_orders: number;
}

interface BottleneckStage {
    stage: string;
    avg_duration_hours: number;
    orders_count: number;
    delayed_count: number;
    delay_rate: number;
}

interface MonthlyTrend {
    month: string;
    avg_processing_hours: number;
    avg_fulfillment_hours: number;
    total_delayed: number;
    bottleneck_stage: string;
}

interface OperationalBottlenecksResponse {
    total_orders: number;
    avg_processing_time_hours: number;
    avg_fulfillment_time_hours: number;
    total_delayed_orders: number;
    delay_rate: number;
    carrier_metrics: CarrierMetrics[];
    bottleneck_stages: BottleneckStage[];
    monthly_trends: MonthlyTrend[];
}

const { isDark } = useTheme();

const props = defineProps<{
  dateRange?: { start: string; end: string }
}>();

const data = ref<OperationalBottlenecksResponse | null>(null);
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
    const url = query ? `/api/operational_bottlenecks?${query}` : '/api/operational_bottlenecks';
    const result = await $fetch<OperationalBottlenecksResponse>(url);
    data.value = result;
  } catch (error) {
    console.error('Failed to load operational bottlenecks data:', error);
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

const bottleneckStages = computed(() => data.value?.bottleneck_stages ?? []);
const carrierMetrics = computed(() => data.value?.carrier_metrics ?? []);
const monthlyTrends = computed(() => data.value?.monthly_trends ?? []);

const delayRateClass = computed(() => {
    const rate = data.value?.delay_rate ?? 0;
    if (rate > 30) return "text-rose-600 dark:text-rose-400";
    if (rate > 15) return "text-amber-600 dark:text-amber-400";
    return "text-emerald-600 dark:text-emerald-400";
});

const formatNumber = (value: number): string => {
    return new Intl.NumberFormat("da-DK").format(value);
};

const formatHours = (hours: number): string => {
    if (hours < 1) {
        return `${Math.round(hours * 60)} min`;
    }
    if (hours < 24) {
        return `${hours.toFixed(1)} t`;
    }
    const days = hours / 24;
    return `${days.toFixed(1)} dage`;
};

const chartData = computed(() => {
    if (!monthlyTrends.value.length) {
        return { labels: [], datasets: [] };
    }

    return {
        labels: monthlyTrends.value.map(d => d.month),
        datasets: [
            {
                label: "Behandlingstid (timer)",
                data: monthlyTrends.value.map(d => d.avg_processing_hours),
                backgroundColor: "rgba(59, 130, 246, 0.7)",
                borderColor: "rgba(59, 130, 246, 1)",
                borderWidth: 1,
            },
            {
                label: "Leveringstid (timer)",
                data: monthlyTrends.value.map(d => d.avg_fulfillment_hours),
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
            callbacks: {
                label: function (context: any) {
                    const hours = context.raw;
                    if (hours < 24) {
                        return `${context.dataset.label}: ${hours.toFixed(1)} timer`;
                    }
                    return `${context.dataset.label}: ${(hours / 24).toFixed(1)} dage`;
                },
            },
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
                callback: function (value: any) {
                    if (value >= 24) {
                        return `${(value / 24).toFixed(0)}d`;
                    }
                    return `${value}t`;
                },
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
.operational-bottlenecks-container {
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

.stages-list,
.carriers-list {
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
