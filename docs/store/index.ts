import { defineStore } from "pinia";

export const useMainStore = defineStore("main", () => {
    const currentDocType: Ref<string | null> = ref(null);
    const docsDrawerOpen: Ref<boolean> = ref(true);

    return { currentDocType, docsDrawerOpen };
});

export default useMainStore;
