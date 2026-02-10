<template>
    <v-navigation-drawer permanent location="right" class="sidebar" width="300">
        <template #prepend>
            <div class="header">CONFIGURATIONS</div>
        </template>

        <div class="list">
            <v-list density="compact" :selected="[selectedId]" mandatory>
                <template
                    v-for="[id, v] of Object.entries(configurationCache)"
                    :key="id"
                >
                    <v-hover>
                        <template #default="{ isHovering, props }">
                            <v-list-item
                                v-bind="props"
                                :value="id"
                                @click="$emit('select', id)"
                                style="line-height: 36px"
                            >
                                <template #prepend>
                                    <div
                                        class="mr-2"
                                        v-if="
                                            v.configuration?.sharedProjects
                                                ?.length
                                        "
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
                                    {{
                                        v.configuration?.configurationName
                                            ? v.configuration.configurationName
                                            : id
                                    }}
                                </span>

                                <template #append>
                                    <v-btn-group
                                        divided
                                        variant="text"
                                        density="compact"
                                        v-if="
                                            isHovering &&
                                            userLevel >= UserLevelEnum.user
                                        "
                                    >
                                        <v-btn
                                            title="Duplicate Configuration"
                                            size="small"
                                            icon="$duplicate"
                                            @click.stop="$emit('duplicate', id)"
                                        />
                                        <v-btn
                                            v-if="canDelete(v)"
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
            </v-list>
        </div>

        <v-list-item>
            <div
                v-if="userLevel > UserLevelEnum.guest"
                class="d-flex justify-center"
            >
                <v-btn
                    title="Add Configuration"
                    elevation="0"
                    variant="tonal"
                    prepend-icon="$newFile"
                    @click="$emit('create')"
                >
                    New configuration
                </v-btn>
            </div>
        </v-list-item>
    </v-navigation-drawer>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
    configurationCache: {
        type: Object,
        required: true
    },
    selectedId: {
        type: String,
        default: null
    },
    user: {
        type: Object,
        required: true
    },
    userLevel: {
        type: Number,
        required: true
    },
    UserLevelEnum: {
        type: Object,
        required: true
    }
});

defineEmits(["select", "create", "duplicate", "delete"]);

const canDelete = (configWrapper) => {
    const owner = configWrapper?.misc?.owner;
    return (
        (owner && owner === props.user.user_name) ||
        props.userLevel > props.UserLevelEnum.user
    );
};
</script>

<style lang="scss" scoped>
@use "~/assets/css/colors.scss" as *;

.sidebar {
    .header {
        margin-top: 25px;
        text-align: center;
        color: $font-light;
    }

    .list {
        overflow-y: auto;
        max-height: 80vh;
    }
}
</style>
