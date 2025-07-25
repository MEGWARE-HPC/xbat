<template>
    <v-container fluid>
        <v-card max-width="95%" class="mx-auto pa-2 mt-5">
            <v-card-title>
                <div class="d-flex align-center gap-20">
                    <Submission @submit="setRefresh">
                        <v-btn
                            color="primary"
                            title="Start Benchmark"
                            :disabled="
                                $authStore.userLevel ==
                                    $authStore.UserLevelEnum.guest ||
                                $authStore.userLevel ==
                                    $authStore.UserLevelEnum.admin
                            "
                        >
                            Start Benchmark
                        </v-btn>
                    </Submission>
                    <v-btn
                        value="share"
                        @click="state.showBenchmarkComparison = true"
                        prepend-icon="$compare"
                    >
                        Compare
                    </v-btn>
                    <OverviewActions
                        :selected="state.selected"
                        @refresh="refresh"
                        @selected:clear="state.selected = []"
                    ></OverviewActions>
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
                    :items-per-page="overviewItemsPerPage"
                    @update:itemsPerPage="overviewItemsPerPage = $event"
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
import { sanitizeDate } from "~/utils/date";
import { encodeBraceNotation } from "~/utils/braceNotation";

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

const { overviewItemsPerPage } = usePreferences();

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

const state = reactive({
    selected: [],
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

const setRefresh = () => {
    setTimeout(async () => {
        if (state.intervalHandle === null) {
            await refresh();
            state.intervalHandle = setInterval(async () => {
                await refresh();
            }, 10000);
        }
    }, 5000);
};

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

const handleRowClick = (_, { item }) => {
    router.push({
        path: `/benchmarks/${item.runNr}`
    });
};

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
