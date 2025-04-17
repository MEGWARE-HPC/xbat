<template>
    <div class="GraphGroup">
        <slot :relayout="setGraphLayout" :relayoutData="relayoutData"></slot>
    </div>
</template>

<script>
export default {
    name: "GraphGroup",
    components: {},
    props: {
        synchronize: {
            type: Boolean,
            default: true
        }
    },
    data() {
        return {
            relayoutData: {}
        };
    },
    methods: {
        setGraphLayout(layout) {
            if (!this.synchronize) return;
            //ignore yaxis
            if ("yaxis.range[0]" in layout) delete layout["yaxis.range[0]"];
            if ("yaxis.range[1]" in layout) delete layout["yaxis.range[1]"];

            if (!Object.keys(layout).length) return;
            this.relayoutData = layout;
        }
    }
};
</script>
