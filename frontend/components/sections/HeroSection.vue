<template>
    <section
        id="hero"
        class="min-h-screen flex items-center relative overflow-hidden bg-gradient-to-br from-slate-50 via-blue-50 to-cyan-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900"
    >
        <!-- Background Elements -->
        <div class="absolute inset-0 opacity-30">
            <div
                class="absolute top-20 left-10 w-72 h-72 bg-metly-400 rounded-full mix-blend-multiply filter blur-3xl animate-pulse"
            ></div>
            <div
                class="absolute bottom-20 right-10 w-72 h-72 bg-cyan-400 rounded-full mix-blend-multiply filter blur-3xl animate-pulse"
                style="animation-delay: 2s"
            ></div>
        </div>

        <div class="max-w-7xl mx-auto px-6 py-24 relative z-10">
            <div class="grid lg:grid-cols-2 gap-12 items-center">
                <div class="space-y-8 animate-slide-up">
                    <h1
                        class="text-5xl sm:text-6xl lg:text-7xl font-bold text-slate-900 dark:text-slate-100 leading-tight"
                    >
                        Fra data til
                        <span class="gradient-text">handling</span>
                    </h1>
                    <p
                        class="text-xl text-slate-600 dark:text-slate-300 leading-relaxed"
                    >
                        Metly hjælper webshops med at træffe bedre beslutninger
                        baseret på data - helt automatisk. Vi samler og
                        analyserer dine data for dig og omdanner dem til
                        konkrete anbefalinger.
                    </p>
                    <p class="text-slate-900 dark:text-slate-100">
                        <b>Få 30 dage gratis på vores regning!</b>
                    </p>
                    <div class="flex flex-col sm:flex-row gap-4">
                        <NuxtLink
                            to="/signup"
                            class="btn-primary text-center px-8 py-4 text-lg shadow-lg shadow-metly-500/20 hover:shadow-metly-500/40 transition-all duration-300"
                        >
                            Kom i gang
                        </NuxtLink>
                        <button
                            @click="handleDemoLogin"
                            :disabled="isLoading"
                            class="btn-tertiary text-center flex items-center justify-center gap-2 px-8 py-4 text-lg bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border border-slate-200 dark:border-slate-700 hover:bg-white dark:hover:bg-slate-800 transition-all duration-300"
                        >
                            <template v-if="isLoading">
                                <svg
                                    class="animate-spin h-5 w-5 text-metly-600 dark:text-metly-400"
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
                                <span class="text-slate-900 dark:text-slate-100"
                                    >Starter demo...</span
                                >
                            </template>
                            <template v-else> Prøv demo </template>
                        </button>
                    </div>
                    <p v-if="errorMessage" class="text-red-500 text-sm">
                        {{ errorMessage }}
                    </p>

                    <!-- Trust indicators -->
                    <div
                        class="pt-8 border-t border-slate-200 dark:border-slate-700"
                    >
                        <p
                            class="text-sm text-slate-500 dark:text-slate-400 mb-4"
                        >
                            Kompatible med
                        </p>
                        <div class="flex items-center space-x-8 opacity-60">
                            <span
                                class="font-semibold text-slate-700 dark:text-slate-300"
                                >Shopify</span
                            >
                            <span
                                class="font-semibold text-slate-700 dark:text-slate-300"
                                >DanDomain</span
                            >
                            <span
                                class="font-semibold text-slate-700 dark:text-slate-300 italic"
                                >Og flere hver dag...</span
                            >
                        </div>
                    </div>
                </div>

                <div
                    class="relative animate-fade-in"
                    style="animation-delay: 0.3s"
                >
                    <div
                        class="bg-white dark:bg-slate-800 rounded-3xl shadow-2xl p-8 border border-slate-100 dark:border-slate-700"
                    >
                        <div class="space-y-6">
                            <div class="flex items-center justify-between">
                                <h3
                                    class="text-lg font-semibold text-slate-900 dark:text-slate-100 italic"
                                >
                                    Eksempel: Ordre Prognoser
                                </h3>
                                <span class="text-sm text-metly-600 font-medium"
                                    >Opdateret dagligt</span
                                >
                            </div>
                            <div
                                class="h-48 bg-gradient-to-br from-metly-50 to-blue-50 dark:from-slate-700 dark:to-slate-600 rounded-xl p-4"
                            >
                                <ChartsDemoChart />
                            </div>
                            <div class="grid grid-cols-2 gap-4">
                                <div
                                    class="bg-slate-50 dark:bg-slate-700 rounded-lg p-4"
                                >
                                    <p
                                        class="text-sm text-slate-500 dark:text-slate-400"
                                    >
                                        Næste måned
                                    </p>
                                    <p
                                        class="text-2xl font-bold text-metly-600"
                                    >
                                        +24%
                                    </p>
                                </div>
                                <div
                                    class="bg-slate-50 dark:bg-slate-700 rounded-lg p-4"
                                >
                                    <p
                                        class="text-sm text-slate-500 dark:text-slate-400"
                                    >
                                        Konfidens
                                    </p>
                                    <p
                                        class="text-2xl font-bold text-green-600"
                                    >
                                        95%
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>
</template>

<script setup lang="ts">
const router = useRouter();
const authStore = useAuthStore();

const isLoading = ref(false);
const errorMessage = ref("");

const handleDemoLogin = async () => {
    if (isLoading.value) return;

    isLoading.value = true;
    errorMessage.value = "";

    try {
        const response = await $fetch("/api/auth/login", {
            method: "POST",
            body: {
                email: "demo@metly.dk",
                password: "demo",
            },
        });

        if (response.success) {
            authStore.setUser(response.user);
            await router.push("/home");
        }
    } catch (error: any) {
        console.error("Demo login error:", error);
        errorMessage.value =
            error?.data?.message || error?.message || "Demo login mislykkedes";
    } finally {
        isLoading.value = false;
    }
};
</script>
