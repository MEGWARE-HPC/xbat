<template>
    <v-list-group :value="`folder-${node.id}`">
        <template #activator="{ props: groupProps }">
            <v-list-item
                v-bind="groupProps"
                :title="node.name"
                prepend-icon="$folder"
            />
        </template>

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
            @select="$emit('select', $event)"
            @duplicate="$emit('duplicate', $event)"
            @delete="$emit('delete', $event)"
        />

        <!-- subfolders -->
        <SidebarFolderNode
            v-for="child in node.children || []"
            :key="child.id"
            :node="child"
            :configs-by-folder="configsByFolder"
            :selected-id="selectedId"
            :user="user"
            :user-level="userLevel"
            :UserLevelEnum="UserLevelEnum"
            @select="$emit('select', $event)"
            @duplicate="$emit('duplicate', $event)"
            @delete="$emit('delete', $event)"
        />
    </v-list-group>
</template>

<script setup>
import { computed } from "vue";
import SidebarConfigItem from "./SidebarConfigItem.vue";

const props = defineProps({
    node: { type: Object, required: true }, // {id,name,children?}
    configsByFolder: { type: Object, required: true }, // Map
    selectedId: { type: String, default: null },
    user: { type: Object, required: true },
    userLevel: { type: Number, required: true },
    UserLevelEnum: { type: Object, required: true }
});

defineEmits(["select", "duplicate", "delete"]);

const configsHere = computed(
    () => props.configsByFolder.get(props.node.id) || []
);
</script>
