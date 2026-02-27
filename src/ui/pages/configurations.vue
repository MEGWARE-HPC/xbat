<template>
    <div>
        <v-container fluid>
            <div class="page-layout">
                <div class="left">
                    <ConfigurationSidebar
                        :configuration-cache="configurationCache"
                        :selected-id="state.currentEdit"
                        :user="$authStore.user"
                        :user-level="$authStore.userLevel"
                        :UserLevelEnum="$authStore.UserLevelEnum"
                        @select="(id) => (state.selectedEdit = [id])"
                        @select-folder="
                            (fid) => {
                                selectedFolderId = fid;
                                state.selectedEdit = [];
                            }
                        "
                        @duplicate="addConfig"
                        @delete="(id) => setAction('delete', id)"
                    />
                </div>
                <div class="right">
                    <ConfigurationEditor
                        v-if="state.currentEdit"
                        ref="editorRef"
                        :form="form"
                        :validity="validity"
                        :current-edit="state.currentEdit"
                        :current-edit-not-yet-saved="currentEditNotYetSaved"
                        :settings-expanded="settingsExpandedCookie"
                        @update:settingsExpanded="
                            settingsExpandedCookie = $event
                        "
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
                    <FolderBrowser
                        v-else-if="selectedFolderNode"
                        :folder="selectedFolderNode"
                        :configs="selectedFolderConfigs"
                        :user-level="$authStore.userLevel"
                        :UserLevelEnum="$authStore.UserLevelEnum"
                        :my-root-id="
                            myHomeNode?.id ? String(myHomeNode.id) : ''
                        "
                        @create-config="addConfig"
                        @open-folder="
                            (fid) => {
                                selectedFolderId = fid;
                            }
                        "
                        @open-config="
                            (cid) => {
                                selectedFolderId = null;
                                state.selectedEdit = [cid];
                            }
                        "
                    />
                    <v-main
                        v-else
                        class="empty"
                        style="--v-layout-bottom: 0; --v-layout-top: 0px"
                    >
                        Select a configuration to edit, or a folder to browse.
                    </v-main>
                </div>
            </div>
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
import FolderBrowser from "~/components/configuration/FolderBrowser.vue";

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

const selectedFolderId = ref(null);
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

const { data: folderTree } = await useAsyncData(
    `configuration-folders-tree-page-${$authStore.user.user_name}`,
    async () => (await $api.configurationFolders.get())?.data || []
);

const folderMap = computed(() => {
    const map = new Map();
    const walk = (nodes = [], parentId = null) => {
        for (const n of nodes) {
            if (!n?.id) continue;

            const node = { ...n, __parentId: parentId };
            map.set(String(node.id), node);

            walk(n.children || [], String(node.id));
        }
    };
    walk(folderTree.value || [], null);
    return map;
});

const rootIdSet = computed(() => {
    const s = new Set();
    for (const n of folderTree.value || []) {
        if (n?.id) s.add(String(n.id));
    }
    return s;
});

const configsByFolder = computed(() => {
    const m = new Map();
    for (const [id, doc] of Object.entries(configurationCache.value || {})) {
        const folderId = doc?.configuration?.folderId
            ? String(doc.configuration.folderId)
            : "root";
        if (!m.has(folderId)) m.set(folderId, []);
        m.get(folderId).push({ id, doc });
    }
    for (const [k, arr] of m.entries()) {
        arr.sort((a, b) =>
            (a.doc?.configuration?.configurationName || a.id).localeCompare(
                b.doc?.configuration?.configurationName || b.id
            )
        );
        m.set(k, arr);
    }
    return m;
});

const projectNameById = computed(() => {
    const m = new Map();
    for (const p of $authStore.user?.projects || []) {
        m.set(String(p._id), p.name);
    }
    return m;
});

const sharedConfigsFlat = computed(() => {
    const arr = [];
    for (const [id, doc] of Object.entries(configurationCache.value || {})) {
        if (doc?.misc?.owner && doc.misc.owner !== $authStore.user.user_name) {
            arr.push({ id, doc });
        }
    }
    return arr;
});

const sharedBucket = (doc) => {
    const ids = doc?.configuration?.sharedProjects || [];
    for (const pid of ids) {
        const k = String(pid);
        if (projectNameById.value.has(k)) return k;
    }
    return "unknown";
};

// groups: [{ key: "__shared__:pid", pid, name, items: [{id,doc}]}]
const sharedGroups = computed(() => {
    const buckets = new Map();

    for (const { id, doc } of sharedConfigsFlat.value) {
        const pid = sharedBucket(doc);
        const name =
            pid === "unknown"
                ? "Unknown / Other"
                : projectNameById.value.get(String(pid)) || "Unknown / Other";

        const groupKey = `__shared__:${pid}`;
        if (!buckets.has(groupKey)) {
            buckets.set(groupKey, { key: groupKey, pid, name, items: [] });
        }
        buckets.get(groupKey).items.push({ id, doc });
    }

    for (const g of buckets.values()) {
        g.items.sort((a, b) =>
            (a.doc?.configuration?.configurationName || a.id).localeCompare(
                b.doc?.configuration?.configurationName || b.id
            )
        );
    }

    return Array.from(buckets.values()).sort((a, b) =>
        a.name.localeCompare(b.name)
    );
});

const sharedGroupByKey = computed(() => {
    const m = new Map();
    for (const g of sharedGroups.value) m.set(g.key, g);
    return m;
});

const selectedFolderNode = computed(() => {
    const key = selectedFolderId.value ? String(selectedFolderId.value) : "";
    if (!key) return null;

    if (key === "__all__") {
        const roots = (folderTree.value || []).map((n) => ({
            ...n,
            __parentId: "__all__"
        }));

        return {
            id: "__all__",
            name: "All Folders",
            __parentId: null,
            children: roots
        };
    }

    if (key === "__shared__") {
        // children = project group "folders"
        const children = sharedGroups.value.map((g) => ({
            id: g.key,
            name: g.name,
            __parentId: "__shared__",
            children: []
        }));

        return {
            id: "__shared__",
            name: "Shared Configurations",
            __parentId: null,
            children
        };
    }

    if (key.startsWith("__shared__:")) {
        const g = sharedGroupByKey.value.get(key);
        if (!g) return null;

        return {
            id: g.key,
            name: g.name,
            __parentId: "__shared__",
            children: []
        };
    }

    const real = folderMap.value.get(key) || null;
    if (!real) return null;

    if (isManager.value && rootIdSet.value.has(key)) {
        return { ...real, __parentId: "__all__" };
    }

    return real;
});

const myHomeNode = computed(() => {
    const roots = folderTree.value || [];
    return roots.find((n) => n?.name === $authStore.user.user_name) || null;
});

const isManager = computed(
    () => $authStore.userLevel >= $authStore.UserLevelEnum.manager
);

watchEffect(() => {
    if (state.currentEdit) return;

    if (selectedFolderId.value) return;

    if (myHomeNode.value?.id) {
        selectedFolderId.value = String(myHomeNode.value.id);
    }
});

const selectedFolderConfigs = computed(() => {
    const key = selectedFolderId.value ? String(selectedFolderId.value) : "";
    if (!key) return [];

    if (key === "__all__") return [];
    if (key === "__shared__") return [];

    if (key.startsWith("__shared__:")) {
        const g = sharedGroupByKey.value.get(key);
        return g?.items || [];
    }

    return configsByFolder.value.get(key) || [];
});
</script>

<style lang="scss" scoped>
@use "~/assets/css/colors.scss" as *;
.empty {
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;

    height: 100%;
    width: 100%;

    font-size: 1rem;
    color: $font-light;
    font-style: italic;
}
</style>
