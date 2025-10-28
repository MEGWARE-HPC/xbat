import vuetify, { transformAssetUrls } from "vite-plugin-vuetify";

const debug = false;

export default defineNuxtConfig({
    ssr: false,
    debug: debug,
    sourcemap: debug,
    devtools: {
        enabled: true,
        timeline: {
            enabled: true
        }
    },
    components: [
        {
            path: "~/components",
            pathPrefix: false
        }
    ],
    experimental: {
        componentIslands: true
    },
    // TODO global css not working
    css: [
        "@/assets/css/general.scss",
        "@/assets/css/colors.scss",
        "@/assets/css/editor-themes.scss"
    ],
    build: {
        transpile: ["vuetify"]
    },
    plugins: [],
    modules: [
        (_options, nuxt) => {
            nuxt.hooks.hook("vite:extendConfig", (config) => {
                // @ts-expect-error
                config.plugins.push(vuetify({ autoImport: true }));
            });
        },
        "@pinia/nuxt",
        "@nuxt/image",
        "@nuxtjs/color-mode",
        "@nuxt/fonts"
    ],
    devServer: {
        https: {
            key: "../../dev/certs/key.pem",
            cert: "../../dev/certs/cert.pem"
        }
    },
    vite: {
        vue: {
            template: {
                transformAssetUrls
            }
        },
        define: { global: "window" },
        optimizeDeps: {
            include: ["plotly.js-basic-dist-min"]
        },
        build: {
            minify: !debug
        },
        css: {
            preprocessorOptions: {
                scss: {
                    quietDeps: true,
                    api: "modern-compiler"
                }
            }
        }
    },
    router: {
        options: {
            scrollBehaviorType: "smooth"
        }
    },
    runtimeConfig: {
        public: {
            apiPrefix: "/api/v1",
            clientIdPrefix: "wf_",
            buildVersion: "1.2.0",
            devRestUrl: "https://localhost:7000",
            demoMode: false,
            demoUser: "",
            demoPassword: ""
        },
        composeBackendUrl: "http://xbat-backend:7001",
        composeFrontendUrl: "http://xbat-ui:7003"
    },
    compatibilityDate: "2024-07-03"
});
