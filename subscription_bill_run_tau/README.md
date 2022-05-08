# subscription_bill_run_tau
Set date of next invoice, manage subscription date and pro-rated amount

[14.0.2.0]
For the first invoice:
If date of next invoice has the same month as date start,
bill the date start month with prorate only.
Else, bill the prorate of date start month and fee of all
unpaid month til the date of next invoice month.

[14.0.3.0]
Scheduled Action to run on every day to confirm the SO if x_date_to_confirm is today
Make x_date_to_confirm and subscription management visible on SO
Change "Upselling" to "Change Order" in subscription_management field on SO
remove smart button on sale.subscription pointing to SO
Add o2m table in a new page called "Change Orders" and show x_date_to_confirm in sale.subscription

[14.0.4.0]
Customization on so and subscription
Add contract term in so, contract end date in subscription
When confirm so, set the created subscription to draft

[14.0.5.0]
Merge invoices created from subscription
Add opearting country, metros, sites in crm menu
Add operating_sites in so
Add customer_reference, sale order name, operating_sites from so to invoice lines

[14.0.6.0]
When create SO line, split task into sub task according to the qty of the SO line
Add deprovisioning stage in project task type.
For downselling a product, put the related task to deprovisioning stage and
cancel the corresponding subtask

[14.0.7.0]
Add new "date to confirm" model.
Add One2many x_date_to_confirm in sale subscription line linked to the new created model
Every time create a new upsell/downsell will create a new "date to confirm" record
While generate invoice, go through the "date to confirm" record to split the invoice lines
and calcualte the prorate of the upsell/downdsell order
