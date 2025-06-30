---
title: Continuous Integration
description: Automating xbat for Continuous Benchmarking
---

xbat can be used as an extension for Continuous Integration (CI) systems to automate benchmarking. This page provides an example of how to trigger a benchmark via `cURL` and integrate xbat into GitLab CI. Visit the [API documentation](./api) for more information on the REST API.

::Headline

## Triggering xbat via _cURL_

::

First, you need to obtain a valid access token by authenticating against `/oauth/token`. Substitute host, port, and credentials accordingly.

::Codeblock

```bash
XBAT_USER=<username>
XBAT_PASSWORD=<password>

curl -X POST --user "$XBAT_USER:$XBAT_PASSWORD"  https://<host>:<port>/oauth/token \
    -d "grant_type=password" \
    -d "username=$XBAT_USER" \
    -d "password=$XBAT_PASSWORD"

```

::
The response will contain an access token that you can use to authenticate against the API.

::Codeblock

```json
{ "token_type": "Bearer", "access_token": "<token>", "expires_in": 864000 }
```

::

Use the access token to post against `/benchmarks` with the desired benchmark name and configuration. `sharedProjects` and `variables` are optional.

::Codeblock

```bash
curl -X POST https://<host>:<port>/benchmarks \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
        "name": "<name-of-benchmark>",
        "configId": "<configuration-id>",
        "variables": [{
            "key": "<key>",
            "selected": ["<value>"]
        }],
        "sharedProjects": [
            "<project-id>"
        ]
      }'
```

::

::Banner{type="info"}
The configuration and project IDs can be obtained from the respective web interfaces.
::

::Headline

## Adding xbat to GitLab CI

::

::Banner{type="warning"}
Do not hardcode sensitive information like passwords in your CI configuration. Use GitLab CI/CD variables instead.
::

::Codeblock

```yaml
test-xbat:
    stage: test
    allow_failure: true
    image: badouralix/curl-jq
    script:
        # assume $XBAT_USER and $XBAT_PASSWORD are set as CI/CD variables
        # obtain token
        - |
            response=$(curl -X POST --user "$XBAT_USER:$XBAT_PASSWORD"  https://<host>:<port>/oauth/token \
                -d "grant_type=password" \
                -d "username=$XBAT_USER" \
                -d "password=$XBAT_PASSWORD"\
                -d "client_id=$XBAT_USER")
        # extract access token
        - access_token=$(echo $response | jq -r '.access_token')
        # trigger benchmark
        - |
            curl -X POST https://<host>:<port>/benchmarks \
                -H "Authorization: Bearer <access_token>" \
                -H "Content-Type: application/json" \
                --data @- << EOF
                    {
                            "name": "<name-of-benchmark>",
                            "configId": "<configuration-id>",
                            "variables": [{
                                "key": "<key>",
                                "selected": ["<value>"]
                            }],
                            "sharedProjects": [
                                "<project-id>"
                            ]
                    }
                EOF
```

::

::Headline

## Using another GitLab instance as Proxy

::

In this scenario, your GitLab instance (GL-external) does not have direct access to the xbat server. Instead, you can use another public-facing GitLab instance (GL-internal) sharing the same network with xbat as a proxy to trigger the benchmark. Visit the [GitLab documentation](https://docs.gitlab.com/ee/ci/triggers/){:target="_blank"} for more information on pipeline triggers.
Firstly, create a new project in GL-internal and add the following `.gitlab-ci.yml` configuration.

::Codeblock

```yaml
forward-xbat:
    stage: forward
    image: badouralix/curl-jq
    script:
        - GITLAB_PAYLOAD=$(cat $TRIGGER_PAYLOAD)
        - |
            response=$(curl -X POST --user "$XBAT_USER:$XBAT_PASSWORD"  https://<host>:<port>/oauth/token \
                -d "grant_type=password" \
                -d "username=$XBAT_USER" \
                -d "password=$XBAT_PASSWORD"\
                -d "client_id=$XBAT_USER")
        - access_token=$(echo $response | jq -r '.access_token')
        - PAYLOAD=$(echo $GITLAB_PAYLOAD | jq '.payload')
        - |
            curl -X POST https://<host>:<port>/benchmarks \
                -H "Authorization: Bearer <access_token>" \
                -H "Content-Type: application/json" \
                --data '"$PAYLOAD"'
```

::

Next, create a new project in GL-external and add the following `.gitlab-ci.yml` configuration. Add the generated pipeline trigger token as a secret variable.

::Codeblock

```yaml
test-xbat:
    stage: test
    allow_failure: true
    image: curlimages/curl:8.8.0
    script:
        - |
            curl -X POST <pipeline-trigger-url> --fail-with-body \
                --header "Content-Type: application/json" \
                --globoff \
                --data @- << EOF
                    {
                    "token": "$PIPELINE_TOKEN",
                    "username": "$XBAT_USER",
                    "password": "$XBAT_PASSWORD",
                    "ref": "master",
                    "payload": {
                        "configId": "<configuration-id>",
                        "name": "<name-of-benchmark>",
                        "variables": [{
                            "key": "<key>",
                            "selected": ["<value>"]
                        }]
                    }
                EOF
```
