<template>
    <v-app>
        <TopBar />
        <NuxtLayout>
            <NuxtLoadingIndicator></NuxtLoadingIndicator>
            <NuxtPage />
        </NuxtLayout>
    </v-app>
</template>
<script lang="ts" setup>
useHead({
    htmlAttrs: {
        lang: "en",
        style: "font-size: 14px; font-family: 'Source Sans Pro', sans-serif;"
    }
});

const { data: nav } = await useAsyncData("navigation", () =>
    fetchContentNavigation()
);

provide("navigation", nav.value);
</script>
<style lang="scss">
@use "~/assets/css/general.scss" as *;
@use "~/assets/css/colors.scss" as *;

:root {
    scroll-padding-top: 65px;
    background-color: $background;
}
</style>
