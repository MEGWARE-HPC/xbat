<template>
    <ClientOnly>
        <v-navigation-drawer
            v-if="
                isClient && (!isMobile || items) && !(isMobile && isAboutOrDemo)
            "
            v-model="$store.docsDrawerOpen"
            v-model:selected="selectedEntry"
            class="pl-2 pr-2"
            :permanent="!isMobile"
            :temporary="isMobile"
        >
            <template v-if="items && !isAboutOrDemo">
                <div class="mt-13">
                    <div class="doc-type-head text-medium-emphasis">
                        {{ $store.currentDocType }} Documentation
                    </div>
                    <div class="d-flex align-center justify-center">
                        <v-btn
                            variant="plain"
                            :to="docStartingRoutes[prevDocType]"
                            prepend-icon="$arrowLeft"
                            :title="`Visit ${prevDocType} documentation`"
                            size="small"
                        >
                            {{ prevDocType }}
                        </v-btn>
                        <v-btn
                            variant="plain"
                            :to="docStartingRoutes[nextDocType]"
                            append-icon="$arrowRight"
                            :title="`Visit ${nextDocType} documentation`"
                            size="small"
                        >
                            {{ nextDocType }}
                        </v-btn>
                    </div>
                </div>
                <v-list
                    v-model:selected="selectedEntry"
                    color="primary-light"
                    class="navigation mt-4"
                    mandatory
                    open-strategy="multiple"
                >
                    <template v-for="item in items.children" :key="item.path">
                        <v-list-item
                            v-if="!item.children?.length"
                            :key="`item-${item.path}`"
                            :title="item.title"
                            :value="item.path"
                            :to="item.path"
                            :id="`item-${encodeURIComponent(item.path)}`"
                            :class="{ 'active-doc': route.path === item.path }"
                            :aria-current="
                                route.path === item.path ? 'page' : undefined
                            "
                        />

                        <v-list-group
                            v-else
                            :key="`group-${item.path}`"
                            :value="item.path"
                        >
                            <template #activator="{ props }">
                                <v-list-item
                                    v-bind="props"
                                    :title="item.title"
                                    :id="`group-${encodeURIComponent(item.path)}`"
                                />
                            </template>

                            <v-list-item
                                v-for="entry in item.children"
                                :key="`entry-${entry.path}`"
                                :title="entry.title"
                                :value="entry.path"
                                :to="entry.path"
                                :id="`entry-${encodeURIComponent(entry.path)}`"
                                :class="{
                                    'active-doc': route.path === entry.path
                                }"
                                :aria-current="
                                    route.path === entry.path
                                        ? 'page'
                                        : undefined
                                "
                            />
                        </v-list-group>
                    </template>
                </v-list>
            </template>
        </v-navigation-drawer>
    </ClientOnly>
</template>
<script setup lang="ts">
import type { ContentNavigationItem } from "@nuxt/content";
import { useWindowSize } from "@vueuse/core";

const route = useRoute();
const { $store } = useNuxtApp();

const isClient = ref(false);
const isMobile = ref(false);

if (import.meta.client) {
    isClient.value = true;
    const { width } = useWindowSize();
    watchEffect(() => {
        isMobile.value = width.value <= 992;
    });
}

const isAboutOrDemo = computed(
    () =>
        route.path.startsWith("/docs/about") ||
        route.path.startsWith("/docs/demo")
);

const docStartingRoutes: Record<string, string> = {
    user: "/docs/user/introduction",
    admin: "/docs/admin/setup/installation",
    developer: "/docs/developer/contribute"
};

async function fetchNavOf(collection: "docs" | "content") {
    try {
        return await queryCollectionNavigation(collection);
    } catch {
        return [];
    }
}

const { data: navDocs } = await useAsyncData<ContentNavigationItem[]>(
    "nav-docs",
    () => fetchNavOf("docs")
);
const { data: navContent } = await useAsyncData<ContentNavigationItem[]>(
    "nav-content",
    () => (navDocs.value?.length ? [] : fetchNavOf("content"))
);

const nav = computed<ContentNavigationItem[]>(
    () => (navDocs.value?.length ? navDocs.value : navContent.value) || []
);

function findNodeByPath(
    nodes: ContentNavigationItem[] | undefined,
    target: string
): ContentNavigationItem | null {
    if (!nodes) return null;
    for (const n of nodes) {
        if (n.path === target) return n;
        const child = findNodeByPath(n.children as any, target);
        if (child) return child;
    }
    return null;
}

function filterOutAboutDemo(
    nodes?: ContentNavigationItem[]
): ContentNavigationItem[] {
    if (!nodes) return [];
    const shouldDrop = (p?: string) =>
        !!p && (p.startsWith("/about") || p.startsWith("/demo"));
    const walk = (list: ContentNavigationItem[]): ContentNavigationItem[] =>
        list
            .filter((n) => !shouldDrop(n.path))
            .map((n) => ({
                ...n,
                children: n.children ? walk(n.children as any) : n.children
            }));
    return walk(nodes);
}

const docsRoot = computed<ContentNavigationItem | null>(() => {
    const root = findNodeByPath(nav.value, "/docs");
    if (root) {
        const cloned: ContentNavigationItem = {
            ...root,
            children: filterOutAboutDemo(root.children as any)
        };
        return cloned;
    }

    const all: ContentNavigationItem[] = [];
    const walk = (nodes?: ContentNavigationItem[]) => {
        if (!nodes) return;
        for (const n of nodes) {
            if (
                n.path?.startsWith("/docs/about") ||
                n.path?.startsWith("/docs/demo")
            )
                continue;
            all.push(n);
            walk(n.children as any);
        }
    };
    walk(nav.value);

    const buckets: Record<string, ContentNavigationItem> = {};
    for (const n of all) {
        if (!n.path?.startsWith("/docs/")) continue;
        const seg = n.path.split("/")[2];
        if (!seg) continue;
        if (!buckets[seg]) {
            buckets[seg] = {
                title: seg,
                path: `/docs/${seg}`,
                children: []
            } as any;
        }
        if (n.path.split("/").length === 4 || !n.children?.length) {
            buckets[seg].children!.push(n as any);
        }
    }

    const children = Object.values(buckets);
    if (!children.length) return null;
    return { title: "Docs", path: "/docs", children } as any;
});

const items = computed<ContentNavigationItem | null>(() => {
    const root = docsRoot.value;
    if (!root?.children?.length) return null;
    const match = route.path.match(/^\/docs\/([a-zA-Z]+)\//);
    const currentCategory = match?.[1];
    if (!currentCategory) return root;
    const hit = root.children!.find((c) =>
        c.path?.startsWith(`/docs/${currentCategory}`)
    );
    return (hit as any) || root;
});

const selectedEntry = ref<string[]>([]);

watch(
    () => route.path,
    (p) => (selectedEntry.value = [p]),
    { immediate: true }
);

const docTypes = ["user", "admin", "developer"];

const currentIndex = computed(() => {
    const docType = $store.currentDocType;
    return docType && docTypes.includes(docType)
        ? docTypes.indexOf(docType)
        : 0;
});

const nextIndex = computed(() => (currentIndex.value + 1) % docTypes.length);
const prevIndex = computed(
    () => (currentIndex.value - 1 + docTypes.length) % docTypes.length
);

const nextDocType = computed(() => docTypes[nextIndex.value]);
const prevDocType = computed(() => docTypes[prevIndex.value]);
</script>
<style scoped lang="scss">
@use "~/assets/css/colors.scss" as *;
.navigation {
    :deep(.v-list-item-title) {
        font-size: 0.875rem;
    }
}
.active-doc {
    color: $primary-light;
    :deep(.v-list-item-title) {
        font-weight: 600;
    }
}
.doc-type-head {
    font-size: 1.125rem;
    text-align: center;
    text-transform: capitalize;
    letter-spacing: 0.009375em;
}
</style>
