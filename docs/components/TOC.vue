<template>
    <v-navigation-drawer
        v-if="props.toc && props.toc.length"
        location="right"
        floating
        class="toc"
    >
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
            <template v-for="link in props.toc" :key="link.id">
                <v-list-item
                    class="toc-item"
                    :value="`${basePath}#${link.id}`"
                    active-class="toc-active"
                    @click="go(link.id)"
                >
                    {{ link.text }}
                </v-list-item>
                <v-list-item
                    v-for="child in link.children || []"
                    :key="child.id"
                    class="toc-item toc-sub-item"
                    :value="`${basePath}#${child.id}`"
                    active-class="toc-active"
                    @click="go(child.id)"
                >
                    {{ child.text }}
                </v-list-item>
            </template>
        </v-list>
    </v-navigation-drawer>
</template>
<script setup lang="ts">
type TocEntry = { id: string; text: string; children?: TocEntry[] };

const props = defineProps<{ toc?: TocEntry[] }>();

const route = useRoute();
const basePath = computed(() => route.path);

const selectedTocEntry = ref<string[]>([]);

const HEADER_OFFSET = 70; // Consider the height of the TopBar

function getScrollTopFor(el: Element) {
    const rect = el.getBoundingClientRect();
    return rect.top + window.scrollY - HEADER_OFFSET;
}

async function waitForEl(id: string, tries = 40) {
    while (tries-- > 0) {
        const el = process.client ? document.getElementById(id) : null;
        if (el) return el;
        await nextTick();
        await new Promise((r) => requestAnimationFrame(r));
    }
    return null;
}

async function scrollToIdExact(id: string, smooth = true) {
    if (process.server) return false;
    const el = await waitForEl(id);
    if (!el) return false;
    const top = getScrollTopFor(el);
    window.scrollTo({ top, behavior: smooth ? "smooth" : "auto" });
    return true;
}

async function go(id: string) {
    selectedTocEntry.value = [`${basePath.value}#${id}`];

    const url = `${basePath.value}#${id}`;
    history.replaceState(history.state, "", url);

    const tries = [0, 50, 160, 320]; // ms
    for (const t of tries) {
        if (t) await new Promise((r) => setTimeout(r, t));
        await scrollToIdExact(id, true); // ALWAYS smooth
    }
}

const headlinePositions = computed(() => {
    if (process.server || !props.toc || !props.toc.length) return [];
    const flat: TocEntry[] = props.toc
        .map((l) => [l, ...(l.children || [])])
        .flat();
    return flat.map((link) => {
        const el = document.getElementById(link.id);
        const top = el ? el.getBoundingClientRect().top + window.scrollY : 0;
        return { id: link.id, top };
    });
});

let ticking = false;
const onScroll = () => {
    if (ticking || process.server) return;

    ticking = true;
    requestAnimationFrame(() => {
        ticking = false;
        const list = headlinePositions.value;
        if (!list.length) return;

        const cursor = window.scrollY + 50;
        let idx = list.findIndex((p) => p.top >= cursor);
        if (idx === -1) idx = list.length - 1;
        if (
            idx > 0 &&
            Math.abs(list[idx].top - cursor) >
                Math.abs(list[idx - 1].top - cursor)
        ) {
            idx = idx - 1;
        }
        const id = list[idx]?.id;
        if (id) {
            const val = `${basePath.value}#${id}`;
            if (selectedTocEntry.value?.[0] !== val) {
                selectedTocEntry.value = [val];
            }
        }
    });
};

onMounted(() => {
    if (process.server) return;
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });

    const initId = (location.hash || "").replace(/^#/, "");
    if (initId) {
        selectedTocEntry.value = [`${basePath.value}#${initId}`];
        requestAnimationFrame(() => scrollToIdExact(initId));
    }

    requestAnimationFrame(onScroll);
});

onBeforeUnmount(() => {
    if (process.server) return;
    window.removeEventListener("scroll", onScroll);
    window.removeEventListener("resize", onScroll);
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
