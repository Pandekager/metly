<template>
    <div class="order-flow-chart-container">
        <div class="summary-cards">
            <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Samlet antal ordrer
                </h3>
                <p class="text-2xl font-bold text-slate-900 dark:text-slate-100">
                    {{ formatNumber(orderCount) }}
                </p>
            </div>
            <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Opfyldelsesrate
                </h3>
                <p class="text-2xl font-bold text-slate-900 dark:text-slate-100">
                    {{ fulfillmentRate.toFixed(1) }}%
                </p>
            </div>
            <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Top carrier
                </h3>
                <p class="text-2xl font-bold text-slate-900 dark:text-slate-100">
                    {{ topCarrier }}
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
                v-if="stageData.length > 0"
                :key="isDark ? 'dark' : 'light'"
                :data="chartData"
                :options="chartOptions"
            />
            <div v-else class="empty-state">
                <p class="empty-text text-slate-500 dark:text-slate-400">
                    Ingen orderflow-data tilgængelig
                </p>
            </div>
        </div>

        <div v-if="topCarriers.length > 0" class="carriers-section mt-6">
            <h4 class="text-lg font-semibold mb-3 text-slate-900 dark:text-slate-100">
                Top carriers
            </h4>
            <div class="carrier-list flex flex-wrap gap-3">
                <div
                    v-for="carrier in topCarriers"
                    :key="carrier.carrier"
                    class="carrier-item p-3 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800"
                >
                    <p class="font-medium text-slate-900 dark:text-slate-100">
                        {{ carrier.carrier }}
                    </p>
                    <p class="text-sm text-slate-600 dark:text-slate-400">
                        {{ formatNumber(carrier.count) }} ordrer
                    </p>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
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
import { COLORS } from "~/utils/colors";

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
);

interface StageChartEntry {
    stage: string;
    avg_hours: number;
}

interface CarrierCount {
    carrier: string;
    count: number;
}

interface Bottlenecks {
    created_to_processed_exceeds_24h_pct: number;
    processed_to_fulfilled_exceeds_48h_pct: number;
}

interface OrderFlowResponse {
    order_count: number;
    stage_durations: Record<string, any>;
    bottlenecks: Bottlenecks;
    fulfillment_rate: number;
    top_carriers: CarrierCount[];
    stage_chart_data: StageChartEntry[];
}

const { isDark } = useTheme();

const { data: orderFlowData, pending, error } = await useFetch<OrderFlowResponse>("/api/order_flow_analysis");

const orderCount = computed(() => orderFlowData.value?.order_count ?? 0);
const fulfillmentRate = computed(() => orderFlowData.value?.fulfillment_rate ?? 0);
const stageData = computed(() => orderFlowData.value?.stage_chart_data ?? []);
const topCarriers = computed(() => orderFlowData.value?.top_carriers ?? []);
const bottlenecks = computed(() => orderFlowData.value?.bottlenecks ?? {
    created_to_processed_exceeds_24h_pct: 0,
    processed_to_fulfilled_exceeds_48h_pct: 0
});

const topCarrier = computed(() => {
    if (topCarriers.value.length === 0) return "N/A";
    return topCarriers.value[0].carrier;
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
    const b = bottlenecks.value;

    if (b.created_to_processed_exceeds_24h_pct > 10) {
        flags.push({
            key: "slow-processing",
            icon: "⚠️",
            title: "Langsom behandling",
            description: `${b.created_to_processed_exceeds_24h_pct.toFixed(1)}% af ordrer tager >24 timer at blive behandlet`,
            class: "bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-200"
        });
    }

    if (b.processed_to_fulfilled_exceeds_48h_pct > 10) {
        flags.push({
            key: "slow-fulfillment",
            icon: "⚠️",
            title: "Langsom levering",
            description: `${b.processed_to_fulfilled_exceeds_48h_pct.toFixed(1)}% af ordrer tager >48 timer at blive afsendt`,
            class: "bg-rose-100 dark:bg-rose-900/30 text-rose-800 dark:text-rose-200"
        });
    }

    return flags;
});

const formatNumber = (value: number): string => {
    return new Intl.NumberFormat("da-DK").format(value);
};

const chartData = computed(() => {
    if (stageData.value.length === 0) {
        return { labels: [], datasets: [] };
    }

    return {
        labels: stageData.value.map(d => d.stage),
        datasets: [
            {
                label: "Gennemsnitlig tid (timer)",
                data: stageData.value.map(d => d.avg_hours),
                backgroundColor: stageData.value.map((d, i) => {
                    // Color red if duration exceeds threshold
                    if (i === 0 && d.avg_hours > 24) {
                        return "rgba(239, 68, 68, 0.7)"; // red
                    }
                    if (i === 1 && d.avg_hours > 48) {
                        return "rgba(239, 68, 68, 0.7)"; // red
                    }
                    if (i === 2 && d.avg_hours > 168) { // >7 days
                        return "rgba(239, 68, 68, 0.7)"; // red
                    }
                    return "rgba(99, 102, 241, 0.7)"; // indigo
                }),
                borderColor: stageData.value.map((d, i) => {
                    if (i === 0 && d.avg_hours > 24) {
                        return "rgba(239, 68, 68, 1)";
                    }
                    if (i === 1 && d.avg_hours > 48) {
                        return "rgba(239, 68, 68, 1)";
                    }
                    if (i === 2 && d.avg_hours > 168) {
                        return "rgba(239, 68, 68, 1)";
                    }
                    return "rgba(99, 102, 241, 1)";
                }),
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
            callbacks: {
                label: function (context: any) {
                    const value = context.raw;
                    const label = context.label;
                    if (!value) return null;
                    // Convert to days if > 24 hours
                    if (value >= 24) {
                        const days = value / 24;
                        return `${label}: ${days.toFixed(1)} dage`;
                    }
                    return `${label}: ${value.toFixed(1)} timer`;
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
            title: {
                display: true,
                text: "Timer (t) / Dage (d)",
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
.order-flow-chart-container {
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

.carriers-section {
    margin-top: 24px;
}

.carrier-list {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
}

.carrier-item {
    min-width: 120px;
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