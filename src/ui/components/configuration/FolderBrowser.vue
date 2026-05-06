<template>
    <v-main style="--v-layout-bottom: 0; --v-layout-top: 0px">
        <div class="fb">
            <div v-if="!folder" class="fb-empty text-medium-emphasis">
                Select a folder to browse, or select a configuration to edit.
            </div>

            <div v-else class="fb-wrap">
                <!-- Header -->
                <div class="fb-header">
                    <div class="fb-title">
                        <v-icon
                            class="mr-2"
                            :class="headerIconClass"
                            :icon="headerIcon"
                        />
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
                                        <template
                                            #activator="{ props: tipProps }"
                                        >
                                            <span
                                                class="fb-toolbar-item"
                                                v-bind="tipProps"
                                            >
                                                <v-btn
                                                    icon="$trashCanDv"
                                                    color="primary-light"
                                                    @click="openDelete()"
                                                />
                                            </span>
                                        </template>
                                        <span>Delete</span>
                                    </v-tooltip>
                                </template>

                                <template v-else>
                                    <v-tooltip
                                        v-if="canDuplicate"
                                        location="bottom"
                                    >
                                        <template
                                            #activator="{ props: tipProps }"
                                        >
                                            <span
                                                class="fb-toolbar-item"
                                                v-bind="tipProps"
                                            >
                                                <v-btn
                                                    icon="$duplicate"
                                                    color="primary-light"
                                                    @click="duplicateConfig()"
                                                />
                                            </span>
                                        </template>
                                        <span>Duplicate</span>
                                    </v-tooltip>

                                    <v-tooltip
                                        v-if="canRename"
                                        location="bottom"
                                    >
                                        <template
                                            #activator="{ props: tipProps }"
                                        >
                                            <span
                                                class="fb-toolbar-item"
                                                v-bind="tipProps"
                                            >
                                                <v-btn
                                                    icon="$edit"
                                                    color="primary-light"
                                                    @click="openRename()"
                                                />
                                            </span>
                                        </template>
                                        <span>Rename</span>
                                    </v-tooltip>

                                    <v-tooltip
                                        v-if="canShare"
                                        location="bottom"
                                    >
                                        <template
                                            #activator="{ props: tipProps }"
                                        >
                                            <span
                                                class="fb-toolbar-item"
                                                v-bind="tipProps"
                                            >
                                                <v-btn
                                                    icon="$shareVariant"
                                                    color="primary-light"
                                                    @click="openShare()"
                                                />
                                            </span>
                                        </template>
                                        <span>Share</span>
                                    </v-tooltip>

                                    <v-tooltip v-if="canMove" location="bottom">
                                        <template
                                            #activator="{ props: tipProps }"
                                        >
                                            <span
                                                class="fb-toolbar-item"
                                                v-bind="tipProps"
                                            >
                                                <v-btn
                                                    icon="$folderMove"
                                                    color="primary-light"
                                                    @click="openMove()"
                                                />
                                            </span>
                                        </template>
                                        <span>Move to</span>
                                    </v-tooltip>

                                    <v-tooltip
                                        v-if="canDelete"
                                        location="bottom"
                                    >
                                        <template
                                            #activator="{ props: tipProps }"
                                        >
                                            <span
                                                class="fb-toolbar-item"
                                                v-bind="tipProps"
                                            >
                                                <v-btn
                                                    icon="$trashCanDv"
                                                    color="primary-light"
                                                    @click="openDelete()"
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
                                        <span
                                            class="fb-toolbar-item"
                                            v-bind="tipProps"
                                        >
                                            <v-btn
                                                icon="$newFile"
                                                color="primary-light"
                                                @click="
                                                    $emit('create-config', {
                                                        folderId:
                                                            createCfgFolderId
                                                    })
                                                "
                                            />
                                        </span>
                                    </template>
                                    <span>New Configuration</span>
                                </v-tooltip>

                                <v-tooltip location="bottom">
                                    <template #activator="{ props: tipProps }">
                                        <span
                                            class="fb-toolbar-item"
                                            v-bind="tipProps"
                                        >
                                            <v-btn
                                                icon="$newFolder"
                                                color="primary-light"
                                                :disabled="
                                                    isSharedView ||
                                                    folderId.startsWith('__')
                                                "
                                                @click="openCreateFolder()"
                                            />
                                        </span>
                                    </template>
                                    <span>New Folder</span>
                                </v-tooltip>

                                <v-tooltip location="bottom">
                                    <template #activator="{ props: tipProps }">
                                        <span
                                            class="fb-toolbar-item"
                                            v-bind="tipProps"
                                        >
                                            <v-btn
                                                icon="$cloudDownload"
                                                color="primary-light"
                                                @click="openExportBackup()"
                                            />
                                        </span>
                                    </template>
                                    <span>Export Backup</span>
                                </v-tooltip>

                                <v-tooltip location="bottom">
                                    <template #activator="{ props: tipProps }">
                                        <span
                                            class="fb-toolbar-item"
                                            v-bind="tipProps"
                                        >
                                            <v-btn
                                                icon="$cloudUpload"
                                                color="primary-light"
                                                @click="openRestoreBackup()"
                                            />
                                        </span>
                                    </template>
                                    <span>Restore Backup</span>
                                </v-tooltip>
                            </v-btn-group>
                        </div>
                    </div>
                </div>

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

                <!-- Table header -->
                <div class="fb-row fb-row--head" :style="rowGridStyle">
                    <div class="fb-col fb-col--check">
                        <v-checkbox-btn
                            v-model="headerCheck"
                            :indeterminate="headerState"
                            density="compact"
                            class="fb-check fb-check--head"
                            @click.stop
                        />
                    </div>

                    <div
                        class="fb-col fb-col--name fb-head-sort"
                        :class="{ 'is-active': sortBy === 'name' }"
                        @click="setSort('name')"
                    >
                        <span>Name</span>
                        <v-icon
                            v-if="sortBy === 'name'"
                            size="small"
                            class="fb-head-sort-icon"
                            :icon="
                                sortDesc ? '$sortAlphaAsc' : '$sortAlphaDesc'
                            "
                        />
                    </div>

                    <div
                        class="fb-col fb-col--owner fb-head-sort"
                        :class="{ 'is-active': sortBy === 'owner' }"
                        @click="setSort('owner')"
                    >
                        <span>Owner</span>
                        <v-icon
                            v-if="sortBy === 'owner'"
                            size="small"
                            class="fb-head-sort-icon"
                            :icon="
                                sortDesc ? '$sortAlphaAsc' : '$sortAlphaDesc'
                            "
                        />
                    </div>

                    <div
                        class="fb-col fb-col--created fb-head-sort"
                        :class="{ 'is-active': sortBy === 'created' }"
                        @click="setSort('created')"
                    >
                        <span>Created</span>
                        <v-icon
                            v-if="sortBy === 'created'"
                            size="small"
                            class="fb-head-sort-icon"
                            :icon="sortDesc ? '$sortNumAsc' : '$sortNumDesc'"
                        />
                    </div>

                    <div
                        class="fb-col fb-col--edited fb-head-sort"
                        :class="{ 'is-active': sortBy === 'edited' }"
                        @click="setSort('edited')"
                    >
                        <span>Modified</span>
                        <v-icon
                            v-if="sortBy === 'edited'"
                            size="small"
                            class="fb-head-sort-icon"
                            :icon="sortDesc ? '$sortNumAsc' : '$sortNumDesc'"
                        />
                    </div>
                </div>

                <v-list class="fb-list" density="compact">
                    <!-- .. (go up) -->
                    <v-list-item
                        v-if="canGoUp"
                        class="fb-rowitem"
                        @click="$emit('open-folder', parentId)"
                    >
                        <v-list-item-title>
                            <div class="fb-row" :style="rowGridStyle">
                                <div class="fb-col fb-col--check"></div>

                                <div class="fb-col fb-col--name fb-name">
                                    <div class="fb-name-wrap">
                                        <v-icon
                                            icon="$arrowLeftTop"
                                            class="fb-ico fb-ico--nav"
                                        />
                                        <span>..</span>
                                    </div>
                                </div>

                                <div class="fb-col fb-col--owner fb-owner">
                                    —
                                </div>
                                <div class="fb-col fb-col--created fb-date">
                                    —
                                </div>
                                <div class="fb-col fb-col--edited fb-date">
                                    —
                                </div>
                            </div>
                        </v-list-item-title>
                    </v-list-item>

                    <!-- folders -->
                    <v-list-item
                        v-for="child in sortedFolders"
                        :key="'f-' + child.id"
                        class="fb-rowitem"
                        @click="$emit('open-folder', child.id)"
                    >
                        <v-list-item-title>
                            <div class="fb-row" :style="rowGridStyle">
                                <div class="fb-col fb-col--check">
                                    <v-checkbox-btn
                                        :model-value="
                                            isSelected(folderToken(child.id))
                                        "
                                        density="compact"
                                        class="fb-check fb-check--row"
                                        @click.stop
                                        @update:modelValue="
                                            toggleSelect(folderToken(child.id))
                                        "
                                    />
                                </div>

                                <div class="fb-col fb-col--name fb-name">
                                    <div class="fb-name-wrap">
                                        <v-icon
                                            :icon="childFolderIcon"
                                            class="fb-ico"
                                            :class="childFolderIconClass"
                                        />
                                        <span>{{ child.name }}</span>
                                    </div>
                                </div>

                                <div class="fb-col fb-col--owner fb-owner">
                                    {{ child?.misc?.owner || "—" }}
                                </div>
                                <div class="fb-col fb-col--created fb-date">
                                    {{ formatDate(child?.misc?.created) }}
                                </div>
                                <div class="fb-col fb-col--edited fb-date">
                                    {{ formatDate(child?.misc?.edited) }}
                                </div>
                            </div>
                        </v-list-item-title>
                    </v-list-item>

                    <!-- configs -->
                    <v-list-item
                        v-for="c in sortedConfigs"
                        :key="'c-' + c.id"
                        class="fb-rowitem"
                        @click="$emit('open-config', c.id)"
                    >
                        <v-list-item-title>
                            <div class="fb-row" :style="rowGridStyle">
                                <div class="fb-col fb-col--check">
                                    <v-checkbox-btn
                                        :model-value="
                                            isSelected(configToken(c.id))
                                        "
                                        density="compact"
                                        class="fb-check fb-check--row"
                                        @click.stop
                                        @update:modelValue="
                                            toggleSelect(configToken(c.id))
                                        "
                                    />
                                </div>

                                <div class="fb-col fb-col--name fb-name">
                                    <div class="fb-name-wrap">
                                        <v-icon
                                            class="fb-ico fb-ico--config"
                                            :icon="
                                                c.doc?.configuration
                                                    ?.sharedProjects?.length
                                                    ? '$share'
                                                    : '$textBox'
                                            "
                                            color="primary-light"
                                        />
                                        <span>
                                            {{
                                                c.doc?.configuration
                                                    ?.configurationName || c.id
                                            }}
                                        </span>
                                    </div>
                                </div>

                                <div class="fb-col fb-col--owner fb-owner">
                                    {{ c.doc?.misc?.owner || "—" }}
                                </div>
                                <div class="fb-col fb-col--created fb-date">
                                    {{ formatDate(c.doc?.misc?.created) }}
                                </div>
                                <div class="fb-col fb-col--edited fb-date">
                                    {{ formatDate(c.doc?.misc?.edited) }}
                                </div>
                            </div>
                        </v-list-item-title>
                    </v-list-item>

                    <!-- empty state -->
                    <v-list-item
                        v-if="
                            !canGoUp &&
                            sortedFolders.length === 0 &&
                            sortedConfigs.length === 0
                        "
                        class="text-medium-emphasis"
                        title="This folder is empty"
                    />
                </v-list>
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

.fb-list {
    border-radius: 8px;
    overflow: hidden;
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

.fb-row {
    display: grid;
    grid-template-columns: var(--fb-cols, 32px 1fr 160px 160px);
    align-items: center;
    gap: 10px;
    width: 100%;
}

.fb-row--head {
    padding: 8px 12px;
    font-size: 0.78rem;
    font-weight: 600;
    opacity: 0.8;
    border-bottom: 1px solid rgba(var(--v-theme-font-base), 0.08);
}

.fb-col {
    min-width: 0;
}

.fb-col--check {
    display: flex;
    align-items: center;
    justify-content: center;
}

.fb-check {
    margin: 0;
}

.fb-check--row :deep(.v-icon) {
    font-size: 19px !important;
}

.fb-check--row :deep(.v-selection-control__wrapper) {
    width: 20px;
    height: 20px;
}

.fb-name {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.fb-name-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
}

.fb-owner {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: $font-light;
    font-size: 0.82rem;
}

.fb-date {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    text-align: right;
    color: $font-light;
    font-size: 0.82rem;
}

.fb-rowitem :deep(.v-list-item-title) {
    width: 100%;
}

.fb-rowitem :deep(.v-list-item__content) {
    overflow: hidden;
}

.fb-ico {
    margin-inline-end: 0;
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

.fb-ico--nav {
    color: $primary-light;
    opacity: 0.7;
}

.fb-head-sort {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    cursor: pointer;
    user-select: none;
}

.fb-head-sort:hover {
    opacity: 1;
}

.fb-head-sort.is-active {
    color: $font-base;
}

.fb-head-sort-icon {
    flex: 0 0 auto;
}
</style>
