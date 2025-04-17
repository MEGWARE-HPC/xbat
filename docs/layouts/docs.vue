<template>
    <div>
        <DocsNavigation :links="navigation || []"></DocsNavigation>
        <v-main>
            <div class="pl-8 pr-8 pt-8 pb-8">
                <slot></slot>
            </div>
        </v-main>
    </div>
</template>

<script setup lang="ts">
import type { NavItem } from "@nuxt/content";

const navigation = inject<NavItem[]>("navigation");
</script>
