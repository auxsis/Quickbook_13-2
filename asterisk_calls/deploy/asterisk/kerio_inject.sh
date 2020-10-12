#!/bin/sh

set -e

filename="$1"

m1=$(stat -c %Y $filename)

while true; do
  sleep 1
  m2=$(stat -c %Y $filename)
  if [ "$m1" != "$m2" ] ; then
    #echo "File has changed!" >&2
    sleep 2 # (let it sync)
    fgrep -q UserEvent $filename || \
      (sed "/exten => s,n(done),DumpChan()/a exten => s,n,UserEvent(CustomCdr,KTS_FROM: \${ktsFrom},KTS_TO: \${ktsTo},DIALSTATUS: \${DIALSTATUS},HANGUPCAUSE: \${HANGUPCAUSE},DIALEDTIME: \${DIALEDTIME},ANSWEREDTIME: \${ANSWEREDTIME})" $filename > ${filename}.ed1 && \
      sed "/exten => busy,1,KerioSet(ktsStatus=Busy)/a exten => busy,n,UserEvent(CustomCdr,KTS_FROM: \${ktsFrom},KTS_TO: \${ktsTo},DIALSTATUS: \${DIALSTATUS},HANGUPCAUSE: \${HANGUPCAUSE},DIALEDTIME: \${DIALEDTIME},ANSWEREDTIME: \${ANSWEREDTIME})" ${filename}.ed1 > ${filename}.ed2 && \
      sed "/exten => noanswer,1,KerioSet(ktsStatus=Busy)/a exten => noanswer,n,UserEvent(CustomCdr,KTS_FROM: \${ktsFrom},KTS_TO: \${ktsTo},DIALSTATUS: \${DIALSTATUS},HANGUPCAUSE: \${HANGUPCAUSE},DIALEDTIME: \${DIALEDTIME},ANSWEREDTIME: \${ANSWEREDTIME})" ${filename}.ed2 > ${filename}.ed3 && \
      mv ${filename}.ed3 $filename && \
      rm ${filename}.ed1 && rm ${filename}.ed2 && \
      asterisk -rx 'dialplan reload' > /dev/null 2>&1)
    m1=$(stat -c %Y $filename)
  fi
done