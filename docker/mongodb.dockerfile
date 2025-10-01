# custom mongodb image to run with custom configuration
FROM docker.io/mongo:8

ENTRYPOINT ["mongod","--config","/etc/mongod.conf"]