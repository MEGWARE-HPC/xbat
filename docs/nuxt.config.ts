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
    nitro: {
        prerender: {
            routes: [...routes]
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
                scss: {
                    api: "modern-compiler"
                }
            }
        }
    },
    content: {
        highlight: {
            theme: {
                default: "github-light",
                dark: "github-dark"
            },
            langs: ["bash", "yml", "json", "javascript", "ini"]
        },
        experimental: {
            // @ts-expect-error
            search: true
        }
    },
    plugins: ["~/plugins/debug-hydration.ts"],
    site: { url: "xbat.dev" },
    router: {
        options: {
            scrollBehaviorType: "smooth"
        }
    },
    compatibilityDate: "2024-11-12"
});
