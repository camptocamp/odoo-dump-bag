FROM nginx
MAINTAINER Camptocamp

ADD https://github.com/kelseyhightower/confd/releases/download/v0.13.0/confd-0.13.0-linux-amd64 /usr/local/bin/confd
RUN echo '96abb18973a2d31f147bf01d000fd92ef60ae371 /usr/local/bin/confd' | sha1sum -c - && \
    chmod +x /usr/local/bin/confd

RUN mkdir -p /etc/confd/{conf.d,templates}
COPY conf.d /etc/confd/conf.d
COPY templates /etc/confd/templates
COPY docker-entrypoint.sh /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]

ENV NGX_BAG_HOST=server

CMD ["nginx", "-g", "daemon off;"]
