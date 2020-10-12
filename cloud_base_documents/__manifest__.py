# -*- coding: utf-8 -*-
{
    "name": "Cloud Sync for Enterprise Documents",
    "version": "12.0.1.0.1",
    "category": "Document Management",
    "author": "Odoo Tools",
    "website": "https://odootools.com/apps/12.0/cloud-sync-for-enterprise-documents-279",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "cloud_base",
        "documents"
    ],
    "data": [
        "data/data.xml",
        "security/ir.model.access.csv"
    ],
    "qweb": [
        
    ],
    "js": [
        
    ],
    "demo": [
        
    ],
    "external_dependencies": {},
    "summary": "The technical extension to sync Odoo Enterprise Documents with cloud clients",
    "description": """
    This is the extension for the cloud storage clients to synchronize Odoo Enterprise Documents.

    This module is a technical extension and is not of use without a real client app. Please select a desired one below
    <a href='https://apps.odoo.com/apps/modules/12.0/onedrive/'>OneDrive / SharePoint</a>
    <a href='https://apps.odoo.com/apps/modules/12.0/owncloud_odoo/'>OwnCLoud / NextCloud</a>
    <a href='https://apps.odoo.com/apps/modules/12.0/dropbox/'>DropBox</a>
    <a href='https://apps.odoo.com/apps/modules/12.0/google_drive_odoo/'>Google Drive</a>
""",
    "images": [
        "static/description/main.png"
    ],
    "price": "44.0",
    "currency": "EUR",
}