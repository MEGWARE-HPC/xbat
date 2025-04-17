<template>
    <!-- TODO upgrade to v-number-input on release, prepend-inner currently not working -->
    <v-text-field
        type="number"
        :modelValue="props.modelValue"
        @update:modelValue="emit('update:modelValue', parseFloat($event))"
    >
        <template #prepend-inner>
            <v-menu persistent v-model="menu">
                <template v-slot:activator="{ props }">
                    <v-btn variant="text" v-bind="props" size="small">
                        <v-icon :icon="`$${operator.icon}`"></v-icon
                    ></v-btn>
                </template>
                <v-list :items="options" :modelValue="operator.value">
                    <v-list-item
                        v-for="(entry, index) in options"
                        :key="index"
                        @click.prevent="set(entry)"
                        style="text-align: center"
                    >
                        <v-icon
                            :icon="`$${entry.icon}`"
                            size="x-small"
                        ></v-icon>
                    </v-list-item>
                </v-list>
            </v-menu>
        </template>
    </v-text-field>
</template>
<script>
const options = [
    {
        value: "gt",
        icon: "greaterThan"
    },
    {
        value: "ge",
        icon: "greaterThanOrEqual"
    },
    {
        value: "lt",
        icon: "lessThan"
    },
    {
        value: "le",
        icon: "lessThanOrEqual"
    },
    {
        value: "eq",
        icon: "equal"
    },
    {
        value: "me",
        icon: "notEqual"
    }
];
</script>
<script setup>
import { ref, watch } from "vue";

const props = defineProps({
    modelValue: { type: [Number, String], default: null },
    defaultOperator: {
        type: String,
        default: "gt",
        validator: (value) => {
            return options.map((x) => x.value).includes(value);
        }
    }
});

const operator = ref(options[0]);
const menu = ref(null);

const emit = defineEmits(["update:modelValue", "update:operator"]);

const set = (op) => {
    operator.value = op;
    // workaround (in combination with persistent prop) to prevent closing of parent menu due to
    // https://github.com/vuetifyjs/vuetify/issues/17004
    menu.value = null;
    emit("update:operator", op.value);
};

watch(
    () => props.defaultOperator,
    (v) => {
        const matching = options.filter((x) => x.value === v);
        if (matching.length == 1) {
            operator.value = matching[0];
            emit("update:operator", operator.value.value);
        }
    },
    { immediate: true }
);
</script>
