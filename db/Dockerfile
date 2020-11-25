FROM postgres:12-alpine

ENV POSTGRES_USER vduser
ENV POSTGRES_PASSWORD virtualdoctor
ENV POSTGRES_DB vd

COPY sql/ /docker-entrypoint-initdb.d/