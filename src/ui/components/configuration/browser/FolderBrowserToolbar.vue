<template>
    <!-- Header -->
    <div class="fb-header">
        <div class="fb-title">
            <v-icon class="mr-2" :class="headerIconClass" :icon="headerIcon" />
            <span class="fb-title-text">{{ headerTitle }}</span>
        </div>

        <div class="fb-header-actions" v-if="canCreate">
            <div class="fb-toolbar-shell">
                <!-- Selection actions -->
                <v-btn-group
                    v-if="hasSelect"
                    divided
                    variant="text"
                    density="comfortable"
                    class="fb-toolbar fb-toolbar--selection"
                >
                    <template v-if="mixedSelect">
                        <v-tooltip location="bottom">
                            <template #activator="{ props: tipProps }">
                                <span class="fb-toolbar-item" v-bind="tipProps">
                                    <v-btn
                                        icon="$trashCanDv"
                                        color="primary-light"
                                        @click="$emit('delete')"
                                    />
                                </span>
                            </template>
                            <span>Delete</span>
                        </v-tooltip>
                    </template>

                    <template v-else>
                        <v-tooltip v-if="canDuplicate" location="bottom">
                            <template #activator="{ props: tipProps }">
                                <span class="fb-toolbar-item" v-bind="tipProps">
                                    <v-btn
                                        icon="$duplicate"
                                        color="primary-light"
                                        @click="$emit('duplicate')"
                                    />
                                </span>
                            </template>
                            <span>Duplicate</span>
                        </v-tooltip>

                        <v-tooltip v-if="canRename" location="bottom">
                            <template #activator="{ props: tipProps }">
                                <span class="fb-toolbar-item" v-bind="tipProps">
                                    <v-btn
                                        icon="$edit"
                                        color="primary-light"
                                        @click="$emit('rename')"
                                    />
                                </span>
                            </template>
                            <span>Rename</span>
                        </v-tooltip>

                        <v-tooltip v-if="canShare" location="bottom">
                            <template #activator="{ props: tipProps }">
                                <span class="fb-toolbar-item" v-bind="tipProps">
                                    <v-btn
                                        icon="$shareVariant"
                                        color="primary-light"
                                        @click="$emit('share')"
                                    />
                                </span>
                            </template>
                            <span>Share</span>
                        </v-tooltip>

                        <v-tooltip v-if="canMove" location="bottom">
                            <template #activator="{ props: tipProps }">
                                <span class="fb-toolbar-item" v-bind="tipProps">
                                    <v-btn
                                        icon="$folderMove"
                                        color="primary-light"
                                        @click="$emit('move')"
                                    />
                                </span>
                            </template>
                            <span>Move to</span>
                        </v-tooltip>

                        <v-tooltip v-if="canDelete" location="bottom">
                            <template #activator="{ props: tipProps }">
                                <span class="fb-toolbar-item" v-bind="tipProps">
                                    <v-btn
                                        icon="$trashCanDv"
                                        color="primary-light"
                                        @click="$emit('delete')"
                                    />
                                </span>
                            </template>
                            <span>Delete</span>
                        </v-tooltip>
                    </template>
                </v-btn-group>

                <div v-if="hasSelect" class="fb-toolbar-divider" />

                <!-- Base actions -->
                <v-btn-group
                    divided
                    variant="text"
                    density="comfortable"
                    class="fb-toolbar"
                >
                    <v-tooltip location="bottom">
                        <template #activator="{ props: tipProps }">
                            <span class="fb-toolbar-item" v-bind="tipProps">
                                <v-btn
                                    icon="$newFile"
                                    color="primary-light"
                                    @click="
                                        $emit('create-config', {
                                            folderId: createCfgFolderId
                                        })
                                    "
                                />
                            </span>
                        </template>
                        <span>New Configuration</span>
                    </v-tooltip>

                    <v-tooltip location="bottom">
                        <template #activator="{ props: tipProps }">
                            <span class="fb-toolbar-item" v-bind="tipProps">
                                <v-btn
                                    icon="$newFolder"
                                    color="primary-light"
                                    :disabled="
                                        isSharedView ||
                                        folderId.startsWith('__')
                                    "
                                    @click="$emit('create-folder')"
                                />
                            </span>
                        </template>
                        <span>New Folder</span>
                    </v-tooltip>

                    <v-tooltip location="bottom">
                        <template #activator="{ props: tipProps }">
                            <span class="fb-toolbar-item" v-bind="tipProps">
                                <v-btn
                                    icon="$cloudDownload"
                                    color="primary-light"
                                    @click="$emit('export-backup')"
                                />
                            </span>
                        </template>
                        <span>Export Backup</span>
                    </v-tooltip>

                    <v-tooltip location="bottom">
                        <template #activator="{ props: tipProps }">
                            <span class="fb-toolbar-item" v-bind="tipProps">
                                <v-btn
                                    icon="$cloudUpload"
                                    color="primary-light"
                                    @click="$emit('restore-backup')"
                                />
                            </span>
                        </template>
                        <span>Restore Backup</span>
                    </v-tooltip>
                </v-btn-group>
            </div>
        </div>
    </div>
</template>

<script setup>
defineProps({
    headerIconClass: { type: String, default: "" },
    headerIcon: { type: String, default: "$folderOpen" },
    headerTitle: { type: String, default: "" },

    canCreate: { type: Boolean, default: false },
    hasSelect: { type: Boolean, default: false },
    mixedSelect: { type: Boolean, default: false },

    canDuplicate: { type: Boolean, default: false },
    canRename: { type: Boolean, default: false },
    canShare: { type: Boolean, default: false },
    canMove: { type: Boolean, default: false },
    canDelete: { type: Boolean, default: false },

    isSharedView: { type: Boolean, default: false },
    folderId: { type: String, default: "" },
    createCfgFolderId: { type: String, default: "" }
});

defineEmits([
    "delete",
    "duplicate",
    "rename",
    "share",
    "move",
    "create-config",
    "create-folder",
    "export-backup",
    "restore-backup"
]);
</script>

<style lang="scss" scoped>
@use "~/assets/css/colors.scss" as *;

.fb-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 10px;
}

.fb-title {
    display: flex;
    align-items: center;
    font-size: 1.05rem;
    font-weight: 600;
    min-width: 0;
}

.fb-title-text {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.fb-header-actions {
    margin-left: auto;
    flex: 0 0 auto;
    display: flex;
    justify-content: flex-end;
    align-items: center;
}

.fb-toolbar-shell {
    display: inline-flex;
    align-items: center;
    padding: 2px 5px;
    border-radius: 12px;
    border: 1px solid rgba(var(--v-theme-font-base), 0.12);
    background: rgba(var(--v-theme-surface-light), 0.35);
    box-shadow:
        0 2px 8px rgba(0, 0, 0, 0.06),
        inset 0 1px 0 rgba(255, 255, 255, 0.18),
        inset 0 -1px 0 rgba(0, 0, 0, 0.02);
    backdrop-filter: blur(8px);
}

.fb-toolbar-divider {
    width: 1px;
    height: 22px;
    margin: 0 6px;
    background: rgba(var(--v-theme-font-base), 0.12);
    flex: 0 0 auto;
}

.fb-toolbar-item {
    display: inline-flex;
}

.fb-toolbar :deep(.v-btn-group) {
    box-shadow: none;
}

.fb-toolbar :deep(.v-btn) {
    min-width: 34px;
    width: 34px;
    height: 34px;
    padding: 0;
    border-radius: 9px;
    color: $primary-light;
    transition:
        background 0.15s ease,
        box-shadow 0.15s ease,
        transform 0.15s ease;
}

.fb-toolbar :deep(.v-btn:hover) {
    background: $surface-light;
    box-shadow:
        0 3px 10px rgba(0, 0, 0, 0.07),
        inset 0 1px 0 rgba(255, 255, 255, 0.2),
        inset 0 -1px 0 rgba(0, 0, 0, 0.025);
}

.fb-toolbar :deep(.v-btn:active) {
    transform: translateY(1px);
}

.fb-ico--folder {
    color: $primary-light;
    opacity: 0.8;
    filter: brightness(1.1);
}

.fb-ico--shared-root,
.fb-ico--shared-project,
.fb-ico--config {
    color: $primary-light;
    opacity: 0.8;
}
</style>
