# This is an example script on importing CDRs from Master.csv
import csv
import json
import logging
import sys
import os
import urllib2
import odoorpc

logging.basicConfig()
logger = logging.getLogger(__name__)

if len(sys.argv) != 2:
    print('Set path to Master.csv')

# Connect to Odoo
odoo = odoorpc.ODOO(os.environ.get('ODOO_HOST', 'odoo'), 
                    port=os.environ.get('ODOO_PORT', '8069'))
odoo.login(
    os.environ.get('ODOO_DB', 'astcalls'),
    os.environ.get('ODOO_LOGIN', 'admin'),
    os.environ.get('ODOO_PASSWORD', 'admin'),
)

errors = open('errors.txt', 'w')

with open(sys.argv[1], 'rb') as csvfile:
    cdrs = csv.reader(csvfile, delimiter=',', quotechar='"')    
    for cdr in cdrs:
        try:
            rec = {}
            rec['accountcode'] = cdr[0]
            rec['src'] = cdr[1]
            rec['dst'] = cdr[2]
            rec['dcontext'] = cdr[3]
            rec['clid'] = cdr[4]
            rec['channel'] = cdr[5]
            rec['dstchannel'] = cdr[6]
            rec['lastapp'] = cdr[7]
            rec['lastdata'] = cdr[8]
            rec['started'] = cdr[9]
            rec['answered'] = cdr[10] if cdr[10] else False
            rec['ended'] = cdr[11] if cdr[11] else False
            rec['duration'] = cdr[12]
            rec['billsec'] = cdr[13]
            rec['disposition'] = cdr[14]
            rec['amaflags'] = cdr[15]
            rec['uniqueid'] = cdr[16]
            rec['userfield'] = cdr[17]
            if not odoo.env['asterisk_calls.call'].search(
                                            [('uniqueid','=',rec['uniqueid'])]):
                odoo.env['asterisk_calls.call'].create(rec, 
                                            context={'mail_create_nolog': True,
                                             'mail_create_nosubscribe': True,
                                             'tracking_disable': True,
                                             'mail_notrack': True})
                print('Creating call ID: {}'.format(rec['uniqueid']))
            else:
                print('Ommiting call ID: {}'.format(rec['uniqueid']))

        except urllib2.URLError as e:
            logger.exception(e)
            sys.exit(-1)

        except Exception as e:
            logger.exception(e)
            errors.write('{}'.format(cdr))
            errors.write('\n')            

        finally:
            errors.close()


