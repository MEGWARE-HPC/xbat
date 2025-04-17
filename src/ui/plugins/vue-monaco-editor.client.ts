import loader from "@monaco-editor/loader";

export default defineNuxtPlugin((app) => {
    // load older version of monaco-editor from CDN
    // due to https://github.com/Pranomvignesh/constrained-editor-plugin/issues/61
    loader.config({
        paths: {
            vs: "https://cdn.jsdelivr.net/npm/monaco-editor@0.33.0/min/vs"
        }
    });
});
