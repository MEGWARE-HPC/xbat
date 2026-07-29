<template>
    <!-- Table header -->
    <div class="fb-row fb-row--head" :style="rowGridStyle">
        <div class="fb-col fb-col--check">
            <v-checkbox-btn
                v-model="headerCheck"
                :indeterminate="headerState"
                density="compact"
                class="fb-check fb-check--head"
                @click.stop
            />
        </div>

        <div
            class="fb-col fb-col--name fb-head-sort"
            :class="{ 'is-active': sortBy === 'name' }"
            @click="$emit('set-sort', 'name')"
        >
            <span>Name</span>
            <v-icon
                v-if="sortBy === 'name'"
                size="small"
                class="fb-head-sort-icon"
                :icon="sortDesc ? '$sortAlphaAsc' : '$sortAlphaDesc'"
            />
        </div>

        <div
            class="fb-col fb-col--owner fb-head-sort"
            :class="{ 'is-active': sortBy === 'owner' }"
            @click="$emit('set-sort', 'owner')"
        >
            <span>Owner</span>
            <v-icon
                v-if="sortBy === 'owner'"
                size="small"
                class="fb-head-sort-icon"
                :icon="sortDesc ? '$sortAlphaAsc' : '$sortAlphaDesc'"
            />
        </div>

        <div
            class="fb-col fb-col--created fb-head-sort"
            :class="{ 'is-active': sortBy === 'created' }"
            @click="$emit('set-sort', 'created')"
        >
            <span>Created</span>
            <v-icon
                v-if="sortBy === 'created'"
                size="small"
                class="fb-head-sort-icon"
                :icon="sortDesc ? '$sortNumAsc' : '$sortNumDesc'"
            />
        </div>

        <div
            class="fb-col fb-col--edited fb-head-sort"
            :class="{ 'is-active': sortBy === 'edited' }"
            @click="$emit('set-sort', 'edited')"
        >
            <span>Modified</span>
            <v-icon
                v-if="sortBy === 'edited'"
                size="small"
                class="fb-head-sort-icon"
                :icon="sortDesc ? '$sortNumAsc' : '$sortNumDesc'"
            />
        </div>
    </div>

    <v-list class="fb-list" density="compact">
        <!-- .. (go up) -->
        <v-list-item
            v-if="canGoUp"
            class="fb-rowitem"
            @click="$emit('open-folder', parentId)"
        >
            <v-list-item-title>
                <div class="fb-row" :style="rowGridStyle">
                    <div class="fb-col fb-col--check"></div>

                    <div class="fb-col fb-col--name fb-name">
                        <div class="fb-name-wrap">
                            <v-icon
                                icon="$arrowLeftTop"
                                class="fb-ico fb-ico--nav"
                            />
                            <span>..</span>
                        </div>
                    </div>

                    <div class="fb-col fb-col--owner fb-owner">—</div>
                    <div class="fb-col fb-col--created fb-date">—</div>
                    <div class="fb-col fb-col--edited fb-date">—</div>
                </div>
            </v-list-item-title>
        </v-list-item>

        <!-- folders -->
        <v-list-item
            v-for="child in sortedFolders"
            :key="'f-' + child.id"
            class="fb-rowitem"
            @click="$emit('open-folder', child.id)"
        >
            <v-list-item-title>
                <div class="fb-row" :style="rowGridStyle">
                    <div class="fb-col fb-col--check">
                        <v-checkbox-btn
                            :model-value="isSelected(folderToken(child.id))"
                            density="compact"
                            class="fb-check fb-check--row"
                            @click.stop
                            @update:modelValue="
                                $emit('toggle-select', folderToken(child.id))
                            "
                        />
                    </div>

                    <div class="fb-col fb-col--name fb-name">
                        <div class="fb-name-wrap">
                            <v-icon
                                :icon="childFolderIcon"
                                class="fb-ico"
                                :class="childFolderIconClass"
                            />
                            <span>{{ child.name }}</span>
                        </div>
                    </div>

                    <div class="fb-col fb-col--owner fb-owner">
                        {{ child?.misc?.owner || "—" }}
                    </div>
                    <div class="fb-col fb-col--created fb-date">
                        {{ formatDate(child?.misc?.created) }}
                    </div>
                    <div class="fb-col fb-col--edited fb-date">
                        {{ formatDate(child?.misc?.edited) }}
                    </div>
                </div>
            </v-list-item-title>
        </v-list-item>

        <!-- configs -->
        <v-list-item
            v-for="c in sortedConfigs"
            :key="'c-' + c.id"
            class="fb-rowitem"
            @click="$emit('open-config', c.id)"
        >
            <v-list-item-title>
                <div class="fb-row" :style="rowGridStyle">
                    <div class="fb-col fb-col--check">
                        <v-checkbox-btn
                            :model-value="isSelected(configToken(c.id))"
                            density="compact"
                            class="fb-check fb-check--row"
                            @click.stop
                            @update:modelValue="
                                $emit('toggle-select', configToken(c.id))
                            "
                        />
                    </div>

                    <div class="fb-col fb-col--name fb-name">
                        <div class="fb-name-wrap">
                            <v-icon
                                class="fb-ico fb-ico--config"
                                :icon="
                                    c.doc?.configuration?.sharedProjects?.length
                                        ? '$share'
                                        : '$textBox'
                                "
                                color="primary-light"
                            />
                            <span>
                                {{
                                    c.doc?.configuration?.configurationName ||
                                    c.id
                                }}
                            </span>
                        </div>
                    </div>

                    <div class="fb-col fb-col--owner fb-owner">
                        {{ c.doc?.misc?.owner || "—" }}
                    </div>
                    <div class="fb-col fb-col--created fb-date">
                        {{ formatDate(c.doc?.misc?.created) }}
                    </div>
                    <div class="fb-col fb-col--edited fb-date">
                        {{ formatDate(c.doc?.misc?.edited) }}
                    </div>
                </div>
            </v-list-item-title>
        </v-list-item>

        <!-- empty state -->
        <v-list-item
            v-if="
                !canGoUp &&
                sortedFolders.length === 0 &&
                sortedConfigs.length === 0
            "
            class="text-medium-emphasis fb-empty-folder-row"
            title="This folder is empty"
        />
    </v-list>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
    rowGridStyle: { type: Object, default: () => ({}) },

    headerCheck: { type: Boolean, default: false },
    headerState: { type: Boolean, default: false },

    sortBy: { type: String, default: "name" },
    sortDesc: { type: Boolean, default: false },

    canGoUp: { type: Boolean, default: false },
    parentId: { type: [String, null], default: null },

    sortedFolders: { type: Array, default: () => [] },
    sortedConfigs: { type: Array, default: () => [] },

    folderToken: { type: Function, required: true },
    configToken: { type: Function, required: true },
    isSelected: { type: Function, required: true },

    childFolderIcon: { type: String, default: "$folder" },
    childFolderIconClass: { type: String, default: "" },

    formatDate: { type: Function, required: true }
});

const emit = defineEmits([
    "update:headerCheck",
    "set-sort",
    "toggle-select",
    "open-folder",
    "open-config"
]);

const headerCheck = computed({
    get: () => props.headerCheck,
    set: (v) => emit("update:headerCheck", v)
});
</script>

<style lang="scss" scoped>
@use "~/assets/css/colors.scss" as *;

.fb-list {
    border-radius: 8px;
    overflow: hidden;
}

.fb-row {
    display: grid;
    grid-template-columns: var(--fb-cols, 32px 1fr 160px 160px);
    align-items: center;
    gap: 10px;
    width: 100%;
}

.fb-row--head {
    padding: 8px 12px;
    font-size: 0.78rem;
    font-weight: 600;
    opacity: 0.8;
    border-bottom: 1px solid rgba(var(--v-theme-font-base), 0.08);
}

.fb-col {
    min-width: 0;
}

.fb-col--check {
    display: flex;
    align-items: center;
    justify-content: center;
}

.fb-check {
    margin: 0;
}

.fb-check--row :deep(.v-icon) {
    font-size: 19px !important;
}

.fb-check--row :deep(.v-selection-control__wrapper) {
    width: 20px;
    height: 20px;
}

.fb-name {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.fb-name-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
}

.fb-owner {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: $font-light;
    font-size: 0.82rem;
}

.fb-date {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    text-align: right;
    color: $font-light;
    font-size: 0.82rem;
}

.fb-rowitem :deep(.v-list-item-title) {
    width: 100%;
}

.fb-rowitem :deep(.v-list-item__content) {
    overflow: hidden;
}

.fb-ico {
    margin-inline-end: 0;
}

.fb-ico--folder {
    color: $primary-light;
    opacity: 0.8;
    filter: brightness(1.1);
}

.fb-ico--shared-root,
.fb-ico--shared-project,
.fb-ico--config {
    color: $primary-light;
    opacity: 0.8;
}

.fb-ico--nav {
    color: $primary-light;
    opacity: 0.7;
}

.fb-head-sort {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    cursor: pointer;
    user-select: none;
}

.fb-head-sort:hover {
    opacity: 1;
}

.fb-head-sort.is-active {
    color: $font-base;
}

.fb-head-sort-icon {
    flex: 0 0 auto;
}

.fb-empty-folder-row :deep(.v-list-item__content) {
    text-align: center;
}

.fb-empty-folder-row :deep(.v-list-item-title) {
    text-align: center;
    width: 100%;
}
</style>
