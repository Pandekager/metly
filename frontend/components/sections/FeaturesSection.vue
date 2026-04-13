<template>
    <section id="features" class="py-24 bg-white dark:bg-slate-900">
        <div class="max-w-7xl mx-auto px-6">
            <div class="text-center mb-16">
                <h2
                    class="text-4xl md:text-5xl font-bold text-slate-900 dark:text-slate-100 mb-4"
                >
                    Alt du skal bruge
                </h2>
                <p
                    class="text-xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto"
                >
                    Et komplet værktøj til at transformere dine data til
                    handling
                </p>
            </div>

            <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                <div
                    v-for="feature in features"
                    :key="feature.title"
                    class="card group dark:bg-slate-800 dark:border-slate-700"
                >
                    <div
                        class="w-14 h-14 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform"
                    >
                        <component
                            :is="feature.icon"
                            class="w-7 h-7 text-metly-600 dark:text-metly-400"
                        />
                    </div>
                    <h3
                        class="text-xl font-semibold text-slate-900 dark:text-slate-100 mb-3"
                    >
                        {{ feature.title }}
                    </h3>
                    <p class="text-slate-600 dark:text-slate-400">
                        {{ feature.description }}
                    </p>
                </div>
            </div>
        </div>
    </section>
</template>

<script setup lang="ts">
import {
    ChartBarIcon,
    SparklesIcon,
    LockClosedIcon,
    CloudIcon,
    BellIcon,
    ArrowTrendingUpIcon,
} from "@heroicons/vue/24/outline";

const features = [
    {
        title: "Avanceret Analyse",
        description:
            "Dybdegående analyse af dine salgsdata med maskinlæring for at identificere mønstre og trends.",
        icon: ChartBarIcon,
    },
    {
        title: "AI Drevet",
        description:
            "Automatisk generering af handlingsanbefalinger baseret på dine data og historiske resultater.",
        icon: SparklesIcon,
    },
    {
        title: "GDPR Kompilant",
        description:
            "Alle dine data behandles sikkert og overholder europæiske dataregler. Vores servere er i EU.",
        icon: LockClosedIcon,
    },
    {
        title: "Cloud Integration",
        description:
            "Sømløs integration med populære platforme som Shopify, WooCommerce og Google Ads.",
        icon: CloudIcon,
    },
    {
        title: "Real-time Alerts",
        description:
            "Få notifikationer når vigtige ændringer eller muligheder opstår i dine data.",
        icon: BellIcon,
    },
    {
        title: "Vækst Optimering",
        description:
            "Få konkrete forslag til at øge din konvertering og maksimere din indtjening.",
        icon: ArrowTrendingUpIcon,
    },
];
</script>
