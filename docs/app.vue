<template>
    <v-app>
        <TopBar />
        <NuxtLayout>
            <NuxtLoadingIndicator />
            <NuxtPage />
        </NuxtLayout>
    </v-app>
</template>
<script lang="ts" setup>
import type { ContentNavigationItem } from "@nuxt/content";

useHead({
    htmlAttrs: {
        lang: "en",
        style: "font-size: 14px; font-family: 'Source Sans Pro', sans-serif;"
    }
});

async function fetchNavOf(collection: "docs" | "content") {
    try {
        return await queryCollectionNavigation(collection);
    } catch {
        return [];
    }
}

const { data: navDocs } = await useAsyncData<ContentNavigationItem[]>(
    "navigation-docs",
    () => fetchNavOf("docs")
);

const { data: navContent } = await useAsyncData<ContentNavigationItem[]>(
    "navigation-content",
    () => (navDocs.value?.length ? [] : fetchNavOf("content"))
);

const nav = computed<ContentNavigationItem[]>(
    () => (navDocs.value?.length ? navDocs.value : navContent.value) || []
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
