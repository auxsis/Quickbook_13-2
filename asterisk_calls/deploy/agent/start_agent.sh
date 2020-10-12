#!/bin/bash

set -e

# Agent settings, DO NOT PUT SPACES AROUND EQUAL SIGN. A= B - this will not work! A=B # This will work.
export AGENT_UID=asterisk_calls
export DEBUG=0 # If you want debug information set it to 1.
export ODOO_LOGIN=asterisk_agent # This is Odoo account with Asterisk Calls Service role.
export ODOO_PASSWORD=service # This is a password for the above account.
export ODOO_DB=astcalls # This id Odoo database, set your own here.
export ODOO_HOST=odoo # This is hostname of your odoo server.
export ODOO_PORT=8069 # This is JSON-RPC Odoo port, if your use nginx it can be 80.
export ODOO_POLLING_PORT=8072 # This is gevent Odoo port, if your use nginx /longpolling/poll proxy pass to 8072 it can be 80.
export ODOO_SCHEME=http # http or https
export ODOO_RECONNECT_TIMEOUT=1 # When Odoo is unavailble try to connect every X seconds. 
export MONITOR_DIR=/var/spool/asterisk/monitor # Check that this is the right path where recordings are saved.
export RECORDING_UPLOAD_ENABLED=1 # Send call recording to Odoo.
export RECORDING_KEEP_FAILED_UPLOAD=0 # Set to 1 if you want to keep recordings that failed to be uploaded.
export RECORDING_UPLOAD_DELAY=3 # We need some time for CDR to be sent to Odoo and after that we upload recording.
export QOS_UPDATE_DELAY=2 # We need that CDR will be sent first and after that update it with QoS info.
export DISABLE_ACTIVE_CALL_TRACKING=0 # Set to 1 if you have Askozia PBX or old Asterisk version.
# Asterisk related variables
export ASTERISK_HOST=127.0.0.1  # Agent connects to this host to Asterisk AMI interface.
export MANAGER_PORT=5038 # This is your Asterisk AMI port number.
export MANAGER_LOGIN=odoo # This is manager account, set in Asterisk manager.conf file.
export MANAGER_PASSWORD=odoo # THis is manager password, set in Asterisk manager.conf file.
export PING_EXPECT_TIMEOUT_MINUTES=2 # Minutes to wait for a ping
export SENTRY_ENABLED=1 # Put here 1 if you want to send the developers error logs
export SENTRY_URL=https://6c3f0633bf0844f8a587e40a62bdc962@sentry.io/1422210


exec python2.7 ./agent.py