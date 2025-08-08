<template>
    <div>
        <div class="docs">
            <ContentDoc v-slot="{ doc }" :components="{ NuxtImg }">
                <h1 class="content-title">{{ doc.title }}</h1>

                <h2 class="content-subtitle">
                    {{ doc.description }}
                </h2>

                <v-divider class="mb-5 mt-3"></v-divider>

                <ContentRenderer
                    v-if="page?.body"
                    class="content"
                    :value="doc"
                    :components="{ NuxtImg }"
                >
                </ContentRenderer>
            </ContentDoc>
            <div class="mt-6">
                <v-divider></v-divider>
                <div class="d-flex justify-space-between flex-wrap">
                    <div class="footer-nav mt-4">
                        <v-btn
                            prepend-icon="$arrowLeft"
                            variant="plain"
                            class="text-left"
                            style="text-transform: none"
                            :to="surround[0]._path"
                            v-if="surround?.[0]"
                            size="large"
                        >
                            <div>
                                <p>
                                    {{ surround[0].title }}
                                </p>
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
                            :to="surround[1]._path"
                            v-if="surround?.[1]"
                            size="large"
                        >
                            <div>
                                <p>
                                    {{ surround[1].title }}
                                </p>
                                <p>
                                    {{ surround[1].description }}
                                </p>
                            </div>
                        </v-btn>
                    </div>
                </div>
            </div>
            <TOC :toc="toc"></TOC>
            <div class="d-flex align-center text-medium-emphasis mt-6">
                Edit this Page on
                <NuxtLink
                    :to="`https://github.com/MEGWARE-HPC/xbat/tree/master/docs/content/${page?._file}`"
                    target="_blank"
                >
                    <span class="font-weight-bold ml-1">GitHub</span>
                    <v-icon
                        class="ml-1"
                        size="x-small"
                        icon="$linkExternal"
                    ></v-icon>
                </NuxtLink>
            </div>
        </div>
    </div>
</template>
<script setup lang="ts">
import { NuxtImg } from "#components";
import type { ParsedContentInternalMeta } from "@nuxt/content";
import { getDocType } from "~/helper";

const titleSuffix =
    "xbat documentation - HPC application benchmarking and optimization tool";

definePageMeta({
    layout: "docs"
});

const route = useRoute();
const { $store } = useNuxtApp();

const { data: page } = await useAsyncData(`docs-${route.path}`, () =>
    queryContent().where({ _path: route.path }).findOne()
);

if (!page.value) {
    throw createError({ statusCode: 404, statusMessage: "Page not found" });
}

const { data: surround } = await useAsyncData(
    `docs-${route.path}-surround`,
    () => {
        return queryContent().findSurround(
            route.path.endsWith("/") ? route.path.slice(0, -1) : route.path
        );
    },
    {
        transform(surround) {
            return surround.map((doc: ParsedContentInternalMeta) =>
                getDocType(doc._path || "") === $store.currentDocType
                    ? doc
                    : null
            );
        }
    }
);

const toc = computed(() => page.value?.body?.toc?.links || []);

useSeoMeta({
    title: `${page.value.title} - ${titleSuffix}`,
    ogTitle: `${page.value.title} - ${titleSuffix}`,
    description: page.value.description,
    ogDescription: page.value.description
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
    // TODO make sure justify-space-between works even with only one button
    min-width: 1px;
    min-height: 1px;
    p:nth-of-type(2) {
        font-size: 0.875rem;
    }
}
</style>
