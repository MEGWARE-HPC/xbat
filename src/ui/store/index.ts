import { defineStore } from "pinia";
import { useAuthStore } from "./auth";

type Error = {
    title: string;
    status: number;
    detail: string;
};

export const useMainStore = defineStore("main", () => {
    const error: Ref<Error | null> = ref(null);
    const benchmarkNr: Ref<number | null> = ref(null);

    const runtimeConfig = useRuntimeConfig();

    const authStore = useAuthStore();

    const clearError = () => (error.value = null);

    const demo = computed(
        () =>
            runtimeConfig.public.demoMode &&
            authStore.user?.user_type != "admin"
    );

    return {
        authStore,
        error,
        benchmarkNr,
        clearError,
        // only enable demo mode if set in config and user is not admin
        demo,
        demoUser: runtimeConfig.public.demoUser,
        demoPassword: runtimeConfig.public.demoPassword,
        demoMessage: "This is a read-only demo instance."
    };
});

export default useMainStore;
