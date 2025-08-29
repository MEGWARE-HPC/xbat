<template>
    <v-dialog
        :model-value="props.modelValue"
        @update:modelValue="emit('update:modelValue', $event)"
        width="600"
    >
        <v-card>
            <v-card-title>
                <v-text-field
                    placeholder="Search..."
                    v-model="searchValue"
                    hide-details
                    autofocus
                    :loading="searching"
                    clearable
                />
            </v-card-title>
            <v-card-text style="margin-top: -20px">
                <v-list>
                    <v-list-item
                        v-for="(entry, idx) in searchResults"
                        :key="entry.id || entry.path || idx"
                        :value="entry.id || entry.path || idx"
                        :to="entry.id || entry.path"
                        @click="emit('update:modelValue', false)"
                    >
                        <v-list-item-title>
                            <div class="d-flex">
                                <span>{{ entry.title }}</span>
                                <div class="text-disabled d-flex">
                                    <v-icon icon="$chevronRight" />
                                    <div class="text-capitalize">
                                        {{ getDocType(entry.path) || "" }}
                                    </div>
                                </div>
                            </div>
                        </v-list-item-title>

                        <v-list-item-subtitle
                            v-if="entry.snippet"
                            v-html="entry.snippet"
                        />
                    </v-list-item>
                </v-list>
            </v-card-text>
        </v-card>
    </v-dialog>
</template>
<script lang="ts" setup>
import { useDebounceFn } from "@vueuse/core";
import { getDocType } from "~/helper";

const props = defineProps<{ modelValue: boolean }>();

const emit = defineEmits(["update:modelValue"]);

const searchValue = ref<string | null>("");
const searching = ref(false);

type Section = {
    id: string;
    title?: string;
    titles?: string[];
    content?: string;
    level?: number;
};

type SearchItem = {
    id: string;
    path: string;
    title: string;
    snippet: string;
};

const allSections = ref<Section[] | null>(null);
const searchResults = ref<SearchItem[]>([]);

async function ensureSectionsLoaded() {
    if (allSections.value) return;
    allSections.value = await queryCollectionSearchSections("docs");
}

function escapeHtml(s: string) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function escapeRegExp(s: string) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function makeSnippet(text: string, query: string, radius = 60) {
    const T = text || "";
    const Q = (query || "").trim();
    if (!Q) return escapeHtml(T.slice(0, radius * 2));

    const lower = T.toLowerCase();
    const qLower = Q.toLowerCase();
    const idx = lower.indexOf(qLower);

    let rawSnippet: string;
    if (idx < 0) {
        rawSnippet = T.slice(0, radius * 2);
    } else {
        const start = Math.max(0, idx - radius);
        const end = Math.min(T.length, idx + Q.length + radius);
        rawSnippet =
            (start > 0 ? "…" : "") +
            T.slice(start, end) +
            (end < T.length ? "…" : "");
    }

    const escaped = escapeHtml(rawSnippet);
    const escapedQuery = escapeHtml(Q);
    const re = new RegExp(`(${escapeRegExp(escapedQuery)})`, "ig");
    return escaped.replace(re, '<span class="highlight">$1</span>');
}

const search = async () => {
    const q = String(searchValue.value ?? "").trim();
    if (!q) {
        searchResults.value = [];
        searching.value = false;
        return;
    }

    searching.value = true;
    try {
        await ensureSectionsLoaded();
        const sections = allSections.value || [];

        const qlc = q.toLowerCase();
        const matched = sections.filter((s) => {
            const inTitle = (s.title || "").toLowerCase().includes(qlc);
            const inContent = (s.content || "").toLowerCase().includes(qlc);
            return inTitle || inContent;
        });

        const seen = new Set<string>();
        searchResults.value = matched
            .map((s) => {
                const id = s.id;
                const path = id.split("#")[0] || id;
                const title =
                    s.title ||
                    s.titles?.slice(-1)?.[0] ||
                    path.split("/").pop() ||
                    id;
                const snippet = makeSnippet(s.content || "", q);
                return { id, path, title, snippet };
            })
            .filter((item) => {
                if (!item.id) return false;
                if (seen.has(item.id)) return false;
                seen.add(item.id);
                return true;
            })
            .slice(0, 20);
    } catch {
        searchResults.value = [];
    } finally {
        searching.value = false;
    }
};

const debouncedSearch = useDebounceFn(() => {
    search();
}, 250);
watch(searchValue, () => debouncedSearch());

const handleKeyPress = (event: KeyboardEvent) => {
    // Check if Ctrl + K is pressed
    if (event.ctrlKey && event.key.toLowerCase() === "k") {
        event.preventDefault(); // Prevent any default action
        emit("update:modelValue", true);
    }
};

onMounted(() => window.addEventListener("keydown", handleKeyPress));

onUnmounted(() => window.removeEventListener("keydown", handleKeyPress));
</script>
<style scoped lang="scss">
@use "~/assets/css/colors.scss" as *;

:deep(.highlight) {
    background-color: $highlight;
    color: $primary-light;
    padding: 0 0px;
    border-radius: 2px;
}
</style>
