import { defineStore } from "pinia";

export const useMainStore = defineStore("main", () => {
    const currentDocType: Ref<string | null> = ref(null);

    return { currentDocType };
});

export default useMainStore;
