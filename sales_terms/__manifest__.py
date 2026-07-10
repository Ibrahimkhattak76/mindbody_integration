{
    'name': 'sale Terms and Conditions',
    'version': '1.0',
    'category': 'sale',
    'summary': 'Manage Terms and Conditions in sale',
    'depends': ['sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_terms_views.xml',
        'views/term_condition.xml',
    ],
    'installable': True,
    'application': False,
}
