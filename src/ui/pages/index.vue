<template>
    <v-container fluid>
        <!-- {{ jobsByRunNr }} -->
        <v-card max-width="95%" class="mx-auto pa-2 mt-5">
            <v-card-title>
                <div class="d-flex align-center gap-20">
                    <v-btn
                        color="primary"
                        title="Start Benchmark"
                        @click="state.startDialog = true"
                        :disabled="
                            $authStore.userLevel ==
                                $authStore.UserLevelEnum.guest ||
                            $authStore.userLevel ==
                                $authStore.UserLevelEnum.admin
                        "
                    >
                        Start Benchmark
                    </v-btn>

                    <v-btn
                        value="share"
                        @click="state.showBenchmarkComparison = true"
                        prepend-icon="$compare"
                    >
                        Compare
                    </v-btn>
                    <v-menu>
                        <template v-slot:activator="{ props }">
                            <v-btn v-bind="props">
                                Actions <v-icon icon="$chevronDown"></v-icon>
                            </v-btn>
                        </template>
                        <v-card>
                            <v-list>
                                <v-list-item
                                    value="share"
                                    v-bind:title.attr="shareExplanation"
                                    @click="setAction('share')"
                                    :disabled="
                                        actionsDisabled || !projects.length
                                    "
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
                                    :disabled="
                                        actionsDisabled || !projects.length
                                    "
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
                                    :disabled="
                                        actionsDisabled || statusDisabled
                                    "
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
                                    value="purge"
                                    v-bind:title.attr="'Purge deleted jobs from QuestDB'"
                                    @click="setAction('purge')"
                                >
                                    <template #prepend>
                                        <div class="mr-2">
                                            <v-icon
                                                size="small"
                                                icon="$purge"
                                            ></v-icon></div></template
                                    >Purge QuestDB</v-list-item
                                >
                            </v-list>
                        </v-card>
                    </v-menu>
                    <v-spacer></v-spacer>
                    <template v-if="projects.length">
                        <div>
                            <v-switch
                                label="Hide shared"
                                v-model="hideShared"
                                v-show="
                                    $authStore.userLevel !=
                                        $authStore.UserLevelEnum.demo &&
                                    $authStore.userLevel !=
                                        $authStore.UserLevelEnum.admin
                                "
                            ></v-switch>
                        </div>
                        <div style="width: 250px">
                            <v-autocomplete
                                label="Filter by project"
                                :items="projects"
                                hide-details
                                prepend-inner-icon="$filter"
                                item-title="name"
                                item-value="_id"
                                clearable
                                v-model="projectFilter"
                                :disabled="hideShared"
                            ></v-autocomplete>
                        </div>
                    </template>
                    <div style="width: 250px">
                        <v-text-field
                            v-model="state.search"
                            prepend-inner-icon="$search"
                            label="Search"
                            hide-details
                            clearable
                        ></v-text-field>
                    </div>
                </div>
            </v-card-title>
            <v-card-text class="pt-2">
                <v-data-table
                    :headers="tableHeaders"
                    :items="filteredBenchmarks"
                    @click:row="handleRowClick"
                    :search="state.search"
                    show-select
                    v-model="state.selected"
                    v-model:sortBy="tableSortBy"
                    :loading="pending"
                    class="overview-table"
                >
                    <template v-slot:[`item.startTime`]="{ item }">
                        <ClientOnly>
                            {{ sanitizeDate(item.startTime) }}
                        </ClientOnly>
                    </template>
                    <template v-slot:[`item.jobIds`]="{ item }">
                        <div class="job-ids">
                            {{
                                encodeBraceNotation(item.jobIds, ", ").join(
                                    ", "
                                )
                            }}
                        </div>
                        <div class="job-hover-info">
                            <Tooltip location="bottom" custom>
                                <v-card>
                                    <v-card-text>
                                        <JobOverviewTable
                                            :jobs="
                                                jobsByRunNr[item.runNr] || []
                                            "
                                        ></JobOverviewTable>
                                    </v-card-text>
                                </v-card>
                            </Tooltip>
                        </div>
                    </template>
                    <template v-slot:[`item.name`]="{ item }">
                        <div class="d-flex justify-space-between">
                            {{ item.name }}
                            <div class="name-edit">
                                <InlineEdit
                                    v-if="
                                        $authStore.userLevel >=
                                            $authStore.UserLevelEnum.user &&
                                        ($authStore.userLevel >=
                                            $authStore.UserLevelEnum.manager ||
                                            item.issuer ===
                                                $authStore.user_name)
                                    "
                                    :modelValue="item.name"
                                    title="Rename Benchmark"
                                    @update:modelValue="
                                        updateBenchmarkName({
                                            runNr: item.runNr,
                                            value: $event
                                        })
                                    "
                                ></InlineEdit>
                            </div>
                        </div>
                    </template>
                    <template v-slot:[`item.attributes`]="{ item }">
                        <ClientOnly>
                            <div class="d-flex justify-center">
                                <v-icon
                                    v-show="item.sharedProjects?.length"
                                    size="small"
                                    icon="$share"
                                    color="primary-light"
                                    title="Shared with other users"
                                ></v-icon>
                                <v-icon
                                    v-show="item.cli"
                                    size="small"
                                    icon="$console"
                                    color="primary-light"
                                    title="Submitted via CLI"
                                ></v-icon>
                            </div>
                        </ClientOnly>
                    </template>
                    <template v-slot:[`item.state`]="{ item }">
                        <v-chip
                            size="small"
                            variant="outlined"
                            :color="benchmarkStates?.[item.runNr]?.color"
                            :title="benchmarkStates?.[item.runNr]?.title"
                            >{{ benchmarkStates?.[item.runNr]?.label }}
                            <v-tooltip
                                :text="benchmarkStates?.[item.runNr]?.info"
                                v-if="benchmarkStates?.[item.runNr]?.info"
                                location="top"
                            >
                                <template v-slot:activator="{ props }">
                                    <v-icon
                                        v-bind="props"
                                        icon="$information"
                                        class="ml-1"
                                    ></v-icon>
                                </template>
                            </v-tooltip>
                        </v-chip>
                    </template>
                </v-data-table>
            </v-card-text>
        </v-card>
        <v-dialog v-model="action.dialog" max-width="600px">
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
                                        {{ state.selected.map((x) => x.state) }}
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
                                        label="Reassign Run Number"
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
                                                    This option will reassign
                                                    the run number in case of
                                                    conflict, otherwise it will
                                                    skip the import of the
                                                    benchmark when the run
                                                    number already exists
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
                    <template v-else>
                        <div class="warning mb-3">
                            <p>
                                WARNING - THIS ACTION MAY LEAD TO PERMANENT DATA
                                LOSS!
                            </p>
                            <p>
                                CONSULT
                                <NuxtLink
                                    to="https://xbat.dev/docs/admin/maintenance#purging-questdb-data"
                                    target="_blank"
                                    >DOCUMENTATION</NuxtLink
                                >
                                AND BACKUP QUESTDB DATA BEFORE PURGING!
                            </p>
                        </div>

                        <p>
                            Do you really want to purge all deleted jobs from
                            QuestDB?
                        </p>
                    </template>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn color="grey" text @click="action.dialog = false">
                        Abort
                    </v-btn>
                    <v-btn
                        v-if="
                            action.type == 'purge' ||
                            (action.eligible.length && action.type != 'import')
                        "
                        :color="
                            action.type != 'share' ? 'danger' : 'primary-light'
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
        </v-dialog>
        <v-dialog v-model="state.startDialog" max-width="600px">
            <v-card>
                <v-card-title> Start Benchmark </v-card-title>
                <v-card-text>
                    <v-form
                        lazy-validation
                        ref="submit_form"
                        v-model="state.submitValid"
                    >
                        <div>
                            <v-text-field
                                label="Benchmark Name"
                                class="mb-2"
                                v-model="form.name"
                                :rules="[vNotEmpty]"
                            ></v-text-field>
                            <div class="d-flex align-top">
                                <v-autocomplete
                                    :items="configurationItems"
                                    label="Configuration"
                                    v-model="form.configId"
                                    :rules="[vNotEmpty]"
                                    class="mb-2"
                                    no-data-text="No configurations found"
                                >
                                    <template v-slot:item="{ props, item }">
                                        <v-list-item
                                            v-bind="props"
                                            append-icon="$cogs"
                                            :title="item?.raw?.title"
                                            :value="item?.raw?.value"
                                        >
                                            <template #append>
                                                <div v-if="item?.raw?.shared">
                                                    <v-icon
                                                        title="This is a shared configuration"
                                                        size="small"
                                                        color="primary-light"
                                                        icon="$share"
                                                    ></v-icon></div
                                            ></template>
                                        </v-list-item>
                                    </template>
                                </v-autocomplete>
                                <v-menu
                                    :close-on-content-click="false"
                                    width="600"
                                    location="bottom"
                                >
                                    <template v-slot:activator="{ props }">
                                        <v-btn
                                            v-bind="props"
                                            class="ml-5 mt-1"
                                            color="primary-light"
                                            icon="$currency"
                                            size="small"
                                            variant="text"
                                            title="Modify Job Variables"
                                            :disabled="!form.configId"
                                        >
                                        </v-btn>
                                    </template>
                                    <v-card>
                                        <v-card-title
                                            >Job Variables</v-card-title
                                        >
                                        <v-card-text>
                                            <p
                                                class="text-medium-emphasis text-caption font-italic"
                                            >
                                                You can overwrite variables for
                                                the selected configuration.
                                                These changes will not be
                                                persisted and only apply to the
                                                current benchmark run.
                                            </p>
                                            <JobVariables
                                                v-if="form.configId"
                                                v-model="
                                                    variableForm[form.configId]
                                                "
                                            ></JobVariables>
                                        </v-card-text>
                                    </v-card>
                                </v-menu>
                            </div>
                            <div class="d-flex align-top">
                                <v-autocomplete
                                    v-show="projects.length"
                                    :items="projects"
                                    v-model="form.sharedProjects"
                                    chips
                                    closable-chips
                                    multiple
                                    item-title="name"
                                    item-value="_id"
                                    label="Share with Project"
                                >
                                </v-autocomplete>
                                <v-tooltip location="bottom">
                                    <template v-slot:activator="{ props }">
                                        <v-icon
                                            color="primary-light"
                                            v-bind="props"
                                            class="ml-5 mt-1"
                                            style="width: 40px"
                                            icon="$information"
                                        >
                                        </v-icon>
                                    </template>
                                    <span>{{ shareExplanation }}</span>
                                </v-tooltip>
                            </div>
                        </div>
                    </v-form>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn
                        color="font-light"
                        variant="text"
                        @click="state.startDialog = false"
                    >
                        Cancel
                    </v-btn>
                    <v-btn
                        color="primary-light"
                        variant="text"
                        :disabled="!state.submitValid"
                        @click="submit"
                    >
                        Submit
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
        <BenchmarkComparison
            :modelValue="state.showBenchmarkComparison"
            @update:modelValue="state.showBenchmarkComparison = false"
            :benchmarks="filteredBenchmarks"
            :selected="selectedJobs"
        ></BenchmarkComparison>
    </v-container>
</template>

<script setup>
import { useRouter, onBeforeRouteLeave } from "vue-router";
import { sanitizeDate, calculateRunTime } from "~/utils/date";
import { encodeBraceNotation } from "~/utils/braceNotation";

const shareExplanation =
    "Shared benchmarks are visible to all other members of the selected project";

const headers = [
    {
        title: "#",
        key: "runNr"
    },
    {
        title: "Job IDs",
        key: "jobIds"
    },
    { title: "Name", key: "name" },
    { title: "Configuration", key: "configName" },
    { title: "Issuer", key: "issuer" },
    { title: "Date", key: "startTime" },
    { title: "State", key: "state", align: "center" },
    { title: "", key: "attributes" }
];

const { $api, $authStore, $store, $snackbar } = useNuxtApp();

const { data, refresh, pending } = await useAsyncData(
    `benchmarks-${$authStore.user?.user_name}`,
    async () => {
        const [b, j] = await Promise.all([
            $api.benchmarks.get(),
            $api.slurm.getJobs()
        ]);
        return {
            benchmarks: b?.data || [],
            slurmJobs: j || {}
        };
    }
);

const { data: configurations } = await useAsyncData(
    `configurations-${$authStore.user?.user_name}`,
    () => $api.configurations.get(),
    { lazy: true, transform: (v) => v?.data || [] }
);

const { data: jobs } = await useAsyncData(
    `jobs-${$authStore.user?.user_name}`,
    () => $api.jobs.get(null, true),
    { lazy: true, transform: (v) => v?.data || [] }
);

const jobsByRunNr = computed(() => {
    if (!jobs.value) return {};
    return jobs.value.reduce((acc, job) => {
        if (!job.runNr) return acc;
        (acc[parseInt(job.runNr)] ||= []).push(job);
        return acc;
    }, {});
});

const slurmJobs = computed(() => data.value.slurmJobs);
const benchmarks = computed(() => data.value.benchmarks);

const { benchmarkStates } = useBenchmarks({
    slurmJobs: slurmJobs,
    benchmarks: benchmarks
});

const projects = computed(() => $authStore.user?.projects || []);

const tableSortBy = ref([{ key: "runNr", order: "desc" }]);
const { vNotEmpty } = useFormValidation();
const router = useRouter();

const projectFilter = useCookie("xbat_project-filter", { default: () => null });
const hideShared = useCookie("xbat_hide-shared", { default: () => true });

watch(
    () => $authStore.userLevel,
    (level) => {
        if (
            level == $authStore.UserLevelEnum.demo ||
            level == $authStore.UserLevelEnum.admin
        )
            hideShared.value = false;
    },
    { immediate: true }
);

const form = reactive({
    name: "",
    configId: null,
    sharedProjects: []
});

const action = reactive({
    type: null,
    eligible: [],
    ineligible: [],
    dialog: false,
    anonymise: false,
    reassignRunNr: true,
    updateColl: true
});

const state = reactive({
    startDialog: false,
    selected: [],
    submitValid: false,
    intervalHandle: null,
    search: "",
    projectsToShareWith: [],
    showShareConflictWarning: false,
    showBenchmarkComparison: false,
    isExporting: false,
    isImporting: false,
    nonExportable: false,
    selectedFile: null
});

const actionsDisabled = computed(() => !state.selected.length);

const statusDisabled = computed(() => {
    return state.selected.every((x) =>
        ["pending", "queued", "running"].includes(x.state)
    );
});

const configurationsById = computed(() =>
    Object.fromEntries(
        configurations.value.map((x) => [x._id, x.configuration])
    )
);

const variableForm = ref({});

watch(
    () => form.configId,
    (v) => {
        if (!v) return;
        if (!variableForm.value[v])
            variableForm.value[v] = configurationsById.value[v].variables;
    }
);

const submit_form = ref(null);

const tableHeaders = computed(() =>
    hideShared.value ? headers.filter((x) => x.key !== "issuer") : headers
);

const selectedJobs = computed(() => {
    return state.selected.map((x) => x.jobIds).flat(1);
});

const filteredBenchmarks = computed(() => {
    if (!benchmarks.value) return [];
    let filtered = unref(benchmarks);

    if (
        hideShared.value &&
        $authStore.userLevel != $authStore.UserLevelEnum.admin &&
        $authStore.userLevel != $authStore.UserLevelEnum.demo
    )
        filtered = filtered.filter(
            (x) => x.issuer == $authStore.user?.user_name
        );
    if (!hideShared.value && projectFilter.value)
        filtered = filtered.filter((x) =>
            x?.sharedProjects?.includes(projectFilter.value)
        );

    return (
        filtered
            // filter old benchmarks
            .filter(
                (x) =>
                    x.cli || x.configuration?.configuration?.configurationName
            )
            .map((x) =>
                Object.assign(x, {
                    configName: x.cli
                        ? null
                        : x.configuration.configuration.configurationName
                })
            )
    );
});

const updateBenchmarkName = async ({ runNr, value }) => {
    if ($store.demo) {
        $snackbar.show($store.demoMessage);
        return;
    }
    await $api.benchmarks.patch(runNr, { name: value });
    await refresh();
    $snackbar.show("Updated Benchmark Name");
};

const setAction = (type) => {
    action.ineligible = [];
    action.eligible = [];

    if (!state.selected.length && type != "purge" && type != "import") return;
    if (type == "export") state.nonExportable = false;

    if (type == "cancel") {
        state.selected.forEach((x) => {
            action[x.state == "running" ? "eligible" : "ineligible"].push(x);
        });
    } else action.eligible = state.selected;

    action.type = type;
    action.dialog = true;
};

const configurationItems = computed(() => {
    return Object.values(configurations.value).map((x) => ({
        title: x.configuration.configurationName,
        value: x._id,
        shared: !!x.configuration?.sharedProjects?.length
    }));
});

const revokeAccess = async () => {
    await Promise.all(
        state.selected.map((x) =>
            $api.benchmarks.patch(x.runNr, {
                sharedProjects: []
            })
        )
    );
    $snackbar.show("Access revoked");

    await refresh();
};

const executeAction = async () => {
    if ($store.demo) {
        $snackbar.show($store.demoMessage);
        action.dialog = false;
        action.type = "";
        return;
    }

    if (
        action.type != "purge" &&
        action.type != "import" &&
        !state.selected.length
    )
        return;

    let message = `Benchmark${action.eligible.length > 1 ? "s" : ""} `;

    if (action.type === "delete") {
        await Promise.all(
            action.eligible.map((x) => $api.benchmarks.delete(x.runNr))
        );
        state.selected.length = [];
        message += "deleted";
    } else if (action.type === "cancel") {
        await Promise.all(
            action.eligible.map((b) => $api.benchmarks.cancel(b.runNr))
        );
        state.selected.length = [];
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
        link.download = `exported_${action.eligible
            .map((x) => x.runNr)
            .join("_")}.tgz`;
        document.body.appendChild(link);
        link.click();

        window.URL.revokeObjectURL(url);
        document.body.removeChild(link);

        action.dialog = false;
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
        state.selectedFile = null;
        message = "Imported Benchmarks to xbat";
        state.isImporting = false;
        action.reassignRunNr = true;
        action.updateColl = true;
    } else if (action.type == "purge") {
        await $api.benchmarks.purge();
        message = "Purged deleted jobs from QuestDB";
    }

    $snackbar.show(message);
    action.dialog = false;
    action.type = "";
    await refresh();
};

const handleRowClick = (_, { item }) => {
    router.push({
        path: `/benchmarks/${item.runNr}`
    });
};

const submit = async () => {
    state.startDialog = false;

    if ($store.demo) {
        $snackbar.show($store.demoMessage);
        return;
    }

    await $api.benchmarks.submit({
        name: form.name,
        configId: form.configId,
        sharedProjects: form.sharedProjects,
        variables: variableForm.value[form.configId] || []
    });

    if (!$store.error) {
        $snackbar.show(
            "Benchmark submitted - it may take a few seconds until the benchmark is displayed"
        );
        setTimeout(async () => {
            if (state.intervalHandle === null) {
                await refresh();
                state.intervalHandle = setInterval(async () => {
                    await refresh();
                }, 10000);
            }
        }, 5000);
    }
};

watch(
    () => state.selected,
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

onBeforeRouteLeave(() => {
    clearInterval(state.intervalHandle);
});
</script>

<style lang="scss" scoped>
@use "~/assets/css/colors.scss" as *;
.submit-variables {
    margin: 20px 0 30px 0;
}

.warning {
    color: $danger;
}

.overview-table {
    .name-edit,
    .job-hover-info {
        opacity: 0;
        visibility: hidden;
        display: inline-block;
    }

    .job-hover-info {
        position: absolute;
        top: calc(50% - 10px);
        left: 20px;
    }
    :deep(tr) {
        &:hover {
            .name-edit,
            .job-hover-info {
                opacity: 1;
                visibility: visible;
            }
            .job-ids {
                opacity: 0;
            }
        }
    }

    :deep(.v-data-table__td) {
        max-width: 200px;
        white-space: normal;
        word-break: break-all;
    }
}
</style>
