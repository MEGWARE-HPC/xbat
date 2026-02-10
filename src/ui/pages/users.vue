<template>
    <div>
        <v-container fluid>
            <v-card max-width="95%" class="mx-auto pa-2 mt-5">
                <v-card-title>
                    <div class="d-flex align-center gap-20">
                        <v-btn
                            @click="state.whitelistDialog = true"
                            prepend-icon="$whitelist"
                            >Whitelist</v-btn
                        >
                        <v-menu>
                            <template v-slot:activator="{ props }">
                                <v-btn
                                    v-bind="props"
                                    :disabled="!state.selected.length"
                                >
                                    Actions
                                    <v-icon icon="$chevronDown"></v-icon>
                                </v-btn>
                            </template>
                            <v-list>
                                <v-list-item
                                    value="unblock"
                                    class="action-item"
                                    @click="setAccess('unblock')"
                                    >Unblock</v-list-item
                                >
                                <v-list-item
                                    value="block"
                                    class="action-item"
                                    @click="setAccess('block')"
                                    >Block</v-list-item
                                >
                            </v-list>
                        </v-menu>
                        <v-btn
                            @click="state.swaggerRedirectDialog = true"
                            v-if="
                                $authStore.userLevel ==
                                $authStore.UserLevelEnum.admin
                            "
                            >Swagger Redirect URIs</v-btn
                        >
                        <v-spacer></v-spacer>
                        <v-text-field
                            v-model="state.search"
                            prepend-inner-icon="$search"
                            label="Search"
                            placeholder="Search"
                            hide-details
                            style="max-width: 300px"
                            clearable
                        ></v-text-field>
                    </div>
                </v-card-title>
                <v-card-text class="pt-2">
                    <div class="text-medium-emphasis text-body-2 mb-2">
                        Users are only imported and visible after their first
                        successfull login.
                    </div>
                    <v-data-table
                        :headers="headers"
                        :items="users"
                        class="clickable-table user-table"
                        :search="state.search"
                        v-model="state.selected"
                        show-select
                        item-key="user_name"
                        @click:row="setEdit"
                        :loading="usersPending"
                        v-model:sortBy="tableSortBy"
                    >
                        <template v-slot:[`item.last_login`]="{ item }">
                            <ClientOnly>
                                {{ sanitizeDate(item.last_login) }}
                            </ClientOnly>
                        </template>
                        <template v-slot:[`item.blocked`]="{ item }">
                            <v-chip
                                v-if="item.blocked"
                                style="text-transform: capitalize"
                                size="small"
                                color="red"
                                title="User has no access to this service"
                                >blocked</v-chip
                            >
                        </template>
                    </v-data-table>
                </v-card-text>
            </v-card>
        </v-container>
        <v-dialog v-model="state.whitelistDialog" max-width="600px">
            <v-card v-show="state.whitelistDialog">
                <v-card-title>
                    <div class="d-flex align-center">
                        Whitelist Users
                        <v-switch
                            dense
                            style="margin-left: 20px"
                            label="Enable"
                            v-model="whitelist.enabled"
                        ></v-switch>
                    </div>
                </v-card-title>
                <v-card-subtitle
                    >List of users allowed to access xbat</v-card-subtitle
                >
                <v-card-text>
                    <v-list density="compact">
                        <v-list-item
                            class="whitelist-entry"
                            denisty="compact"
                            v-for="user of whitelist.users || []"
                            :key="user"
                            :value="user"
                        >
                            <div class="d-flex">
                                <div>{{ user }}</div>
                                <v-spacer class="me-auto"></v-spacer
                                ><v-icon
                                    style="margin-top: 3px"
                                    size="small"
                                    @click="removeFromWhitelist(user)"
                                    icon="$close"
                                ></v-icon>
                            </div>
                        </v-list-item>
                    </v-list>
                    <v-form
                        ref="form"
                        v-model="state.whitelistAddValid"
                        @submit.prevent="addToWhitelist"
                    >
                        <v-text-field
                            label="Add User"
                            append-icon="$plus"
                            @click:append="addToWhitelist"
                            v-model="state.whitelistAdd"
                        ></v-text-field>
                    </v-form>
                    <div class="text-medium-emphasis text-caption">
                        This only affects the xbat web interface. Submissin via
                        the CLI is still possible.
                    </div>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn
                        color="grey"
                        text
                        @click="state.whitelistDialog = false"
                    >
                        Cancel
                    </v-btn>
                    <v-btn color="primary" text @click="saveWhitelist">
                        Save
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
        <v-dialog v-model="state.editDialog" max-width="600px">
            <v-card>
                <v-card-title> Edit User </v-card-title>
                <v-card-text class="edit-container">
                    <v-row dense align="center">
                        <v-col sm="3" class="item">User</v-col>
                        <v-col sm="9" class="item">{{ edit.user_name }}</v-col>
                        <v-col sm="3" class="item">Type</v-col>
                        <v-col sm="9"
                            ><v-select
                                dense
                                v-model="edit.user_type"
                                :items="roles"
                                style="max-width: 50%"
                                v-if="!editIsAdminOrDemo"
                                hide-details
                            >
                                <template v-slot:append>
                                    <Tooltip>
                                        <p>
                                            Demo - View configurations,
                                            benchmarks, users and projects
                                        </p>
                                        <p>
                                            Guest - View configurations and
                                            benchmarks
                                        </p>
                                        <p>
                                            User - Edit configurations and
                                            launch benchmarks, delete own
                                            benchmarks and configurations
                                        </p>
                                        <p>
                                            Manager - Edit configurations,
                                            launch benchmarks, delete benchmarks
                                            and configurations of other users,
                                            manage users and projects
                                        </p>
                                    </Tooltip>
                                </template>
                            </v-select>
                            <div v-else class="item">{{ edit.user_type }}</div>
                        </v-col>
                        <template v-if="!editIsAdminOrDemo">
                            <v-col sm="3" class="item">UID</v-col>
                            <v-col sm="9" class="item">{{
                                edit.uidnumber
                            }}</v-col>
                            <v-col sm="3" class="item">GID</v-col>
                            <v-col sm="9" class="item">{{
                                edit.gidnumber
                            }}</v-col>
                            <v-col sm="3" class="item">Home Directory</v-col>
                            <v-col sm="9" class="item">{{
                                edit.homedirectory
                            }}</v-col>
                        </template>
                        <template v-else="editIsAdminOrDemo">
                            <v-col sm="6">
                                <v-text-field
                                    label="New Password"
                                    type="password"
                                    v-model="state.form.password"
                                ></v-text-field>
                            </v-col>
                            <v-col sm="6">
                                <v-text-field
                                    label="Repeat New Password"
                                    type="password"
                                    v-model="state.form.passwordRepeat"
                                ></v-text-field>
                            </v-col>
                            <v-col sm="12" v-show="state.passwordNotMatching"
                                >Passwords are not matching!</v-col
                            >
                        </template>
                    </v-row>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn text @click="resetEdit"> Cancel </v-btn>
                    <v-btn color="primary-light" text @click="save">
                        Save
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>

        <v-dialog v-model="state.swaggerRedirectDialog" max-width="800px">
            <v-card>
                <v-card-title> Edit Swagger Redirect URIs </v-card-title>
                <v-card-text>
                    <v-textarea
                        label="Redirect URIs"
                        v-model="state.redirect_uris"
                    ></v-textarea>
                    <div class="text-medium-emphasis text-body-2">
                        Redirect URIs for Swagger are space separated and must
                        match the following pattern:
                        <p class="font-italic font-weight-bold">
                            &ltSCHEMA&gt://&ltHOSTNAME or
                            IP&gt:&ltPORT&gt/api/v1/ui/oauth2-redirect.html
                        </p>
                        <br />
                        <p>
                            <span class="font-weight-bold">WARNING!</span> Use
                            non-https redirect uris only for development
                            purposes!
                        </p>
                    </div>
                </v-card-text>
                <v-card-actions>
                    <v-spacer></v-spacer>
                    <v-btn
                        color="grey"
                        text
                        @click="state.swaggerRedirectDialog = false"
                    >
                        Cancel
                    </v-btn>
                    <v-btn color="primary" text @click="patchSwaggerRedirect">
                        Apply
                    </v-btn>
                </v-card-actions>
            </v-card>
        </v-dialog>
    </div>
</template>

<script setup>
import { deepClone } from "~/utils/misc";
import { sanitizeDate } from "~/utils/date";
import { ArrayUtils } from "~/utils/array";

useSeoMeta({
    title: "Users",
    description: "User management for xbat",
});

const headers = [
    {
        title: "User",
        key: "user_name"
    },
    { title: "Type", key: "user_type" },
    { title: "UID", key: "uidnumber" },
    { title: "GID", key: "gidnumber" },
    { title: "Home Directory", key: "homedirectory" },
    { title: "Last Login", key: "last_login" },
    { title: "Status", key: "blocked" }
];

const roles = [
    { value: "demo", title: "demo" },
    { value: "guest", title: "guest" },
    { value: "user", title: "user" },
    { value: "manager", title: "manager" }
];

const tableSortBy = ref([{ key: "user_name", order: "asc" }]);

definePageMeta({
    requiresAdmin: true
});

const { $api, $snackbar, $authStore, $store } = useNuxtApp();

const edit = ref({});

const state = reactive({
    editDialog: false,
    whitelistDialog: false,
    search: "",
    form: {
        password: "",
        passwordRepeat: ""
    },
    whitelistAdd: "",
    whitelistAddValid: false,
    passwordNotMatching: false,
    selected: [],
    swaggerRedirectDialog: false,
    redirect_uris: ""
});

const { data: whitelist, refresh: refreshSettings } = await useAsyncData(
    "settings",
    async () =>
        (await $api.settings.get())?.whitelist || {
            enabled: false,
            users: []
        }
);

const {
    data: users,
    pending: usersPending,
    refresh: refreshUsers
} = await useAsyncData("users", () => $api.users.get());

const { data: swaggerRedirects, refresh: refreshSwaggerRedirect } =
    useAsyncData(
        "swaggerRedirects",
        async () => {
            if ($authStore.userLevel != $authStore.UserLevelEnum.admin)
                return { redirect_uris: "" };
            return await $api.users.getSwaggerRedirectURIs();
        },
        { lazy: true, transform: (v) => v?.redirect_uris || "" }
    );

watch(
    swaggerRedirects,
    () => {
        state.redirect_uris = swaggerRedirects.value;
    },
    { immediate: true }
);

const patchSwaggerRedirect = async () => {
    if ($authStore.userLevel != $authStore.UserLevelEnum.admin) return;

    await $api.users.patchSwaggerRedirectURIs({
        redirect_uris: state.redirect_uris
    });
    await refreshSwaggerRedirect();
    state.swaggerRedirectDialog = false;

    if (!$store.error) $snackbar.show("Saved Changes");
};

const editIsAdminOrDemo = computed(
    () => edit.value.user_type === "admin" || edit.value.user_type === "demo"
);

const currentUserName = computed(() => $authStore.user?.user_name || "");
const unselectableUsers = computed(() => [
    currentUserName.value,
    ...(currentUserName.value != "admin" ? ["admin"] : [])
]);

const userIsSelectable = (user) => {
    return !unselectableUsers.value.includes(user);
};

const save = async () => {
    if ($store.demo) {
        $snackbar.show($store.demoMessage);
        resetEdit();
        return;
    }

    let postData = {};
    if (editIsAdminOrDemo.value) {
        if (!state.form.password) return;

        if (state.form.password != state.form.passwordRepeat) {
            state.passwordNotMatching = true;
            return;
        }
        state.passwordNotMatching = false;
        postData = { password: state.form.password };
    } else {
        postData = {
            user_type: edit.value.user_type
        };
    }

    await $api.users.patch(edit.value.user_name, postData);
    $snackbar.show("Saved Changes");
    await refreshUsers();
    resetEdit();
};

const addToWhitelist = () => {
    if (!state.whitelistAdd || state.whitelistAdd in whitelist.value.users)
        return;

    whitelist.value.users.push(state.whitelistAdd);
    state.whitelistAdd = "";
};
const removeFromWhitelist = (user) => {
    ArrayUtils.popValue(whitelist.value.users, user);
};

const saveWhitelist = async () => {
    if ($store.demo) {
        $snackbar.show($store.demoMessage);
        state.whitelistDialog = false;
        return;
    }
    await $api.settings.patch({ whitelist: whitelist.value });
    state.whitelistDialog = false;
    await refreshSettings();
    $snackbar.show("Saved Changes");
};

const setAccess = async (action) => {
    state.selected = state.selected.filter((x) =>
        userIsSelectable(x.user_name)
    );

    if (!state.selected.length) return;

    if ($store.demo) {
        $snackbar.show($store.demoMessage);
        return;
    }

    const postData = { blocked: action == "block" ? true : false };
    for (const user of state.selected) {
        await $api.users.patch(user.user_name, postData);
    }
    $snackbar.show(
        `${action == "block" ? "Blocked" : "Unblocked"} ${
            state.selected.length > 1 ? "Users" : "User"
        }`
    );
    state.selected = [];
    await refreshUsers();
};

const setEdit = (event, { item }) => {
    if (!event.target.className.includes("v-data-table")) return;
    edit.value = deepClone(item);
    state.editDialog = true;
};

const resetEdit = () => {
    state.editDialog = false;
    edit.value = {};
    state.form.password = "";
    state.form.passwordRepeat = "";
};
</script>

<style lang="scss" scoped>
@use "~/assets/css/colors.scss" as *;

.whitelist-entry {
    background-color: $font-disabled;
    border-radius: 3px;
    margin-bottom: 3px;
}

.action-item {
    cursor: pointer;
}

.edit-container {
    font-size: 0.875rem !important;
    .item {
        color: $font-light;
    }
}

// hide select all as this is currently broken
.user-table {
    :deep(.v-data-table__th) {
        .v-selection-control {
            display: none;
        }
    }
}
</style>
