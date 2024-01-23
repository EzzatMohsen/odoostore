{
    'name': 'Vendor Portal',
    'sequence': '0',
    'version': '12.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Module for managing the vendor RFQ',
    'version': '0.1',
    'author': 'Ezzat',
    'depends': ['base', 'mail', 'sale', 'website', 'stock', 'web_notify', 'purchase',
                ],
    'data': [
        'data/data.xml',
        'data/sequence.xml',
        'security/ir.model.access.csv',
        'views/agil_rfq_template.xml',
        'views/agil_send_rfq.xml',
        'views/agial_receive_rfq.xml',
        'views/menus.xml',
    ],
    'images': ['static/description/image.png'],

    'version': '0.0.1',
    'application': True,
    'installable': True,

}
