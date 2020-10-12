FROM alpine:3.8

RUN apk add --no-cache  python2 py2-pip py2-gevent tini

#Install optional tools
RUN apk add --no-cache tcpdump ngrep bash vim screen curl git

RUN mkdir -p /agent/ && cd /tmp && git clone -b 12.0 --depth=1 https://github.com/litnimax/remote_agent && \
    mv remote_agent/agent/ /agent/remote_agent/ && rm -rf /mnt/addons/tmp

COPY requirements.txt /agent/
RUN pip install -r /agent/requirements.txt

COPY agent.py / /agent/

COPY start_agent.sh /agent/

WORKDIR /agent

ENTRYPOINT ["/sbin/tini", "--"]

CMD ["python2", "agent.py"]
