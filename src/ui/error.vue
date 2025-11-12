<template>
    <div>
        <v-card
            class="mx-auto pa-12 pb-8 mt-16 text-center"
            elevation="0"
            max-width="768"
        >
            <div class="title">
                {{ props.error.statusCode }} - {{ props.error.message }}
            </div>
            <p>
                {{
                    errorDescriptions[String(props.error.statusCode)] ??
                    "An unexpected error occurred"
                }}
            </p>

            <div
                v-if="props.error.statusCode === 404"
                class="mt-4 text-medium-emphasis"
            >
                <p>Back to Homepage in {{ countdown }} seconds...</p>
            </div>

            <div class="d-flex justify-center mt-12 gap-4">
                <v-btn
                    color="primary-light"
                    size="large"
                    :to="error.statusCode === 401 ? '/login' : '/'"
                    >{{ error.statusCode === 401 ? "Login" : "Return" }}</v-btn
                >
            </div>
        </v-card>
    </div>
</template>
<script lang="ts" setup>
const props = withDefaults(
    defineProps<{
        error: ReturnType<typeof createError>;
        layout?: string;
    }>(),
    { layout: "default" }
);

const countdown = ref(5);
let timer: ReturnType<typeof setInterval> | null = null;

const clearTimer = () => {
    if (timer) {
        clearInterval(timer);
        timer = null;
    }
};
onMounted(() => {
    if (props.error.statusCode === 404) {
        timer = setInterval(() => {
            countdown.value--;
            if (countdown.value <= 0) {
                clearTimer();
                navigateTo("/");
            }
        }, 1000);
    }
});

onUnmounted(() => {
    clearTimer();
});

const errorDescriptions: Record<string, string> = {
    "404": "Sorry, but the page you were trying to view does not exist.",
    "400": "Your submission contains invalid parameters, please check and try again.",
    "401": "You are not authorized to view this page. Please login.",
    "403": "You do not have permission to access this page.",
    "408": "Request Timeout - The server took too long to respond.",
    "429": "Too Many Requests - Please try again later.",
    "500": "Internal Server Error",
    "502": "Bad Gateway",
    "503": "Service Unavailable",
    "504": "Gateway Timeout"
};

useSeoMeta({
    title: `Error - ${props.error.statusCode}`,
    description:
        errorDescriptions[props.error.statusCode] ||
        "An unexpected error occurred"
});
</script>

<style scoped lang="scss">
@use "~/assets/css/colors.scss" as *;

.title {
    font-size: 2.5em;
    margin-bottom: 20px;
    color: $primary-light;
}
</style>
