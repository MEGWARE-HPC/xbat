<template>
    <div>
        <v-app-bar :elevation="2" color="primary">
            <template #prepend>
                <div class="d-flex align-center">
                    <NuxtLink to="/">
                        <NuxtImg
                            src="/logo/xbat-logo-white.svg"
                            alt="xbat Logo"
                            width="40px"
                            class="ml-5"
                        ></NuxtImg>
                    </NuxtLink>
                    <span style="font-size: 1rem" class="hide-sm"> XBAT </span>
                </div>
            </template>

            <v-app-bar-title>
                <div class="d-flex">
                    <v-btn append-icon="$chevronDown">
                        Documentation

                        <v-menu activator="parent" location="end">
                            <v-list>
                                <v-list-item
                                    title="User"
                                    subtitle="Benchmarking with xbat"
                                    value="user"
                                    to="/docs/user/introduction"
                                    :active="$store.currentDocType === 'user'"
                                ></v-list-item>
                                <v-list-item
                                    title="Admin"
                                    subtitle="Installation and Maintenance"
                                    value="admin"
                                    to="/docs/admin/setup/installation"
                                    :active="$store.currentDocType === 'admin'"
                                ></v-list-item>
                                <v-list-item
                                    title="Developer"
                                    subtitle="Contributing to xbat"
                                    value="developer"
                                    to="/docs/developer/contribute"
                                    :active="
                                        $store.currentDocType === 'developer'
                                    "
                                ></v-list-item>
                            </v-list>
                        </v-menu>
                    </v-btn>
                    <v-btn to="/docs/about">About</v-btn>
                    <v-btn to="/docs/demo" class="hide-sm">Demo</v-btn>
                </div>
            </v-app-bar-title>

            <template #append>
                <div class="d-flex align-center">
                    <div class="hide-sm">
                        <v-text-field
                            placeholder="Search..."
                            hide-details
                            prepend-inner-icon="$magnify"
                            width="200"
                            class="mr-3"
                            @update:focused="searchDialog = true"
                        >
                            <template #append-inner
                                ><span class="search-info">
                                    CTRL+K
                                </span></template
                            >
                        </v-text-field>
                    </div>
                    <div class="hide-sm">
                        <v-btn
                            size="large"
                            href="https://www.megware.com/en/products/xbat"
                            target="_blank"
                        >
                            <NuxtImg
                                src="/logo/megware-logo-white.svg"
                                alt="Megware logo"
                                width="70px"
                                title="Visit MEGWARE"
                            ></NuxtImg>
                        </v-btn>
                        <v-btn
                            icon="$github"
                            size="large"
                            href="https://github.com/MEGWARE-HPC/xbat"
                            target="_blank"
                            title="Visit GitHub"
                        ></v-btn>
                    </div>
                    <v-btn
                        icon="$menu"
                        v-if="
                            windowWidth <= 992 &&
                            route.path.startsWith('/docs') &&
                            route.path !== '/docs/about'
                        "
                        @click="$store.docsDrawerOpen = !$store.docsDrawerOpen"
                    ></v-btn>
                </div>
            </template>
        </v-app-bar>
        <Search v-model="searchDialog"></Search>
    </div>
</template>
<script setup lang="ts">
import { useWindowSize } from "@vueuse/core";

const searchDialog = ref(false);
const { width: windowWidth } = useWindowSize();

const { $store } = useNuxtApp();

const route = useRoute();
</script>
<style lang="scss" scoped>
.search-info {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.5);
    white-space: nowrap;
}

@media (max-width: 1200px) {
    .search {
        display: none;
    }
}

@media (max-width: 992px) {
    .hide-sm {
        display: none;
    }
}
</style>
