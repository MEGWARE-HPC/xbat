import "vuetify/styles";
import { createVuetify } from "vuetify";
import { aliases, mdi } from "vuetify/iconsets/mdi-svg";
import {
    mdiGithub,
    mdiMagnify,
    mdiChevronDown,
    mdiChevronRight,
    mdiLinkVariant,
    mdiLightbulbOutline,
    mdiAlertOutline,
    mdiInformationOutline,
    mdiContentCopy,
    mdiArrowLeft,
    mdiArrowRight,
    mdiOpenInNew,
    mdiFileDocumentOutline,
    mdiTelevisionPlay,
    mdiMenu
} from "@mdi/js";

/*
 * Opacity is not supported in vue themes.
 * According to material design specifications the fonts should have the following values:
 * base: hsla(0, 0%, 0%, 0.87);
 * light: hsla(0, 0%, 0%, 0.6);
 * disabled: hsla(0, 0%, 0%, 0.38);
 * The chosen rgb values below are only rough approximations...
 */
export default defineNuxtPlugin((app) => {
    const vuetify = createVuetify({
        ssr: true,
        theme: {
            themes: {
                light: {
                    dark: false,
                    colors: {
                        primary: "#114232",
                        "primary-light": "#1d6d59",
                        danger: "#B33951",
                        warning: "#EFA00B",
                        info: "#636262",
                        "font-base": "#0f0f0f",
                        "font-light": "#767676",
                        "font-disabled": "#a3a3a3",
                        background: "#f9f9f9",
                        surface: "#f9f9f9"
                    }
                },
                dark: {
                    dark: true,
                    colors: {
                        primary: "#114232",
                        "primary-light": "#1d6d59",
                        danger: "#B33951",
                        warning: "#EFA00B",
                        info: "#E2E8DD",
                        "font-base": "#f3f3f3",
                        "font-light": "#b1b1b1",
                        "font-disabled": "#686868"
                    }
                }
            }
        },
        icons: {
            defaultSet: "mdi",
            aliases: {
                ...aliases,
                github: mdiGithub,
                magnify: mdiMagnify,
                chevronDown: mdiChevronDown,
                link: mdiLinkVariant,
                lightbulb: mdiLightbulbOutline,
                alert: mdiAlertOutline,
                information: mdiInformationOutline,
                copy: mdiContentCopy,
                arrowLeft: mdiArrowLeft,
                arrowRight: mdiArrowRight,
                linkExternal: mdiOpenInNew,
                chevronRight: mdiChevronRight,
                file: mdiFileDocumentOutline,
                play: mdiTelevisionPlay,
                menu: mdiMenu
            },
            sets: {
                mdi
            }
        },
        defaults: {
            VTextField: {
                density: "compact",
                variant: "outlined"
            },
            VBtn: {
                density: "default",
                rounded: "lg"
            },
            VCard: {
                density: "compact"
            },
            VDialog: {
                transition: "dialog-bottom-transition"
            },
            VList: {
                density: "compact"
            }
        }
    });
    app.vueApp.use(vuetify);
});
