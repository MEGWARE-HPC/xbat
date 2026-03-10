<template>
    <div class="mftn">
        <div
            class="mftn-row"
            :class="{ 'is-selected': selectedId === node.id }"
            @click="$emit('select', node)"
        >
            <v-icon
                class="mftn-icon"
                :icon="hasChildren ? '$folderOpen' : '$folder'"
                size="small"
            />
            <span class="mftn-label">{{ node.name }}</span>
        </div>

        <div v-if="hasChildren" class="mftn-children">
            <MoveFolderTreeNode
                v-for="child in node.children"
                :key="child.id"
                :node="child"
                :selected-id="selectedId"
                @select="$emit('select', $event)"
            />
        </div>
    </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
    node: { type: Object, required: true },
    selectedId: { type: String, default: "" }
});

defineEmits(["select"]);

const hasChildren = computed(
    () => Array.isArray(props.node?.children) && props.node.children.length > 0
);
</script>

<style scoped lang="scss">
@use "~/assets/css/colors.scss" as *;

.mftn-row {
    display: flex;
    align-items: center;
    gap: 8px;
    min-height: 32px;
    padding: 4px 8px;
    border-radius: 6px;
    cursor: pointer;
}

.mftn-row:hover {
    background: $highlight;
}

.mftn-row.is-selected {
    background: $highlight;
}

.mftn-icon {
    color: $primary-light;
    opacity: 0.85;
}

.mftn-label {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.mftn-children {
    margin-left: 18px;
    padding-left: 8px;
    border-left: 1px solid rgba(var(--v-theme-font-base), 0.08);
}
</style>
