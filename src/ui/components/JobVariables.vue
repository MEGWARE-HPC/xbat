<template>
    <div>
        <div
            class="d-flex gap-10 mt-5"
            v-for="(v, idx) in variables"
            :key="idx"
        >
            <v-text-field
                label="Variable"
                style="width: 350px"
                v-model="v.key"
                clearable
                :error-messages="
                    duplicateVariable[idx] ? ['Duplicate Variable'] : []
                "
            />
            <v-select
                label="Value(s)"
                style="width: 350px"
                :items="v.values"
                v-model="v.selected"
                :disabled="!v.key"
                multiple
                clearable
                chips
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
                                editValue(idx, selectIdx, $event)
                            "
                            @click.stop=""
                            @keydown.stop
                            @keyup.stop
                            @keypress.stop
                            :error-messages="
                                duplicateState[idx]?.edit === props.value
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
                                />
                            </template>
                            <template #append>
                                <v-btn
                                    icon="$close"
                                    size="x-small"
                                    variant="plain"
                                    @click="removeValue(idx, item.value)"
                                />
                            </template>
                        </v-text-field>
                    </v-list-item>
                </template>
                <template #chip="{ item }">
                    <v-chip color="primary-light" style="font-size: 0.875rem">{{
                        item.title
                    }}</v-chip>
                </template>
                <template #prepend-item>
                    <v-text-field
                        variant="outlined"
                        label="Add Value"
                        class="ml-3 mr-3"
                        v-model="v.input"
                        :error-messages="
                            duplicateState[idx]?.add
                                ? [
                                      `Value '${duplicateState[idx].add}' already exists`
                                  ]
                                : []
                        "
                        @keyup.enter.stop="addNewValue(idx, v.input)"
                        @keydown.stop
                        @keyup.stop
                        @keypress.stop
                    >
                        <template #append-inner>
                            <v-btn
                                variant="plain"
                                :color="
                                    duplicateState[idx]?.add
                                        ? 'danger'
                                        : 'primary-light'
                                "
                                icon="$plus"
                                size="small"
                                :disabled="
                                    !v.input || !!duplicateState[idx]?.add
                                "
                                @click="addNewValue(idx, v.input)"
                            />
                            <v-btn
                                v-bind:title="'Toggle Sort Order'"
                                :icon="
                                    v.sortOrder === 'desc'
                                        ? '$sortDesc'
                                        : '$sortAsc'
                                "
                                size="small"
                                variant="plain"
                                @click="toggleSortOrder(idx)"
                            />
                        </template>
                    </v-text-field>
                </template>

                <template #append-item v-if="v.values.length">
                    <div class="d-flex justify-center mt-3">
                        <v-btn
                            v-bind:title="'Clear All Values'"
                            icon="$trashCan"
                            variant="plain"
                            color="danger"
                            size="small"
                            @click="removeAllValues(idx)"
                        />
                    </div>
                </template>
            </v-select>
            <v-btn
                variant="plain"
                size="x-small"
                icon="$close"
                @click="removeVariable(idx)"
            />
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
import type { JobVariable as BaseVariable } from "@/repository/modules/configurations";

interface ExtendedVariable extends BaseVariable {
    input: string;
    sortOrder?: "asc" | "desc";
}

const props = defineProps({
    modelValue: {
        type: Array as PropType<BaseVariable[]>,
        default: () => []
    }
});

const emit = defineEmits(["update:modelValue"]);

const variables = ref<ExtendedVariable[]>([]);

const duplicateState = ref<
    Record<number, { add?: string | false; edit?: string }>
>({});

const getDuplicateState = (idx: number) => {
    if (!duplicateState.value[idx]) duplicateState.value[idx] = {};
    return duplicateState.value[idx];
};

const propagateChanges = () => {
    if (!deepEqual(variables.value, props.modelValue)) {
        emit("update:modelValue", variables.value);
    }
};

const debounceVariableUpdate = useDebounceFn(propagateChanges, 500);

watch(
    () => props.modelValue,
    (v) => {
        if (!Array.isArray(v)) {
            variables.value = [];
            return;
        }
        variables.value = deepClone(v).map((x) => {
            const extended = x as Partial<ExtendedVariable>;
            return {
                ...x,
                input: extended.input ?? "",
                sortOrder: extended.sortOrder ?? "asc"
            };
        });
    },
    { immediate: true, deep: true }
);

watch(() => variables.value, debounceVariableUpdate, { deep: true });

const addVariable = () => {
    variables.value.push({
        key: "",
        values: [],
        selected: [],
        input: "",
        sortOrder: "asc"
    });
};

const removeVariable = (idx: number) => {
    variables.value.splice(idx, 1);
    delete duplicateState.value[idx];
};

const addNewValue = (idx: number, value: string) => {
    if (!value) return;
    const v = variables.value[idx];
    const state = getDuplicateState(idx);

    if (v.values.includes(value)) {
        state.add = value;
        if (!v.selected.includes(value)) {
            v.selected.push(value);
            v.selected = sortValues(v.selected, v.sortOrder);
        }
        return;
    }

    v.values.push(value);
    v.selected.push(value);

    v.values = sortValues(v.values, v.sortOrder);
    v.selected = sortValues(v.selected, v.sortOrder);

    v.input = "";
    state.add = false;
};

const editValue = (idx: number, valIdx: number, newValue: string) => {
    const v = variables.value[idx];
    const oldValue = v.values[valIdx];
    const state = getDuplicateState(idx);

    const existsElsewhere =
        v.values.includes(newValue) && v.values.indexOf(newValue) !== valIdx;
    state.edit = existsElsewhere ? newValue : "";

    if (existsElsewhere) return;

    v.values[valIdx] = newValue;

    const selIdx = v.selected.indexOf(oldValue);
    if (selIdx !== -1) {
        v.selected.splice(selIdx, 1, newValue);
    }

    v.values = sortValues(v.values, v.sortOrder);
    v.selected = sortValues(v.selected, v.sortOrder);

    state.edit = "";
};

const removeValue = (idx: number, value: string) => {
    const v = variables.value[idx];
    const selIdx = v.selected.indexOf(value);
    if (selIdx !== -1) v.selected.splice(selIdx, 1);

    const valIdx = v.values.indexOf(value);
    if (valIdx !== -1) v.values.splice(valIdx, 1);
};

const removeAllValues = (idx: number) => {
    variables.value[idx].values = [];
    variables.value[idx].selected = [];
    delete duplicateState.value[idx];
};

const toggleSortOrder = (idx: number) => {
    const v = variables.value[idx];
    v.sortOrder = v.sortOrder === "asc" ? "desc" : "asc";
    v.values = sortValues(v.values, v.sortOrder);
    v.selected = sortValues(v.selected, v.sortOrder);
};

const sortValues = (arr: string[], order: "asc" | "desc" = "asc") => {
    return [...arr].sort((a, b) => {
        const na = Number(a),
            nb = Number(b);
        return order === "asc" ? na - nb : nb - na;
    });
};

watch(
    () => variables.value.map((v) => v.input),
    (inputs) => {
        inputs.forEach((val, idx) => {
            const state = getDuplicateState(idx);
            if (state.add && !variables.value[idx].values.includes(val)) {
                state.add = false;
            }
        });
    }
);

watch(
    () => variables.value.map((v) => [...v.values]),
    (valueLists) => {
        valueLists.forEach((values, idx) => {
            const editVal = duplicateState.value[idx]?.edit;
            if (editVal && values.filter((v) => v === editVal).length <= 1) {
                duplicateState.value[idx].edit = "";
            }
        });
    },
    { deep: true }
);

watch(
    () => variables.value.map((v) => [...v.selected]),
    (newSelections) => {
        newSelections.forEach((selected, idx) => {
            const v = variables.value[idx];
            const sorted = sortValues(selected, v.sortOrder);
            if (!deepEqual(selected, sorted)) {
                nextTick(() => {
                    v.selected = sorted;
                });
            }
        });
    },
    { deep: true }
);

const duplicateVariable = computed(() => {
    const map = new Map<string, number>();
    variables.value.forEach((v) => {
        if (v.key) {
            map.set(v.key, (map.get(v.key) || 0) + 1);
        }
    });
    return variables.value.map((v) => !!v.key && map.get(v.key)! > 1);
});
</script>
