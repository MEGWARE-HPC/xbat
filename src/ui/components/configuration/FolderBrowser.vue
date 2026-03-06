<template>
    <v-main style="--v-layout-bottom: 0; --v-layout-top: 0px">
        <div class="fb">
            <div v-if="!folder" class="fb-empty text-medium-emphasis">
                Select a folder to browse, or select a configuration to edit.
            </div>

            <div v-else class="fb-wrap">
                <!-- Header -->
                <div class="fb-header">
                    <div class="fb-title">
                        <v-icon
                            class="mr-2"
                            :class="headerIconClass"
                            :icon="headerIcon"
                        />
                        <span class="fb-title-text">{{ headerTitle }}</span>
                    </div>
                </div>

                <!-- Actions -->
                <div class="fb-actions" v-if="canCreate">
                    <div class="fb-action-group">
                        <v-btn
                            color="primary-light"
                            prepend-icon="$newFile"
                            @click="$emit('create-config')"
                        >
                            New Config
                        </v-btn>

                        <v-btn
                            color="primary-light"
                            prepend-icon="$newFolder"
                            @click="openCreateFolder()"
                            :disabled="
                                isSharedView || folderId.startsWith('__')
                            "
                        >
                            New Folder
                        </v-btn>

                        <!-- bulk actions -->
                        <template v-if="hasSelect">
                            <template v-if="mixedSelect">
                                <v-btn
                                    color="primary-light"
                                    prepend-icon="$folderMove"
                                    @click="openMove()"
                                >
                                    Move to
                                </v-btn>

                                <v-btn
                                    color="primary-light"
                                    prepend-icon="$trashCan"
                                    @click="openDelete()"
                                >
                                    Delete
                                </v-btn>
                            </template>

                            <template v-else>
                                <v-btn
                                    v-if="canDownload"
                                    color="primary-light"
                                    prepend-icon="$download"
                                    @click="downloadSelected()"
                                >
                                    Download
                                </v-btn>

                                <v-btn
                                    v-if="canShare"
                                    color="primary-light"
                                    prepend-icon="$share"
                                    @click="openShare()"
                                >
                                    Share
                                </v-btn>

                                <v-btn
                                    v-if="canRename"
                                    color="primary-light"
                                    prepend-icon="$edit"
                                    @click="openRename()"
                                >
                                    Rename
                                </v-btn>

                                <v-btn
                                    v-if="canMove"
                                    color="primary-light"
                                    prepend-icon="$folderMove"
                                    @click="openMove()"
                                >
                                    Move to
                                </v-btn>

                                <v-btn
                                    v-if="canDelete"
                                    color="primary-light"
                                    prepend-icon="$trashCan"
                                    @click="openDelete()"
                                >
                                    Delete
                                </v-btn>
                            </template>
                        </template>
                    </div>
                </div>

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
                    <div class="fb-col fb-col--name">Name</div>
                    <div v-if="showOwner" class="fb-col fb-col--owner">
                        Owner
                    </div>
                    <div class="fb-col fb-col--created">Created</div>
                    <div class="fb-col fb-col--edited">Modified</div>
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

                                <div
                                    v-if="showOwner"
                                    class="fb-col fb-col--owner fb-owner"
                                >
                                    —
                                </div>
                                <div class="fb-col fb-col--created fb-date">
                                    —
                                </div>
                                <div class="fb-col fb-col--edited fb-date">
                                    —
                                </div>
                            </div>
                        </v-list-item-title>
                    </v-list-item>

                    <!-- folders -->
                    <v-list-item
                        v-for="child in folders"
                        :key="'f-' + child.id"
                        class="fb-rowitem"
                        @click="$emit('open-folder', child.id)"
                    >
                        <v-list-item-title>
                            <div class="fb-row" :style="rowGridStyle">
                                <div class="fb-col fb-col--check">
                                    <v-checkbox-btn
                                        :model-value="
                                            isSelected(folderToken(child.id))
                                        "
                                        density="compact"
                                        class="fb-check fb-check--row"
                                        @click.stop
                                        @update:modelValue="
                                            toggleSelect(folderToken(child.id))
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

                                <div
                                    v-if="showOwner"
                                    class="fb-col fb-col--owner fb-owner"
                                >
                                    —
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
                        v-for="c in configs"
                        :key="'c-' + c.id"
                        class="fb-rowitem"
                        @click="$emit('open-config', c.id)"
                    >
                        <v-list-item-title>
                            <div class="fb-row" :style="rowGridStyle">
                                <div class="fb-col fb-col--check">
                                    <v-checkbox-btn
                                        :model-value="
                                            isSelected(configToken(c.id))
                                        "
                                        density="compact"
                                        class="fb-check fb-check--row"
                                        @click.stop
                                        @update:modelValue="
                                            toggleSelect(configToken(c.id))
                                        "
                                    />
                                </div>

                                <div class="fb-col fb-col--name fb-name">
                                    <div class="fb-name-wrap">
                                        <v-icon
                                            class="fb-ico fb-ico--config"
                                            :icon="
                                                c.doc?.configuration
                                                    ?.sharedProjects?.length
                                                    ? '$share'
                                                    : '$textBox'
                                            "
                                            color="primary-light"
                                        />
                                        <span>
                                            {{
                                                c.doc?.configuration
                                                    ?.configurationName || c.id
                                            }}
                                        </span>
                                    </div>
                                </div>

                                <div
                                    v-if="showOwner"
                                    class="fb-col fb-col--owner fb-owner"
                                >
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
                            folders.length === 0 &&
                            configs.length === 0
                        "
                        class="text-medium-emphasis"
                        title="This folder is empty"
                    />
                </v-list>
            </div>
        </div>
    </v-main>
</template>

<script setup>
import { computed, ref, watch } from "vue";
const { $api, $snackbar, $store } = useNuxtApp();

const props = defineProps({
    folder: { type: Object, default: null }, // expects { id, name, children?, __parentId? }
    configs: { type: Array, default: () => [] },
    userName: { type: String, required: true },
    projects: { type: Array, default: () => [] },
    userLevel: { type: Number, required: true },
    UserLevelEnum: { type: Object, required: true },
    myRootId: { type: String, default: "" },
    selected: { type: Array, default: () => [] } // string tokens: "f:<id>" | "c:<id>"
});

const emit = defineEmits([
    "open-folder",
    "open-config",
    "create-config",
    "create-folder",
    "update:selected",
    "refresh"
]);

const selectItems = ref((props.selected || []).map(String));

watch(
    () => props.selected,
    (v) => {
        selectItems.value = (v || []).map(String);
    }
);

const selectedSet = computed(() => new Set(selectItems.value));

const folderToken = (id) => `f:${String(id)}`;
const configToken = (id) => `c:${String(id)}`;

const isSelected = (token) => selectedSet.value.has(String(token));

const setSelected = (arr) => {
    selectItems.value = arr.map(String);
    emit("update:selected", selectItems.value.slice());
};

const toggleSelect = (token) => {
    const t = String(token);
    const s = new Set(selectedSet.value);
    if (s.has(t)) s.delete(t);
    else s.add(t);
    setSelected(Array.from(s));
};

const selectedTokens = computed(() => selectItems.value || []);

const selectedFolderIds = computed(() =>
    selectedTokens.value
        .filter((t) => String(t).startsWith("f:"))
        .map((t) => String(t).slice(2))
);

const selectedConfigIds = computed(() =>
    selectedTokens.value
        .filter((t) => String(t).startsWith("c:"))
        .map((t) => String(t).slice(2))
);

const hasSelect = computed(
    () => selectedFolderIds.value.length + selectedConfigIds.value.length > 0
);

const mixedSelect = computed(
    () =>
        selectedFolderIds.value.length > 0 && selectedConfigIds.value.length > 0
);

const configById = computed(() => {
    const m = new Map();
    for (const item of props.configs || []) m.set(String(item.id), item.doc);
    return m;
});

const ownSelectConfigIds = computed(() =>
    selectedConfigIds.value.filter((id) => {
        const doc = configById.value.get(String(id));
        return doc?.misc?.owner === props.userName;
    })
);

const folderNodeById = computed(() => {
    const m = new Map();
    for (const f of props.folder?.children || []) m.set(String(f.id), f);
    return m;
});

const ownSelectFolderIds = computed(() =>
    selectedFolderIds.value.filter((id) => {
        const node = folderNodeById.value.get(String(id));
        return (
            (node?.misc?.owner && node.misc.owner === props.userName) ||
            props.userLevel >= props.UserLevelEnum.manager
        );
    })
);

const canDownload = computed(
    () => !mixedSelect.value && selectedConfigIds.value.length > 0
);
const canShare = computed(
    () => !mixedSelect.value && ownSelectConfigIds.value.length > 0
);
const canRename = computed(
    () =>
        !mixedSelect.value &&
        selectedFolderIds.value.length + selectedConfigIds.value.length === 1
);
const canMove = computed(() => hasSelect.value);
const canDelete = computed(() => hasSelect.value);

const canCreate = computed(
    () => props.userLevel > (props.UserLevelEnum?.guest ?? 0)
);

const isMyRoot = computed(() => {
    const fid = String(props.folder?.id ?? "");
    return !!props.myRootId && fid === String(props.myRootId);
});

const headerTitle = computed(() => {
    if (isSharedView.value) return props.folder?.name || "";
    if (folderId.value === "__all__") return props.folder?.name || "";

    if (isMyRoot.value) return "Home";

    return props.folder?.name || "";
});

const folderId = computed(() => String(props.folder?.id ?? ""));

const isSharedView = computed(() => folderId.value.startsWith("__shared__"));
const isSharedRoot = computed(() => folderId.value === "__shared__");
const isSharedProject = computed(() =>
    folderId.value.startsWith("__shared__:")
);

const showOwner = computed(() => isSharedView.value);

const parentId = computed(() => props.folder?.__parentId ?? null);

const canGoUp = computed(() => !!props.folder && !!parentId.value);

const folders = computed(() => (props.folder?.children || []).slice());

const visibleTokens = computed(() => {
    const tokens = [];
    for (const f of folders.value) if (f?.id) tokens.push(folderToken(f.id));
    for (const c of props.configs || [])
        if (c?.id) tokens.push(configToken(c.id));
    return tokens;
});

const headerCheck = computed({
    get() {
        const toks = visibleTokens.value;
        if (!toks.length) return false;
        return toks.every((t) => selectedSet.value.has(t));
    },
    set(v) {
        const toks = visibleTokens.value;
        if (!toks.length) return;

        const s = new Set(selectedSet.value);
        if (v) {
            for (const t of toks) s.add(t);
        } else {
            for (const t of toks) s.delete(t);
        }
        setSelected(Array.from(s));
    }
});

const headerState = computed(() => {
    const toks = visibleTokens.value;
    if (!toks.length) return false;

    let hit = 0;
    for (const t of toks) if (selectedSet.value.has(t)) hit++;

    return hit > 0 && hit < toks.length;
});

const rowGridStyle = computed(() => ({
    "--fb-cols": showOwner.value
        ? "32px 1fr 160px 160px 160px"
        : "32px 1fr 160px 160px"
}));

const headerIcon = computed(() => {
    if (isSharedRoot.value) return "$folderNetwork";
    if (isSharedProject.value) return "$group";
    return "$folderOpen";
});

const headerIconClass = computed(() => {
    if (isSharedRoot.value) return "fb-ico--shared-root";
    if (isSharedProject.value) return "fb-ico--shared-project";
    return "fb-ico--folder";
});

const childFolderIcon = computed(() => {
    if (isSharedRoot.value) return "$group";
    return "$folder";
});

const childFolderIconClass = computed(() => {
    if (isSharedRoot.value) return "fb-ico--shared-project";
    return "fb-ico--folder";
});

const formatDate = (v) => {
    if (!v) return "—";

    const d = new Date(v);
    if (Number.isNaN(d.getTime())) return "—";
    return new Intl.DateTimeFormat(undefined, {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit"
    }).format(d);
};
</script>

<style lang="scss" scoped>
@use "~/assets/css/colors.scss" as *;

.fb {
    padding: 16px;
}

.fb-empty {
    padding: 24px;
}

.fb-wrap {
    max-width: 100%;
}

.fb-header {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
}

.fb-title {
    display: flex;
    align-items: center;
    font-size: 1.05rem;
    font-weight: 600;
}

.fb-title-text {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.fb-actions {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 12px 0 8px;
    flex-wrap: wrap;
}

.fb-action-group {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
}

.fb-action-group :deep(.v-btn) {
    min-width: 145px;
    justify-content: center;
}

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
    opacity: 0.75;
    border-bottom: 1px solid rgba(0, 0, 0, 0.08);
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
    opacity: 0.75;
    font-size: 0.82rem;
}

.fb-date {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    text-align: right;
    opacity: 0.75;
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

.fb-ico--shared-root {
    color: $primary-light;
    opacity: 0.8;
}

.fb-ico--shared-project {
    color: $primary-light;
    opacity: 0.8;
}

.fb-ico--config {
    color: $primary-light;
    opacity: 1;
}

.fb-ico--nav {
    color: $primary-light;
    opacity: 0.7;
}
</style>
