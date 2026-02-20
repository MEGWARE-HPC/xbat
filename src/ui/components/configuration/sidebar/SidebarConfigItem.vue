<template>
    <v-hover>
        <template #default="{ isHovering, props: hoverProps }">
            <v-list-item
                v-bind="hoverProps"
                class="sb-row"
                density="comfortable"
                :style="rowStyle"
                :value="id"
                :active="selectedId === id"
                @click="$emit('select', id)"
            >
                <template #prepend>
                    <v-icon
                        class="sb-icon"
                        color="primary-light"
                        :icon="
                            doc.configuration?.sharedProjects?.length
                                ? '$share'
                                : '$textBox'
                        "
                        :title="
                            doc.configuration?.sharedProjects?.length
                                ? 'This configuration is shared with other users'
                                : undefined
                        "
                    />
                </template>

                <v-list-item-title class="sb-title">
                    {{ doc?.configuration?.configurationName || id }}
                </v-list-item-title>

                <template #append>
                    <v-btn-group
                        divided
                        variant="text"
                        density="compact"
                        v-if="isHovering && userLevel >= UserLevelEnum.user"
                    >
                        <v-btn
                            title="Duplicate Configuration"
                            size="small"
                            icon="$duplicate"
                            @click.stop="$emit('duplicate', id)"
                        />
                        <v-btn
                            v-if="canDelete"
                            title="Delete Configuration"
                            size="small"
                            icon="$trashCan"
                            @click.stop="$emit('delete', id)"
                        />
                    </v-btn-group>
                </template>
            </v-list-item>
        </template>
    </v-hover>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
    id: { type: String, required: true },
    doc: { type: Object, required: true },
    selectedId: { type: String, default: null },
    user: { type: Object, required: true },
    userLevel: { type: Number, required: true },
    UserLevelEnum: { type: Object, required: true },
    depth: { type: Number, default: 0 }
});

defineEmits(["select", "duplicate", "delete"]);

const INDENT = 12;

const rowStyle = computed(() => ({
    "--sb-indent": `${props.depth * INDENT}px`
}));

const canDelete = computed(() => {
    const owner = props.doc?.misc?.owner;
    return (
        (owner && owner === props.user.user_name) ||
        props.userLevel > props.UserLevelEnum.user
    );
});
</script>

<style lang="scss" scoped>
.configuration-name {
    white-space: normal;
    word-break: break-all;
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

.sb-icon {
    margin-inline-end: 6px;
}
</style>
