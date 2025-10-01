# custom mongodb image to run with custom configuration
FROM docker.io/mongo:7

ENTRYPOINT ["mongod","--config","/etc/mongod.conf"]