<template>
    <div>
        <div class="d-flex gap-10 mt-5" v-for="[idx, v] of variables.entries()">
            <v-text-field
                label="Variable"
                style="width: 350px"
                v-model="v.key"
                clearable
                :error-messages="
                    duplicateVariable[idx] ? ['Duplicate Variable'] : []
                "
            ></v-text-field>
            <v-select
                label="Value(s)"
                style="width: 350px"
                :items="v.values"
                v-model="v.selected"
                :disabled="!v.key"
                multiple
                clearable
                chips
                :focused="false"
                no-data-text="No values configured"
                persistent-hint
                :hint="
                    v.key && !v.selected?.length
                        ? 'No value configured - variable will be empty String'
                        : ''
                "
            >
                <template v-slot:item="{ props, item, index: selectIdx }">
                    <v-list-item v-bind="props" :title="undefined">
                        <v-text-field
                            :model-value="props.value"
                            @update:model-value="
                                updateValue(idx, selectIdx, $event)
                            "
                            @click.stop=""
                            :error-messages="
                                props.value === duplicateValue
                                    ? ['Duplicate Value']
                                    : []
                            "
                            hide-details="auto"
                            autofocus
                        >
                            <template #prepend>
                                <v-checkbox-btn
                                    color="primary-light"
                                    v-model="v.selected"
                                    :value="item.value"
                                ></v-checkbox-btn>
                            </template>
                            <template #append>
                                <v-btn
                                    icon="$close"
                                    size="x-small"
                                    variant="plain"
                                    @click="removeValue(idx, item.value)"
                                ></v-btn>
                            </template>
                        </v-text-field>
                    </v-list-item>
                </template>
                <template v-slot:chip="{ item }"
                    ><v-chip
                        color="primary-light"
                        style="font-size: 0.875rem"
                        >{{ item.title }}</v-chip
                    ></template
                >
                <template #prepend-item
                    ><v-text-field
                        variant="outlined"
                        label="Add Value"
                        class="ml-3 mr-3"
                        v-model="v.input"
                        :error-messages="
                            duplicateAddValue[idx]
                                ? ['Value already exists']
                                : []
                        "
                        @keyup.enter="addValue(idx, v.input)"
                    >
                        <template #append-inner
                            ><v-btn
                                variant="plain"
                                :color="
                                    duplicateAddValue[idx]
                                        ? 'danger'
                                        : 'primary-light'
                                "
                                icon="$plus"
                                size="small"
                                :disabled="!v.input || duplicateAddValue[idx]"
                                @click="addValue(idx, v.input)"
                            ></v-btn></template></v-text-field
                ></template>
                <template #append-item v-if="v.values.length">
                    <div class="d-flex justify-center mt-3">
                        <v-btn
                            variant="plain"
                            color="danger"
                            size="small"
                            @click="removeAllValues(idx)"
                            >clear all values</v-btn
                        >
                    </div>
                </template>
            </v-select>
            <v-btn
                variant="plain"
                size="x-small"
                icon="$close"
                @click="removeVariable(idx)"
            >
            </v-btn>
        </div>
        <div class="d-flex align-center justify-center mt-5">
            <v-btn
                variant="text"
                color="primary-light"
                @click="addVariable"
                prepend-icon="$plus"
                size="small"
                >Add variable</v-btn
            >
        </div>
    </div>
</template>
<script lang="ts" setup>
import { useDebounceFn } from "@vueuse/core";
import { deepClone, deepEqual } from "~/utils/misc";
import type { JobVariable as Variable } from "@/repository/modules/configurations";

const props = defineProps({
    modelValue: {
        type: Array as PropType<Variable[]>,
        default: () => []
    }
});

const emit = defineEmits(["update:modelValue"]);

const variables: Ref<Variable[]> = ref([]);

const propagateChanges = () => {
    if (deepEqual(variables.value, props.modelValue)) return;

    emit("update:modelValue", variables.value);
};

const debounceVariableUpdate = useDebounceFn(propagateChanges, 500);

watch(
    () => props.modelValue,
    (v) => {
        if (!Array.isArray(v)) {
            variables.value = [];
            return;
        } else {
            variables.value = deepClone(v).map((x: Variable) =>
                Object.assign(x, x.input ? {} : { input: "" })
            );
        }
    },
    { immediate: true, deep: true }
);

watch(
    () => variables.value,
    (v) => {
        debounceVariableUpdate();
    },
    { deep: true }
);

const addVariable = () => {
    variables.value.push({ key: "", values: [], selected: [], input: "" });
};

const removeVariable = (idx: number) => {
    variables.value.splice(idx, 1);
};

const addValue = (idx: number, value: string) => {
    variables.value[idx].values.push(value);
    variables.value[idx].selected.push(value);
    variables.value[idx].input = "";
};

const duplicateValue = ref<string | null>();

const updateValue = (idx: number, selectedIdx: number, value: string) => {
    const oldVal = variables.value[idx].values[selectedIdx];
    variables.value[idx].values[selectedIdx] = value;

    if (
        variables.value[idx].values.includes(value) &&
        variables.value[idx].values.indexOf(value) !== selectedIdx
    ) {
        duplicateValue.value = value;
    } else {
        duplicateValue.value = null;
    }

    if (variables.value[idx].selected.includes(oldVal)) {
        variables.value[idx].selected.splice(
            variables.value[idx].selected.indexOf(oldVal),
            1,
            value
        );
    }
};

const removeValue = (idx: number, value: string) => {
    // WARNING 'selected' must be modified before 'values'
    variables.value[idx].selected.splice(
        variables.value[idx].values.indexOf(value),
        1
    );
    variables.value[idx].values.splice(
        variables.value[idx].values.indexOf(value),
        1
    );
};

const removeAllValues = (idx: number) => {
    variables.value[idx].values = [];
    variables.value[idx].selected = [];
};

const duplicateVariable = computed(() => {
    const variableNames = variables.value.map((v) => v.key);

    return Array.from(
        variables.value,
        (v) => v.key && variableNames.filter((vn) => vn === v.key).length > 1
    );
});

const duplicateAddValue = computed(() => {
    return Array.from(
        variables.value,
        (v) => v.input && v.values.includes(v.input)
    );
});
</script>
