<template>
    <v-navigation-drawer location="right" floating class="toc">
        <v-list
            v-model:selected="selectedTocEntry"
            mandatory
            variant="text"
            class="mt-10 ml-2 mr-2"
        >
            <v-list-subheader class="mb-3 subheader"
                >Table of Contents</v-list-subheader
            >
            <!-- use click handler instead of "to" because vuetify assumes all entries match the current route
         (which messes up the styling) since the shard is not respected -->
            <template v-for="link of props.toc">
                <v-list-item
                    class="toc-item"
                    :class="{ 'toc-sub-item': link.children?.includes(entry) }"
                    v-for="entry of [link, ...(link?.children || [])]"
                    :value="`${route.path}#${entry.id}`"
                    active-class="toc-active"
                    @click="() => router.push(`${route.path}#${entry.id}`)"
                    >{{ entry.text }}
                </v-list-item>
            </template>
        </v-list>
    </v-navigation-drawer>
</template>
<script setup lang="ts">
import type { TocLink } from "@nuxt/content";
const selectedTocEntry = ref<string[] | null>(null);
const route = useRoute();
const router = useRouter();

const props = defineProps<{
    toc: TocLink[];
}>();

watch(
    () => props.toc,
    () => {
        if (!selectedTocEntry.value && props.toc.length)
            selectedTocEntry.value = [`${route.path}#${props.toc[0].id}`];
    },
    { immediate: true }
);

let scrollTimeout: ReturnType<typeof setTimeout> | null = null;

const setActiveTocEntry = (hash: string) => {
    selectedTocEntry.value = [hash];
};

// TODO use debounce
const onScroll = (e: Event) => {
    if (typeof window === "undefined") return;

    const yScroll = window.scrollY || (e.target as HTMLElement).scrollTop || 0;

    for (let i = 0; i < headlinePositions.value.length; i++) {
        if (headlinePositions.value[i].y >= yScroll) {
            // use timeout workaround to prevent all entries from being selected when scrolling to bottom through hash link
            if (scrollTimeout) clearTimeout(scrollTimeout);

            scrollTimeout = setTimeout(() => {
                setActiveTocEntry(
                    `${route.path}#${headlinePositions.value[i].id}`
                );
            }, 100);

            break;
        }
    }
};

const headlinePositions = computed(() => {
    if (!props.toc.length) return [];

    const headlines = props.toc
        .map((link) => [link, ...(link?.children || [])])
        .flat();

    return headlines.map((link) => {
        const el = document.getElementById(link.id);

        return {
            id: link.id,
            y: el ? el.getBoundingClientRect().y : 0
        };
    });
});

onMounted(() => {
    window.addEventListener("scroll", onScroll);
});

onBeforeUnmount(() => {
    window.removeEventListener("scroll", onScroll);
});
</script>
<style scoped lang="scss">
@use "~/assets/css/colors.scss" as *;

.toc {
    :deep(.v-list-item__content) {
        font-size: 0.875rem;
        width: 100%;
    }

    :deep(.v-list-item) {
        color: $font-base;
        &.toc-active {
            color: $primary-light !important;
            background-color: unset !important;
        }
    }

    .toc-sub-item {
        :deep(.v-list-item__content) {
            padding-left: 20px;
        }
    }
}
</style>
