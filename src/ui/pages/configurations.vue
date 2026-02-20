<template>
    <div>
        <v-container fluid>
            <ConfigurationSidebar
                :configuration-cache="configurationCache"
                :selected-id="state.currentEdit"
                :user="$authStore.user"
                :user-level="$authStore.userLevel"
                :UserLevelEnum="$authStore.UserLevelEnum"
                @select="(id) => (state.selectedEdit = [id])"
                @create="addConfig"
                @duplicate="addConfig"
                @delete="(id) => setAction('delete', id)"
            />
            <ConfigurationEditor
                ref="editorRef"
                :form="form"
                :validity="validity"
                :current-edit="state.currentEdit"
                :current-edit-not-yet-saved="currentEditNotYetSaved"
                :settings-expanded="settingsExpandedCookie"
                @update:settingsExpanded="settingsExpandedCookie = $event"
                :vNotEmpty="vNotEmpty"
                :vNumber="vNumber"
                :vInteger="vInteger"
                :projects="$authStore.user.projects"
                :partitions="partitions"
                :partition-tree="partitionTree"
                :variable-count="variableCount"
                :variant-tab="state.variantTab"
                @update:variantTab="state.variantTab = $event"
                :user-level="$authStore.userLevel"
                :UserLevelEnum="$authStore.UserLevelEnum"
                @add-variant="addVariant"
                @remove-variant="removeVariant"
                @save="save"
                @cancel="cancelEdit"
            />
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

import ConfigurationSidebar from "~/components/configuration/ConfigurationSidebar.vue";
import ConfigurationEditor from "~/components/configuration/ConfigurationEditor.vue";

const { vNotEmpty, vNumber, vInteger } = useFormValidation();
const { $authStore, $api, $snackbar, $store } = useNuxtApp();

useSeoMeta({
    title: "Configurations",
    description: "Configuration management for xbat"
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
const form = ref(deepClone(defaultForm));

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
    const items = [];
    for (let [key, value] of Object.entries(partitions.value || {})) {
        items.push({
            title: key,
            children: value.map((x) => ({ title: x }))
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

const editorRef = ref(null);
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
            editorRef.value?.validateForms?.();
        });
    }
);

const addConfig = (presetId = "") => {
    // generate random uuid as a temporary _id -> will be replaced after insertion to database
    const _id = uuidv4();

    const newConfig = deepClone(
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
    const copy = deepClone(form.value.jobscript[state.variantTab]);
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
        const payload =
            configurationCache.value[state.currentEdit].configuration;
        // filter empty variables (only empty key)
        payload.variables = payload.variables.filter((x) => x.key.length);
        response = await $api.configurations.post({
            configuration: payload
        });
        $snackbar.show("Created Configuration");
    }
    // put
    else {
        const configId = state.currentEdit;
        const payload = configurations.value.find((x) => x._id === configId);
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

    if (currentEditNotYetSaved.value) {
        state.selectedEdit = [response._id];
    }
    nextTick(() => {
        const saved = configurations.value.find(
            (x) => x._id === state.currentEdit
        );
        if (saved)
            formBeforeEdit.value[state.currentEdit] = deepClone(
                saved.configuration
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
        if (v === undefined) {
            nextTick(() => {
                state.variantTab = form.value.jobscript.length - 1;
            });
        }
    }
);
</script>
