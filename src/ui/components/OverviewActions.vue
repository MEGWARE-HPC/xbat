<template>
    <v-dialog v-model="dialog" max-width="600px">
        <template v-slot:activator="{ props: activatorProps }">
            <div v-bind="activatorProps">
                <v-menu>
                    <template v-slot:activator="{ props: activatorPropsMenu }">
                        <v-btn
                            v-bind="activatorPropsMenu"
                            prepend-icon="$gestureTap"
                        >
                            Actions <v-icon icon="$chevronDown"></v-icon>
                        </v-btn>
                    </template>
                    <v-card>
                        <v-list>
                            <v-list-item
                                value="share"
                                v-bind:title.attr="shareExplanation"
                                @click="setAction('share')"
                                :disabled="actionsDisabled || !projects.length"
                            >
                                <template #prepend>
                                    <div class="mr-2">
                                        <v-icon
                                            size="small"
                                            icon="$share"
                                        ></v-icon></div></template
                                >Share</v-list-item
                            >
                            <v-list-item
                                value="revoke"
                                v-bind:title.attr="shareExplanation"
                                @click="revokeAccess()"
                                :disabled="actionsDisabled || !projects.length"
                            >
                                <template #prepend>
                                    <div class="mr-2">
                                        <v-icon
                                            size="small"
                                            icon="$revokeshared"
                                        ></v-icon></div></template
                                >Revoke Shared Access</v-list-item
                            >
                            <v-list-item
                                value="delete"
                                v-bind:title.attr="'Delete selected benchmarks'"
                                @click="setAction('delete')"
                                :disabled="actionsDisabled"
                            >
                                <template #prepend>
                                    <div class="mr-2">
                                        <v-icon
                                            size="small"
                                            icon="$trashCan"
                                        ></v-icon></div></template
                                >Delete</v-list-item
                            >
                            <v-list-item
                                value="cancel"
                                v-bind:title.attr="'Cancel all jobs of selected benchmarks'"
                                @click="setAction('cancel')"
                                :disabled="actionsDisabled"
                            >
                                <template #prepend>
                                    <div class="mr-2">
                                        <v-icon
                                            size="small"
                                            icon="$cancel"
                                        ></v-icon></div></template
                                >Cancel</v-list-item
                            >
                            <v-list-item
                                v-if="
                                    $authStore.userLevel >=
                                    $authStore.UserLevelEnum.demo
                                "
                                value="export"
                                v-bind:title.attr="'Export all benchmark data for backup'"
                                @click="setAction('export')"
                                :disabled="actionsDisabled || statusDisabled"
                            >
                                <template #prepend>
                                    <div class="mr-2">
                                        <v-icon
                                            size="small"
                                            icon="$dataExport"
                                        ></v-icon></div></template
                                >Export</v-list-item
                            >
                            <v-list-item
                                v-if="
                                    $authStore.userLevel >=
                                    $authStore.UserLevelEnum.demo
                                "
                                value="import"
                                v-bind:title.attr="'Import benchmarks to xbat'"
                                @click="setAction('import')"
                            >
                                <template #prepend>
                                    <div class="mr-2">
                                        <v-icon
                                            size="small"
                                            icon="$dataImport"
                                        ></v-icon></div></template
                                >Import</v-list-item
                            >
                            <v-list-item
                                v-if="
                                    $authStore.userLevel ==
                                    $authStore.UserLevelEnum.admin
                                "
                                value="backup"
                                v-bind:title.attr="'Backup the entire mongodb database'"
                                @click="setAction('backup')"
                            >
                                <template #prepend>
                                    <div class="mr-2">
                                        <v-icon
                                            size="small"
                                            icon="$backupRestore"
                                        ></v-icon></div></template
                                >Backup MongoDB</v-list-item
                            >
                        </v-list>
                    </v-card>
                </v-menu>
            </div>
        </template>
        <template v-slot:default="{ isActive }">
            <v-card>
                <v-card-title class="text-capitalize">
                    {{ action.type }}
                </v-card-title>
                <v-card-text>
                    <template
                        v-if="
                            action.type == 'revoke' ||
                            action.type == 'cancel' ||
                            action.type == 'delete'
                        "
                    >
                        <template v-if="action.eligible.length">
                            Do you really want to
                            <span class="font-weight-bold">{{
                                action.type
                            }}</span>
                            the following benchmarks?
                            <v-list dense>
                                <v-list-item
                                    v-for="[i, s] of action.eligible.entries()"
                                    :key="i"
                                >
                                    #{{ s.runNr }} - {{ s.name }}
                                </v-list-item>
                            </v-list>

                            <template v-if="action.ineligible.length">
                                The following benchmarks are not eligible for
                                this action and will be ignored

                                <v-list dense>
                                    <v-list-item
                                        v-for="[
                                            i,
                                            s
                                        ] of action.ineligible.entries()"
                                        :key="i"
                                    >
                                        #{{ s.runNr }} - {{ s.name }}
                                    </v-list-item>
                                </v-list>
                            </template>
                        </template>
                        <template v-else>
                            Selected benchmarks are not eligible for this
                            action!
                        </template>
                    </template>
                    <template v-else-if="action.type == 'backup'">
                        Do you want to backup the entire MongoDB database?
                        <template>
                            <v-overlay
                                v-model="state.isExporting"
                                contained
                                class="align-center justify-center"
                            >
                                <!-- use v-show on progress as overlay does not correctly hide its slot under on rapid loading state changes -->
                                <v-progress-circular
                                    color="primary"
                                    v-show="state.isExporting"
                                    indeterminate
                                    size="32"
                                ></v-progress-circular>
                            </v-overlay>
                        </template>
                    </template>
                    <template v-else-if="action.type == 'export'">
                        Do you want to export selected benchmarks?
                        <template v-if="action.eligible.length">
                            <v-overlay
                                v-model="state.isExporting"
                                contained
                                class="align-center justify-center"
                            >
                                <!-- use v-show on progress as overlay does not correctly hide its slot under on rapid loading state changes -->
                                <v-progress-circular
                                    color="primary"
                                    v-show="state.isExporting"
                                    indeterminate
                                    size="32"
                                ></v-progress-circular>
                            </v-overlay>
                            <v-list dense>
                                <v-list-item
                                    v-for="[i, s] of action.eligible.entries()"
                                    :key="i"
                                >
                                    #{{ s.runNr }} - {{ s.name }}
                                </v-list-item>
                            </v-list>
                            <v-container>
                                <v-row>
                                    <v-checkbox
                                        color="primary-light"
                                        v-model="action.anonymise"
                                        label="Anonymise"
                                    >
                                        <template #append>
                                            <v-tooltip location="bottom">
                                                <template
                                                    v-slot:activator="{ props }"
                                                >
                                                    <v-icon
                                                        v-bind="props"
                                                        color="primary-light"
                                                        class="ml-1"
                                                        icon="$information"
                                                    >
                                                    </v-icon>
                                                </template>
                                                <span>
                                                    This option will anonymise
                                                    all user-related data
                                                </span>
                                            </v-tooltip>
                                        </template>
                                    </v-checkbox>
                                </v-row>
                            </v-container>
                            <template v-if="action.ineligible.length">
                                The following benchmarks are not eligible for
                                this action and will be ignored
                                <v-list dense>
                                    <v-list-item
                                        v-for="[
                                            i,
                                            s
                                        ] of action.ineligible.entries()"
                                        :key="i"
                                    >
                                        #{{ s.runNr }} - {{ s.name }}
                                    </v-list-item>
                                </v-list>
                            </template>
                            <template v-if="state.nonExportable">
                                <div class="warning mb-3">
                                    <p>
                                        The benchmark cannot be exported at the
                                        moment,
                                    </p>
                                    <p>
                                        please check its current status:
                                        {{ props.selected.map((x) => x.state) }}
                                    </p>
                                </div>
                            </template>
                        </template>
                        <template v-else>
                            Selected benchmarks are not eligible for this
                            action!
                        </template>
                    </template>
                    <template v-else-if="action.type == 'import'">
                        Select the file you want to import.
                        <v-overlay
                            v-model="state.isImporting"
                            contained
                            class="align-center justify-center"
                        >
                            <!-- use v-show on progress as overlay does not correctly hide its slot under on rapid loading state changes -->
                            <v-progress-circular
                                color="primary"
                                v-show="state.isImporting"
                                indeterminate
                                size="32"
                            ></v-progress-circular>
                        </v-overlay>
                        <v-file-upload
                            v-model="state.selectedFile"
                            browse-text="Local Filesystem"
                            divider-text="or choose locally"
                            icon="$cloudUpload"
                            title="Drag and Drop Here"
                            show-size
                            clearable
                        >
                        </v-file-upload>
                        <v-container>
                            <v-row>
                                <v-col>
                                    <v-checkbox
                                        color="primary-light"
                                        v-model="action.reassignRunNr"
                                        label="Reassign"
                                    >
                                        <template #append>
                                            <v-tooltip location="bottom">
                                                <template
                                                    v-slot:activator="{ props }"
                                                >
                                                    <v-icon
                                                        v-bind="props"
                                                        color="primary-light"
                                                        class="ml-1"
                                                        icon="$information"
                                                    >
                                                    </v-icon>
                                                </template>
                                                <span>
                                                    This option will assign new
                                                    run numbers and job IDs to
                                                    the imported benchmark(s) to
                                                    avoid conflicts with
                                                    existing data.
                                                </span>
                                            </v-tooltip>
                                        </template>
                                    </v-checkbox>
                                </v-col>
                                <v-col>
                                    <v-checkbox
                                        color="primary-light"
                                        v-model="action.updateColl"
                                        label="Update relevant data"
                                    >
                                        <template #append>
                                            <v-tooltip location="bottom">
                                                <template
                                                    v-slot:activator="{ props }"
                                                >
                                                    <v-icon
                                                        v-bind="props"
                                                        color="primary-light"
                                                        class="ml-1"
                                                        icon="$information"
                                                    >
                                                    </v-icon>
                                                </template>
                                                <span>
                                                    This option will update the
                                                    relevant collections, such
                                                    as users, projects,
                                                    configurations, etc. when
                                                    they already exist in the
                                                    database
                                                </span>
                                            </v-tooltip>
                                        </template>
                                    </v-checkbox>
                                </v-col>
                            </v-row>
                        </v-container>
                    </template>
                    <template v-else-if="action.type == 'share'">
                        Share the selected benchmarks with other projects?
                        <v-autocomplete
                            class="mt-5"
                            :items="projects"
                            v-model="state.projectsToShareWith"
                            chips
                            closable-chips
                            multiple
                            item-title="name"
                            item-value="_id"
                            label="Share with Project"
                        >
                        </v-autocomplete>
                        <div
                            class="error-hint"
                            v-if="state.showShareConflictWarning"
                        >
                            Your current selection includes benchmarks with
                            different project settings. This action will
                            overwrite all existing settings!
                        </div>
                    </template>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn color="grey" text @click="isActive.value = false">
                        Abort
                    </v-btn>
                    <v-btn
                        v-if="
                            action.type === 'backup' ||
                            (action.eligible.length && action.type !== 'import')
                        "
                        :color="
                            ['share', 'export', 'backup'].includes(
                                action.type ?? ''
                            )
                                ? 'primary-light'
                                : 'danger'
                        "
                        text
                        @click="executeAction"
                    >
                        {{ action.type }}
                    </v-btn>
                    <v-btn
                        v-if="action.type == 'import' && state.selectedFile"
                        color="primary-light"
                        text
                        @click="executeAction"
                    >
                        Import
                    </v-btn>
                </v-card-actions>
            </v-card>
        </template>
    </v-dialog>
</template>
<script lang="ts" setup>
import type { Benchmark } from "@/repository/modules/benchmarks";

const { $api, $authStore, $store, $snackbar } = useNuxtApp();

const shareExplanation =
    "Shared benchmarks are visible to all other members of the selected project";

const dialog = ref(false);

const props = defineProps<{
    selected: Benchmark[];
}>();

const actionsDisabled = computed(() => !props.selected.length);

const statusDisabled = computed(() => {
    return props.selected.every((x) =>
        ["pending", "queued", "running"].includes(x.state)
    );
});

const projects = computed(() => $authStore.user?.projects || []);

interface State {
    projectsToShareWith: string[];
    showShareConflictWarning: boolean;
    showBenchmarkComparison: boolean;
    isExporting: boolean;
    isImporting: boolean;
    nonExportable: boolean;
    selectedFile: File | undefined;
}

const state = reactive<State>({
    projectsToShareWith: [],
    showShareConflictWarning: false,
    showBenchmarkComparison: false,
    isExporting: false,
    isImporting: false,
    nonExportable: false,
    selectedFile: undefined
});

interface Action {
    type: string | null;
    eligible: Benchmark[];
    ineligible: Benchmark[];
    anonymise: boolean;
    reassignRunNr: boolean;
    updateColl: boolean;
}

const action = reactive<Action>({
    type: null,
    eligible: [],
    ineligible: [],
    anonymise: false,
    reassignRunNr: true,
    updateColl: true
});

const setAction = (type: string) => {
    action.ineligible = [];
    action.eligible = [];

    if (!props.selected.length && type != "import" && type != "backup") return;
    if (type == "export") state.nonExportable = false;

    if (type == "cancel") {
        props.selected.forEach((x) => {
            action[x.state == "running" ? "eligible" : "ineligible"].push(x);
        });
    } else {
        if (type != "backup") {
            action.eligible = props.selected;
        }
    }

    action.type = type;
    dialog.value = true;
};

const emit = defineEmits<{
    (e: "selected:clear"): void;
    (e: "refresh"): void;
}>();

const revokeAccess = async () => {
    await Promise.all(
        props.selected.map((x) =>
            $api.benchmarks.patch(x.runNr, {
                sharedProjects: []
            })
        )
    );
    $snackbar.show("Access revoked");

    emit("refresh");
};

const executeAction = async () => {
    if ($store.demo) {
        $snackbar.show($store.demoMessage);
        dialog.value = false;
        action.type = "";
        return;
    }

    if (
        action.type != "import" &&
        action.type != "backup" &&
        !props.selected.length
    )
        return;

    let message = `Benchmark${action.eligible.length > 1 ? "s" : ""} `;

    if (action.type === "delete") {
        await Promise.all(
            action.eligible.map((x) => $api.benchmarks.delete(x.runNr))
        );
        emit("selected:clear");
        message += "deleted";
    } else if (action.type === "cancel") {
        await Promise.all(
            action.eligible.map((b) => $api.benchmarks.cancel(b.runNr))
        );
        emit("selected:clear");
        message += "cancelled";
    } else if (action.type == "share") {
        await Promise.all(
            action.eligible.map((x) =>
                $api.benchmarks.patch(x.runNr, {
                    sharedProjects: state.projectsToShareWith
                })
            )
        );
        message += "shared";
    } else if (action.type == "export") {
        state.isExporting = true;
        const responseBlob = await $api.benchmarks.export({
            runNrs: action.eligible.map((x) => x.runNr),
            anonymise: action.anonymise
        });
        if (!responseBlob || responseBlob.size === 0) {
            state.nonExportable = true;
            $snackbar.show("No benchmark data available for export");
            state.isExporting = false;
            return;
        }
        const url = window.URL.createObjectURL(responseBlob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `xbat_export_${action.eligible
            .map((x) => x.runNr)
            .join("_")}.tgz`;
        document.body.appendChild(link);
        link.click();

        window.URL.revokeObjectURL(url);
        document.body.removeChild(link);

        dialog.value = false;
        action.type = "";
        state.isExporting = false;
        return;
    } else if (action.type == "import" && state.selectedFile) {
        state.isImporting = true;
        await $api.benchmarks.import({
            file: state.selectedFile,
            reassignRunNr: action.reassignRunNr,
            updateColl: action.updateColl
        });
        state.selectedFile = undefined;
        message = "Imported Benchmarks to xbat";
        state.isImporting = false;
        action.reassignRunNr = true;
        action.updateColl = true;
    } else if (action.type == "backup") {
        state.isExporting = true;
        const responseBlob = await $api.benchmarks.backup();

        if (!responseBlob || responseBlob.size === 0) {
            $snackbar.show("No backup data available");
            state.isExporting = false;
            return;
        }

        const url = window.URL.createObjectURL(responseBlob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `MongoDB_backup_${new Date()
            .toISOString()
            .replace(/[:.]/g, "-")}.tgz`;
        document.body.appendChild(link);
        link.click();

        window.URL.revokeObjectURL(url);
        document.body.removeChild(link);

        message = "Created backup from MongoDB";
        state.isExporting = false;
    }

    $snackbar.show(message);
    dialog.value = false;
    action.type = "";
    emit("refresh");
};

watch(
    () => props.selected,
    (v) => {
        const shared = v.map((x) => x.sharedProjects || []);
        state.projectsToShareWith = Array.from(new Set(shared.flat(1)));
        for (const entry of shared) {
            if (
                entry.length &&
                !(
                    entry.length === state.projectsToShareWith.length ||
                    entry.every(
                        (y, idx) => y === state.projectsToShareWith[idx]
                    )
                )
            ) {
                state.showShareConflictWarning = true;
                return;
            }
        }
        state.showShareConflictWarning = false;
    }
);
</script>
