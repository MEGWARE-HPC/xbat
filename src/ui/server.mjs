#!/bin/env/node

// Production server - only for local testing!

import fs from "fs";

process.env.NITRO_SSL_CERT = fs.readFileSync("../backend/certs/cert.pem");
process.env.NITRO_SSL_KEY = fs.readFileSync("../backend/certs/key.pem");

await import("./.output/server/index.mjs");
