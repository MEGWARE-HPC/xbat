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
                    :value="`${route.path}#${link.id}`"
                    active-class="toc-active"
                    @click="go(link.id)"
                >
                    {{ link.text }}
                </v-list-item>
                <v-list-item
                    v-for="child in link.children || []"
                    :key="child.id"
                    class="toc-item toc-sub-item"
                    :value="`${route.path}#${child.id}`"
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
const router = useRouter();

const selectedTocEntry = ref<string[]>([]);

const MANUAL_LOCK_MS = 500;
let lastManualTs = 0;
function withManualLock(fn: () => void) {
    lastManualTs = Date.now();
    fn();
}

let suppressNextScroll = false;

async function scrollToId(id: string, attempts = 8) {
    const el = document.getElementById(id);
    if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
        return true;
    }
    if (attempts > 0) {
        await nextTick();
        await new Promise((r) => requestAnimationFrame(r));
        return scrollToId(id, attempts - 1);
    }
    return false;
}

async function selectAndScroll(id: string) {
    withManualLock(() => {
        selectedTocEntry.value = [`${route.path}#${id}`];
    });
    await scrollToId(id);
}

async function waitForEl(id: string, tries = 20) {
    while (tries-- > 0) {
        if (document.getElementById(id)) return true;
        await nextTick();
        await new Promise((r) => requestAnimationFrame(r));
    }
    return false;
}

async function go(id: string) {
    await waitForEl(id);
    suppressNextScroll = true;
    await router.replace({ path: route.path, hash: `#${id}` });
    withManualLock(() => {
        selectedTocEntry.value = [`${route.path}#${id}`];
    });
}

watch(
    () => route.hash,
    async (h) => {
        const id = (h || "").replace(/^#/, "");
        if (!id) return;

        if (suppressNextScroll) {
            suppressNextScroll = false;
            withManualLock(() => {
                selectedTocEntry.value = [`${route.path}#${id}`];
            });
            return;
        }

        await selectAndScroll(id);
    }
);

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
    if (Date.now() - lastManualTs < MANUAL_LOCK_MS) return;

    ticking = true;
    requestAnimationFrame(() => {
        ticking = false;
        const list = headlinePositions.value;
        if (!list.length) return;

        const cursor = window.scrollY + 100;

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
            const val = `${route.path}#${id}`;
            if (selectedTocEntry.value?.[0] !== val) {
                selectedTocEntry.value = [val];
            }
        }
    });
};

onMounted(async () => {
    if (process.server) return;

    const initialId =
        (route.hash || "").replace(/^#/, "") ||
        (props.toc && props.toc[0] ? props.toc[0].id : "");

    if (initialId) {
        await selectAndScroll(initialId);
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
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
