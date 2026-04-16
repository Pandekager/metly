<template>
    <div class="product-table-container">
        <div class="table-header mb-4">
            <h2 class="text-xl font-semibold text-slate-900 dark:text-slate-100">
                Top sælgende produkter
            </h2>
            <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
                Viser {{ displayedProducts.length }} af {{ sortedProducts.length }} produkter
            </p>
        </div>

        <div class="overflow-x-auto">
            <table class="w-full">
                <thead>
                    <tr class="border-b border-slate-200 dark:border-slate-700">
                        <th
                            class="text-left py-3 px-4 text-sm font-semibold text-slate-700 dark:text-slate-300 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
                            @click="toggleSort('product_name')"
                        >
                            <div class="flex items-center gap-2">
                                Produkt
                                <SortIcon column="product_name" :current-sort="sortColumn" :direction="sortDirection" />
                            </div>
                        </th>
                        <th
                            class="text-left py-3 px-4 text-sm font-semibold text-slate-700 dark:text-slate-300 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
                            @click="toggleSort('subcategory_name')"
                        >
                            <div class="flex items-center gap-2">
                                Kategori
                                <SortIcon column="subcategory_name" :current-sort="sortColumn" :direction="sortDirection" />
                            </div>
                        </th>
                        <th
                            class="text-right py-3 px-4 text-sm font-semibold text-slate-700 dark:text-slate-300 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
                            @click="toggleSort('units_sold')"
                        >
                            <div class="flex items-center justify-end gap-2">
                                Solgt
                                <SortIcon column="units_sold" :current-sort="sortColumn" :direction="sortDirection" />
                            </div>
                        </th>
                        <th
                            class="text-right py-3 px-4 text-sm font-semibold text-slate-700 dark:text-slate-300 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
                            @click="toggleSort('total_revenue')"
                        >
                            <div class="flex items-center justify-end gap-2">
                                Omsætning
                                <SortIcon column="total_revenue" :current-sort="sortColumn" :direction="sortDirection" />
                            </div>
                        </th>
                        <th
                            class="text-right py-3 px-4 text-sm font-semibold text-slate-700 dark:text-slate-300 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
                            @click="toggleSort('order_count')"
                        >
                            <div class="flex items-center justify-end gap-2">
                                Ordrer
                                <SortIcon column="order_count" :current-sort="sortColumn" :direction="sortDirection" />
                            </div>
                        </th>
                    </tr>
                </thead>
                <tbody>
                    <tr
                        v-for="(product, index) in displayedProducts"
                        :key="product.product_id"
                        class="border-b border-slate-100 dark:border-slate-700/50 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                        :class="{ 'bg-slate-50/50 dark:bg-slate-800/25': index % 2 === 1 }"
                    >
                        <td class="py-3 px-4 text-sm text-slate-900 dark:text-slate-100">
                            {{ product.product_name }}
                        </td>
                        <td class="py-3 px-4 text-sm text-slate-600 dark:text-slate-400">
                            {{ product.subcategory_name || "-" }}
                        </td>
                        <td class="py-3 px-4 text-sm text-slate-900 dark:text-slate-100 text-right font-medium">
                            {{ formatNumber(product.units_sold) }}
                        </td>
                        <td class="py-3 px-4 text-sm text-slate-900 dark:text-slate-100 text-right font-medium">
                            {{ formatCurrency(product.total_revenue) }}
                        </td>
                        <td class="py-3 px-4 text-sm text-slate-600 dark:text-slate-400 text-right">
                            {{ formatNumber(product.order_count) }}
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div v-if="sortedProducts.length > displayLimit" class="mt-4 text-center">
            <button
                @click="showMore"
                class="px-4 py-2 text-sm font-medium text-metly-600 dark:text-metly-400 hover:text-metly-700 dark:hover:text-metly-300 transition-colors"
            >
                Vis flere produkter
            </button>
        </div>

        <div v-if="products.length === 0" class="text-center py-8">
            <p class="text-slate-500 dark:text-slate-400">
                Ingen produktdata tilgængelig
            </p>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, h, defineComponent } from "vue";
import type { ProductAnalytics } from "~/types/product";

const props = defineProps<{
    products: ProductAnalytics[];
}>();

const sortColumn = ref<keyof ProductAnalytics>("total_revenue");
const sortDirection = ref<"asc" | "desc">("desc");
const displayLimit = ref(10);

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

const sortedProducts = computed(() => {
    return [...props.products].sort((a, b) => {
        const aVal = a[sortColumn.value];
        const bVal = b[sortColumn.value];

        if (typeof aVal === "string" && typeof bVal === "string") {
            return sortDirection.value === "asc"
                ? aVal.localeCompare(bVal)
                : bVal.localeCompare(aVal);
        }

        if (typeof aVal === "number" && typeof bVal === "number") {
            return sortDirection.value === "asc" ? aVal - bVal : bVal - aVal;
        }

        return 0;
    });
});

const displayedProducts = computed(() => {
    return sortedProducts.value.slice(0, displayLimit.value);
});

const toggleSort = (column: keyof ProductAnalytics) => {
    if (sortColumn.value === column) {
        sortDirection.value = sortDirection.value === "asc" ? "desc" : "asc";
    } else {
        sortColumn.value = column;
        sortDirection.value = "desc";
    }
};

const showMore = () => {
    displayLimit.value += 10;
};

// SortIcon component
const SortIcon = defineComponent({
    props: {
        column: { type: String, required: true },
        currentSort: { type: String, required: true },
        direction: { type: String, required: true },
    },
    setup(props) {
        return () => {
            const isActive = props.column === props.currentSort;
            const isAsc = props.direction === "asc";

            if (!isActive) {
                return h("span", {
                    class: "text-slate-400 dark:text-slate-600",
                    innerHTML: `
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4"/>
                        </svg>
                    `,
                });
            }

            return h("span", {
                class: "text-metly-600 dark:text-metly-400",
                innerHTML: isAsc
                    ? `
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"/>
                        </svg>
                    `
                    : `
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                        </svg>
                    `,
            });
        };
    },
});
</script>

<style scoped>
.product-table-container {
    @apply w-full;
}

.table-header {
    @apply mb-4;
}

@media (max-width: 640px) {
    table {
        display: block;
        overflow-x: auto;
        white-space: nowrap;
    }

    th,
    td {
        min-width: 100px;
    }
}
</style>
