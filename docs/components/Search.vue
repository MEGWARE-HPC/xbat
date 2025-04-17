<template>
    <v-dialog
        :model-value="props.modelValue"
        @update:modelValue="emit('update:modelValue', $event)"
        width="600"
    >
        <v-card>
            <v-card-title
                ><v-text-field
                    placeholder="Search..."
                    v-model="searchValue"
                    hide-details
                    autofocus
                    :loading="searching"
                    clearable
                ></v-text-field
            ></v-card-title>
            <v-card-text style="margin-top: -20px">
                <v-list>
                    <v-list-item
                        v-for="entry in searchResults"
                        :value="entry.id"
                        :to="entry.id"
                        @click="emit('update:modelValue', false)"
                    >
                        <v-list-item-title>
                            <div class="d-flex">
                                <span class="">{{ entry.title }}</span>
                                <div class="text-disabled d-flex">
                                    <v-icon icon="$chevronRight"></v-icon>
                                    <div class="text-capitalize">
                                        {{ getDocType(entry.id) }}
                                    </div>
                                </div>
                            </div></v-list-item-title
                        >
                        <v-list-item-subtitle
                            v-if="entry.id in searchContentMatches"
                            v-html="searchContentMatches[entry.id]"
                        ></v-list-item-subtitle>
                    </v-list-item>
                </v-list>
            </v-card-text>
        </v-card>
    </v-dialog>
</template>
<script lang="ts" setup>
import { useDebounceFn } from "@vueuse/core";
import { getDocType } from "~/helper";

const props = defineProps<{
    modelValue: boolean;
}>();

const emit = defineEmits(["update:modelValue"]);

const searchValue = ref("");
const searching = ref(false);

const debouncedSearch = useDebounceFn(() => {
    search();
}, 300);

const searchResults = ref([]);
watch(searchValue, () => debouncedSearch());

const searchContentMatches = computed(() => {
    if (!searchResults.value) return {};

    let matches = {};

    searchResults.value.forEach((entry) => {
        if (!Object.values(entry.match).flat().includes("content")) return;

        const searchValueLowerCase = searchValue.value.toLowerCase().trim();

        const matchIndex = entry.content
            .toLowerCase()
            .indexOf(searchValueLowerCase);
        if (matchIndex === -1) return;
        const surroundingText =
            entry.content.slice(Math.max(0, matchIndex - 25), matchIndex + 50) +
            "...";

        matches[entry.id] = surroundingText
            .split(" ")
            .map((x) =>
                x.toLowerCase().includes(searchValueLowerCase)
                    ? `<span class="font-weight-bold">${x}</span>`
                    : x
            )
            .join(" ");
    });
    return matches;
});

const search = async () => {
    if (!searchValue.value) {
        searchResults.value = [];
        searching.value = false;
        return;
    }

    searching.value = true;
    // TODO missing SearchResult type
    const res = await searchContent(searchValue, {});
    searchResults.value = res.value; // res is a computed so we pluck out the .value and just add it to our ref
    searching.value = false;
};

const handleKeyPress = (event: KeyboardEvent) => {
    // Check if Ctrl + K is pressed
    if (event.ctrlKey && event.key === "k") {
        event.preventDefault(); // Prevent any default action
        emit("update:modelValue", true);
    }
};

onMounted(() => {
    window.addEventListener("keydown", handleKeyPress);
});

onUnmounted(() => {
    window.removeEventListener("keydown", handleKeyPress);
});
</script>
