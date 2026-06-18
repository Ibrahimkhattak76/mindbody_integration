# -*- coding: utf-8 -*-
{
    'name': 'Mindbody Integration',
    'summary': 'One-way integration: Mindbody → Odoo',
    'description': 'Sync Clients, Classes, Bookings from Mindbody to Odoo.',
    'author': 'Your Company',
    'website': 'https://yourcompany.com',
    'category': 'Sales',
    'version': '1.0.0',
    'depends': ['base', 'contacts', 'event'],
    'data': [
        # Security
        'security/security.xml',
        'security/ir.model.access.csv',

        # Common Views
        'views/mindbody_common_views.xml',

        # Sale/Purchase Views
        'views/mindbody_accepted_card_type_views.xml',
        'views/mindbody_payment_method_views.xml',
        'views/mindbody_contract_views.xml',
        'views/mindbody_gift_card_views.xml',
        'views/mindbody_package_views.xml',
        'views/mindbody_product_views.xml',
        'views/mindbody_service_views.xml',
        'views/mindbody_price_views.xml',
        'views/mindbody_purchase_totals_views.xml',
        'views/mindbody_purchase_contract_status_views.xml',
        'views/mindbody_shopping_cart_views.xml',
        'views/mindbody_transaction_views.xml',
        'views/mindbody_sale_views.xml',

        # Site Views
        'views/mindbody_site_views.xml',

        # Client Views
        'views/mindbody_client_views.xml',

        # Staff Views
        'views/mindbody_staff_views.xml',

        # Appointment Views
        'views/mindbody_appointment_views.xml',

        # Class/Enrollment Views
        'views/mindbody_class_views.xml',

        # Pick-a-Spot Views
        'views/mindbody_pickaspot_views.xml',

        # Configuration
        'views/res_config_views.xml',

        # Wizards
        'wizards/session_type_selection_views.xml',

        # Menu
        'views/actions.xml',
        'views/menu.xml',

    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
}
