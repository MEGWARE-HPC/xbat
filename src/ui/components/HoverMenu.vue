<template>
    <div class="d-flex align-center justify-center mt-1">
        <v-menu location="start" open-on-hover :close-on-content-click="false">
            <template v-slot:activator="{ props: slotProps }">
                <div v-bind="slotProps">
                    <slot name="activator"> </slot>
                </div>
            </template>
            <v-card>
                <v-card-text>
                    <slot></slot>
                </v-card-text>
            </v-card>
        </v-menu>
    </div>
</template>
