<template>
    <div>
        <v-container fluid>
            <v-main style="--v-layout-bottom: 0; --v-layout-top: 0px">
                <div
                    class="selection-info mx-auto font-italic"
                    v-if="!state.currentEdit"
                >
                    select configuration to edit
                    <v-icon class="tab-icon" icon="$arrowRight"></v-icon>
                </div>
                <div v-else>
                    <v-expansion-panels
                        :modelValue="settingsExpandedCookie ? 'settings' : null"
                        @update:modelValue="settingsExpandedCookie = !!$event"
                        eager
                    >
                        <v-expansion-panel value="settings">
                            <v-expansion-panel-title>
                                <div class="expansion-title">Settings</div>
                                <v-icon
                                    color="error"
                                    v-show="!validity.settings"
                                    size="x-small"
                                    title="Invalid inputs detected"
                                    icon="$alertCircle"
                                ></v-icon>
                            </v-expansion-panel-title>
                            <v-expansion-panel-text>
                                <v-form
                                    class="mt-3"
                                    v-model="validity.settings"
                                    ref="settings_form"
                                >
                                    <v-row>
                                        <v-col md="6" sm="12"
                                            ><v-text-field
                                                label="Configuration Name"
                                                v-model="form.configurationName"
                                                :rules="[vNotEmpty]"
                                            ></v-text-field
                                        ></v-col>
                                        <v-col md="6" sm="12"
                                            ><v-number-input
                                                label="Iterations"
                                                v-model.number="form.iterations"
                                                :rules="[vNotEmpty, vInteger]"
                                            ></v-number-input
                                        ></v-col>
                                        <v-col
                                            md="6"
                                            sm="12"
                                            v-if="
                                                $authStore.user.projects.length
                                            "
                                        >
                                            <v-autocomplete
                                                :items="
                                                    $authStore.user.projects
                                                "
                                                v-model="form.sharedProjects"
                                                chips
                                                closable-chips
                                                multiple
                                                item-title="name"
                                                item-value="_id"
                                                label="Share with Project"
                                            >
                                                <template #prepend-inner>
                                                    <v-tooltip
                                                        location="bottom"
                                                    >
                                                        <template
                                                            v-slot:activator="{
                                                                props
                                                            }"
                                                        >
                                                            <v-icon
                                                                color="primary-light"
                                                                v-bind="props"
                                                                class="ml-1"
                                                                icon="$information"
                                                            >
                                                            </v-icon>
                                                        </template>
                                                        <span
                                                            >Shared
                                                            configurations are
                                                            accessible to all
                                                            project
                                                            members</span
                                                        >
                                                    </v-tooltip>
                                                </template>
                                            </v-autocomplete>
                                        </v-col>
                                        <v-col md="6" sm="12">
                                            <v-number-input
                                                label="Measurement Interval (seconds)"
                                                v-model.number="form.interval"
                                                :rules="[
                                                    vNotEmpty,
                                                    vNumber,
                                                    vInteger,
                                                    (v) =>
                                                        parseInt(v) >= 5 ||
                                                        'Value must be at least 5 seconds'
                                                ]"
                                            >
                                                <template #prepend-inner>
                                                    <v-tooltip location="top">
                                                        <template
                                                            v-slot:activator="{
                                                                props
                                                            }"
                                                        >
                                                            <v-icon
                                                                color="primary-light"
                                                                v-bind="props"
                                                                class="ml-1"
                                                                icon="$information"
                                                            >
                                                            </v-icon>
                                                        </template>
                                                        <span
                                                            >Current minimum
                                                            interval is 5
                                                            seconds</span
                                                        >
                                                    </v-tooltip>
                                                </template>
                                            </v-number-input>
                                        </v-col>
                                        <v-col sm="12">
                                            <v-row>
                                                <v-col sm="12" md="6">
                                                    <v-switch
                                                        label="Enable Monitoring"
                                                        v-model="
                                                            form.enableMonitoring
                                                        "
                                                    ></v-switch>
                                                </v-col>
                                                <v-col sm="12" md="6">
                                                    <v-switch
                                                        label="Enable Monitoring of Hardware Performance Counters"
                                                        v-model="
                                                            form.enableLikwid
                                                        "
                                                        :disabled="
                                                            !form.enableMonitoring
                                                        "
                                                    ></v-switch>
                                                </v-col>
                                            </v-row>
                                        </v-col>

                                        <v-col md="12">
                                            <!-- show only mongodb _id, not temporary uuid -->
                                            <div
                                                class="text-medium-emphasis text-caption"
                                            >
                                                Configuration ID:
                                                {{
                                                    state.currentEdit &&
                                                    currentEditNotYetSaved
                                                        ? "save to view ID"
                                                        : state.currentEdit
                                                }}
                                            </div>
                                        </v-col>
                                    </v-row>
                                </v-form>
                            </v-expansion-panel-text>
                        </v-expansion-panel>
                    </v-expansion-panels>
                    <v-card class="mt-5">
                        <v-card-title>
                            Job Script
                            <v-icon
                                color="error"
                                v-show="!validity.jobscript"
                                size="x-small"
                                title="Invalid inputs detected in one or multiple variants"
                                icon="$alertCircle"
                            ></v-icon>
                        </v-card-title>
                        <v-card-text>
                            <v-form
                                v-model="validity.jobscript"
                                ref="jobscript_form"
                            >
                                <div class="d-flex justify-end">
                                    <v-dialog width="800">
                                        <template v-slot:activator="{ props }">
                                            <v-btn
                                                v-bind="props"
                                                prepend-icon="$currency"
                                                size="small"
                                                variant="text"
                                                >Job Variables
                                                {{
                                                    `(${variableCount})`
                                                }}</v-btn
                                            >
                                        </template>
                                        <v-card>
                                            <v-card-title
                                                >Job Variables</v-card-title
                                            >
                                            <v-card-text>
                                                <p
                                                    class="text-medium-emphasis text-caption font-italic"
                                                    style="margin-top: -10px"
                                                >
                                                    Access variables in your
                                                    jobscript with $VARIABLE.
                                                    Defining multiple values for
                                                    a variable will create a job
                                                    for each value. Variables
                                                    will be shared across all
                                                    variants and are not
                                                    specific to the current
                                                    variant!
                                                </p>
                                                <JobVariables
                                                    v-model="form.variables"
                                                ></JobVariables>
                                            </v-card-text>
                                        </v-card>
                                    </v-dialog>
                                    <v-dialog
                                        :close-on-content-click="false"
                                        width="800"
                                    >
                                        <template v-slot:activator="{ props }">
                                            <v-btn
                                                v-bind="props"
                                                prepend-icon="$server"
                                                size="small"
                                                variant="text"
                                                >Partitions & Nodes</v-btn
                                            >
                                        </template>
                                        <v-card>
                                            <v-card-title
                                                >Partitions &
                                                Nodes</v-card-title
                                            >
                                            <v-card-text>
                                                <v-treeview
                                                    color="primary-light"
                                                    :items="partitionTree"
                                                    item-value="title"
                                                    open-on-click
                                                ></v-treeview>
                                            </v-card-text>
                                        </v-card>
                                    </v-dialog>
                                    <v-btn
                                        href="https://xbat.dev/docs/user/get-started/job-configuration"
                                        variant="text"
                                        target="_blank"
                                        prepend-icon="$documentation"
                                        title="Visit Documentation for more details"
                                        size="small"
                                        >Docs</v-btn
                                    >
                                    <v-btn
                                        href="https://slurm.schedmd.com/sbatch.html#SECTION_OPTIONS"
                                        variant="text"
                                        target="_blank"
                                        prepend-icon="$openInNew"
                                        title="Visit Slurm Documentation"
                                        size="small"
                                        >Slurm Documentation</v-btn
                                    >
                                </div>
                                <div
                                    class="d-flex justify-space-between align-center"
                                >
                                    <v-tabs
                                        v-model="state.variantTab"
                                        class="variant-tabs"
                                        center-active
                                        force
                                        show-arrows
                                        color="primary-light"
                                    >
                                        <v-tab
                                            v-for="[
                                                i,
                                                v
                                            ] in form.jobscript.entries()"
                                            :value="i"
                                            :key="i"
                                            :color="
                                                form.jobscript[i].variantName
                                                    ? 'primary-light'
                                                    : 'danger'
                                            "
                                        >
                                            <v-dialog max-width="400">
                                                <template
                                                    v-slot:activator="{
                                                        props: activatorProps
                                                    }"
                                                >
                                                    <v-btn
                                                        size="x-small"
                                                        title="Remove Variant"
                                                        color="danger"
                                                        variant="plain"
                                                        v-show="
                                                            state.variantTab ===
                                                                i &&
                                                            form.jobscript
                                                                .length > 1
                                                        "
                                                        icon="$close"
                                                        v-bind="activatorProps"
                                                    >
                                                    </v-btn>
                                                </template>

                                                <template
                                                    v-slot:default="{
                                                        isActive
                                                    }"
                                                >
                                                    <v-card
                                                        title="Delete Variant"
                                                    >
                                                        <v-card-text
                                                            >Do you really want
                                                            to delete variant
                                                            "<span
                                                                class="font-italic"
                                                                >{{
                                                                    form
                                                                        .jobscript[
                                                                        i
                                                                    ]
                                                                        .variantName
                                                                }}</span
                                                            >"?</v-card-text
                                                        >
                                                        <template
                                                            v-slot:actions
                                                        >
                                                            <v-spacer></v-spacer>
                                                            <v-btn
                                                                text="Cancel"
                                                                @click="
                                                                    isActive.value = false
                                                                "
                                                            ></v-btn>
                                                            <v-btn
                                                                color="danger"
                                                                @click="
                                                                    removeVariant(
                                                                        i
                                                                    );
                                                                    isActive.value = false;
                                                                "
                                                                >Delete</v-btn
                                                            >
                                                        </template>
                                                    </v-card>
                                                </template>
                                            </v-dialog>
                                            {{ form.jobscript[i].variantName }}
                                            <InlineEdit
                                                title="Rename Variant"
                                                :modelValue="
                                                    form.jobscript[i]
                                                        .variantName
                                                "
                                                @update:modelValue="
                                                    form.jobscript[
                                                        i
                                                    ].variantName = $event
                                                "
                                            >
                                                <template #activator>
                                                    <v-btn
                                                        size="x-small"
                                                        title="Rename Variant"
                                                        v-if="
                                                            state.variantTab ==
                                                            i
                                                        "
                                                        icon="$edit"
                                                        variant="plain"
                                                    >
                                                    </v-btn>
                                                </template>
                                            </InlineEdit>
                                        </v-tab>
                                    </v-tabs>
                                    <v-btn
                                        @click="addVariant"
                                        variant="outlined"
                                        size="small"
                                        color="primary-light"
                                        prepend-icon="$plus"
                                        >Add Variant
                                    </v-btn>
                                </div>
                                <v-window v-model="state.variantTab">
                                    <v-window-item
                                        v-for="[
                                            i,
                                            v
                                        ] of form.jobscript.entries()"
                                        :value="i"
                                        :key="i"
                                    >
                                        <div>
                                            <Editor
                                                v-model="form.jobscript[i]"
                                                auto-resize
                                                constrained-jobscript
                                                @update:validity="
                                                    validity.jobscript = $event
                                                "
                                                :partitions="partitions"
                                            >
                                            </Editor>
                                        </div>
                                    </v-window-item>
                                </v-window>
                            </v-form>
                        </v-card-text>
                    </v-card>

                    <div
                        v-if="
                            $authStore.userLevel >=
                            $authStore.UserLevelEnum.user
                        "
                    >
                        <div class="d-flex gap-20 mt-5">
                            <v-btn
                                color="primary"
                                @click="save()"
                                :disabled="
                                    Object.values(validity)
                                        .map((x) => !!x)
                                        .includes(false)
                                "
                            >
                                Save
                            </v-btn>
                            <v-btn @click="cancelEdit"> Cancel </v-btn>
                        </div>
                    </div>
                </div>
            </v-main>
            <v-navigation-drawer
                permanent
                location="right"
                class="sidebar"
                width="300"
            >
                <template #prepend
                    ><div class="header">CONFIGURATIONS</div></template
                >
                <template #append> </template>
                <div class="list">
                    <v-list
                        density="compact"
                        v-model:selected="state.selectedEdit"
                        mandatory
                    >
                        <template
                            v-for="[id, v] of Object.entries(
                                configurationCache
                            )"
                            :value="id"
                        >
                            <v-hover>
                                <template
                                    v-slot:default="{ isHovering, props }"
                                >
                                    <v-list-item
                                        v-bind="props"
                                        @click="state.selectedEdit = [id]"
                                        :value="id"
                                        style="line-height: 36px"
                                    >
                                        <template #prepend>
                                            <div
                                                class="mr-2"
                                                v-if="
                                                    v.configuration
                                                        .sharedProjects?.length
                                                "
                                            >
                                                <v-icon
                                                    size="small"
                                                    color="primary-light"
                                                    title="This configuration is shared with other users"
                                                    icon="$share"
                                                ></v-icon>
                                            </div>
                                        </template>
                                        <span class="configuration-name">
                                            {{
                                                "configurationName" in
                                                v.configuration
                                                    ? v.configuration
                                                          .configurationName
                                                    : id
                                            }}
                                        </span>
                                        <template #append>
                                            <v-btn-group
                                                devided
                                                variant="text"
                                                density="compact"
                                                v-if="
                                                    isHovering &&
                                                    $authStore.userLevel >=
                                                        $authStore.UserLevelEnum
                                                            .user
                                                "
                                            >
                                                <v-btn
                                                    title="Duplicate Configuration"
                                                    size="small"
                                                    @click.stop="addConfig(id)"
                                                    icon="$duplicate"
                                                >
                                                </v-btn>
                                                <v-btn
                                                    title="Delete Configuration"
                                                    size="small"
                                                    @click.stop="
                                                        setAction('delete', id)
                                                    "
                                                    v-if="
                                                        (v?.misc?.owner &&
                                                            $authStore.user
                                                                .user_name ===
                                                                v.misc.owner) ||
                                                        $authStore.userLevel >
                                                            $authStore
                                                                .UserLevelEnum
                                                                .user
                                                    "
                                                    icon="$trashCan"
                                                >
                                                </v-btn>
                                            </v-btn-group>
                                        </template>
                                    </v-list-item>
                                </template>
                            </v-hover>
                        </template>
                    </v-list>
                </div>
                <v-list-item
                    ><div
                        v-if="
                            $authStore.userLevel >
                            $authStore.UserLevelEnum.guest
                        "
                        class="d-flex justify-center"
                    >
                        <v-btn
                            @click="addConfig()"
                            title="Add Configuration"
                            elevation="0"
                            variant="tonal"
                            prepend-icon="$newFile"
                        >
                            New configuration
                        </v-btn>
                    </div></v-list-item
                >
            </v-navigation-drawer>
        </v-container>
        <v-dialog v-model="state.showActionDialog" max-width="600px">
            <v-card>
                <v-card-title class="text-capitalize">
                    {{ state.action }}
                </v-card-title>
                <v-card-text>
                    <div v-if="state.action == 'delete'">
                        Do you really want to
                        <span class="font-weight-bold">{{ state.action }}</span>
                        the configuration '<span class="font-weight-bold">{{
                            state.actionTargetName
                        }}</span
                        >'?
                    </div>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn
                        color="grey"
                        text
                        @click="state.showActionDialog = false"
                    >
                        Cancel
                    </v-btn>
                    <v-btn
                        :color="
                            state.action == 'delete'
                                ? 'red darken-3'
                                : 'primary'
                        "
                        text
                        @click="executeAction(state.action, state.actionTarget)"
                    >
                        {{ state.action }}
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </div>
</template>

<script setup>
import { ref, computed, watch, reactive, nextTick } from "vue";
import { deepClone } from "~/utils/misc";
import { v4 as uuidv4 } from "uuid";
const { vNotEmpty, vNumber, vInteger } = useFormValidation();
const { $authStore, $api, $snackbar, $store } = useNuxtApp();

useSeoMeta({
    title: "Configurations",
    ogTitle: "Configurations",
    description: "Configuration management for xbat",
    ogDescription: "Configuration management for xbat"
});

const validity = reactive({ settings: true, jobscript: true });

const settingsExpandedCookie = useCookie(
    "xbat_configuration-settings-expanded",
    { default: () => true }
);

const defaultForm = {
    jobscript: [
        {
            variantName: "Default Variant",
            "job-name": "",
            partition: "",
            nodes: 1,
            ntasks: 1,
            time: "01:00:00",
            output: ".xbat/outputs/%j.out",
            error: ".xbat/outputs/%j.out",
            script: "\n# Your script here\n"
        }
    ],
    variables: [],
    iterations: 1,
    enableLikwid: true,
    enableMonitoring: true,
    interval: 5,
    configurationName: "new configuration",
    sharedProjects: []
};

const configurationCache = ref({});
const form = ref({});

form.value = deepClone(defaultForm);

const setConfigurationCache = () => {
    configurationCache.value = Object.fromEntries(
        deepClone(configurations.value).map((x) => [x._id, x])
    );
};

const { data: partitions } = await useAsyncData(
    "slurm-partitions",
    () => $api.slurm.getPartitions(),
    { lazy: true }
);

const { data: configurations, refresh } = await useAsyncData(
    `configurations-${$authStore.user.user_name}`,
    async () => (await $api.configurations.get())?.data || []
);

setConfigurationCache();

const partitionTree = computed(() => {
    let items = [];

    for (let [key, value] of Object.entries(partitions.value)) {
        items.push({
            title: key,
            children: value.map((x) => Object.assign({ title: x }))
        });
    }
    return items;
});

const variableCount = computed(() => {
    return (
        form.value.variables?.filter((x) => x.key.length && x.values.length)
            .length || 0
    );
});

const fetchConfigurations = async () => {
    await refresh();
    // TODO known issue - this causes unsaved changes to be overwritten
    setConfigurationCache();
};

const state = reactive({
    variantTab: 0,
    currentEdit: "",
    previousEdit: "",
    selectedEdit: [],
    action: null,
    actionTarget: null,
    showActionDialog: false,
    actionTargetName: null
});

const settings_form = ref(null);
const jobscript_form = ref(null);

const formBeforeEdit = ref({});

const currentEditNotYetSaved = computed(() =>
    (state.currentEdit || "").includes("-")
);

watch(
    () => state.selectedEdit,
    (v) => {
        if (!v || !v.length) {
            state.currentEdit = null;
            return;
        }
        // v-list always returns array of selected entries even though only one is selectable at a time
        const id = v[0];

        state.currentEdit = id;
        if (!id || id == state.previousEdit) return;

        const c = configurationCache.value[id]?.configuration;

        if (!c) return;

        form.value = c;
        if (!form.value.sharedProjects) form.value.sharedProjects = [];
        if (!(id in formBeforeEdit.value)) {
            formBeforeEdit.value[id] = deepClone(form.value);
        }
        state.previousEdit = id;
        nextTick(() => {
            settings_form.value.validate();
            jobscript_form.value.validate();
        });
    }
);

const addConfig = (presetId = "") => {
    // generate random uuid as a temporary _id -> will be replaced after insertion to database
    const _id = uuidv4();

    let newConfig = deepClone(
        presetId
            ? configurationCache.value[presetId].configuration
            : defaultForm
    );

    // TODO add "(copy)" n times when creating n copies
    configurationCache.value[_id] = {
        configuration: {
            ...newConfig,
            configurationName:
                presetId && presetId in configurationCache.value
                    ? `${configurationCache.value[presetId].configuration.configurationName} (copy)`
                    : "new configuration"
        }
    };

    state.selectedEdit = [Object.keys(configurationCache.value).at(-1)];
};

const addVariant = () => {
    let copy = deepClone(form.value.jobscript[state.variantTab]);
    copy.variantName = `${copy.variantName} (copy)`;
    form.value.jobscript.push(copy);
    state.variantTab = form.value.jobscript.length - 1;
};

const resetForm = () => {
    if (
        !(state.currentEdit in formBeforeEdit.value) ||
        !Object.keys(formBeforeEdit.value[state.currentEdit]).length
    )
        return;
    configurationCache.value[state.currentEdit].configuration = deepClone(
        formBeforeEdit.value[state.currentEdit]
    );
    form.value = configurationCache.value[state.currentEdit].configuration;
};

const cancelEdit = () => {
    // reset form to state before edit
    resetForm();
    state.selectedEdit = [];
};

const save = async () => {
    if (!validity.settings || !validity.jobscript) return;

    if ($store.demo) {
        $snackbar.show($store.demoMessage);
        return;
    }

    let response = {};

    // post
    if (!configurations.value.map((x) => x._id).includes(state.currentEdit)) {
        let payload = configurationCache.value[state.currentEdit].configuration;
        // filter empty variables (only empty key)
        payload.variables = payload.variables.filter((x) => x.key.length);
        response = await $api.configurations.post({
            configuration:
                configurationCache.value[state.currentEdit].configuration
        });
        $snackbar.show("Created Configuration");
    }
    // put
    else {
        const configId = state.selectedEdit;
        let payload = configurations.value.filter((x) => x._id == configId)[0];
        payload.configuration = form.value;
        if (payload.configuration.variables === undefined)
            payload.configuration.variables = [];
        // filter empty variables (only empty key)
        payload.configuration.variables =
            payload.configuration.variables.filter((x) => x.key.length);
        response = await $api.configurations.put(state.currentEdit, payload);
        $snackbar.show("Configuration Saved");
    }

    await fetchConfigurations();

    if (currentEditNotYetSaved.value) state.selectedEdit = [response._id];
    nextTick(() => {
        if (state.currentEdit in configurations.value)
            formBeforeEdit.value[state.currentEdit] = deepClone(
                configurations.value[state.currentEdit].configuration
            );
    });
};

const setAction = (action, target) => {
    state.action = action;
    state.actionTarget = target;
    state.showActionDialog = true;
    state.actionTargetName =
        target in configurationCache.value
            ? configurationCache.value[target].configuration.configurationName
            : target;
    state.selectedEdit = [target];
};

const executeAction = async (action, target) => {
    if ($store.demo) {
        $snackbar.show($store.demoMessage);
        state.showActionDialog = false;
        return;
    }

    if (action == "delete") {
        delete configurationCache.value[state.currentEdit];
        if (!currentEditNotYetSaved.value) {
            await $api.configurations.delete(target);
            fetchConfigurations();
        }
        if (target == state.currentEdit) state.selectedEdit = [];
    }
    state.showActionDialog = false;
    $snackbar.show("Deleted configuration");
};

const removeVariant = (i) => {
    if (form.value.jobscript.length < 2) return;
    state.variantTab = form.value.jobscript.length - 2;

    form.value.jobscript.splice(i, 1);
};

// TODO workaround due to internal vuetify bug that resets variantTab to undefined when splicing v-model of tabs
watch(
    () => state.variantTab,
    (v) => {
        if (v === undefined)
            nextTick(() => {
                state.variantTab = form.value.jobscript.length - 1;
            });
    }
);
</script>

<style lang="scss" scoped>
@use "~/assets/css/colors.scss" as *;

.selection-info {
    color: $font-light;
    width: fit-content;
    font-size: 0.925rem;
}

.variant-tabs {
    margin-bottom: 10px;
    max-width: 100%;
}

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
    .configuration-name {
        white-space: normal;
        word-break: break-all;
    }
}

.expansion-title {
    font-size: 1.25rem;
    font-weight: 500;
}
</style>
