<template>
    <v-main style="--v-layout-bottom: 0; --v-layout-top: 0px">
        <div class="selection-info mx-auto font-italic" v-if="!currentEdit">
            select configuration to edit
            <v-icon class="tab-icon" icon="$arrowRight" />
        </div>

        <div v-else>
            <v-expansion-panels
                :modelValue="settingsExpanded ? 'settings' : null"
                @update:modelValue="$emit('update:settingsExpanded', !!$event)"
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
                        />
                    </v-expansion-panel-title>

                    <v-expansion-panel-text>
                        <v-form
                            class="mt-3"
                            v-model="validity.settings"
                            ref="settings_form"
                        >
                            <v-row>
                                <v-col md="6" sm="12">
                                    <v-text-field
                                        label="Configuration Name"
                                        v-model="form.configurationName"
                                        :rules="[vNotEmpty]"
                                    />
                                </v-col>

                                <v-col md="6" sm="12">
                                    <v-number-input
                                        label="Iterations"
                                        v-model.number="form.iterations"
                                        :rules="[vNotEmpty, vInteger]"
                                    />
                                </v-col>

                                <v-col md="6" sm="12" v-if="projects?.length">
                                    <v-autocomplete
                                        :items="projects"
                                        v-model="form.sharedProjects"
                                        chips
                                        closable-chips
                                        multiple
                                        item-title="name"
                                        item-value="_id"
                                        label="Share with Project"
                                    >
                                        <template #prepend-inner>
                                            <v-tooltip location="bottom">
                                                <template
                                                    #activator="{ props }"
                                                >
                                                    <v-icon
                                                        color="primary-light"
                                                        v-bind="props"
                                                        class="ml-1"
                                                        icon="$information"
                                                    />
                                                </template>
                                                <span>
                                                    Shared configurations are
                                                    accessible to all project
                                                    members
                                                </span>
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
                                                    #activator="{ props }"
                                                >
                                                    <v-icon
                                                        color="primary-light"
                                                        v-bind="props"
                                                        class="ml-1"
                                                        icon="$information"
                                                    />
                                                </template>
                                                <span
                                                    >Current minimum interval is
                                                    5 seconds</span
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
                                                v-model="form.enableMonitoring"
                                            />
                                        </v-col>
                                        <v-col sm="12" md="6">
                                            <v-switch
                                                label="Enable Monitoring of Hardware Performance Counters"
                                                v-model="form.enableLikwid"
                                                :disabled="
                                                    !form.enableMonitoring
                                                "
                                            />
                                        </v-col>
                                    </v-row>
                                </v-col>

                                <v-col md="12">
                                    <div
                                        class="text-medium-emphasis text-caption"
                                    >
                                        Configuration ID:
                                        {{ showConfigurationID }}
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
                    />
                </v-card-title>

                <v-card-text>
                    <v-form v-model="validity.jobscript" ref="jobscript_form">
                        <div class="d-flex justify-end">
                            <v-dialog width="800">
                                <template #activator="{ props }">
                                    <v-btn
                                        v-bind="props"
                                        prepend-icon="$currency"
                                        size="small"
                                        variant="text"
                                    >
                                        Job Variables ({{ variableCount }})
                                    </v-btn>
                                </template>
                                <v-card>
                                    <v-card-title>Job Variables</v-card-title>
                                    <v-card-text>
                                        <p
                                            class="text-medium-emphasis text-caption font-italic"
                                            style="margin-top: -10px"
                                        >
                                            Access variables in your jobscript
                                            with $VARIABLE. Defining multiple
                                            values for a variable will create a
                                            job for each value. Variables will
                                            be shared across all variants and
                                            are not specific to the current
                                            variant!
                                        </p>
                                        <JobVariables
                                            v-model="form.variables"
                                        />
                                    </v-card-text>
                                </v-card>
                            </v-dialog>

                            <v-dialog
                                :close-on-content-click="false"
                                width="800"
                            >
                                <template #activator="{ props }">
                                    <v-btn
                                        v-bind="props"
                                        prepend-icon="$server"
                                        size="small"
                                        variant="text"
                                    >
                                        Partitions & Nodes
                                    </v-btn>
                                </template>
                                <v-card>
                                    <v-card-title
                                        >Partitions & Nodes</v-card-title
                                    >
                                    <v-card-text>
                                        <v-treeview
                                            color="primary-light"
                                            :items="partitionTree"
                                            item-value="title"
                                            open-on-click
                                        />
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
                            >
                                Docs
                            </v-btn>

                            <v-btn
                                href="https://slurm.schedmd.com/sbatch.html#SECTION_OPTIONS"
                                variant="text"
                                target="_blank"
                                prepend-icon="$openInNew"
                                title="Visit Slurm Documentation"
                                size="small"
                            >
                                Slurm Documentation
                            </v-btn>
                        </div>

                        <div class="d-flex justify-space-between align-center">
                            <v-tabs
                                v-model="variantTabModel"
                                class="variant-tabs"
                                center-active
                                force
                                show-arrows
                                color="primary-light"
                            >
                                <v-tab
                                    v-for="[i, v] in form.jobscript.entries()"
                                    :key="i"
                                    :value="i"
                                    :color="
                                        form.jobscript[i].variantName
                                            ? 'primary-light'
                                            : 'danger'
                                    "
                                >
                                    <v-dialog max-width="400">
                                        <template
                                            #activator="{
                                                props: activatorProps
                                            }"
                                        >
                                            <v-btn
                                                size="x-small"
                                                title="Remove Variant"
                                                color="danger"
                                                variant="plain"
                                                v-show="
                                                    variantTabModel === i &&
                                                    form.jobscript.length > 1
                                                "
                                                icon="$close"
                                                v-bind="activatorProps"
                                            />
                                        </template>

                                        <template #default="{ isActive }">
                                            <v-card title="Delete Variant">
                                                <v-card-text>
                                                    Do you really want to delete
                                                    variant "<span
                                                        class="font-italic"
                                                        >{{
                                                            form.jobscript[i]
                                                                .variantName
                                                        }}</span
                                                    >"?
                                                </v-card-text>
                                                <template #actions>
                                                    <v-spacer />
                                                    <v-btn
                                                        text="Cancel"
                                                        @click="
                                                            isActive.value = false
                                                        "
                                                    />
                                                    <v-btn
                                                        color="danger"
                                                        @click="
                                                            $emit(
                                                                'remove-variant',
                                                                i
                                                            );
                                                            isActive.value = false;
                                                        "
                                                    >
                                                        Delete
                                                    </v-btn>
                                                </template>
                                            </v-card>
                                        </template>
                                    </v-dialog>

                                    {{ form.jobscript[i].variantName }}

                                    <InlineEdit
                                        title="Rename Variant"
                                        :modelValue="
                                            form.jobscript[i].variantName
                                        "
                                        @update:modelValue="
                                            form.jobscript[i].variantName =
                                                $event
                                        "
                                    >
                                        <template #activator>
                                            <v-btn
                                                size="x-small"
                                                title="Rename Variant"
                                                v-if="variantTabModel === i"
                                                icon="$edit"
                                                variant="plain"
                                            />
                                        </template>
                                    </InlineEdit>
                                </v-tab>
                            </v-tabs>

                            <v-btn
                                @click="$emit('add-variant')"
                                variant="outlined"
                                size="small"
                                color="primary-light"
                                prepend-icon="$plus"
                            >
                                Add Variant
                            </v-btn>
                        </div>

                        <v-window v-model="variantTabModel">
                            <v-window-item
                                v-for="[i, v] of form.jobscript.entries()"
                                :key="i"
                                :value="i"
                            >
                                <Editor
                                    v-model="form.jobscript[i]"
                                    auto-resize
                                    constrained-jobscript
                                    @update:validity="
                                        validity.jobscript = $event
                                    "
                                    :partitions="partitions"
                                />
                            </v-window-item>
                        </v-window>
                    </v-form>
                </v-card-text>
            </v-card>

            <div v-if="userLevel >= UserLevelEnum.user">
                <div class="d-flex gap-20 mt-5">
                    <v-btn
                        color="primary"
                        @click="$emit('save')"
                        :disabled="
                            Object.values(validity)
                                .map((x) => !!x)
                                .includes(false)
                        "
                    >
                        Save
                    </v-btn>
                    <v-btn @click="$emit('cancel')">Cancel</v-btn>
                </div>
            </div>
        </div>
    </v-main>
</template>

<script setup>
import { ref, computed } from "vue";

const props = defineProps({
    form: { type: Object, required: true },
    validity: { type: Object, required: true },

    currentEdit: { type: String, default: "" },
    currentEditNotYetSaved: { type: Boolean, default: false },

    settingsExpanded: { type: Boolean, required: true },

    vNotEmpty: { type: Function, required: true },
    vNumber: { type: Function, required: true },
    vInteger: { type: Function, required: true },

    projects: { type: Array, default: () => [] },

    partitions: { type: Object, default: () => ({}) },
    partitionTree: { type: Array, default: () => [] },

    variableCount: { type: Number, default: 0 },

    variantTab: { type: Number, required: true },
    userLevel: { type: Number, required: true },
    UserLevelEnum: { type: Object, required: true }
});

const emit = defineEmits([
    "update:settingsExpanded",
    "update:variantTab",
    "add-variant",
    "remove-variant",
    "save",
    "cancel"
]);

const showConfigurationID = computed(() => {
    if (!props.currentEdit) return "";
    return props.currentEditNotYetSaved ? "save to view ID" : props.currentEdit;
});

const settings_form = ref(null);
const jobscript_form = ref(null);

const validateForms = async () => {
    try {
        await settings_form.value?.validate?.();
        await jobscript_form.value?.validate?.();
    } catch {
        // no-op
    }
};

defineExpose({ validateForms });

const variantTabModel = computed({
    get: () => props.variantTab,
    set: (v) => emit("update:variantTab", v)
});
</script>

<style scoped lang="scss">
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

.expansion-title {
    font-size: 1.25rem;
    font-weight: 500;
}
</style>
