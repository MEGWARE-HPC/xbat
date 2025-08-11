<template>
    <div>
        <v-container fluid>
            <v-card max-width="95%" class="mx-auto pa-2 mt-5">
                <v-card-title>
                    <div
                        class="d-flex align-center justify-space-between gap-20"
                    >
                        <v-btn color="primary" @click="setAdd"
                            >Add Project</v-btn
                        >
                        <v-text-field
                            v-model="state.search"
                            prepend-inner-icon="$search"
                            label="Search"
                            hide-details
                            style="max-width: 300px"
                            clearable
                        ></v-text-field>
                    </div>
                </v-card-title>
                <v-card-text class="pt-2">
                    <v-data-table
                        :headers="headers"
                        :items="projects || []"
                        :loading="pending"
                        :search="state.search"
                        v-model="state.selected"
                        item-key="name"
                        @click:row="setEdit"
                        v-model:sortBy="tableSortBy"
                    >
                        <template v-slot:[`item.created`]="{ item }">
                            <ClientOnly>
                                {{ sanitizeDate(item.created) }}
                            </ClientOnly>
                        </template>
                    </v-data-table>
                </v-card-text>
            </v-card>
        </v-container>
        <v-dialog v-model="state.dialog" max-width="600px">
            <v-card>
                <v-card-title>
                    <span class="capitalize"
                        >{{ state.action }}
                        <span class="font-italic">{{ edit.name }}</span></span
                    >
                </v-card-title>
                <v-card-text>
                    <div v-show="state.action != 'delete'">
                        <v-text-field
                            label="Name"
                            v-model="form.name"
                            :hint="
                                duplicateName
                                    ? 'A project with this name does already exist!'
                                    : ''
                            "
                        ></v-text-field>
                        <v-autocomplete
                            label="Members"
                            v-model="form.members"
                            chips
                            closable-chips
                            multiple
                            :items="userNames"
                        ></v-autocomplete>
                    </div>
                    <div v-show="state.action == 'delete'">
                        <p>
                            Do you really want to
                            <span class="font-weight-bold">delete</span> the
                            project
                            <span class="font-weight-bold">{{
                                edit.name
                            }}</span>
                            ?
                        </p>
                    </div>
                    <div
                        class="text-medium-emphasis text-caption"
                        v-show="edit._id"
                    >
                        Project ID: {{ edit._id }}
                    </div>
                </v-card-text>
                <v-card-actions>
                    <v-btn
                        color="red"
                        variant="text"
                        @click="state.action = 'delete'"
                        v-show="state.action == 'edit'"
                    >
                        Delete
                    </v-btn>
                    <v-spacer></v-spacer>
                    <v-btn color="font-light" variant="text" @click="resetForm">
                        Cancel
                    </v-btn>
                    <v-btn
                        :color="
                            state.action == 'delete' ? 'red' : 'primary-light'
                        "
                        variant="text"
                        @click="commit"
                        :disabled="duplicateName"
                    >
                        {{ actionCommitNames[state.action] }}
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </div>
</template>

<script setup>
import { sanitizeDate } from "~/utils/date";
const { $api, $snackbar, $store } = useNuxtApp();

useSeoMeta({
    title: "Projects",
    description: "Projects management for xbat",
});

const headers = [
    { title: "Name", key: "name" },
    { title: "Created", key: "created" }
];

const actionCommitNames = {
    edit: "Save",
    delete: "Delete",
    add: "Add"
};

const tableSortBy = ref([{ key: "name", order: "asc" }]);

definePageMeta({
    requiresAdmin: true
});

const state = reactive({
    selected: [],
    search: "",
    dialog: false,
    action: "",
    edit: {},
    duplicateName: false
});

const form = ref({
    name: "",
    members: []
});

const edit = ref({});

const { data: users } = await useAsyncData("users", () => $api.users.get(), {
    lazy: true
});

const {
    data: projects,
    refresh,
    pending
} = await useAsyncData(
    "projects",
    async () => (await $api.projects.get())?.data || []
);

const setEdit = (_, { item }) => {
    state.action = "edit";
    form.value.name = item.name;
    form.value.members = item?.members || [];
    state.dialog = true;
    edit.value = item;
};

const setAdd = () => {
    state.action = "add";
    state.dialog = true;
};

const resetForm = () => {
    state.action = null;
    form.value.name = "";
    form.value.members = [];
    state.dialog = false;
    edit.value = {};
};

const commit = async () => {
    if (state.duplicateName || (state.action != "add" && !edit.value._id))
        return;
    if ($store.demo) {
        $snackbar.show($store.demoMessage);
    } else if (state.action == "add") {
        await $api.projects.post(form.value);
        $snackbar.show("Added project");
    } else if (state.action == "edit") {
        await $api.projects.patch(edit.value._id, form.value);
        $snackbar.show("Saved project");
    } else {
        await $api.projects.delete(edit.value._id);
        $snackbar.show("Deleted project");
    }
    resetForm();

    await refresh();
};

const duplicateName = computed(() => {
    return (
        projects.value.map((x) => x.name).includes(form.value.name) &&
        edit.value.name != form.value.name
    );
});

const userNames = computed(() =>
    users.value.map((x) => x.user_name).filter((x) => x != "admin")
);
</script>

<style lang="scss" scoped>
@use "~/assets/css/colors.scss" as *;
</style>
