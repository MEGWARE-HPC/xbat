<template></template>
<script lang="ts" setup>
const { $authStore } = useNuxtApp();
const router = useRouter();
await $authStore.logout();
router.push("/login");
</script>
