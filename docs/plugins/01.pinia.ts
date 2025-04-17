import { useMainStore } from "~/store";
import type { Pinia } from "pinia";

export default defineNuxtPlugin(({ $pinia }) => {
    return {
        provide: {
            store: useMainStore($pinia as Pinia)
        }
    };
});
