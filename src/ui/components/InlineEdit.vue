<template>
    <v-menu v-model="menu" :close-on-content-click="false" location="bottom">
        <template v-slot:activator="{ props }">
            <div style="display: inline-block" v-bind="props">
                <slot name="activator">
                    <v-icon
                        :title="props.hoverTitle || 'Edit'"
                        icon="$edit"
                        class="ml-1 edit"
                        size="x-small"
                    ></v-icon>
                </slot>
            </div>
        </template>
        <v-card min-width="300">
            <v-card-title v-if="props.title">{{ props.title }}</v-card-title>
            <v-card-text>
                <v-form v-model="formValid">
                    <v-text-field
                        v-model="value"
                        hide-details="auto"
                        :rules="props.clearable ? [] : [vNotEmpty]"
                        :clearable="props.clearable"
                        :placeholder="props.placeholder || undefined"
                    ></v-text-field>
                </v-form>
            </v-card-text>

            <v-card-actions>
                <v-spacer></v-spacer>

                <v-btn variant="text" @click="cancel" size="small">
                    Cancel
                </v-btn>
                <v-btn
                    color="primary-light"
                    variant="text"
                    @click="save"
                    size="small"
                    :disabled="!formValid"
                >
                    Save
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-menu>
</template>
<script lang="ts" setup>
interface Props {
    modelValue: string | null;
    modelValueMenu?: boolean;
    title?: string;
    hoverTitle?: string;
    clearable?: boolean;
    placeholder?: string;
}

const props = defineProps<Props>();
const emit = defineEmits(["update:modelValue", "update:modelValue:menu"]);
const { vNotEmpty } = useFormValidation();

const menu = ref<boolean>(false);
const value = ref<string | null>("");
const formValid = ref<boolean>(false);

const cancel = () => {
    menu.value = false;
    value.value = props.modelValue;
};

const save = () => {
    menu.value = false;
    emit("update:modelValue", value.value);
};

watch(
    () => props.modelValue,
    (newValue) => {
        value.value = newValue;
    },
    {
        immediate: true
    }
);
</script>
<style lang="scss">
@use "~/assets/css/colors.scss" as *;

.edit {
    cursor: pointer;
    &:hover {
        color: $primary-light;
    }
}
</style>
