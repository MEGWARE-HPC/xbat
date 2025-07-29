import { storeToRefs } from "pinia";

export default defineNuxtRouteMiddleware(async (to, from) => {
    const { $authStore } = useNuxtApp();
    const { isAuthenticated, user, userLevel } = storeToRefs($authStore);

    if (!isAuthenticated.value) {
        if (to.path !== "/login") return navigateTo("/login");
        return;
    }

    if (!user.value) {
        try {
            await $authStore.loadUser();
        } catch (error) {
            console.error("Error loading user:", error);
            $authStore.clearToken();
            return navigateTo("/login");
        }
        if (!user.value) return navigateTo("/login");
    }

    if (to.path === "/login") {
        return navigateTo("/");
    }

    if (
        to.meta.requiresAdmin &&
        userLevel.value < $authStore.UserLevelEnum.demo
    ) {
        throw createError({ statusCode: 403, statusMessage: "Forbidden" });
    }
});
