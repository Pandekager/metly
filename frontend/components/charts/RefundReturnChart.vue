<template>
    <div class="refund-return-chart-container">
        <div class="summary-cards">
            <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Samlet refunderinger
                </h3>
                <p class="text-2xl font-bold text-slate-900 dark:text-slate-100">
                    {{ formatNumber(totalRefunds) }}
                </p>
            </div>
            <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Refunderet omsætning
                </h3>
                <p class="text-2xl font-bold text-slate-900 dark:text-slate-100">
                    {{ formatCurrency(totalRefundRevenue) }}
                </p>
            </div>
            <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Refunderingsrate
                </h3>
                <p class="text-2xl font-bold" :class="refundRateClass">
                    {{ refundRate.toFixed(1) }}%
                </p>
            </div>
            <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                    Gns. dage til refundering
                </h3>
                <p class="text-2xl font-bold text-slate-900 dark:text-slate-100">
                    {{ avgDaysToRefund.toFixed(1) }} dage
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
            <Line
                v-if="refundsByMonth.length > 0"
                :key="isDark ? 'dark' : 'light'"
                :data="trendChartData"
                :options="trendChartOptions"
            />
            <div v-else class="empty-state">
                <p class="empty-text text-slate-500 dark:text-slate-400">
                    Ingen returdata tilgængelig
                </p>
            </div>
        </div>

        <div v-if="topRefundedProducts.length > 0" class="product-breakdown mt-6">
            <h4 class="text-lg font-semibold mb-3 text-slate-900 dark:text-slate-100">
                Produkter med flest refunderinger
            </h4>
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="border-b border-slate-200 dark:border-slate-600">
                            <th class="text-left py-3 px-2 text-slate-600 dark:text-slate-400">Produkt</th>
                            <th class="text-right py-3 px-2 text-slate-600 dark:text-slate-400">Antal</th>
                            <th class="text-right py-3 px-2 text-slate-600 dark:text-slate-400">Rate</th>
                            <th class="text-right py-3 px-2 text-slate-600 dark:text-slate-400">Omsætning</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr
                            v-for="product in topRefundedProducts"
                            :key="product.product_id"
                            class="border-b border-slate-100 dark:border-slate-700"
                        >
                            <td class="py-3 px-2 text-slate-900 dark:text-slate-100">
                                {{ product.product_name }}
                            </td>
                            <td class="py-3 px-2 text-right text-slate-900 dark:text-slate-100">
                                {{ product.refund_count }}
                            </td>
                            <td class="py-3 px-2 text-right" :class="product.refund_rate > 20 ? 'text-rose-600 dark:text-rose-400' : 'text-slate-600 dark:text-slate-400'">
                                {{ product.refund_rate.toFixed(1) }}%
                            </td>
                            <td class="py-3 px-2 text-right text-slate-600 dark:text-slate-400">
                                {{ formatCurrency(product.total_revenue) }}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <div v-if="returnReasons.length > 0" class="reasons-breakdown mt-6">
            <h4 class="text-lg font-semibold mb-3 text-slate-900 dark:text-slate-100">
                Returårsager
            </h4>
            <div class="reasons-chart-wrapper">
                <Doughnut
                    :key="isDark ? 'dark-reason' : 'light-reason'"
                    :data="reasonsChartData"
                    :options="reasonsChartOptions"
                />
            </div>
            <div class="reasons-legend mt-4">
                <div
                    v-for="(reason, index) in returnReasons"
                    :key="reason.reason"
                    class="reason-item flex items-center justify-between py-2 px-3 rounded"
                    :class="index % 2 === 0 ? 'bg-slate-50 dark:bg-slate-800/50' : ''"
                >
                    <div class="flex items-center gap-2">
                        <span
                            class="w-3 h-3 rounded-full"
                            :style="{ backgroundColor: reasonsChartData.datasets[0].backgroundColor[index] }"
                        ></span>
                        <span class="text-slate-900 dark:text-slate-100">{{ reason.reason }}</span>
                    </div>
                    <span class="text-slate-600 dark:text-slate-400">
                        {{ reason.count }} ({{ reason.percentage.toFixed(0) }}%)
                    </span>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    Filler,
} from "chart.js";
import { Line, Doughnut } from "vue-chartjs";

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

interface TopRefundedProduct {
    product_id: string;
    product_name: string;
    refund_count: number;
    refund_rate: number;
    total_revenue: number;
}

interface ReturnReason {
    reason: string;
    count: number;
    percentage: number;
}

interface RefundByMonth {
    month: string;
    refund_count: number;
    refund_revenue: number;
    refund_rate: number;
}

interface RefundReturnResponse {
    total_refunds: number;
    total_refund_revenue: number;
    refund_rate: number;
    avg_days_to_refund: number;
    top_refunded_products: TopRefundedProduct[];
    return_reasons: ReturnReason[];
    refunds_by_month: RefundByMonth[];
}

const { isDark } = useTheme();

const { data: refundData } = await useFetch<RefundReturnResponse>("/api/refund_return_analysis");

const totalRefunds = computed(() => refundData.value?.total_refunds ?? 0);
const totalRefundRevenue = computed(() => refundData.value?.total_refund_revenue ?? 0);
const refundRate = computed(() => refundData.value?.refund_rate ?? 0);
const avgDaysToRefund = computed(() => refundData.value?.avg_days_to_refund ?? 0);
const topRefundedProducts = computed(() => refundData.value?.top_refunded_products ?? []);
const returnReasons = computed(() => refundData.value?.return_reasons ?? []);
const refundsByMonth = computed(() => refundData.value?.refunds_by_month ?? []);

const refundRateClass = computed(() => {
    if (refundRate.value > 15) return "text-rose-600 dark:text-rose-400";
    if (refundRate.value > 10) return "text-amber-600 dark:text-amber-400";
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

    if (refundRate.value > 15) {
        flags.push({
            key: "high-refund-rate",
            icon: "⚠️",
            title: "Høj refunderingsrate",
            description: `${refundRate.value.toFixed(1)}% af ordrer bliver refunderet`,
            class: "bg-rose-100 dark:bg-rose-900/30 text-rose-800 dark:text-rose-200"
        });
    }

    // Check for products with >20% refund rate
    const highRefundProducts = topRefundedProducts.value.filter(p => p.refund_rate > 20);
    if (highRefundProducts.length > 0) {
        flags.push({
            key: "high-refund-products",
            icon: "📦",
            title: "Produkter med høj returrate",
            description: `${highRefundProducts.length} produkt(er) har over 20% refunderingsrate`,
            class: "bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-200"
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

const trendChartData = computed(() => {
    if (refundsByMonth.value.length === 0) {
        return { labels: [], datasets: [] };
    }

    return {
        labels: refundsByMonth.value.map(d => d.month),
        datasets: [
            {
                label: "Refunderingsrate (%)",
                data: refundsByMonth.value.map(d => d.refund_rate),
                borderColor: "rgba(139, 92, 246, 1)",
                backgroundColor: "rgba(139, 92, 246, 0.1)",
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
            display: false,
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
                label: (context: any) => `${context.parsed.y.toFixed(1)}%`
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
                callback: (value: any) => `${value}%`,
            },
            title: {
                display: true,
                text: "Refunderingsrate (%)",
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

const reasonsChartColors = [
    "rgba(239, 68, 68, 0.8)",   // Red
    "rgba(245, 158, 11, 0.8)", // Amber
    "rgba(139, 92, 246, 0.8)", // Purple
    "rgba(34, 197, 94, 0.8)", // Green
    "rgba(59, 130, 246, 0.8)", // Blue
];

const reasonsChartData = computed(() => {
    if (returnReasons.value.length === 0) {
        return { labels: [], datasets: [] };
    }

    return {
        labels: returnReasons.value.map(r => r.reason),
        datasets: [
            {
                data: returnReasons.value.map(r => r.count),
                backgroundColor: reasonsChartColors.slice(0, returnReasons.value.length),
                borderColor: reasonsChartColors.slice(0, returnReasons.value.length).map(c => c.replace("0.8", "1")),
                borderWidth: 2,
            },
        ],
    };
});

const reasonsChartOptions = computed(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            display: false,
        },
        tooltip: {
            backgroundColor: isDark.value ? "#1e293b" : "#ffffff",
            titleColor: isDark.value ? "#e2e8f0" : "#1e293b",
            bodyColor: isDark.value ? "#cbd5e1" : "#475569",
            borderColor: isDark.value ? "#475569" : "#e2e8f0",
            borderWidth: 1,
        },
    },
}));
</script>

<style scoped>
.refund-return-chart-container {
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

.chart-wrapper {
    width: 100%;
    max-width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1.5rem;
    border-radius: 12px;
    min-height: 300px;
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

.product-breakdown {
    margin-top: 24px;
}

.reasons-breakdown {
    margin-top: 24px;
}

.reasons-chart-wrapper {
    width: 100%;
    max-width: 300px;
    margin: 0 auto;
}

.reasons-legend {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.reason-item {
    font-size: 14px;
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
        min-height: 250px;
    }
}

@media (max-width: 640px) {
    .chart-wrapper {
        padding: 0.5rem;
        min-height: 200px;
    }
}
</style>