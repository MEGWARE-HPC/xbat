// pm2 configuration for docker container
module.exports = {
    apps: [
        {
            name: "xbat-ui",
            port: "7003",
            exec_mode: "cluster",
            instances: "8",
            script: "./.output/server/index.mjs"
        }
    ]
};
