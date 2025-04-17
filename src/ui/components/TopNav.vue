<template>
    <v-app-bar fixed density="compact" color="primary" class="app-bar">
        <template #prepend>
            <NuxtLink to="https://xbat.dev" target="_blank">
                <NuxtImg
                    src="/logo/xbat-logo-white.svg"
                    alt="xbat Logo"
                    width="40px"
                    class="logo"
                ></NuxtImg>
            </NuxtLink>
        </template>
        <v-tabs>
            <v-tab to="/" prepend-icon="$home">Benchmarks</v-tab>
            <v-tab to="/configurations" prepend-icon="$textBox"
                >Configurations</v-tab
            >
            <v-tab
                to="/projects"
                prepend-icon="$group"
                v-show="
                    $authStore.userLevel != $authStore.UserLevelEnum.guest &&
                    $authStore.userLevel != $authStore.UserLevelEnum.user
                "
                >Projects</v-tab
            >
            <v-tab
                prepend-icon="$accountGroup"
                to="/users"
                v-show="
                    $authStore.userLevel != $authStore.UserLevelEnum.guest &&
                    $authStore.userLevel != $authStore.UserLevelEnum.user
                "
                >Users</v-tab
            >
            <!-- must use ClientOnly as vuetify has an issue (?) with dynamic rendering of this slot -->
            <ClientOnly>
                <v-tab
                    :to="`/benchmarks/${$store.benchmarkNr}`"
                    v-show="$store.benchmarkNr"
                    >Benchmark #{{ $store.benchmarkNr }}</v-tab
                >
            </ClientOnly>
        </v-tabs>
        <template v-slot:append>
            <div class="d-flex align-center">
                <v-icon
                    v-if="$store.demo"
                    icon="$read"
                    size="small"
                    class="mr-2"
                    title="Read-only demo mode activated"
                ></v-icon>
                <v-btn
                    icon="$github"
                    href="https://github.com/MEGWARE-HPC/xbat/"
                    target="_blank"
                    title="Visit GitHub"
                ></v-btn>
                <MultiPageMenu
                    @update:theme="emit('update:theme', $event)"
                ></MultiPageMenu>
            </div>
        </template>
    </v-app-bar>
</template>

<script setup>
const { $store, $authStore } = useNuxtApp();
const emit = defineEmits(["update:theme"]);
</script>

<style scoped lang="scss">
@use "~/assets/css/colors.scss" as *;

.app-bar {
    .logo {
        position: absolute;
        left: 12.5px;
        top: 5px;
    }
    :deep(.v-toolbar__prepend) {
        margin-right: 20px;
        margin-left: 42.5px;
    }
}
</style>
