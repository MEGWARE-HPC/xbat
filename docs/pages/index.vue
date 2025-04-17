<template>
    <div>
        <div class="content">
            <div class="card" variant="text">
                <div>
                    <h1 class="title">
                        Simplify HPC application benchmarking and optimization.
                    </h1>
                    <h2 class="subtitle">
                        Dive deep into application performance with xbat - an
                        easy to use, fully automated tool providing
                        comprehensive metrics and insights for analysis and
                        optimization.
                    </h2>
                    <div class="d-flex actions">
                        <v-btn
                            prepend-icon="$github"
                            href="https://github.com/MEGWARE-HPC/xbat"
                            target="_blank"
                            size="large"
                            elevation="0"
                            >GitHub</v-btn
                        >
                        <v-btn
                            prepend-icon="$file"
                            to="/docs/user/introduction"
                            elevation="0"
                            size="large"
                            >Documentation</v-btn
                        >
                        <v-btn
                            prepend-icon="$play"
                            to="/docs/demo"
                            elevation="0"
                            size="large"
                            >Demo</v-btn
                        >
                    </div>
                </div>
            </div>
            <div class="landing-img-wrapper">
                <NuxtImg
                    src="/img/landing_page.png"
                    class="landing-img"
                    alt="xbat example"
                ></NuxtImg>
            </div>
        </div>

        <div class="footer">
            <div class="d-flex users justify-space-between pl-16 pr-16">
                <NuxtLink v-for="user in users" :to="user.href">
                    <NuxtImg :src="user.src" :alt="user.alt"></NuxtImg
                ></NuxtLink>
            </div>
            <v-btn to="/imprint" class="imprint" variant="plain">
                Imprint</v-btn
            >
        </div>
    </div>
</template>
<script lang="ts" setup>
const title = "xbat documentation and demo by MEGWARE";
const description = "xbat HPC application benchmarking and optimization tool";

const users = [
    {
        src: "/img/logo-microcard.svg",
        alt: "Microcard Logo",
        href: "https://microcard.eu/"
    },
    {
        src: "/img/logo-opencarp.png",
        alt: "openCARP Logo",
        href: "https://opencarp.org/"
    },
    {
        src: "/img/logo-hsu.png",
        alt: "HSU Hamburg Logo",
        href: "https://www.hsu-hh.de/"
    },
    {
        src: "/img/logo-mast.png",
        alt: "MaST Logo",
        href: "https://www.hsu-hh.de/hpc/mast-consortium/"
    },
    {
        src: "/img/logo-hpc-bw.png",
        alt: "hpc.bw Logo",
        href: "https://www.hsu-hh.de/wb/hpc-bw/"
    },
    {
        src: "/img/logo-dtec.bw-eu.png",
        alt: "dtec.bw Logo",
        href: "https://dtecbw.de/home"
    },
    {
        src: "/img/logo-eki.png",
        alt: "EKI Logo",
        href: "https://www.uni-paderborn.de/projekt/296"
    }
];

useSeoMeta({
    title: title,
    ogTitle: title,
    description: description,
    ogDescription: description
});
</script>
<style lang="scss" scoped>
@use "~/assets/css/colors.scss" as *;
.content {
    margin-top: 64px;
    height: 77.5vh;
    width: 100vw;
    position: relative;

    .landing-img-wrapper {
        position: absolute;
        right: 3.5%;
        top: 42.5%;
        transform: translate(0, -50%);
        box-shadow: 3px 3px 13px -4px hsla(160, 59%, 16%, 0.5);
        border-radius: 10px;
        background-color: white;
        .landing-img {
            border-radius: 10px;
            max-height: 50vh;
            max-width: 50vw;
            object-fit: contain;
        }
    }

    .card {
        margin: 0;
        width: 50vw;
        position: absolute;
        top: 17.5%;
        left: 27.5%;
        transform: translate(-50%, 0);
        text-align: left;
    }

    .title {
        font-size: 4rem;
        line-height: 1.25;
        letter-spacing: -0.015625em;
        max-width: 40vw;
        font-weight: 400;
        color: $primary;
    }

    .subtitle {
        font-size: 1.75rem;
        color: $font-light;
        margin-top: 20px;
        max-width: 40vw;
        font-weight: 400;
    }

    .actions {
        gap: 25px;
        margin-top: 60px;
    }
}
.footer {
    position: relative;
    height: calc(22.5vh - 64px);

    .users {
        width: 95vw;
        margin: auto;
    }

    img {
        height: 8vh;
        width: auto;
    }

    .imprint {
        text-decoration: none;
        font-size: 1rem;
        position: absolute;
        bottom: 0;
        right: 0;
        transform: translate(-50%, 0);
        color: black;
    }
}

@media (max-width: 1200px) {
    .landing-img,
    .users {
        display: none !important;
    }

    .card {
        left: 50% !important;
        .title,
        .subtitle {
            max-width: 100%;
        }
    }
}
</style>
