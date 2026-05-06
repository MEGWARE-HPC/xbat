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
                    <v-btn color="primary-light" @click="createFolder"
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
                    <v-btn color="primary-light" @click="applyRename"
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
                    <v-btn color="primary-light" @click="applyShare"
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
                            @select="moveDestination"
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
                            moveDestId &&
                            moveInvalid &&
                            cfgFolderIdSet.size === 1
                        "
                        class="text-warning text-caption mt-2"
                    >
                        The selected configuration(s) are already in this
                        folder.
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
                        @click="applyMove"
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
                    <v-btn color="danger" @click="applyDelete">Delete</v-btn>
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
                                Create a JSON backup of configurations and
                                folders.
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
                        Export creates a JSON backup containing configurations
                        and folders for the selected scope.
                    </div>
                </v-card-text>

                <v-card-actions class="backup-dialog-actions">
                    <v-spacer />
                    <v-btn color="font-light" @click="ExportBackupDlg = false">
                        Cancel
                    </v-btn>
                    <v-btn color="primary-light" @click="applyExportBackup">
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
                            <strong>Rename</strong>: restore duplicates with a
                            new name.
                        </div>
                        <div>
                            <strong>Skip</strong>: skip duplicate configurations
                            and reuse duplicate folders.
                        </div>
                    </div>

                    <div class="backup-dialog-caption mt-2">
                        Restoring to <strong>My configurations</strong> or
                        <strong>Specific user</strong> clears shared project
                        assignments. <strong>All users</strong> preserves
                        original owners.
                    </div>
                </v-card-text>

                <v-card-actions class="backup-dialog-actions">
                    <v-spacer />
                    <v-btn color="font-light" @click="RestoreBackupDlg = false">
                        Cancel
                    </v-btn>
                    <v-btn color="primary-light" @click="applyRestoreBackup">
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
                        <div class="restore-meta-card-title">
                            Restore Details
                        </div>

                        <div class="restore-meta-grid">
                            <div class="restore-meta-row">
                                <span class="restore-meta-label"
                                    >Restore To</span
                                >
                                <span class="restore-meta-value">
                                    {{
                                        restoreModeLabel(
                                            restoreSummary.restoreMode
                                        )
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
                                <span class="restore-meta-label"
                                    >Destination</span
                                >
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
                                        {{
                                            restoreSummary.configurationsCreated
                                        }}
                                    </span>
                                </div>

                                <div class="restore-summary-row">
                                    <span class="restore-summary-label"
                                        >Skipped</span
                                    >
                                    <span class="restore-summary-value">
                                        {{
                                            restoreSummary.configurationsSkipped
                                        }}
                                    </span>
                                </div>

                                <div class="restore-summary-row">
                                    <span class="restore-summary-label"
                                        >Renamed</span
                                    >
                                    <span class="restore-summary-value">
                                        {{
                                            restoreSummary.configurationsRenamed
                                        }}
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
                    <v-btn
                        color="primary-light"
                        @click="RestoreResultDlg = false"
                    >
                        Close
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </v-main>
</template>

<script setup>
import MoveFolderTreeNode from "./browser/MoveFolderTreeNode.vue";
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
