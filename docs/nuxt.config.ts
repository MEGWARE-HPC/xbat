import vuetify, { transformAssetUrls } from "vite-plugin-vuetify";
import { globSync } from "glob";
const routes = globSync("./content/**/*.md").map((path) =>
    path.slice(7, -3).replace(/\d+\./g, "")
);

export default defineNuxtConfig({
    ssr: true,
    build: {
        transpile: ["vuetify"]
    },
    modules: [
        (_options, nuxt) => {
            nuxt.hooks.hook("vite:extendConfig", (config) => {
                // @ts-expect-error
                config.plugins.push(vuetify({ autoImport: true }));
            });
        },
        "@nuxt/image",
        "@nuxt/fonts",
        "@nuxtjs/robots",
        "@nuxt/content",
        "@pinia/nuxt",
        "@nuxtjs/sitemap"
    ],
    fonts: {
        families: [
            {
                name: "Source Sans 3",
                provider: "google",
                weights: [400, 500, 600, 700],
                styles: ["normal", "italic"],
                subsets: ["latin"],
                display: "swap"
            },
            {
                name: "Source Code Pro",
                provider: "google",
                weights: [400, 500, 600, 700],
                styles: ["normal", "italic"],
                subsets: ["latin"],
                display: "swap"
            }
        ]
    },
    nitro: {
        prerender: {
            routes: [...routes]
        },
        routeRules: {
            "/**/*.wasm": {
                headers: {
                    "Content-Type": "application/wasm"
                }
            }
        }
    },
    image: {
        alias: {
            // TODO not working
            "shared-logos": "../ui/public/logo"
        }
    },
    vite: {
        vue: {
            template: {
                transformAssetUrls
            }
        },
        css: {
            preprocessorOptions: {
                scss: {}
            }
        }
    },
    content: {
        build: {
            markdown: {
                toc: { depth: 3 },
                highlight: {
                    theme: {
                        default: "github-light",
                        dark: "github-dark"
                    },
                    langs: ["bash", "yml", "json", "javascript", "ini"]
                }
            }
        }
    },
    site: { url: "xbat.dev" },
    router: {
        options: {
            scrollBehaviorType: "smooth"
        }
    },
    compatibilityDate: "2024-11-12"
});
