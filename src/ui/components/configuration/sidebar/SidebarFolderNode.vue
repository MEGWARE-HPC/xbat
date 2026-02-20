<template>
    <v-list-group :value="`folder-${node.id}`" class="sb-folder">
        <template #activator="{ props: groupProps, isOpen }">
            <v-list-item
                v-bind="groupProps"
                class="sb-row"
                density="comfortable"
                :style="rowStyle"
            >
                <template #prepend>
                    <v-icon
                        class="sb-chevron"
                        size="small"
                        :icon="isOpen ? '$chevronDown' : '$chevronRight'"
                    />
                    <v-icon
                        class="sb-folder-icon"
                        icon="$folder"
                    />
                </template>

                <v-list-item-title class="sb-title">
                    {{ node.name }}
                </v-list-item-title>
            </v-list-item>
        </template>

        <div class="sb-children" :style="childrenStyle">
            <!-- configs in this folder -->
            <SidebarConfigItem
                v-for="c in configsHere"
                :key="c.id"
                :id="c.id"
                :doc="c.doc"
                :selected-id="selectedId"
                :user="user"
                :user-level="userLevel"
                :UserLevelEnum="UserLevelEnum"
                :depth="depth + 1"
                @select="$emit('select', $event)"
                @duplicate="$emit('duplicate', $event)"
                @delete="$emit('delete', $event)"
            />

            <!-- subfolders -->
            <SidebarFolderNode
                v-for="child in node.children || []"
                v-if="depth < maxDepth"
                :key="child.id"
                :node="child"
                :configs-by-folder="configsByFolder"
                :selected-id="selectedId"
                :user="user"
                :user-level="userLevel"
                :UserLevelEnum="UserLevelEnum"
                :depth="depth + 1"
                :max-depth="maxDepth"
                @select="$emit('select', $event)"
                @duplicate="$emit('duplicate', $event)"
                @delete="$emit('delete', $event)"
            />
        </div>
    </v-list-group>
</template>

<script setup>
import { computed } from "vue";
import SidebarConfigItem from "./SidebarConfigItem.vue";

const props = defineProps({
    node: { type: Object, required: true },
    configsByFolder: { type: Object, required: true }, // Map
    selectedId: { type: String, default: null },
    user: { type: Object, required: true },
    userLevel: { type: Number, required: true },
    UserLevelEnum: { type: Object, required: true },
    depth: { type: Number, default: 0 },
    maxDepth: { type: Number, default: 2 }
});

defineEmits(["select", "duplicate", "delete"]);

const INDENT = 12;
const GUIDE_GAP = 6;

const configsHere = computed(
    () => props.configsByFolder.get(props.node.id) || []
);

const rowStyle = computed(() => ({
    "--sb-indent": `${props.depth * INDENT}px`
}));

const childrenStyle = computed(() => ({
    "--sb-indent": `${(props.depth + 1) * INDENT}px`,
    "--sb-guide-gap": `${GUIDE_GAP}px`
}));
</script>

<style scoped lang="scss">
:deep(.v-list-group__items) {
    padding-inline-start: 0 !important;
}

.sb-row {
    padding-inline-start: var(--sb-indent) !important;
    min-height: 30px;
}

.sb-title {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.sb-chevron {
    margin-inline-end: 2px;
    color: rgb(var(--v-theme-on-surface)) !important;
    opacity: var(--v-medium-emphasis-opacity) !important;
}
.sb-folder-icon {
    margin-inline-end: 6px;
    color: rgb(var(--v-theme-on-surface)) !important;
    opacity: var(--v-medium-emphasis-opacity) !important;
}

.sb-children {
    position: relative;
    margin-inline-start: var(--sb-indent);
    padding-inline-start: calc(var(--sb-guide-gap) + 6px);
}

.sb-children::before {
    content: "";
    position: absolute;
    top: 0;
    bottom: 0;
    left: calc(var(--sb-guide-gap) / 2);
    width: 1px;
    opacity: 0.35;
}
</style>
