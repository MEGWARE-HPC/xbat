<template>
    <v-dialog max-width="600px" v-model="dialog">
        <template v-slot:activator="{ props: activatorProps }">
            <div v-bind="activatorProps">
                <slot></slot>
            </div>
        </template>
        <template v-slot:default="{ isActive }">
            <v-card>
                <v-card-title> Start Benchmark </v-card-title>
                <v-card-text>
                    <v-form
                        lazy-validation
                        ref="submit_form"
                        v-model="formValid"
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
                                    label="Share with Project (optional)"
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
                        @click="isActive.value = false"
                    >
                        Cancel
                    </v-btn>
                    <v-btn
                        color="primary-light"
                        variant="text"
                        type="submit"
                        @click="submit"
                        :disabled="!formValid"
                    >
                        Submit
                    </v-btn>
                </v-card-actions>
            </v-card>
        </template>
    </v-dialog>
</template>
<script lang="ts" setup>
const shareExplanation =
    "Shared benchmarks are visible to all other members of the selected project";

const { $api, $authStore, $store, $snackbar } = useNuxtApp();

const { vNotEmpty } = useFormValidation();

const projects = computed(() => $authStore.user?.projects || []);

const dialog = ref(false);

const form = reactive({
    name: "",
    configId: null,
    sharedProjects: []
});

const { data: configurations } = await useAsyncData(
    `configurations-${$authStore.user?.user_name}`,
    () => $api.configurations.get(),
    { lazy: true, transform: (v) => v?.data || [] }
);

const configurationItems = computed(() => {
    if (!configurations.value) return [];
    return Object.values(configurations.value).map((x) => ({
        title: x.configuration.configurationName,
        value: x._id,
        shared: !!x.configuration?.sharedProjects?.length
    }));
});

const configurationsById = computed(() =>
    Object.fromEntries(
        (configurations.value || []).map((x) => [x._id, x.configuration])
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

const formValid = ref(false);

const emit = defineEmits<{
    (e: "submit"): void;
}>();

const submit = async () => {
    if ($store.demo) {
        $snackbar.show($store.demoMessage);
        dialog.value = false;
        return;
    }

    // check of form.name and form.configId for ts
    if (!formValid.value || !form.name || !form.configId) return;

    const businessVars = Array.isArray(variableForm.value[form.configId])
        ? variableForm.value[form.configId].map((v: any) => ({
              key: v.key,
              values: v.values,
              selected: v.selected,
              input: v.input
          }))
        : [];

    await $api.benchmarks.submit({
        name: form.name,
        configId: form.configId,
        sharedProjects: form.sharedProjects,
        variables: businessVars
    });

    if (!$store.error) {
        $snackbar.show(
            "Benchmark submitted - it may take a few seconds until the benchmark is displayed"
        );
        emit("submit");
        dialog.value = false;
    }
};
</script>
