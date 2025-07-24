<template>
    <v-app :theme="theme">
        <TopNav v-if="isAuthenticated" @update:theme="theme = $event"></TopNav>
        <NuxtLoadingIndicator></NuxtLoadingIndicator>
        <NuxtLayout>
            <NuxtPage />
        </NuxtLayout>
        <v-dialog
            :model-value="!!$store.error"
            @update:model-value="$store.error = null"
            max-width="600px"
        >
            <v-card>
                <v-card-title>
                    Error {{ $store.error?.status }} -
                    {{ $store.error?.title }}
                </v-card-title>
                <v-card-text>
                    <v-container>{{
                        $store.error?.message || $store.error?.detail
                    }}</v-container>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn color="grey" text @click="$store.error = null">
                        OK
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
        <div class="build-info text-medium-emphasis text-caption">
            v{{ runtimeConfig.public.buildVersion }}
        </div>
        <ClientOnly>
            <VLayoutItem
                model-value
                position="bottom"
                class="text-end"
                size="auto"
                v-show="state.showScrollToTop"
                v-scroll="onScroll"
                style="pointer-events: none"
            >
                <div class="ma-4">
                    <VBtn
                        style="pointer-events: all"
                        icon="$chevronUp"
                        color="primary"
                        elevation="8"
                        @click="toTop"
                    />
                </div>
            </VLayoutItem>
        </ClientOnly>
        <Snackbar></Snackbar>
    </v-app>
</template>

<script setup>
import "~/utils/array"; // for Array.prototype functions
import "~/utils/object"; // for Object.prototype functions

const { $store, $authStore } = useNuxtApp();

// TODO cookies should be synchonized as per https://github.com/nuxt/nuxt/pull/20970
// but this is somehow not working here (and with graph settings)
// remove update:theme emit when fixed
const theme = useCookie("xbat_theme", { default: () => "light" });

const state = reactive({
    showScrollToTop: false
});

const { isAuthenticated } = storeToRefs($authStore);

const runtimeConfig = useRuntimeConfig();

const onScroll = (e) => {
    if (typeof window === "undefined") return;
    state.showScrollToTop = (window.scrollY || e.target.scrollTop || 0) > 100;
};

const toTop = () => {
    window.scrollTo({
        top: 0,
        left: 0,
        behavior: "smooth"
    });
};
</script>

<style lang="scss">
@use "~/assets/css/general.scss" as *;
@use "~/assets/css/editor-themes.scss" as *;
@use "~/assets/css/colors.scss" as *;

:root {
    font-size: 16px;
    font-family: "Source Sans Pro", sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    font-style: normal;
    color: $font-base;

    caret-color: $font-base;

    .build-info {
        height: 25px;
        cursor: default;
        position: absolute;
        bottom: 0px;
        right: 10px;
    }
}
</style>
