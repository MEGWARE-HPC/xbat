<template>
    <v-snackbar
        v-model="store.display"
        :timeout="store.timeout"
        :color="store.color"
        bottom
        outlined
    >
        <slot>
            <div class="snackbar-text">{{ store.text }}</div>
        </slot>
    </v-snackbar>
</template>
<script setup>
const { $snackbarStore: store } = useNuxtApp();
</script>
<style lang="scss">
.snackbar-text {
    width: 100%;
    height: 100%;
    text-align: center;
}
</style>
