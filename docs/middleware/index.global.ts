import { getDocType } from "~/helper";

export default defineNuxtRouteMiddleware(async (to, from) => {
    const { $store } = useNuxtApp();

    if (!to.fullPath.startsWith("/docs")) {
        $store.currentDocType = null;
        return;
    }

    $store.currentDocType = getDocType(to.fullPath);
});
