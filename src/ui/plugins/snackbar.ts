export default defineNuxtPlugin((nuxtApp) => {
    const show = (text = "", color = "primary", timeout = 5000) => {
        nuxtApp.$snackbarStore.SHOW({ text, timeout, color });
    };

    const hide = () => {
        nuxtApp.$snackbar.HIDE();
    };
    return {
        provide: {
            snackbar: {
                show,
                hide
            }
        }
    };
});
