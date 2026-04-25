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

                            <div v-if="hasSelect" class="fb-toolbar-divider" />

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

                    <div class="backup-dialog-note mt-3">
                        <v-icon
                            icon="$information"
                            class="backup-dialog-note-icon"
                            size="small"
                        />
                        <span>
                            The exported file includes all folders and
                            configurations available in the selected scope.
                        </span>
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
            <v-card>
                <v-card-title>Restore Backup</v-card-title>
                <v-card-text>
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
                        class="mt-2"
                        v-model="restoreScope"
                        :items="backupScopeItems"
                        item-title="title"
                        item-value="value"
                        label="Restore scope"
                    />

                    <v-text-field
                        v-if="restoreScope === 'owner'"
                        v-model="restoreOwner"
                        label="Target username"
                    />

                    <v-select
                        class="mt-2"
                        v-model="restoreConflictStrategy"
                        :items="conflictStrategyItems"
                        item-title="title"
                        item-value="value"
                        label="Conflict strategy"
                    />

                    <div class="text-medium-emphasis text-caption mt-2">
                        <div>
                            <strong>overwrite</strong>: overwrite duplicate
                            configurations and update duplicate folders
                        </div>
                        <div>
                            <strong>rename</strong>: restore duplicates with a
                            new name
                        </div>
                        <div>
                            <strong>skip</strong>: skip duplicate configurations
                            and reuse duplicate folders
                        </div>
                    </div>

                    <div class="text-medium-emphasis text-caption mt-2">
                        When restoring into <strong>self</strong> or
                        <strong>owner</strong>, shared project assignments are
                        cleared by the backend. <strong>all</strong> preserves
                        original owners.
                    </div>
                </v-card-text>
                <v-card-actions>
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
import { computed, ref, watch } from "vue";
import MoveFolderTreeNode from "./browser/MoveFolderTreeNode.vue";

const { $api, $snackbar, $store } = useNuxtApp();

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

const selectItems = ref((props.selected || []).map(String));

watch(
    () => props.selected,
    (v) => {
        selectItems.value = (v || []).map(String);
    }
);

const selectedSet = computed(() => new Set(selectItems.value));

const folderToken = (id) => `f:${String(id)}`;
const configToken = (id) => `c:${String(id)}`;

const isSelected = (token) => selectedSet.value.has(String(token));

const setSelected = (arr) => {
    selectItems.value = arr.map(String);
    emit("update:selected", selectItems.value.slice());
};

const toggleSelect = (token) => {
    const t = String(token);
    const s = new Set(selectedSet.value);
    if (s.has(t)) s.delete(t);
    else s.add(t);
    setSelected(Array.from(s));
};

const selectedTokens = computed(() => selectItems.value || []);

const selectedFolderIds = computed(() =>
    selectedTokens.value
        .filter((t) => String(t).startsWith("f:"))
        .map((t) => String(t).slice(2))
);

const selectedConfigIds = computed(() =>
    selectedTokens.value
        .filter((t) => String(t).startsWith("c:"))
        .map((t) => String(t).slice(2))
);

const hasSelect = computed(
    () => selectedFolderIds.value.length + selectedConfigIds.value.length > 0
);

const mixedSelect = computed(
    () =>
        selectedFolderIds.value.length > 0 && selectedConfigIds.value.length > 0
);

const configById = computed(() => {
    const m = new Map();
    for (const item of props.configs || []) m.set(String(item.id), item.doc);
    return m;
});

const ownSelectConfigIds = computed(() =>
    selectedConfigIds.value.filter((id) => {
        const doc = configById.value.get(String(id));
        return doc?.misc?.owner === props.userName;
    })
);

const cfgFolderIds = computed(() => {
    const ids = [];

    for (const cid of ownSelectConfigIds.value) {
        const doc = configById.value.get(String(cid));
        const fid = doc?.configuration?.folderId;
        if (fid) ids.push(String(fid));
    }

    return ids;
});

const cfgFolderIdSet = computed(() => new Set(cfgFolderIds.value));

const moveInvalid = computed(() => {
    const dest = String(moveDestId.value || "");
    if (!dest) return true;

    if (cfgFolderIdSet.value.size === 1) {
        return cfgFolderIdSet.value.has(dest);
    }

    return false;
});

const folderNodeById = computed(() => {
    const m = new Map();
    for (const f of props.folder?.children || []) m.set(String(f.id), f);
    return m;
});

const ownSelectFolderIds = computed(() =>
    selectedFolderIds.value.filter((id) => {
        const node = folderNodeById.value.get(String(id));
        return (
            (node?.misc?.owner && node.misc.owner === props.userName) ||
            props.userLevel >= props.UserLevelEnum.manager
        );
    })
);

const canDownload = computed(
    () => !mixedSelect.value && selectedConfigIds.value.length > 0
);
const canShare = computed(
    () => !mixedSelect.value && ownSelectConfigIds.value.length > 0
);
const canRename = computed(
    () =>
        !mixedSelect.value &&
        selectedFolderIds.value.length + selectedConfigIds.value.length === 1
);
const canDuplicate = computed(
    () =>
        selectedFolderIds.value.length === 0 &&
        selectedConfigIds.value.length === 1 &&
        ownSelectConfigIds.value.length === 1
);
const canMove = computed(
    () =>
        !mixedSelect.value &&
        selectedFolderIds.value.length === 0 &&
        selectedConfigIds.value.length > 0 &&
        ownSelectConfigIds.value.length > 0
);
const canDelete = computed(() => hasSelect.value);

const canCreate = computed(
    () => props.userLevel > (props.UserLevelEnum?.guest ?? 0)
);

const isPrivileged = computed(
    () => props.userLevel >= props.UserLevelEnum.manager
);

const backupScopeItems = computed(() => {
    if (!isPrivileged.value) {
        return [{ title: "My configurations", value: "self" }];
    }

    return [
        { title: "My configurations", value: "self" },
        { title: "Specific user", value: "owner" },
        { title: "All users (preserve owners)", value: "all" }
    ];
});

const conflictStrategyItems = [
    { title: "Overwrite", value: "overwrite" },
    { title: "Rename", value: "rename" },
    { title: "Skip", value: "skip" }
];

const isMyRoot = computed(() => {
    const fid = String(props.folder?.id ?? "");
    return !!props.myRootId && fid === String(props.myRootId);
});

const headerTitle = computed(() => {
    if (isSharedView.value) return props.folder?.name || "";
    if (folderId.value === "__all__") return props.folder?.name || "";

    if (isMyRoot.value) return "Home";

    return props.folder?.name || "";
});

const folderId = computed(() => String(props.folder?.id ?? ""));

const isSharedView = computed(() => folderId.value.startsWith("__shared__"));
const isSharedRoot = computed(() => folderId.value === "__shared__");
const isSharedProject = computed(() =>
    folderId.value.startsWith("__shared__:")
);

const parentId = computed(() => props.folder?.__parentId ?? null);

const canGoUp = computed(() => !!props.folder && !!parentId.value);

const folders = computed(() => (props.folder?.children || []).slice());

const sortBy = ref("name");
const sortDesc = ref(false);

const setSort = (key) => {
    if (sortBy.value === key) {
        sortDesc.value = !sortDesc.value;
        return;
    }

    sortBy.value = key;
    sortDesc.value = false;
};

const normalizeString = (v) => String(v || "").toLocaleLowerCase();

const parseDateValue = (v) => {
    if (!v) return 0;
    const t = new Date(v).getTime();
    return Number.isNaN(t) ? 0 : t;
};

const compareValues = (a, b) => {
    if (a < b) return sortDesc.value ? 1 : -1;
    if (a > b) return sortDesc.value ? -1 : 1;
    return 0;
};

const sortedFolders = computed(() => {
    const arr = folders.value.slice();

    arr.sort((a, b) => {
        switch (sortBy.value) {
            case "owner":
                return compareValues(
                    normalizeString(a?.misc?.owner),
                    normalizeString(b?.misc?.owner)
                );

            case "created":
                return compareValues(
                    parseDateValue(a?.misc?.created),
                    parseDateValue(b?.misc?.created)
                );

            case "edited":
                return compareValues(
                    parseDateValue(a?.misc?.edited),
                    parseDateValue(b?.misc?.edited)
                );

            case "name":
            default:
                return compareValues(
                    normalizeString(a?.name),
                    normalizeString(b?.name)
                );
        }
    });

    return arr;
});

const sortedConfigs = computed(() => {
    const arr = (props.configs || []).slice();

    arr.sort((a, b) => {
        switch (sortBy.value) {
            case "owner":
                return compareValues(
                    normalizeString(a?.doc?.misc?.owner),
                    normalizeString(b?.doc?.misc?.owner)
                );

            case "created":
                return compareValues(
                    parseDateValue(a?.doc?.misc?.created),
                    parseDateValue(b?.doc?.misc?.created)
                );

            case "edited":
                return compareValues(
                    parseDateValue(a?.doc?.misc?.edited),
                    parseDateValue(b?.doc?.misc?.edited)
                );

            case "name":
            default:
                return compareValues(
                    normalizeString(
                        a?.doc?.configuration?.configurationName || a?.id
                    ),
                    normalizeString(
                        b?.doc?.configuration?.configurationName || b?.id
                    )
                );
        }
    });

    return arr;
});

const visibleTokens = computed(() => {
    const tokens = [];
    for (const f of folders.value) if (f?.id) tokens.push(folderToken(f.id));
    for (const c of props.configs || [])
        if (c?.id) tokens.push(configToken(c.id));
    return tokens;
});

const headerCheck = computed({
    get() {
        const toks = visibleTokens.value;
        if (!toks.length) return false;
        return toks.every((t) => selectedSet.value.has(t));
    },
    set(v) {
        const toks = visibleTokens.value;
        if (!toks.length) return;

        const s = new Set(selectedSet.value);
        if (v) {
            for (const t of toks) s.add(t);
        } else {
            for (const t of toks) s.delete(t);
        }
        setSelected(Array.from(s));
    }
});

const headerState = computed(() => {
    const toks = visibleTokens.value;
    if (!toks.length) return false;

    let hit = 0;
    for (const t of toks) if (selectedSet.value.has(t)) hit++;

    return hit > 0 && hit < toks.length;
});

const rowGridStyle = computed(() => ({
    "--fb-cols": "32px 1fr 160px 160px 160px"
}));

const headerIcon = computed(() => {
    if (isSharedRoot.value) return "$folderNetwork";
    if (isSharedProject.value) return "$group";
    return "$folderOpen";
});

const headerIconClass = computed(() => {
    if (isSharedRoot.value) return "fb-ico--shared-root";
    if (isSharedProject.value) return "fb-ico--shared-project";
    return "fb-ico--folder";
});

const childFolderIcon = computed(() => {
    if (isSharedRoot.value) return "$group";
    return "$folder";
});

const childFolderIconClass = computed(() => {
    if (isSharedRoot.value) return "fb-ico--shared-project";
    return "fb-ico--folder";
});

const formatDate = (v) => {
    if (!v) return "—";

    const d = new Date(v);
    if (Number.isNaN(d.getTime())) return "—";
    return new Intl.DateTimeFormat(undefined, {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit"
    }).format(d);
};

const restoreModeLabel = (mode) => {
    switch (String(mode || "").toLowerCase()) {
        case "self":
            return "My Configurations";
        case "owner":
            return "Specific User";
        case "all":
            return "All Users";
        default:
            return String(mode || "—");
    }
};

const CreateFolderDlg = ref(false);
const RenameDlg = ref(false);
const MoveDlg = ref(false);
const ShareDlg = ref(false);
const DeleteDlg = ref(false);
const ExportBackupDlg = ref(false);
const RestoreBackupDlg = ref(false);
const RestoreResultDlg = ref(false);

const exportScope = ref("self");
const exportOwner = ref("");

const restoreFile = ref(null);
const restoreScope = ref("self");
const restoreOwner = ref("");
const restoreConflictStrategy = ref("rename");
const restoreSummary = ref(null);

const inputFolderName = ref("");
const inputRename = ref("");
const shareProjectIds = ref([]); // string[]

const moveDestId = ref(""); // string folder id
const moveFolderTree = ref([]);
const moveFolderPath = ref("");

const selectedRestoreFile = computed(() => {
    if (Array.isArray(restoreFile.value)) {
        return restoreFile.value[0] || null;
    }
    return restoreFile.value || null;
});

const normalizeOwner = (v) => String(v || "").trim();

const getErrorMessage = (error, fallback) => {
    if (error instanceof Error && error.message) return error.message;
    return fallback;
};

const clearDialogs = () => {
    CreateFolderDlg.value = false;
    RenameDlg.value = false;
    MoveDlg.value = false;
    ShareDlg.value = false;
    DeleteDlg.value = false;
    ExportBackupDlg.value = false;
    RestoreBackupDlg.value = false;
    RestoreResultDlg.value = false;
};

const createCfgFolderId = computed(() => {
    const fid = String(props.folder?.id || "");
    if (!fid || fid.startsWith("__")) return "";
    return fid;
});

const duplicateConfig = () => {
    if (!canDuplicate.value) return;

    for (const cid of ownSelectConfigIds.value) {
        emit("duplicate", { presetId: String(cid) });
    }

    setSelected([]);
};

const openCreateFolder = () => {
    inputFolderName.value = "";
    CreateFolderDlg.value = true;
};

const normalizeName = (v) => String(v || "").trim();

const sibFolderName = (name, excludeId = "") => {
    const target = normalizeName(name);

    return (props.folder?.children || []).some(
        (child) =>
            String(child?.id || "") !== String(excludeId) &&
            normalizeName(child?.name) === target
    );
};

const sibConfigName = (name, excludeId = "") => {
    const target = normalizeName(name);

    return (props.configs || []).some(
        (item) =>
            String(item?.id || "") !== String(excludeId) &&
            normalizeName(
                item?.doc?.configuration?.configurationName || item?.id
            ) === target
    );
};

const createFolder = async () => {
    if ($store?.demo) return $snackbar.show($store.demoMessage);

    const name = normalizeName(inputFolderName.value);
    if (!name) return;

    if (sibFolderName(name)) {
        $snackbar.show(
            "A folder with the same name already exists in this location"
        );
        return;
    }

    const parent = folderId.value.startsWith("__")
        ? null
        : String(props.folder?.id || null);

    await $api.configurationFolders.post({
        folder: {
            folderName: name,
            parentFolderId: parent,
            sharedProjects: []
        }
    });

    CreateFolderDlg.value = false;
    $snackbar.show("Folder created");
    setSelected([]); // clear selection
    emit("refresh");
};

// TODO: Provide a download feature for specific configurations (v2.1.0)
const downloadSelected = () => {};

const openExportBackup = () => {
    exportScope.value = "self";
    exportOwner.value = "";
    ExportBackupDlg.value = true;
};

const applyExportBackup = async () => {
    if ($store?.demo) return $snackbar.show($store.demoMessage);

    const scope = String(exportScope.value || "self");
    const owner = normalizeOwner(exportOwner.value);

    if (scope === "owner" && !owner) {
        $snackbar.show("Please enter a username");
        return;
    }

    try {
        await $api.configurationBackups.download(scope, owner);
        ExportBackupDlg.value = false;
        $snackbar.show("Backup exported");
    } catch (error) {
        $snackbar.show(getErrorMessage(error, "Failed to export backup"));
    }
};

const openRestoreBackup = () => {
    restoreFile.value = null;
    restoreScope.value = "self";
    restoreOwner.value = "";
    restoreConflictStrategy.value = "rename";
    RestoreBackupDlg.value = true;
};

const applyRestoreBackup = async () => {
    if ($store?.demo) return $snackbar.show($store.demoMessage);

    const file = selectedRestoreFile.value;
    const scope = String(restoreScope.value || "self");
    const owner = normalizeOwner(restoreOwner.value);
    const conflictStrategy = String(restoreConflictStrategy.value || "rename");

    if (!file) {
        $snackbar.show("Please select a backup file");
        return;
    }

    if (scope === "owner" && !owner) {
        $snackbar.show("Please enter a username");
        return;
    }

    try {
        const result = await $api.configurationBackups.restore(file, {
            scope,
            owner,
            conflictStrategy
        });

        if (!result?.data) {
            throw new Error("Restore completed without summary");
        }

        restoreSummary.value = result.data;
        RestoreBackupDlg.value = false;
        RestoreResultDlg.value = true;

        setSelected([]);
        emit("refresh");

        $snackbar.show("Backup restored");
    } catch (error) {
        $snackbar.show(getErrorMessage(error, "Failed to restore backup"));
    }
};

const openShare = () => {
    shareProjectIds.value = [];
    ShareDlg.value = true;
};

const applyShare = async () => {
    if ($store?.demo) return $snackbar.show($store.demoMessage);

    const targetIds = ownSelectConfigIds.value;
    const pids = (shareProjectIds.value || []).map(String);

    for (const cid of targetIds) {
        const doc = configById.value.get(String(cid));
        if (!doc) continue;

        const payload = {
            _id: String(cid),
            configuration: { ...doc.configuration, sharedProjects: pids },
            misc: doc.misc
        };

        await $api.configurations.put(String(cid), payload);
    }

    ShareDlg.value = false;
    $snackbar.show("Sharing updated");
    setSelected([]);
    emit("refresh");
};

const openRename = async () => {
    inputRename.value = "";

    // folder selected
    if (selectedFolderIds.value.length === 1) {
        const id = selectedFolderIds.value[0];
        const node = folderNodeById.value.get(String(id));
        inputRename.value = node?.name || "";
        RenameDlg.value = true;
        return;
    }

    // config selected
    if (selectedConfigIds.value.length === 1) {
        const id = selectedConfigIds.value[0];
        const doc = configById.value.get(String(id));
        inputRename.value = doc?.configuration?.configurationName || "";
        RenameDlg.value = true;
    }
};

const applyRename = async () => {
    if ($store?.demo) return $snackbar.show($store.demoMessage);

    const name = normalizeName(inputRename.value);
    if (!name) return;

    // rename folder
    if (selectedFolderIds.value.length === 1) {
        const fid = selectedFolderIds.value[0];

        if (sibFolderName(name, fid)) {
            $snackbar.show(
                "A folder with the same name already exists in this location"
            );
            return;
        }

        const full = await $api.configurationFolders.getOne(String(fid));
        const updated = {
            folder: {
                ...full.folder,
                folderName: name
            },
            misc: full.misc
        };

        await $api.configurationFolders.put(String(fid), updated);

        RenameDlg.value = false;
        $snackbar.show("Folder renamed");
        setSelected([]);
        emit("refresh");
        return;
    }

    // rename config
    if (selectedConfigIds.value.length === 1) {
        const cid = selectedConfigIds.value[0];

        if (sibConfigName(name, cid)) {
            $snackbar.show(
                "A configuration with the same name already exists in this folder"
            );
            return;
        }

        const doc = configById.value.get(String(cid));
        if (!doc) return;

        // only owner or manager/admin should pass; we already filtered in UI
        const payload = {
            _id: String(cid),
            configuration: { ...doc.configuration, configurationName: name },
            misc: doc.misc
        };

        await $api.configurations.put(String(cid), payload);

        RenameDlg.value = false;
        $snackbar.show("Configuration renamed");
        setSelected([]);
        emit("refresh");
    }
};

const buildMoveTree = (nodes, parentPath = "home") => {
    const result = [];

    for (const node of nodes || []) {
        if (!node?.id) continue;

        const currentPath =
            parentPath === "home"
                ? `home/${node.name}`
                : `${parentPath}/${node.name}`;

        result.push({
            id: String(node.id),
            name: node.name,
            path: currentPath,
            children: buildMoveTree(node.children || [], currentPath)
        });
    }

    return result;
};

const findUserHomeTree = (treeNodes, userName) => {
    return (
        (treeNodes || []).find(
            (n) => n?.name === userName && n?.misc?.owner === userName
        ) || null
    );
};

const openMove = async () => {
    if (!canMove.value) return;

    moveDestId.value = "";
    moveFolderPath.value = "";
    MoveDlg.value = true;

    const treeResp = await $api.configurationFolders.get();
    const fullTree = treeResp?.data || [];

    const myHome = findUserHomeTree(fullTree, props.userName);

    if (!myHome) {
        moveFolderTree.value = [];
        return;
    }

    moveFolderTree.value = [
        {
            id: String(myHome.id),
            name: "home",
            path: "home",
            children: buildMoveTree(myHome.children || [], "home")
        }
    ];
};

const moveDestination = (node) => {
    if (!node?.id) return;
    moveDestId.value = String(node.id);
    moveFolderPath.value = node.path || "";
};

const selectMoveDestination = (node) =>
    String(moveDestId.value || "") === String(node?.id || "");

const applyMove = async () => {
    if ($store?.demo) return $snackbar.show($store.demoMessage);

    const dest = String(moveDestId.value || "");
    if (!dest) return;

    for (const cid of ownSelectConfigIds.value) {
        const doc = configById.value.get(String(cid));
        if (!doc) continue;

        const payload = {
            _id: String(cid),
            configuration: { ...doc.configuration, folderId: dest },
            misc: doc.misc
        };

        await $api.configurations.put(String(cid), payload);
    }

    MoveDlg.value = false;
    $snackbar.show("Moved");
    setSelected([]);
    emit("refresh");
};

const openDelete = () => {
    DeleteDlg.value = true;
};

const applyDelete = async () => {
    if ($store?.demo) return $snackbar.show($store.demoMessage);

    for (const fid of ownSelectFolderIds.value) {
        await $api.configurationFolders.delete(String(fid));
    }

    for (const cid of ownSelectConfigIds.value) {
        await $api.configurations.delete(String(cid));
    }

    DeleteDlg.value = false;
    $snackbar.show("Deleted");
    setSelected([]);
    emit("refresh");
};
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

.backup-dialog-note {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    padding: 10px 12px;
    border-radius: 10px;
    background: rgba(var(--v-theme-surface-light), 0.55);
    border: 1px solid rgba(var(--v-theme-font-base), 0.05);
    color: $font-light;
    font-size: 0.82rem;
    line-height: 1.45;
}

.backup-dialog-note-icon {
    color: $primary-light;
    opacity: 0.85;
    margin-top: 1px;
    flex: 0 0 auto;
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
