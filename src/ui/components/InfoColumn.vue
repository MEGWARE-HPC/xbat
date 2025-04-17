<template>
    <div class="info-column">
        <div class="d-flex gap-10 align-center" v-show="props.title">
            <div class="title">{{ props.title }}</div>
            <slot></slot>
        </div>
        <v-row dense no-gutters class="text-body-1">
            <template v-for="entry of props.items">
                <v-col md="6" sm="12" class="entry key">{{
                    entry.title
                }}</v-col>
                <v-col md="6" sm="12" class="entry value">
                    <span v-html="entry.value"></span>
                    <InlineEdit
                        :modelValue="entry.value"
                        v-if="entry.editable"
                        :title="entry.title"
                        @update:model-value="
                            ($event) =>
                                emit('update', {
                                    key: entry.key,
                                    value: $event,
                                    title: entry.title
                                })
                        "
                    >
                    </InlineEdit>
                </v-col>
            </template>
            <slot name="append-row"></slot>
        </v-row>
        <slot name="append"></slot>
    </div>
</template>
<script setup>
const props = defineProps({
    title: { type: String, default: "" },
    items: { type: Array, default: () => [], required: true }
});

const emit = defineEmits(["update"]);
</script>
<style lang="scss">
@use "~/assets/css/colors.scss" as *;

.info-column {
    .title {
        margin-bottom: 10px;
        margin-top: 10px;
        color: $font-disabled;
        text-transform: uppercase;
    }
    .entry {
        font-size: 0.85rem;
        text-align: left;
        line-height: 1.1rem;
        &.key {
            font-weight: 600;
        }
        &.value {
            white-space: pre-wrap;
            word-break: break-all;

            .edit {
                cursor: pointer;
                &:hover {
                    color: $primary-light;
                }
            }
        }
    }
}
</style>
