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

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}