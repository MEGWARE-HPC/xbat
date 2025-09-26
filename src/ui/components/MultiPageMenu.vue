<template>
    <div>
        <v-menu :close-on-content-click="false" location="bottom">
            <template v-slot:activator="{ props }">
                <v-btn v-bind="props" append-icon="$menu">
                    {{ $authStore.userName }}
                </v-btn>
            </template>
            <v-card min-width="350">
                <v-list>
                    <v-list-item
                        @click="dark = !dark"
                        v-bind:title.attr="'Activate dark mode'"
                    >
                        <template #prepend
                            ><v-icon
                                size="small"
                                icon="$themeLightDark"
                            ></v-icon
                        ></template>
                        <div class="d-flex align-center">
                            <div>Dark mode</div>
                            <v-spacer></v-spacer>
                            <div>
                                <v-switch v-model="dark" class="menu-switch">
                                </v-switch>
                            </div>
                        </div>
                    </v-list-item>
                    <v-list-item
                        v-bind:title.attr="'User Documentation'"
                        href="https://xbat.dev/docs/user/introduction"
                        target="_blank"
                    >
                        <template #prepend
                            ><v-icon size="small" icon="$documentation"></v-icon
                        ></template>
                        Documentation
                    </v-list-item>
                    <v-list-item
                        v-bind:title.attr="'Changelog'"
                        href="https://github.com/MEGWARE-HPC/xbat/blob/master/CHANGELOG.md"
                        target="_blank"
                    >
                        <template #prepend
                            ><v-icon size="small" icon="$fileDocument"></v-icon
                        ></template>
                        Changelog
                    </v-list-item>
                    <v-list-item
                        :href="`${$authStore.backendUrl}/api/v1/ui/`"
                        target="_blank"
                        v-bind:title.attr="'Visit API documentation'"
                    >
                        <template #prepend
                            ><v-icon
                                size="small"
                                icon="$api"
                            ></v-icon></template
                        >REST-API Documentation
                    </v-list-item>
                    <v-list-item
                        v-bind:title.attr="'Visit web console of metric database'"
                        :href="`${$authStore.backendUrl}/questdb/index.html`"
                        target="_blank"
                    >
                        <template #prepend
                            ><v-icon size="small" icon="$database"></v-icon
                        ></template>
                        Metric Database
                    </v-list-item>
                    <v-divider class="mt-2 mb-2"></v-divider>
                    <v-list-item to="/logout" v-bind:title.attr="'Sign out'">
                        <template #prepend
                            ><v-icon size="small" icon="$logout"></v-icon
                        ></template>
                        Sign out
                    </v-list-item>
                </v-list>
            </v-card>
        </v-menu>
    </div>
</template>
<script setup>
import { useTheme } from "vuetify";
const { $authStore } = useNuxtApp();
const theme = useTheme();
const emit = defineEmits(["update:theme"]);

const themeCookie = useCookie("xbat_theme", { default: () => "light" });

const dark = ref(false);

const colorMode = useColorMode();
watch(dark, async (v) => {
    const t = v ? "dark" : "light";
    themeCookie.value = t;
    theme.global.name.value = t;
    emit("update:theme", themeCookie.value);
    // for shiki
    colorMode.preference = t;
});

theme.global.name.value = themeCookie.value;
dark.value = themeCookie.value == "dark";
emit("update:theme", themeCookie.value);
// for shiki
colorMode.preference = dark.value ? "dark" : "light";
</script>
<style lang="scss">
@use "~/assets/css/colors.scss" as *;
.menu-switch {
    margin-right: 10px;
}

.changelog {
    font-size: 0.875rem;
    max-height: 80vh;
    overflow-y: scroll;
    h1:not(:first-child) {
        margin: 20px 0;
    }
    h1 {
        font-size: 1.5rem;
        margin: 20px 0;
    }
    h2 {
        font-size: 1.125rem;
        margin: 20px 0;
    }
    h3 {
        font-size: 1rem;
        margin: 10px 0;
    }
    ul {
        margin: 10px 0 10px 40px !important;
    }
}
</style>
