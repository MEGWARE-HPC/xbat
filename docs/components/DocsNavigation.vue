<template>
    <v-navigation-drawer
        v-model="$store.docsDrawerOpen"
        v-model:selected="selectedEntry"
        class="pl-2 pr-2"
        :permanent="windowWidth > 992"
        :temporary="windowWidth <= 992"
    >
        <template v-if="items">
            <div class="doc-type-header">
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
                color="primary-light"
                class="navigation mt-4"
                mandatory
                open-strategy="multiple"
            >
                <template v-for="item in items.children">
                    <v-list-item
                        v-if="!item.children?.length"
                        :key="`item-${item._path}`"
                        :title="item.title"
                        :value="item._path"
                        :to="item._path"
                        :id="`item-${encodeURIComponent(item._path)}`"
                        :class="{ 'active-doc': route.path === item._path }"
                        :aria-current="
                            route.path === item._path ? 'page' : undefined
                        "
                    ></v-list-item>

                    <v-list-group
                        v-else
                        :key="`group-${item._path}`"
                        :value="item._path"
                    >
                        <template v-slot:activator="{ props }">
                            <v-list-item
                                v-bind="props"
                                :title="item.title"
                                :id="`group-${encodeURIComponent(item._path)}`"
                            ></v-list-item>
                        </template>

                        <v-list-item
                            v-for="entry in item.children"
                            :key="`entry-${entry._path}`"
                            :title="entry.title"
                            :value="entry._path"
                            :to="entry._path"
                            :id="`entry-${encodeURIComponent(entry._path)}`"
                            :class="{
                                'active-doc': route.path === entry._path
                            }"
                            :aria-current="
                                route.path === entry._path ? 'page' : undefined
                            "
                        ></v-list-item>
                    </v-list-group>
                </template>
            </v-list>
        </template>
    </v-navigation-drawer>
</template>
<script setup lang="ts">
import type { NavItem } from "@nuxt/content";
import { useWindowSize } from "@vueuse/core";

const route = useRoute();
const { width: windowWidth } = useWindowSize();
const docStartingRoutes: Record<string, string> = {
    user: "/docs/user/introduction",
    admin: "/docs/admin/setup/installation",
    developer: "/docs/developer/contribute"
};
const { $store } = useNuxtApp();

const props = defineProps({
    links: {
        type: Object as PropType<NavItem[]>,
        required: true
    }
});

const selectedEntry = ref<string[] | null>(null);

const items: Ref<NavItem | null> = computed(() => {
    const categories =
        Array.isArray(props.links) && props.links[0]?.children
            ? props.links[0].children
            : [];
    const match = route.path.match(/^\/docs\/([a-zA-Z]+)\//);
    const currentCategory = match?.[1];
    const filtered = categories.filter((cat) =>
        cat._path.startsWith(`/docs/${currentCategory}`)
    );
    return filtered.length ? filtered[0] : null;
});

const docTypes = ["user", "admin", "developer"];

const currentIndex = computed(() => {
    const docType = $store.currentDocType;
    if (docType && docTypes.includes(docType)) {
        return docTypes.indexOf(docType);
    }
    return 0;
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
.doc-type-header {
    margin-top: 52px; // replaces mt-13
}
.doc-type-head {
    font-size: 1.125rem;
    text-align: center;
    text-transform: capitalize;
    letter-spacing: 0.009375em;
}
</style>
