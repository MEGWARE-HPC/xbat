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
                    <template
                        v-for="[idx, docType] of ['user', 'admin', 'developer']
                            .filter((x) => x != $store.currentDocType)
                            .entries()"
                    >
                        <v-btn
                            variant="plain"
                            :to="docStartingRoutes[docType]"
                            :prepend-icon="idx == 0 ? '$arrowLeft' : ''"
                            :append-icon="idx == 1 ? '$arrowRight' : ''"
                            :title="`Visit ${docType} documentation`"
                            size="small"
                            >{{ docType }}</v-btn
                        ></template
                    >
                </div>
            </div>
            <v-list
                color="primary-light"
                class="navigation mt-4"
                mandatory
                open-strategy="multiple"
            >
                <template v-for="item of items.children">
                    <v-list-item
                        v-if="!item.children?.length"
                        :title="item.title"
                        :value="item._path"
                        :to="item._path"
                    >
                    </v-list-item>
                    <v-list-group v-else :value="item._path">
                        <template v-slot:activator="{ props }">
                            <v-list-item
                                v-bind="props"
                                :title="item.title"
                            ></v-list-item>
                        </template>

                        <v-list-item
                            v-for="entry of item.children"
                            :title="entry.title"
                            :value="entry._path"
                            :to="entry._path"
                        >
                        </v-list-item>
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
