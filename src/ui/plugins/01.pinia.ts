import { useMainStore } from "~/store";
import { useAuthStore } from "~/store/auth";
import { useSnackbarStore } from "~/store/snackbar";
import { useGraphStore } from "~/store/graph";
import type { Pinia } from "pinia";

export default defineNuxtPlugin(({ $pinia }) => {
    return {
        provide: {
            store: useMainStore($pinia as Pinia),
            authStore: useAuthStore($pinia as Pinia),
            snackbarStore: useSnackbarStore($pinia as Pinia),
            graphStore: useGraphStore($pinia as Pinia)
        }
    };
});
