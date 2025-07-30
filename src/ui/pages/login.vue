<template>
    <div>
        <div class="demo-banner mx-auto" v-if="$store.demo">
            <p class="font-weight-bold mb-2">xbat is in read-only demo mode</p>

            <div v-if="$store.demoUser && $store.demoPassword">
                <p>
                    Username:
                    <span class="font-italic">{{ $store.demoUser }}</span>
                </p>
                <p>
                    Password:
                    <span class="font-italic">{{ $store.demoPassword }}</span>
                </p>
            </div>
        </div>
        <v-snackbar
            v-model="state.snackbarVisible"
            color="warning"
            timeout="3500"
            location="top"
        >
            {{ state.snackbarMessage }}
        </v-snackbar>
        <v-card class="mx-auto pa-12 pb-8" elevation="4" max-width="448">
            <v-card-title class="text-center relative font-weight-bold title">
                <div class="d-flex justify-center mb-2">
                    <NuxtLink to="https://xbat.dev" target="_blank">
                        <NuxtImg
                            src="/logo/xbat-logo-effect.png"
                            alt="xbat Logo"
                            width="100px"
                        ></NuxtImg>
                    </NuxtLink>
                </div>
                xbat
            </v-card-title>

            <v-card-subtitle class="text-center mb-10"
                >e<span class="font-weight-bold">x</span>tended
                <span class="font-weight-bold">b</span>enchmarking
                <span class="font-weight-bold">a</span>utomation
                <span class="font-weight-bold">t</span>ool</v-card-subtitle
            >
            <div class="text-medium-emphasis text-caption">
                Use your cluster credentials to log in to xbat
            </div>
            <v-form v-model="state.loginValid" @submit.prevent="login">
                <v-text-field
                    v-model="form.username"
                    :rules="[vNotEmpty]"
                    prepend-inner-icon="$username"
                    placeholder="Enter your username"
                    autocomplete="username"
                    variant="outlined"
                    label="Username"
                    class="mt-4 mb-4"
                ></v-text-field>
                <v-text-field
                    :append-inner-icon="
                        state.passwordVisible ? '$hide' : '$show'
                    "
                    :type="state.passwordVisible ? 'text' : 'password'"
                    placeholder="Enter your password"
                    prepend-inner-icon="$password"
                    autocomplete="current-password"
                    v-model="form.password"
                    variant="outlined"
                    label="Password"
                    :rules="[vNotEmpty]"
                    @click:append-inner="
                        state.passwordVisible = !state.passwordVisible
                    "
                ></v-text-field>

                <v-btn
                    class="mb-8 mt-8"
                    color="primary-light"
                    size="large"
                    variant="tonal"
                    block
                    type="submit"
                >
                    Log In
                </v-btn>
            </v-form>
            <div class="d-flex justify-space-between align-center">
                <NuxtLink
                    to="https://www.megware.com/en/products/xbat"
                    target="_blank"
                    title="Visit xbat at MEGWARE"
                >
                    <NuxtImg
                        src="/logo/megware-logo.svg"
                        alt="Megware Logo"
                        width="100px"
                    ></NuxtImg>
                </NuxtLink>
                <v-btn
                    icon="$github"
                    title="Contribute at GitHub"
                    size="large"
                    variant="text"
                    href="https://github.com/MEGWARE-HPC/xbat"
                ></v-btn>
            </div>
        </v-card>
    </div>
</template>

<script setup lang="ts">
const router = useRouter();
const { $authStore, $store } = useNuxtApp();
const { vNotEmpty } = useFormValidation();

useSeoMeta({
    title: "Login",
    ogTitle: "Login",
    description: "Login to xbat",
    ogDescription: "Login to xbat"
});

const form = reactive<{
    username: string;
    password: string;
    remember: boolean;
}>({
    username: "",
    password: "",
    remember: false
});

const state = reactive<{
    loginValid: boolean;
    passwordVisible: boolean;
    snackbarVisible: boolean;
    snackbarMessage: string;
}>({
    loginValid: false,
    passwordVisible: false,
    snackbarVisible: false,
    snackbarMessage: ""
});

onMounted(() => {
    if ($authStore.tokenExpired) {
        state.snackbarMessage = "Session expired. Please log in again.";
        state.snackbarVisible = true;
        $authStore.resetTokenState();
    }
});

const login = async () => {
    if (!state.loginValid) return;
    await $authStore.login(form);
    nextTick(() => {
        if ($authStore.isAuthenticated) router.push("/");
    });
};

const _alert = () => {
    alert("xbat is not open source yet. Stay tuned!");
};
</script>

<style lang="scss" scoped>
@use "~/assets/css/colors.scss" as *;

.demo-banner {
    width: fit-content;
    padding: 10px 20px;
    margin-bottom: 25px;
    border-radius: 5px;
    color: $font-base;
    background-color: $highlight;
    font-size: 0.925rem;
    font-family: Source Code Pro, monospace;
}

.title {
    font-size: 2.125rem;
}
</style>
