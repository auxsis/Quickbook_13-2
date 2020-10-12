# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': 'Material Purchase Requisition and Cost Sheet Integration',
    'version': '1.1',
    'currency': 'EUR',
        'price': 49.0,

    'depends': [
        'odoo_job_costing_management',
    ],
    'support': 'contact@probuse.com',
    'author': 'Probuse Consulting Service Pvt. Ltd.',
    'website': 'www.probuse.com',
    'images': ['static/description/img1.jpg'],
    'live_test_url': 'https://youtu.be/_zM0gpuB5VM',
    'license': 'Other proprietary',
    'category' : 'Projects',
    'summary': 'This module integrate Material Requisition with Job Cost Sheet',
    'description': """
Material Requisition Cost Sheet
- Allow you to create job cost sheets for your projects/contract.<br>
- Allow you to have Project/Contract with Job orders.<br>
- Allow you to have Create Purchase Requisition for perticulat Jobcost.<br>
Purchase_Requisition_Via_iProcurement
Purchase Requisitions
Purchase Requisition
iProcurement
Inter-Organization Shipping Network
Online Requisitions
Issue Enforcement
Inventory Replenishment Requisitions
Replenishment Requisitions
MRP Generated Requisitions
generated Requisitions
purchase Sales Orders
Complete Requisitions Status Visibility
Using purchase Requisitions
purchase requisitions
replenishment requisitions
employee Requisition
employee purchase Requisition
user Requisition
stock Requisition
inventory Requisition
warehouse Requisition
factory Requisition
department Requisition
manager Requisition
Submit requisition
Create purchase Orders
purchase Orders
product Requisition
item Requisition
material Requisition
product Requisitions
material purchase Requisition
material Requisition purchase
purchase material Requisition
product purchase Requisition
item Requisitions
material Requisitions
products Requisitions
purchase Requisition Process
Approving or Denying the purchase Requisition
Denying purchase Requisition​
construction managment
real estate management
construction app
Requisition
Requisitions
indent management
indent
indent stock
indent system
indent request
indent order
odoo indent
internal Requisitions
* INHERIT hr.department.form.view (form)
* INHERIT hr.employee.form.view (form)
* INHERIT stock.picking.form.view (form)
purchase.requisition search (search)
purchase.requisition.form.view (form)
purchase.requisition.view.tree (tree)
purchase_requisition (qweb)
Main Features:
allow your employees to Create Purchase Requisition.
Employees can request multiple material/items on single purchase Requisition request.
Approval of Department Head.
Approval of Purchase Requisition Head.
Email notifications to Department Manager, Requisition Manager for approval.
- Request for Purchase Requisition will go to stock/warehouse as internal picking / internal order and purchase order.
- Warehouse can dispatch material to employee location and if material not present then procurment will created by Odoo standard.
- Purchase Requisition user can decide whether product requested by employee will come from stock/warehouse directly or it needs to be purchase from vendor. So we have field on requisition lines where responsible can select Requisition action: 1. Purchase Order 2. Internal Picking. If option 1 is selected then system will create internal order / internal picking request and if option 2 is selected system will create multiple purchase order / RFQ to vendors selected on lines.
- For more details please see Video on live preview or ask us by email...

job cost sheet
Odoo Job Costing And Job Cost Sheet (Contracting)
Odoo job cost sheet
job cost sheet odoo
contracting odoo
odoo construction
job costing (Contracting)
odoo job costing (Contracting)
odoo job costing Contracting
job order odoo
work order odoo
job Contracting
job costing
job cost Contracting
odoo Contracting
Contracting odoo job
Jobs
Jobs/Configuration
Jobs/Configuration/Job Types
Jobs/Configuration/Stages
Jobs/Job Costs
Jobs/Job Costs/Job Cost Sheets
Jobs/Job Orders
Jobs/Job Orders/Job Notes
Jobs/Job Orders/Job Orders
Jobs/Job Orders/Project Issues
BOQ
Job Costing
Notes
Project Report
Task Report
Jobs/Materials / BOQ 
Jobs/Materials / BOQ /Material Requisitions/ BOQ
Jobs/Materials / BOQ /Materials
Jobs/Projects
Jobs/Projects/Project Budgets
Jobs/Projects/Project Notes
Jobs/Projects/Projects
Jobs/Sub Contractors 
Jobs/Sub Contractors /Sub Contractors
material requision odoo
Contracting
job Contracting
job sheet
job cost Contracting
job cost plan
costing
cost Contracting
subcontracting
Email: contact@probuse.com for more details.
This module provide Construction Management Related Activity.
Construction
Construction Projects
Budgets
Notes
Materials
Material Request For Job Orders
Add Materials
Job Orders
Create Job Orders
Job Order Related Notes
Issues Related Project
Vendors
Vendors / Contractors

Construction Management
Construction Activity
Construction Jobs
Job Order Construction
Job Orders Issues
Job Order Notes
Construction Notes
Job Order Reports
Construction Reports
Job Order Note
Construction app
Construction 

Construction Management

This module provide feature to manage Construction Management activity.
Menus:
Construction
Construction/Configuration
Construction/Configuration /Stages
Construction/Construction
Construction/Construction/Budgets
Construction/Construction/Notes
Construction/Construction/Projects
Construction/Job Orders
Construction/Job Orders /Issues
Construction/Job Orders /Job Orders
Construction/Job Orders /Notes
Construction/Materials / BOQ
Construction/Materials /Material Requisitions / BOQ
Construction/Materials /Materials
Construction/Vendors
Construction/Vendors /Contractors
Defined Reports
Notes
Project Report
Task Report
Construction Project - Project Manager
real estate property
propery management
bill of material
Material Planning On Job Order

Bill of Quantity On Job Order
Bill of Quantity construction
job costing
job cost sheet
cost sheet
project cost sheet
project planning
project sheet cost
job costing plan
Construction cost sheet
Construction job cost sheet
Construction jobs
Construction job sheet
Construction material
Construction labour
Construction overheads
Construction sheet plan
costing
workshop
job workshop
workshop
jobs
cost centers
Construction purchase order
Construction activities
Basic Job Costing
Job Costing Example
job order costing
job order
job orders
Tracking Labor
Tracking Material
Tracking Overhead
overhead
material plan
job overhead
job labor
Job Cost Sheet
Example For Larger Job
Job costing is a method of costing applied in industries where production is measured in terms of completed jobs. Industries where job costing is generally applied are Printing Press. Automobile Garage, Repair workshops, Ship Building, Foundry and other similar manufacturing units which manufacture to customers� specific requirements.

Job costing is a method of costing whereby cost is compiled for a job or work order. The production is against customer�s orders and not for stock. The cost is not related to the unit of production but is a cost for the job, e. g printing of 5000 ledger sheets, repairs of 50 equipment�s, instead of printing one sheet or repair of one equipment.

The elements of cost comprising Prime Cost viz. direct materials, direct labour and direct expenses are charged directly to the jobs concerned, the overhead charged to a job is an apportioned portion of the departmental overhead.
Advantages of Job Order Costing

Features of Job Costing
Enabling Job Costing
Creating Cost Centres for Job Costing
project job cost
project job costing
project job contracting
project job contract
job contract
jobs contract
construction
Construction app
Construction odoo
odoo Construction

            """,
    'data': [
        'views/mpr_line_view.xml',
        'views/jobcost_line_view.xml',
        'views/job_cost_report.xml',
        'views/mpr_view.xml',
             ],
    'installable': True,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
