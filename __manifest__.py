{
    'name' : 'Khabir Hijama',
    'version' : '17.0.0.1',
    'depends': [
        'base','account','product',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/khabir_hijama.xml',
        'views/hijama_type.xml',
        'views/hijama_doctor.xml',
        'views/hijama_reports.xml',
        'wizard/journal_views.xml',
        'report/report.xml',
        'report/hijama_report.xml',
        'report/hijama_record_report.xml',
        'views/hijama_source_info_views.xml',
        'views/account_journal_views.xml',
        # 'security/branch_access_rule.xml',
        # 'views/res_users_view.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}