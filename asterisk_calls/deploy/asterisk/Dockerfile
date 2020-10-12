FROM alpine:3.8
ENV TZ=Europe/Moscow

RUN apk add --no-cache tini tzdata asterisk asterisk-odbc asterisk-curl \
    asterisk-sample-config asterisk-sounds-en asterisk-sounds-moh asterisk-srtp

#Install optional tools
RUN apk add --no-cache tcpdump iftop ngrep bash vim screen curl

ENV DOCKERIZE_VERSION v0.6.1
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-alpine-linux-amd64-$DOCKERIZE_VERSION.tar.gz

COPY ./etc/asterisk/ /etc/asterisk/

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY ./docker-entrypoint.sh /

ENTRYPOINT ["/docker-entrypoint.sh"]

