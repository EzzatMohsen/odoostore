{
    'name': 'vendor_evaluation (Tender Analysis)',
    'sequence': '0',
    'version': '12.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Module for managing the vendor Evaluation',
    'license': 'AGPL-3',
    'author': 'Diwan Tech',
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
    'images': ['static/description/icon.png'],

    'application': True,
    'installable': True,

}
