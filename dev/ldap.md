# LDAP for Local Development

Use the LDAP setup for local testing of the LDAP connector and authentication system.

This setup is based on [this guide](https://medium.com/@amrutha_20595/setting-up-openldap-server-with-docker-d38781c259b2).

## Setup

Start ldap docker container

```
cd tests/ldap
docker-compose up -d
```

Execute `ldap_setup.sh` in the container. This adds the OU and users to the LDAP server.

```
docker exec xbat-ldap /bin/bash -c /ldap_setup.sh
```

Shut down container when done

```
docker-compose down
```

## Login

Log into xbat with `johndoe:password`.
