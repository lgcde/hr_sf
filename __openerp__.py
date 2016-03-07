# _*_ coding: utf-8 _*_
{
    'name': "hr sf",
    'version': '1.0',
    'depends': ["hr_attendance", "hr_holidays"],
    'author': "糖葫芦(39181819@qq.com)",
    'category': '',
    'description': """
    
    """,
    'data': ["templates/attendance_template.xml",
             "views/hr_attendance_view.xml",
             "views/hr_employee_view.xml",
             "views/hr_attendance_upload_log_view.xml",
             "views/hr_holidays_view.xml",
             "views/hr_overtime_view.xml",
             "data/ir_cron_data.xml",
             "data/ir_config_parameter_data.xml"],
    'demo': [],
}
