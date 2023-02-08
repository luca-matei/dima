class lmHtml:
    characters = string.digits + string.ascii_lowercase + string.ascii_uppercase + '/.-'

    escapes = {
        '&': '&amp;',
        '"': '&quot;',
        "'": '&apos;',
        '>': '&gt;',
        '<': '&lt;',
        }
    diacritics = {
        'ă': 'a',
        'â': 'a',
        'î': 'i',
        'ș': 's',
        'ş': 's',
        'ț': 't',
        ' ': '-',
        '_': '-',
        }

lm.html = lmHtml()
