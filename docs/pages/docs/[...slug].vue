<template>
    <div>
        <div class="docs">
            <h1 class="content-title">{{ page?.title }}</h1>

            <h2 class="content-subtitle">
                {{ page?.description }}
            </h2>

            <v-divider class="mb-5 mt-3"></v-divider>

            <ContentRenderer
                v-if="page?.body"
                class="content"
                :value="page"
                :components="{ NuxtImg }"
            />

            <div class="mt-6">
                <v-divider></v-divider>
                <div class="d-flex justify-space-between flex-wrap">
                    <div class="footer-nav mt-4">
                        <v-btn
                            prepend-icon="$arrowLeft"
                            variant="plain"
                            class="text-left"
                            style="text-transform: none"
                            :to="surround?.[0]?.path"
                            v-if="surround?.[0]"
                            size="large"
                        >
                            <div>
                                <p>{{ surround[0].title }}</p>
                                <p>{{ surround[0].description }}</p>
                            </div>
                        </v-btn>
                    </div>
                    <div class="footer-nav mt-4">
                        <v-btn
                            append-icon="$arrowRight"
                            variant="plain"
                            class="text-right"
                            style="text-transform: none"
                            :to="surround?.[1]?.path"
                            v-if="surround?.[1]"
                            size="large"
                        >
                            <div>
                                <p>{{ surround[1].title }}</p>
                                <p>{{ surround[1].description }}</p>
                            </div>
                        </v-btn>
                    </div>
                </div>
            </div>

            <TOC :toc="toc" />

            <div class="d-flex align-center text-medium-emphasis mt-6">
                Edit this Page on
                <NuxtLink :to="editLink" target="_blank" v-if="editLink">
                    <span class="font-weight-bold ml-1">GitHub</span>
                    <v-icon class="ml-1" size="x-small" icon="$linkExternal" />
                </NuxtLink>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { NuxtImg } from "#components";
import { getDocType } from "~/helper";

const titleSuffix =
    "xbat documentation - HPC application benchmarking and optimization tool";

definePageMeta({ layout: "docs" });

const route = useRoute();
const { $store } = useNuxtApp();

const { data: page } = await useAsyncData(
    () => `docs:${route.fullPath}`,
    () => queryCollection("content").path(route.fullPath).first()
);

if (!page.value) {
    throw createError({ statusCode: 404, statusMessage: "Page not found" });
}

const normalizedPath = route.path.endsWith("/")
    ? route.path.slice(0, -1)
    : route.path;

const { data: surround } = await useAsyncData(
    () => `docs:${normalizedPath}:surround`,
    () =>
        queryCollectionItemSurroundings("content", normalizedPath, {
            fields: ["title", "description", "path"]
        }),
    {
        transform(list: Array<any | null>) {
            return list.map((doc) =>
                doc && getDocType(doc.path || "") === $store.currentDocType
                    ? doc
                    : null
            );
        }
    }
);

const toc = computed(() => page.value?.body?.toc?.links || []);

useSeoMeta({
    title: `${page.value?.title} - ${titleSuffix}`,
    ogTitle: `${page.value?.title} - ${titleSuffix}`,
    description: page.value?.description,
    ogDescription: page.value?.description
});

const editLink = computed(() => {
    const fileFromSource =
        (page.value as any)?.source?.filePath ||
        (page.value as any)?.file ||
        (page.value as any)?._file;

    if (fileFromSource) {
        return `https://github.com/MEGWARE-HPC/xbat/tree/master/docs/${fileFromSource}`;
    }

    const guess =
        "content" +
        (page.value?.path?.endsWith("/")
            ? `${page.value?.path}index.md`
            : `${page.value?.path}.md`);

    return `https://github.com/MEGWARE-HPC/xbat/tree/master/docs/${guess}`;
});
</script>
<style scoped lang="scss">
@use "~/assets/css/colors.scss" as *;

.content-title {
    font-size: 2rem;
}

.content-subtitle {
    color: $font-light;
    font-weight: 400;
    font-size: 1.25rem;
}

.footer-nav {
    /* TODO make sure justify-space-between works even with only one button */
    min-width: 1px;
    min-height: 1px;
    p:nth-of-type(2) {
        font-size: 0.875rem;
    }
}
</style>
