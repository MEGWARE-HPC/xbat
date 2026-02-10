<template>
    <v-hover>
        <template #default="{ isHovering, props: hoverProps }">
            <v-list-item
                v-bind="hoverProps"
                :value="id"
                :active="selectedId === id"
                @click="$emit('select', id)"
                style="line-height: 36px"
            >
                <template #prepend>
                    <div
                        class="mr-2"
                        v-if="doc?.configuration?.sharedProjects?.length"
                    >
                        <v-icon
                            size="small"
                            color="primary-light"
                            title="This configuration is shared with other users"
                            icon="$share"
                        />
                    </div>
                </template>

                <span class="configuration-name">
                    {{ doc?.configuration?.configurationName || id }}
                </span>

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
    UserLevelEnum: { type: Object, required: true }
});

defineEmits(["select", "duplicate", "delete"]);

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
</style>
