from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ActivitiesDashboard(models.TransientModel):
    _name = 'activities.dashboard'
    _description = 'Activities Dashboard'

    display_name = fields.Char(string='Display Name')
    sales_person = fields.Char(string='Sales Person')
    meeting_online = fields.Integer(string='Meeting Online')
    meeting_offline = fields.Integer(string='Meeting Offline')
    call = fields.Char(string='Call')

    @api.model
    def update_activities_dashboard(self):
        try:
            query_truncate = """
            TRUNCATE TABLE activities_dashboard;
            """
            self.env.cr.execute(query_truncate)
            self.env.cr.commit()

            query = """
            SELECT *
            FROM (
                SELECT
                    res_partner.display_name,
                    COALESCE(res_users.login, 'NO Sales Person') AS sales_person,
                    COUNT(CASE WHEN mail_message.subtype_id = 3 AND mail_message.mail_activity_type_id = 24 THEN mail_message.id END) as MeetingOnline,
                    COUNT(CASE WHEN mail_message.subtype_id = 3 AND mail_message.mail_activity_type_id = 25 THEN mail_message.id END) as MeetingOffline,
                    COUNT(CASE WHEN mail_message.subtype_id = 3 AND mail_message.mail_activity_type_id = 2 THEN mail_message.id END) as Call_
                FROM
                    mail_message
                INNER JOIN
                    crm_lead ON res_id = crm_lead.id
                INNER JOIN
                    res_partner ON crm_lead.partner_id = res_partner.id
                LEFT JOIN
                    res_users ON crm_lead.user_id = res_users.id
                WHERE
                    (
                        (mail_message.subtype_id = 3 AND mail_message.mail_activity_type_id = 24 and mail_message.create_date >= current_date)
                        OR (mail_message.subtype_id = 3 AND mail_message.mail_activity_type_id = 25 and mail_message.create_date >= current_date)
                        OR (mail_message.subtype_id = 3 AND mail_message.mail_activity_type_id = 2 and mail_message.create_date >= current_date)
                    )
                    AND model = 'crm.lead'
                GROUP BY
                    res_partner.display_name, res_users.login

                UNION

                SELECT
                    res_partner.display_name,
                    COALESCE(res_users.login, 'NO Sales Person') AS sales_person,
                    COUNT(CASE WHEN mail_message.subtype_id = 3 AND mail_message.mail_activity_type_id = 24 THEN mail_message.id END) as MeetingOnline,
                    COUNT(CASE WHEN mail_message.subtype_id = 3 AND mail_message.mail_activity_type_id = 25 THEN mail_message.id END) as MeetingOffline,
                    COUNT(CASE WHEN mail_message.subtype_id = 3 AND mail_message.mail_activity_type_id = 2 THEN mail_message.id END) as Call_
                FROM
                    mail_message
                INNER JOIN
                    res_partner ON res_id = res_partner.id
                LEFT JOIN
                    res_users ON mail_message.create_uid = res_users.id
                WHERE
                    (
                        (mail_message.subtype_id = 3 AND mail_message.mail_activity_type_id = 24 and mail_message.create_date >= current_date)
                        OR (mail_message.subtype_id = 3 AND mail_message.mail_activity_type_id = 25 and mail_message.create_date >= current_date)
                        OR (mail_message.subtype_id = 3 AND mail_message.mail_activity_type_id = 2 and mail_message.create_date >= current_date)
                    )
                    AND model = 'res.partner'
                GROUP BY
                    res_partner.display_name, res_users.login
            ) AS combined_result;
            """
            self.env.cr.execute(query)
            result = self.env.cr.fetchall()

            for row in result:
                vals = {
                    'display_name': row[0],
                    'sales_person': row[1],
                    'meeting_online': row[2],
                    'meeting_offline': row[3],
                    'call': row[4],
                }
                create_first_data = self.create(vals)
                _logger.info('Created record with ID: %s', create_first_data.id)

            self.env.cr.commit()
        except Exception as e:
            _logger.error("Error while writing to the database: %s", e)
