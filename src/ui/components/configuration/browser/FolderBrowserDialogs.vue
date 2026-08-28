<template>
    <v-dialog v-model="CreateFolderDlg" max-width="520">
        <v-card>
            <v-card-title>Create Folder</v-card-title>
            <v-card-text>
                <v-text-field
                    label="Folder name"
                    v-model="inputFolderName"
                    autofocus
                />
            </v-card-text>
            <v-card-actions>
                <v-spacer />
                <v-btn color="font-light" @click="CreateFolderDlg = false"
                    >Cancel</v-btn
                >
                <v-btn color="primary-light" @click="$emit('create-folder')"
                    >Create</v-btn
                >
            </v-card-actions>
        </v-card>
    </v-dialog>

    <v-dialog v-model="RenameDlg" max-width="520">
        <v-card>
            <v-card-title>Rename</v-card-title>
            <v-card-text>
                <v-text-field
                    label="New name"
                    v-model="inputRename"
                    autofocus
                />
            </v-card-text>
            <v-card-actions>
                <v-spacer />
                <v-btn color="font-light" @click="RenameDlg = false"
                    >Cancel</v-btn
                >
                <v-btn color="primary-light" @click="$emit('rename')"
                    >Save</v-btn
                >
            </v-card-actions>
        </v-card>
    </v-dialog>

    <v-dialog v-model="ShareDlg" max-width="720">
        <v-card>
            <v-card-title>Share configurations</v-card-title>
            <v-card-text>
                <v-autocomplete
                    :items="projects"
                    v-model="shareProjectIds"
                    chips
                    closable-chips
                    multiple
                    item-title="name"
                    item-value="_id"
                    label="Share with Project(s)"
                />
                <div class="text-medium-emphasis text-caption mt-2">
                    Only your own configurations will be updated.
                </div>
            </v-card-text>
            <v-card-actions>
                <v-spacer />
                <v-btn color="font-light" @click="ShareDlg = false"
                    >Cancel</v-btn
                >
                <v-btn color="primary-light" @click="$emit('share')"
                    >Apply</v-btn
                >
            </v-card-actions>
        </v-card>
    </v-dialog>

    <v-dialog v-model="MoveDlg" max-width="720">
        <v-card>
            <v-card-title>Move to...</v-card-title>
            <v-card-text>
                <div class="move-tree">
                    <MoveFolderTreeNode
                        v-for="node in moveFolderTree"
                        :key="node.id || node.path"
                        :node="node"
                        :selected-id="moveDestId"
                        @select="$emit('move-destination', $event)"
                    />
                </div>

                <div class="move-selected mt-4">
                    <span class="text-medium-emphasis"
                        >Selected destination:</span
                    >
                    <span class="ml-2">
                        {{ moveFolderPath || "—" }}
                    </span>
                </div>

                <div class="text-medium-emphasis text-caption mt-2">
                    Only your own configurations could be moved.
                </div>

                <div
                    v-if="
                        moveDestId && moveInvalid && cfgFolderIdSet.size === 1
                    "
                    class="text-warning text-caption mt-2"
                >
                    The selected configuration(s) are already in this folder.
                </div>
            </v-card-text>
            <v-card-actions>
                <v-spacer />
                <v-btn color="font-light" @click="MoveDlg = false"
                    >Cancel</v-btn
                >
                <v-btn
                    color="primary-light"
                    :disabled="moveInvalid"
                    @click="$emit('move')"
                >
                    Move
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

    <v-dialog v-model="DeleteDlg" max-width="600">
        <v-card>
            <v-card-title>Delete</v-card-title>
            <v-card-text>
                <div v-if="selectedFolderIds.length">
                    Selected folders will be deleted recursively (rm -rf).
                </div>
                <div v-if="selectedConfigIds.length" class="mt-2">
                    Selected configurations will be deleted.
                </div>
                <div class="text-medium-emphasis text-caption mt-2">
                    Only items you own (or manager/admin) will be affected.
                </div>
            </v-card-text>
            <v-card-actions>
                <v-spacer />
                <v-btn color="font-light" @click="DeleteDlg = false"
                    >Cancel</v-btn
                >
                <v-btn color="danger" @click="$emit('delete')">Delete</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

    <v-dialog v-model="ExportBackupDlg" max-width="640">
        <v-card class="backup-dialog-card">
            <v-card-title class="backup-dialog-title">
                <div class="backup-dialog-title-wrap">
                    <v-icon
                        icon="$cloudDownload"
                        class="backup-dialog-title-icon"
                    />
                    <div class="backup-dialog-title-texts">
                        <div class="backup-dialog-title-main">
                            Export Backup
                        </div>
                        <div class="backup-dialog-title-sub">
                            Create a JSON backup of configurations and folders.
                        </div>
                    </div>
                </div>
            </v-card-title>

            <v-card-text class="backup-dialog-text">
                <v-select
                    v-model="exportScope"
                    :items="backupScopeItems"
                    item-title="title"
                    item-value="value"
                    label="Export scope"
                    hide-details="auto"
                />

                <v-text-field
                    v-if="exportScope === 'owner'"
                    v-model="exportOwner"
                    label="Target username"
                    class="mt-3"
                    autofocus
                    hide-details="auto"
                />

                <div class="backup-dialog-caption mt-3">
                    Export creates a JSON backup containing configurations and
                    folders for the selected scope.
                </div>
            </v-card-text>

            <v-card-actions class="backup-dialog-actions">
                <v-spacer />
                <v-btn color="font-light" @click="ExportBackupDlg = false">
                    Cancel
                </v-btn>
                <v-btn color="primary-light" @click="$emit('export-backup')">
                    Export
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

    <v-dialog v-model="RestoreBackupDlg" max-width="720">
        <v-card class="backup-dialog-card">
            <v-card-title class="backup-dialog-title">
                <div class="backup-dialog-title-wrap">
                    <v-icon
                        icon="$cloudUpload"
                        class="backup-dialog-title-icon"
                    />
                    <div class="backup-dialog-title-texts">
                        <div class="backup-dialog-title-main">
                            Restore Backup
                        </div>
                        <div class="backup-dialog-title-sub">
                            Upload a backup file and choose how it should be
                            restored.
                        </div>
                    </div>
                </div>
            </v-card-title>

            <v-card-text class="backup-dialog-text">
                <v-file-upload
                    v-model="restoreFile"
                    divider-text="or choose locally"
                    browse-text="Local Filesystem"
                    filter-by-type=".json,application/json"
                    icon="$cloudUpload"
                    title="Drag and Drop Here"
                    show-size
                    clearable
                >
                    <template #item="{ item, props }">
                        <v-file-upload-item
                            v-bind="props"
                            :file="item"
                            file-icon="$jsonRestore"
                        />
                    </template>
                </v-file-upload>

                <v-select
                    class="mt-3"
                    v-model="restoreScope"
                    :items="backupScopeItems"
                    item-title="title"
                    item-value="value"
                    label="Restore scope"
                    hide-details="auto"
                />

                <v-text-field
                    v-if="restoreScope === 'owner'"
                    v-model="restoreOwner"
                    label="Target username"
                    class="mt-3"
                    hide-details="auto"
                />

                <v-select
                    class="mt-3"
                    v-model="restoreConflictStrategy"
                    :items="conflictStrategyItems"
                    item-title="title"
                    item-value="value"
                    label="Conflict strategy"
                    hide-details="auto"
                />

                <div class="backup-dialog-caption mt-3">
                    <div>
                        <strong>Overwrite</strong>: overwrite duplicate
                        configurations and update duplicate folders.
                    </div>
                    <div>
                        <strong>Rename</strong>: restore duplicates with a new
                        name.
                    </div>
                    <div>
                        <strong>Skip</strong>: skip duplicate configurations and
                        reuse duplicate folders.
                    </div>
                </div>

                <div class="backup-dialog-caption mt-2">
                    Restoring to <strong>My configurations</strong> or
                    <strong>Specific user</strong> clears shared project
                    assignments. <strong>All users</strong> preserves original
                    owners.
                </div>
            </v-card-text>

            <v-card-actions class="backup-dialog-actions">
                <v-spacer />
                <v-btn color="font-light" @click="RestoreBackupDlg = false">
                    Cancel
                </v-btn>
                <v-btn color="primary-light" @click="$emit('restore-backup')">
                    Restore
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

    <v-dialog v-model="RestoreResultDlg" max-width="760">
        <v-card class="restore-result-card">
            <v-card-title class="restore-result-title">
                <div class="restore-result-title-wrap">
                    <v-icon
                        icon="$cloudUpload"
                        class="restore-result-title-icon"
                    />
                    <div class="restore-result-title-texts">
                        <div class="restore-result-title-main">
                            Restore Summary
                        </div>
                        <div class="restore-result-title-sub">
                            Backup restore completed successfully
                        </div>
                    </div>
                </div>
            </v-card-title>

            <v-card-text v-if="restoreSummary">
                <div class="restore-meta-card">
                    <div class="restore-meta-card-title">Restore Details</div>

                    <div class="restore-meta-grid">
                        <div class="restore-meta-row">
                            <span class="restore-meta-label">Restore To</span>
                            <span class="restore-meta-value">
                                {{
                                    restoreModeLabel(restoreSummary.restoreMode)
                                }}
                            </span>
                        </div>

                        <div class="restore-meta-row">
                            <span class="restore-meta-label"
                                >Duplicate Handling</span
                            >
                            <span class="restore-meta-value">
                                {{ restoreSummary.conflictStrategy }}
                            </span>
                        </div>

                        <div
                            v-if="restoreSummary.targetOwner"
                            class="restore-meta-row"
                        >
                            <span class="restore-meta-label">Destination</span>
                            <span class="restore-meta-value">
                                {{ restoreSummary.targetOwner }}
                            </span>
                        </div>
                    </div>
                </div>

                <div class="restore-stat-grid">
                    <div class="restore-stat-card">
                        <div class="restore-stat-card-title">
                            Folder Results
                        </div>

                        <div class="restore-summary-list">
                            <div class="restore-summary-row">
                                <span class="restore-summary-label"
                                    >Created</span
                                >
                                <span class="restore-summary-value">
                                    {{ restoreSummary.foldersCreated }}
                                </span>
                            </div>

                            <div class="restore-summary-row">
                                <span class="restore-summary-label"
                                    >Matched Existing</span
                                >
                                <span class="restore-summary-value">
                                    {{ restoreSummary.foldersMerged }}
                                </span>
                            </div>

                            <div class="restore-summary-row">
                                <span class="restore-summary-label"
                                    >Renamed</span
                                >
                                <span class="restore-summary-value">
                                    {{ restoreSummary.foldersRenamed }}
                                </span>
                            </div>

                            <div class="restore-summary-row">
                                <span class="restore-summary-label">
                                    Overwritten
                                </span>
                                <span class="restore-summary-value">
                                    {{ restoreSummary.foldersOverwritten }}
                                </span>
                            </div>
                        </div>
                    </div>

                    <div class="restore-stat-card">
                        <div class="restore-stat-card-title">
                            Configuration Results
                        </div>

                        <div class="restore-summary-list">
                            <div class="restore-summary-row">
                                <span class="restore-summary-label"
                                    >Created</span
                                >
                                <span class="restore-summary-value">
                                    {{ restoreSummary.configurationsCreated }}
                                </span>
                            </div>

                            <div class="restore-summary-row">
                                <span class="restore-summary-label"
                                    >Skipped</span
                                >
                                <span class="restore-summary-value">
                                    {{ restoreSummary.configurationsSkipped }}
                                </span>
                            </div>

                            <div class="restore-summary-row">
                                <span class="restore-summary-label"
                                    >Renamed</span
                                >
                                <span class="restore-summary-value">
                                    {{ restoreSummary.configurationsRenamed }}
                                </span>
                            </div>

                            <div class="restore-summary-row">
                                <span class="restore-summary-label">
                                    Overwritten
                                </span>
                                <span class="restore-summary-value">
                                    {{
                                        restoreSummary.configurationsOverwritten
                                    }}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </v-card-text>

            <v-card-actions class="restore-result-actions">
                <v-spacer />
                <v-btn color="primary-light" @click="RestoreResultDlg = false">
                    Close
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script setup>
import { computed } from "vue";
import MoveFolderTreeNode from "./MoveFolderTreeNode.vue";

const props = defineProps({
    createFolder: { type: Boolean, default: false },
    rename: { type: Boolean, default: false },
    share: { type: Boolean, default: false },
    move: { type: Boolean, default: false },
    delete: { type: Boolean, default: false },
    exportBackup: { type: Boolean, default: false },
    restoreBackup: { type: Boolean, default: false },
    restoreResult: { type: Boolean, default: false },

    inputFolderName: { type: String, default: "" },
    inputRename: { type: String, default: "" },
    shareProjectIds: { type: Array, default: () => [] },

    moveDestId: { type: String, default: "" },
    moveFolderTree: { type: Array, default: () => [] },
    moveFolderPath: { type: String, default: "" },
    moveInvalid: { type: Boolean, default: false },
    cfgFolderIdSet: { type: Object, required: true },

    selectedFolderIds: { type: Array, default: () => [] },
    selectedConfigIds: { type: Array, default: () => [] },

    projects: { type: Array, default: () => [] },

    exportScope: { type: String, default: "self" },
    exportOwner: { type: String, default: "" },

    restoreFile: { default: null },
    restoreScope: { type: String, default: "self" },
    restoreOwner: { type: String, default: "" },
    restoreConflictStrategy: { type: String, default: "rename" },
    restoreSummary: { type: Object, default: null },

    backupScopeItems: { type: Array, default: () => [] },
    conflictStrategyItems: { type: Array, default: () => [] },
    restoreModeLabel: { type: Function, required: true }
});

const emit = defineEmits([
    "update:createFolder",
    "update:rename",
    "update:share",
    "update:move",
    "update:delete",
    "update:exportBackup",
    "update:restoreBackup",
    "update:restoreResult",

    "update:inputFolderName",
    "update:inputRename",
    "update:shareProjectIds",
    "update:moveDestId",

    "update:exportScope",
    "update:exportOwner",
    "update:restoreFile",
    "update:restoreScope",
    "update:restoreOwner",
    "update:restoreConflictStrategy",

    "create-folder",
    "rename",
    "share",
    "move",
    "delete",
    "export-backup",
    "restore-backup",
    "move-destination"
]);

const model = (prop, event) =>
    computed({
        get: () => props[prop],
        set: (v) => emit(event, v)
    });

const CreateFolderDlg = model("createFolder", "update:createFolder");
const RenameDlg = model("rename", "update:rename");
const ShareDlg = model("share", "update:share");
const MoveDlg = model("move", "update:move");
const DeleteDlg = model("delete", "update:delete");
const ExportBackupDlg = model("exportBackup", "update:exportBackup");
const RestoreBackupDlg = model("restoreBackup", "update:restoreBackup");
const RestoreResultDlg = model("restoreResult", "update:restoreResult");

const inputFolderName = model("inputFolderName", "update:inputFolderName");
const inputRename = model("inputRename", "update:inputRename");
const shareProjectIds = model("shareProjectIds", "update:shareProjectIds");

const moveDestId = model("moveDestId", "update:moveDestId");

const exportScope = model("exportScope", "update:exportScope");
const exportOwner = model("exportOwner", "update:exportOwner");

const restoreFile = model("restoreFile", "update:restoreFile");
const restoreScope = model("restoreScope", "update:restoreScope");
const restoreOwner = model("restoreOwner", "update:restoreOwner");
const restoreConflictStrategy = model(
    "restoreConflictStrategy",
    "update:restoreConflictStrategy"
);
</script>

<style lang="scss" scoped>
@use "~/assets/css/colors.scss" as *;

.backup-dialog-card {
    overflow: hidden;
}

.backup-dialog-title {
    padding-bottom: 10px;
}

.backup-dialog-title-wrap {
    display: flex;
    align-items: center;
    gap: 12px;
}

.backup-dialog-title-icon {
    color: $primary-light;
    opacity: 0.9;
}

.backup-dialog-title-texts {
    display: flex;
    flex-direction: column;
    min-width: 0;
}

.backup-dialog-title-main {
    font-size: 1.05rem;
    font-weight: 600;
    color: $font-base;
    line-height: 1.2;
}

.backup-dialog-title-sub {
    font-size: 0.82rem;
    color: $font-light;
    margin-top: 2px;
}

.backup-dialog-text {
    padding-top: 8px;
}

.backup-dialog-caption {
    color: $font-light;
    font-size: 0.82rem;
    line-height: 1.45;
}

.backup-dialog-actions {
    padding-top: 6px;
}

.restore-result-card {
    overflow: hidden;
}

.restore-result-title {
    padding-bottom: 10px;
}

.restore-result-title-wrap {
    display: flex;
    align-items: center;
    gap: 12px;
}

.restore-result-title-icon {
    color: $primary-light;
    opacity: 0.9;
}

.restore-result-title-texts {
    display: flex;
    flex-direction: column;
    min-width: 0;
}

.restore-result-title-main {
    font-size: 1.05rem;
    font-weight: 600;
    color: $font-base;
    line-height: 1.2;
}

.restore-result-title-sub {
    font-size: 0.82rem;
    color: $font-light;
    margin-top: 2px;
}

.restore-meta-card {
    padding: 12px 14px;
    border-radius: 12px;
    background: rgba(var(--v-theme-surface-light), 0.55);
    border: 1px solid rgba(var(--v-theme-font-base), 0.06);
    margin-bottom: 14px;
}

.restore-meta-card-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: $font-base;
    margin-bottom: 10px;
}

.restore-meta-grid {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.restore-meta-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
}

.restore-meta-label {
    color: $font-base;
    font-size: 0.88rem;
}

.restore-meta-value {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 26px;
    padding: 0 10px;
    border-radius: 999px;
    background: rgba(var(--v-theme-primary-light), 0.12);
    color: $primary-light;
    font-size: 0.84rem;
    font-weight: 600;
    line-height: 1;
    text-transform: capitalize;
    white-space: nowrap;
}

.restore-stat-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
}

.restore-stat-card {
    padding: 12px 14px;
    border-radius: 12px;
    background: rgba(var(--v-theme-surface-light), 0.6);
    border: 1px solid rgba(var(--v-theme-font-base), 0.06);
}

.restore-stat-card-title {
    font-size: 0.92rem;
    font-weight: 600;
    color: $font-base;
    margin-bottom: 10px;
}

.restore-summary-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.restore-summary-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 8px 10px;
    border-radius: 10px;
    background: rgba(var(--v-theme-background), 0.45);
    border: 1px solid rgba(var(--v-theme-font-base), 0.05);
}

.restore-summary-label {
    color: $font-base;
    font-size: 0.9rem;
}

.restore-summary-value {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 38px;
    height: 26px;
    padding: 0 10px;
    border-radius: 999px;
    background: $highlight;
    color: $primary-light;
    font-variant-numeric: tabular-nums;
    font-weight: 700;
    line-height: 1;
    flex: 0 0 auto;
}

.restore-result-actions {
    padding-top: 6px;
}

@media (max-width: 760px) {
    .restore-stat-grid {
        grid-template-columns: 1fr;
    }
}
</style>
