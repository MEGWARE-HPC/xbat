#!/bin/bash

sleep 5

# Create OU (orgainaization Units)
ldapadd -x -w password -D "cn=admin,dc=example,dc=com" << EOF
# LDIF file to add organizational unit "ou=users" under "dc=example,dc=com"
dn: ou=users,dc=example,dc=com
objectClass: organizationalUnit
ou: users
EOF

# Create User account
# TODO fix "attribute 'uid' not allowed" error
# uid: johndoe
ldapadd -x -w password -D "cn=admin,dc=example,dc=com" << EOF
# LDIF file to Create user "johndoe" in "ou=users" under "dc=example,dc=com"
dn: cn=johndoe,ou=users,dc=example,dc=com
objectClass: person
cn: johndoe
sn: Doe
userPassword: password
EOF