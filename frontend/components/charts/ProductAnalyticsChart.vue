<template>
    <div class="product-analytics-chart-container">
        <div class="top-section">
            <div class="filter-section">
                <div class="filter-group">
                    <label
                        for="product"
                        class="filter-label text-slate-700 dark:text-slate-200 font-semibold text-sm mb-2 block"
                        >Produkt</label
                    >
                    <select
                        id="product"
                        v-model="selectedProduct"
                        class="filter-select w-full p-4 text-sm border border-slate-200 dark:border-slate-600 rounded-lg cursor-pointer transition-all duration-200 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100"
                    >
                        <option value="all">Alle produkter</option>
                        <option
                            v-for="product in productNames"
                            :key="product"
                            :value="product"
                        >
                            {{ product }}
                        </option>
                    </select>
                </div>
            </div>

            <div class="summary-cards">
                <div class="summary-card p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800">
                    <h3 class="text-sm font-medium text-slate-600 dark:text-slate-400 mb-1">
                        Samlet enheder
                    </h3>
                    <p class="text-2xl font-bold text-slate-900 dark:text-slate-100">
                        {{ formatNumber(totalUnitsSold) }}
                    </p>
                </div>
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
                        Antal produkter
                    </h3>
                    <p class="text-2xl font-bold text-slate-900 dark:text-slate-100">
                        {{ topProducts.length }}
                    </p>
                </div>
            </div>
        </div>

        <div class="chart-wrapper">
            <Line
                v-if="filteredTrends.length > 0"
                :key="isDark ? 'dark' : 'light'"
                :data="chartData"
                :options="chartOptions"
                ref="chartRef"
            />
            <div v-else class="empty-state">
                <p class="empty-text text-slate-500 dark:text-slate-400">
                    Ingen salgdata tilgængelig for den valgte filtrering
                </p>
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
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler,
} from "chart.js";
import { Line } from "vue-chartjs";
import { COLORS } from "~/utils/colors";
import type { ProductAnalytics, ProductTrend } from "~/types/product";

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
    Filler,
);

const props = defineProps<{
    topProducts: ProductAnalytics[];
    salesTrends: ProductTrend[];
}>();

const selectedProduct = ref<string>("all");
const chartRef = ref<any>(null);

const productNames = computed(() => {
    const products = new Set(
        props.topProducts.map((p) => p.product_name || "Ukategoriseret"),
    );
    return Array.from(products).sort();
});

const filteredTrends = computed(() => {
    if (selectedProduct.value === "all") return props.salesTrends;
    return props.salesTrends.filter(
        (t) => t.product_name === selectedProduct.value,
    );
});

const totalUnitsSold = computed(() => {
    if (selectedProduct.value === "all") {
        return props.salesTrends.reduce((sum, t) => sum + t.units_sold, 0);
    }
    return filteredTrends.value.reduce((sum, t) => sum + t.units_sold, 0);
});

const totalRevenue = computed(() => {
    if (selectedProduct.value === "all") {
        return props.salesTrends.reduce((sum, t) => sum + t.revenue, 0);
    }
    return filteredTrends.value.reduce((sum, t) => sum + t.revenue, 0);
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
    // Aggregate by month
    const monthMap = new Map<string, number>();

    for (const trend of filteredTrends.value) {
        const current = monthMap.get(trend.month) || 0;
        monthMap.set(trend.month, current + trend.units_sold);
    }

    const sortedMonths = Array.from(monthMap.keys()).sort();
    const labels = sortedMonths.map((month) => {
        const [year, m] = month.split("-");
        const date = new Date(parseInt(year), parseInt(m) - 1);
        return date.toLocaleString("default", { month: "short", year: "2-digit" });
    });
    const data = sortedMonths.map((month) => monthMap.get(month) || 0);

    return {
        labels,
        datasets: [
            {
                label: "Solgte enheder",
                data,
                borderColor: COLORS.actualLine,
                backgroundColor: COLORS.actualBackground,
                fill: true,
                borderWidth: 2,
                pointRadius: 4,
                pointBackgroundColor: COLORS.actualLine,
                tension: 0.4,
            },
        ],
    };
});

const { isDark } = useTheme();

const chartOptions = computed(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            display: true,
            labels: {
                color: isDark.value ? "#94a3b8" : "#475569",
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
                    return value ? `Enheder: ${formatNumber(value)}` : null;
                },
            },
        },
    },
    scales: {
        x: {
            grid: { color: isDark.value ? "#334155" : "#cbd5e1" },
            ticks: { color: isDark.value ? "#94a3b8" : "#475569" },
        },
        y: {
            beginAtZero: true,
            grid: { color: isDark.value ? "#334155" : "#cbd5e1" },
            ticks: {
                color: isDark.value ? "#94a3b8" : "#475569",
                callback: function (value: any) {
                    return formatNumber(value);
                },
            },
        },
    },
}));
</script>

<style scoped>
.product-analytics-chart-container {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
}

.top-section {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-start;
    margin-bottom: 24px;
    gap: 16px;
}

.filter-section {
    flex: 0 0 auto;
    display: flex;
    justify-content: flex-start;
}

.filter-group {
    width: 100%;
    min-width: 200px;
}

.filter-select:hover {
    border-color: #cbd5e1;
}

.filter-select:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.summary-cards {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    flex: 1 1 auto;
}

.summary-card {
    flex: 1;
    min-width: 140px;
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
    .top-section {
        flex-direction: column;
    }

    .filter-section {
        width: 100%;
    }

    .filter-group {
        min-width: 100%;
    }

    .summary-cards {
        width: 100%;
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
