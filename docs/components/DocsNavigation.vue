<template>
    <v-navigation-drawer
        v-model="$store.docsDrawerOpen"
        v-model:selected="selectedEntry"
        class="pl-2 pr-2"
        :permanent="windowWidth > 992"
        :temporary="windowWidth <= 992"
    >
        <template v-if="items">
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
                color="primary-light"
                class="navigation mt-4"
                mandatory
                open-strategy="multiple"
            >
                <template v-for="item of items.children" :key="item._path">
                    <v-list-item
                        v-if="!item.children?.length"
                        :key="`item-${item._path}`"
                        :title="item.title"
                        :value="item._path"
                        :to="item._path"
                        :id="`item-${encodeURIComponent(item._path)}`"
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
const docStartingRoutes: { [key: string]: string } = {
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

// only display docs of current category in navigation
const items: Ref<NavItem | null> = computed(() => {
    const categories = props.links?.[0]?.children || [];
    const regex = new RegExp(`^/docs/([a-zA-Z]+)/.*$`);
    const currentCategory = route.path.match(regex)?.[1];
    const filteredCategories = categories.filter((category) =>
        category._path.startsWith(`/docs/${currentCategory}`)
    );
    return filteredCategories.length ? filteredCategories[0] : null;
});

const docTypes = ["user", "admin", "developer"];

const currentIndex = computed(() => {
    return $store.currentDocType !== null
        ? docTypes.indexOf($store.currentDocType)
        : -1;
});

const nextIndex = computed(() => {
    return (currentIndex.value + 1) % docTypes.length;
});

const prevIndex = computed(() => {
    return (currentIndex.value - 1 + docTypes.length) % docTypes.length;
});

const nextDocType = computed(() => {
    return docTypes[nextIndex.value];
});

const prevDocType = computed(() => {
    return docTypes[prevIndex.value];
});
</script>
<style scoped lang="scss">
@use "~/assets/css/colors.scss" as *;
.navigation {
    :deep(.v-list-item-title) {
        font-size: 0.875rem;
    }
}
.doc-selection {
    :deep(.v-list-item-title) {
        font-size: 1rem;
        background-color: unset;
    }
    :deep(.v-list-item__overlay) {
        background-color: $background;
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
