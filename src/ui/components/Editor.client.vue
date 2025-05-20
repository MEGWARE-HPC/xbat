<template>
    <div>
        <div style="position: relative" ref="containerRef">
            <template v-if="props.loading">
                <v-skeleton-loader type="paragraph"></v-skeleton-loader>
            </template>
            <template v-else>
                <div
                    class="d-flex actions"
                    :style="{
                        'background-color':
                            theme == 'light' ? 'white' : 'rgb(30,30,30,)'
                    }"
                >
                    <v-btn
                        size="small"
                        v-show="props.copyable && props.modelValue"
                        variant="text"
                        @click="copyToClipboard(props.modelValue)"
                        title="Copy to Clipboard"
                        ><v-icon icon="$copy"></v-icon
                    ></v-btn>
                    <v-btn
                        size="small"
                        v-if="props.downloadable && props.modelValue"
                        variant="text"
                        @click="download(props.filename, props.modelValue)"
                        title="Download as File"
                        ><v-icon icon="$fileDownload"></v-icon
                    ></v-btn>
                </div>
                <template v-if="props.constrainedJobscript">
                    <div
                        class="input-validation-hint"
                        v-show="inputValidation.visible"
                        :style="`left: ${
                            inputValidation.left + scrollOffset.left
                        }px; top: ${inputValidation.top - scrollOffset.top}px`"
                    >
                        <div class="input-validation-wrapper">
                            <div class="arrow-up"></div>

                            <v-icon icon="$alertCircle"></v-icon>
                            {{ inputValidation.message }}
                        </div>
                    </div>
                    <div
                        v-if="hoverTarget"
                        class="slurm-info"
                        :style="`left: ${
                            hoverInfo.left + scrollOffset.left
                        }px; top: ${hoverInfo.top - scrollOffset.top}px`"
                    >
                        <v-btn
                            icon="$openInNew"
                            size="x-small"
                            variant="plain"
                            :href="hoverInfo.href"
                            target="_blank"
                            title="Visit Documentation"
                        >
                        </v-btn>
                    </div>
                    <template v-for="error of submissionValidation">
                        <div
                            class="submission-validation-hint"
                            :style="`top: ${
                                error.top - scrollOffset.top - 1
                            }px;`"
                        >
                            <v-tooltip location="bottom">
                                <template v-slot:activator="{ props }">
                                    <v-icon
                                        v-bind="props"
                                        size="small"
                                        icon="$alertCircle"
                                        color="danger"
                                    ></v-icon>
                                </template>
                                <span class="font-italic font-weight-bold"
                                    >--{{ error.label }}</span
                                ><br />
                                {{ error.message }}
                            </v-tooltip>
                        </div>
                    </template>
                </template>
                <VueMonacoEditor
                    v-model:value="value"
                    :language="props.language"
                    :theme="theme == 'light' ? 'vs' : 'vs-dark'"
                    :options="options"
                    @mount="handleMount"
                    ref="editorRef"
                ></VueMonacoEditor>
            </template>
        </div>
    </div>
</template>
<script lang="ts" setup>
import { VueMonacoEditor } from "@guolao/vue-monaco-editor";
import * as monacoEditor from "monaco-editor/esm/vs/editor/editor.api";
import { download, copyToClipboard } from "~/utils/misc";
import type { Jobscript } from "@/repository/modules/configurations";
import { useElementHover } from "@vueuse/core";

type MonacoEditor = typeof monacoEditor;

// CSV language registration
const csvLangId = "csv";
monacoEditor.languages.register({ id: csvLangId });

// Color list
const colors = [
    "#c00040",
    "#00a000",
    "#8000c0",
    "#c09e18",
    "#0080a0",
    "#e000e0",
    "#60a000",
    "#0020f0",
    "#e08000",
    "#00c080"
];

monacoEditor.languages.setMonarchTokensProvider(csvLangId, {
    tokenizer: {
        root: [
            [/[^,\r\n]+/, { token: "identifier" }],
            [/,/, "delimiter"],
            [/$/, ""]
        ]
    }
});

const styleElement = document.createElement("style");
colors.forEach((color, index) => {
    styleElement.innerHTML += `.csv-column-${index} { color: ${color}; }`;
});
document.head.appendChild(styleElement);

const value = ref<string | Jobscript>("");

let editorInstance: monacoEditor.editor.IStandaloneCodeEditor | null = null;

const editorRef = ref<HTMLElement | null>(null);
const containerRef = ref<HTMLElement | null>(null);

const theme = useCookie("xbat_theme");
const emit = defineEmits(["update:modelValue", "update:validity"]);

const containerHovered = useElementHover(containerRef);

const props = defineProps({
    modelValue: {
        type: [String, Object] as PropType<Jobscript | string>,
        default: ""
    },
    languages: {
        type: Array,
        default: () => []
    },
    readonly: {
        type: Boolean,
        default: false
    },
    minimap: {
        type: Boolean,
        default: false
    },
    autoResize: {
        type: Boolean,
        default: false
    },
    autoResizeMaxHeight: {
        type: Number,
        default: 500
    },
    height: {
        type: [String, Number],
        default: 500
    },
    noWrap: {
        type: Boolean,
        default: false
    },
    lineNumbers: {
        type: Boolean,
        default: true
    },
    jobscript: {
        type: Object,
        default: () => {}
    },
    constrainedJobscript: {
        type: Boolean,
        default: false
    },
    copyable: {
        type: Boolean,
        default: true
    },
    downloadable: {
        type: Boolean,
        default: true
    },
    filename: {
        type: String,
        default: "output.txt"
    },
    language: {
        type: String,
        default: "shell"
    },
    loading: {
        type: Boolean,
        default: false
    }
});

const mv = computed(() => {
    return props.modelValue as Jobscript;
});

const {
    initConstrainedEditor,
    inputValidation,
    directives,
    hoverInfo,
    hoverTarget,
    submissionValidation,
    scrollOffset
} = useConstrainedEditor(mv, emit);

watch(submissionValidation, (v) => emit("update:validity", !v.length), {
    immediate: true,
    deep: true
});

watch(containerHovered, (v) => {
    if (!v) hoverTarget.value = null;
});

watch(
    () => props.modelValue,
    (v) => {
        if (!v) return;

        if (
            (typeof v === "object" && !props.constrainedJobscript) ||
            (typeof v === "string" && props.constrainedJobscript)
        ) {
            console.error(
                "Invalid modelValue type in combination with constrainedJobscript prop"
            );
            return;
        }

        if (props.constrainedJobscript)
            value.value = directives.value + "\n" + (v as Jobscript).script;
        else value.value = v;
    },
    { immediate: true }
);

watch(
    () => value.value,
    (v) => {
        if (props.constrainedJobscript) return;
        emit("update:modelValue", v);
    },
    { immediate: true }
);

const options = computed(() => {
    return {
        readOnly: props.readonly,
        minimap: { enabled: props.minimap },
        wordWrap: props.noWrap ? "off" : "on",
        lineNumbers: props.lineNumbers ? "on" : "off",
        scrollBeyondLastLine: false,
        fontFamily: "Source Code Pro",
        quickSuggestions: false
    } as monacoEditor.editor.IStandaloneEditorConstructionOptions;
});

const updateHeight = () => {
    if (!editorInstance || !containerRef.value) return;

    if (!props.autoResize) {
        containerRef.value.style.height = `${props.height}px`;
        return;
    }

    const contentHeight = Math.min(
        props.autoResizeMaxHeight,
        editorInstance.getContentHeight()
    );
    containerRef.value.style.height = `${contentHeight}px`;
};

const handleMount = (
    _editor: monacoEditor.editor.IStandaloneCodeEditor,
    monaco: MonacoEditor
) => {
    editorInstance = _editor;
    editorInstance.onDidContentSizeChange(updateHeight);

    if (props.language === csvLangId) {
        const model = editorInstance.getModel();
        const applyRainbowColors = () => {
            if (!model) return;

            const decorations: monacoEditor.editor.IModelDeltaDecoration[] = [];
            const text = model.getValue();
            const lines = text.split("\n");

            lines.forEach((line, lineNumber) => {
                const columns = line.split(",");
                let currentOffset = 1;
                columns.forEach((column, columnIndex) => {
                    if (colors[columnIndex % colors.length]) {
                        decorations.push({
                            range: new monacoEditor.Range(
                                lineNumber + 1,
                                currentOffset,
                                lineNumber + 1,
                                currentOffset + column.length
                            ),
                            options: {
                                inlineClassName: `csv-column-${
                                    columnIndex % colors.length
                                }`
                            }
                        });
                    }
                    currentOffset += column.length + 1;
                });
            });

            editorInstance.deltaDecorations([], decorations);
        };

        applyRainbowColors();
        if (model) {
            model.onDidChangeContent(() => {
                applyRainbowColors();
                // console.log("props.language", props.language, "csvLangId", csvLangId);
                // console.log("model", model);
            });
        }
    }

    if (!props.constrainedJobscript) return;

    initConstrainedEditor(_editor, monaco);
};
</script>
<style lang="scss" scoped>
@use "~/assets/css/colors.scss" as *;
.actions {
    position: absolute;
    right: 15px;
    top: 5px;
    z-index: 1;
}

.submission-validation-hint {
    position: absolute;
    z-index: 1;
    left: 0;
}

.input-validation-hint {
    position: absolute;
    border: 1px solid;
    border-color: $danger;
    background-color: $background;
    color: $danger;
    padding: 5px 10px;
    font-size: 0.875rem;
    border-radius: 3px;
    z-index: 1;
    left: 0;
    top: 0;
    transform: translate(-50%, -50%);

    .arrow-up {
        position: absolute;
        left: 0;
        right: 0;
        top: -5px;
        margin: 0 auto;
        width: 0;
        height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-bottom: 5px solid $danger;
    }
}

.slurm-info {
    position: absolute;
    z-index: 1;
    display: flex;
    justify-content: center;
    align-items: center;
}
.slurm-info > .v-btn {
    transform: translate(10%, 0);
}
</style>
