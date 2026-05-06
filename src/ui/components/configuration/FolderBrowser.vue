<template>
    <v-main style="--v-layout-bottom: 0; --v-layout-top: 0px">
        <div class="fb">
            <div v-if="!folder" class="fb-empty text-medium-emphasis">
                Select a folder to browse, or select a configuration to edit.
            </div>

            <div v-else class="fb-wrap">
                <FolderBrowserToolbar
                    :header-icon-class="headerIconClass"
                    :header-icon="headerIcon"
                    :header-title="headerTitle"
                    :can-create="canCreate"
                    :has-select="hasSelect"
                    :mixed-select="mixedSelect"
                    :can-duplicate="canDuplicate"
                    :can-rename="canRename"
                    :can-share="canShare"
                    :can-move="canMove"
                    :can-delete="canDelete"
                    :is-shared-view="isSharedView"
                    :folder-id="folderId"
                    :create-cfg-folder-id="createCfgFolderId"
                    @delete="openDelete"
                    @duplicate="duplicateConfig"
                    @rename="openRename"
                    @share="openShare"
                    @move="openMove"
                    @create-config="$emit('create-config', $event)"
                    @create-folder="openCreateFolder"
                    @export-backup="openExportBackup"
                    @restore-backup="openRestoreBackup"
                />

                <div v-if="hasSelect" class="fb-selection-info">
                    <span>
                        {{ selectedFolderIds.length }} folder<span
                            v-if="selectedFolderIds.length !== 1"
                            >s</span
                        >, {{ selectedConfigIds.length }} configuration<span
                            v-if="selectedConfigIds.length !== 1"
                            >s</span
                        >
                        selected
                    </span>

                    <v-btn
                        variant="text"
                        density="comfortable"
                        size="small"
                        prepend-icon="$close"
                        color="info"
                        @click="setSelected([])"
                        title="Clear selection"
                    >
                        Clear selection
                    </v-btn>
                </div>

                <FolderBrowserTable
                    v-model:header-check="headerCheck"
                    :header-state="headerState"
                    :row-grid-style="rowGridStyle"
                    :sort-by="sortBy"
                    :sort-desc="sortDesc"
                    :can-go-up="canGoUp"
                    :parent-id="parentId"
                    :sorted-folders="sortedFolders"
                    :sorted-configs="sortedConfigs"
                    :folder-token="folderToken"
                    :config-token="configToken"
                    :is-selected="isSelected"
                    :child-folder-icon="childFolderIcon"
                    :child-folder-icon-class="childFolderIconClass"
                    :format-date="formatDate"
                    @set-sort="setSort"
                    @toggle-select="toggleSelect"
                    @open-folder="$emit('open-folder', $event)"
                    @open-config="$emit('open-config', $event)"
                />
            </div>
        </div>
        <FolderBrowserDialogs
            v-model:create-folder="CreateFolderDlg"
            v-model:rename="RenameDlg"
            v-model:share="ShareDlg"
            v-model:move="MoveDlg"
            v-model:delete="DeleteDlg"
            v-model:export-backup="ExportBackupDlg"
            v-model:restore-backup="RestoreBackupDlg"
            v-model:restore-result="RestoreResultDlg"
            v-model:input-folder-name="inputFolderName"
            v-model:input-rename="inputRename"
            v-model:share-project-ids="shareProjectIds"
            v-model:move-dest-id="moveDestId"
            v-model:export-scope="exportScope"
            v-model:export-owner="exportOwner"
            v-model:restore-file="restoreFile"
            v-model:restore-scope="restoreScope"
            v-model:restore-owner="restoreOwner"
            v-model:restore-conflict-strategy="restoreConflictStrategy"
            :projects="projects"
            :move-folder-tree="moveFolderTree"
            :move-folder-path="moveFolderPath"
            :move-invalid="moveInvalid"
            :cfg-folder-id-set="cfgFolderIdSet"
            :selected-folder-ids="selectedFolderIds"
            :selected-config-ids="selectedConfigIds"
            :backup-scope-items="backupScopeItems"
            :conflict-strategy-items="conflictStrategyItems"
            :restore-summary="restoreSummary"
            :restore-mode-label="restoreModeLabel"
            @create-folder="createFolder"
            @rename="applyRename"
            @share="applyShare"
            @move="applyMove"
            @delete="applyDelete"
            @export-backup="applyExportBackup"
            @restore-backup="applyRestoreBackup"
            @move-destination="moveDestination"
        />
    </v-main>
</template>

<script setup>
import FolderBrowserDialogs from "./browser/FolderBrowserDialogs.vue";
import FolderBrowserTable from "./browser/FolderBrowserTable.vue";
import FolderBrowserToolbar from "./browser/FolderBrowserToolbar.vue";
import { useFolderBrowser } from "~/composables/useFolderBrowser";

const props = defineProps({
    folder: { type: Object, default: null }, // expects { id, name, children?, __parentId? }
    configs: { type: Array, default: () => [] },
    userName: { type: String, required: true },
    projects: { type: Array, default: () => [] },
    userLevel: { type: Number, required: true },
    UserLevelEnum: { type: Object, required: true },
    myRootId: { type: String, default: "" },
    selected: { type: Array, default: () => [] } // string tokens: "f:<id>" | "c:<id>"
});

const emit = defineEmits([
    "open-folder",
    "open-config",
    "create-config",
    "create-folder",
    "duplicate",
    "update:selected",
    "refresh"
]);

const {
    selectItems,
    selectedSet,
    folderToken,
    configToken,
    isSelected,
    setSelected,
    toggleSelect,
    selectedTokens,
    selectedFolderIds,
    selectedConfigIds,
    hasSelect,
    mixedSelect,
    configById,
    ownSelectConfigIds,
    cfgFolderIds,
    cfgFolderIdSet,
    moveInvalid,
    folderNodeById,
    ownSelectFolderIds,
    canDownload,
    canShare,
    canRename,
    canDuplicate,
    canMove,
    canDelete,
    canCreate,
    isPrivileged,
    backupScopeItems,
    conflictStrategyItems,
    isMyRoot,
    headerTitle,
    folderId,
    isSharedView,
    isSharedRoot,
    isSharedProject,
    parentId,
    canGoUp,
    folders,
    sortBy,
    sortDesc,
    setSort,
    normalizeString,
    parseDateValue,
    compareValues,
    sortedFolders,
    sortedConfigs,
    visibleTokens,
    headerCheck,
    headerState,
    rowGridStyle,
    headerIcon,
    headerIconClass,
    childFolderIcon,
    childFolderIconClass,
    formatDate,
    restoreModeLabel,
    CreateFolderDlg,
    RenameDlg,
    MoveDlg,
    ShareDlg,
    DeleteDlg,
    ExportBackupDlg,
    RestoreBackupDlg,
    RestoreResultDlg,
    exportScope,
    exportOwner,
    restoreFile,
    restoreScope,
    restoreOwner,
    restoreConflictStrategy,
    restoreSummary,
    inputFolderName,
    inputRename,
    shareProjectIds,
    moveDestId,
    moveFolderTree,
    moveFolderPath,
    selectedRestoreFile,
    normalizeOwner,
    getErrorMessage,
    clearDialogs,
    createCfgFolderId,
    duplicateConfig,
    openCreateFolder,
    normalizeName,
    sibFolderName,
    sibConfigName,
    createFolder,
    downloadSelected,
    openExportBackup,
    applyExportBackup,
    openRestoreBackup,
    applyRestoreBackup,
    openShare,
    applyShare,
    openRename,
    applyRename,
    buildMoveTree,
    findUserHomeTree,
    openMove,
    moveDestination,
    selectMoveDestination,
    applyMove,
    openDelete,
    applyDelete
} = useFolderBrowser(props, emit);
</script>

<style lang="scss" scoped>
@use "~/assets/css/colors.scss" as *;

.fb {
    padding: 16px;
}

.fb-empty {
    padding: 24px;
}

.fb-wrap {
    max-width: 100%;
}

.fb-selection-info {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 0 0 10px;
    font-size: 0.88rem;
    color: $font-light;
}

.fb-selection-info :deep(.v-btn) {
    padding-inline: 6px;
}
</style>
