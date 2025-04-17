import { defineStore } from "pinia";

export const useSnackbarStore = defineStore("snackbar", {
    state: () => ({
        text: "",
        timeout: 5000,
        color: "primary",
        display: false
    }),
    actions: {
        SHOW({ text = "", timeout = 5000, color = "primary" }) {
            this.text = text;
            this.timeout = timeout;
            this.color = color;
            this.display = true;
        },
        HIDE() {
            this.display = false;
        }
    }
});
