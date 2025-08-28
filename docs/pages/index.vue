<template>
    <div class="layout">
        <div class="content">
            <div class="card" variant="text">
                <h1 class="title">
                    Simplify HPC application benchmarking and optimization.
                </h1>
                <h2 class="subtitle">
                    Dive deep into application performance with xbat - an easy
                    to use, fully automated tool providing comprehensive metrics
                    and insights for analysis and optimization.
                </h2>
                <div class="d-flex flex-wrap justify-start actions">
                    <v-btn
                        prepend-icon="$github"
                        href="https://github.com/MEGWARE-HPC/xbat"
                        target="_blank"
                        rel="noopener noreferrer"
                        size="large"
                        elevation="0"
                        class="ma-2"
                    >
                        GitHub
                    </v-btn>
                    <v-btn
                        prepend-icon="$file"
                        to="/docs/user/introduction"
                        elevation="0"
                        size="large"
                        class="ma-2"
                    >
                        Documentation
                    </v-btn>
                    <v-btn
                        prepend-icon="$play"
                        to="/docs/demo"
                        elevation="0"
                        size="large"
                        class="ma-2"
                    >
                        Demo
                    </v-btn>
                </div>
            </div>

            <div class="landing-img-wrapper">
                <NuxtImg
                    src="/img/landing_page.png"
                    class="landing-img"
                    alt="xbat example"
                />
            </div>
        </div>

        <div class="footer">
            <div class="users">
                <NuxtLink
                    v-for="user in users"
                    :key="user.href"
                    :to="user.href"
                >
                    <NuxtImg :src="user.src" :alt="user.alt" />
                </NuxtLink>
            </div>
            <v-btn to="/imprint" class="imprint" variant="plain">
                Imprint
            </v-btn>
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
    title,
    ogTitle: title,
    description,
    ogDescription: description
});
</script>

<style scoped lang="scss">
@use "~/assets/css/colors.scss" as *;

.layout {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
}

.content {
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: stretch;
    padding: 6rem 3rem 0 3rem;
    min-height: 77.5vh;
    margin-top: 64px;

    .card {
        max-width: 40vw;
        padding-top: 4rem;

        .title {
            font-size: 4rem;
            line-height: 1.25;
            letter-spacing: -0.015625em;
            font-weight: 400;
            color: $primary;
        }

        .subtitle {
            font-size: 1.75rem;
            color: $font-light;
            margin-top: 20px;
            font-weight: 400;
        }

        .actions {
            margin-top: 1.5rem;
        }
    }

    .landing-img-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
        height: fit-content;
        width: fit-content;
        max-width: 50vw;
        border-radius: 10px;
        background-color: white;
        box-shadow: 3px 3px 13px -4px hsla(160, 59%, 16%, 0.5);

        .landing-img {
            border-radius: 10px;
            max-width: 100%;
            max-height: 50vh;
            object-fit: contain;
        }
    }
}

.footer {
    padding: 0 1rem;

    .users {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-evenly;
        gap: 1.5rem;
        width: 100%;
        margin-bottom: 2rem;
    }

    img {
        height: 80px;
        width: auto;
    }

    .imprint {
        display: block;
        text-align: center;
        font-size: 1rem;
        color: black;
    }
}

@media (max-width: 1200px) {
    .content {
        flex-direction: column;
        align-items: center;
        padding-top: 4rem;

        .card {
            max-width: unset;
            padding-top: 0rem;
        }

        .landing-img-wrapper {
            max-width: 90%;
            margin-top: 1rem;
        }

        .landing-img {
            max-height: 40vh;
        }
    }

    .footer {
        margin-top: 4rem;
        img {
            height: 60px;
        }
    }
}

@media (max-width: 768px) {
    .footer {
        img {
            height: 40px;
        }
    }
}
</style>
