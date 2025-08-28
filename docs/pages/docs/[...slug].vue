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

            <TOC v-if="toc && toc.length" :toc="toc" />

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

const purePath = computed(() => {
    const p = route.path;
    return p !== "/" && p.endsWith("/") ? p.slice(0, -1) : p;
});

const { data: page } = await useAsyncData(
    () => `docs:${purePath.value}`,
    () => queryCollection("docs").path(purePath.value).first()
);

if (!page.value) {
    throw createError({ statusCode: 404, statusMessage: "Page not found" });
}

const { data: rawSurround } = await useAsyncData(
    () => `docs:${purePath.value}:surround`,
    () =>
        queryCollectionItemSurroundings("docs", purePath.value, {
            fields: ["title", "description", "path"]
        })
);

const surround = computed(() => {
    const list = (rawSurround.value || []) as Array<any | null>;
    return list.map((doc) =>
        doc && getDocType(doc.path || "") === $store.currentDocType ? doc : null
    );
});

const toc = computed(() => page.value?.body?.toc?.links || []);

useSeoMeta({
    title: `${page.value?.title} - ${titleSuffix}`,
    ogTitle: `${page.value?.title} - ${titleSuffix}`,
    description: page.value?.description,
    ogDescription: page.value?.description
});

const editLink = computed(() => {
    const repoBase = "https://github.com/MEGWARE-HPC/xbat";
    const branch = "master";

    const stem: string | undefined = (page.value as any)?.stem;
    const ext: string = ((page.value as any)?.extension || "md") as string;

    if (stem) {
        return `${repoBase}/blob/${branch}/docs/content/${stem}.${ext}`;
    }

    const id: string | undefined = (page.value as any)?.id;
    if (id) {
        const normalized = id.replace(/^docs\//, "");
        return `${repoBase}/blob/${branch}/docs/content/${normalized}`;
    }

    return `${repoBase}/blob/${branch}/docs/content/`;
});

async function scrollToHash(h?: string, tries = 8) {
    const raw = (h || route.hash || "").replace(/^#/, "");
    if (!raw) return;
    const candidates = [raw, decodeURIComponent(raw)];
    for (const id of candidates) {
        const el = document.getElementById(id);
        if (el) {
            el.scrollIntoView({ behavior: "smooth", block: "start" });
            return;
        }
    }
    if (tries > 0) {
        await nextTick();
        requestAnimationFrame(() => scrollToHash(raw, tries - 1));
    }
}

onMounted(() => {
    scrollToHash();
});

watch(
    () => route.hash,
    (h) => scrollToHash(h)
);
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
