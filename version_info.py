# -*- coding: utf-8 -*-
# Informations de version pour l'exécutable Windows

import sys
import os

version_info = (
    6,  # Version majeure
    0,  # Version mineure  
    0,  # Version patch
    0,  # Build
)

version = ".".join(map(str, version_info))

VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=version_info,
        prodvers=version_info,
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    u'040904B0',  # Langue française (0x0409) et codepage Windows-1252 (0x04B0)
                    [
                        StringStruct(u'CompanyName', u'Zebra Technologies'),
                        StringStruct(u'FileDescription', u'Image Label Tool - Outil de classification d\'images'),
                        StringStruct(u'FileVersion', version),
                        StringStruct(u'InternalName', u'ImageLabelTool'),
                        StringStruct(u'LegalCopyright', u'© 2025 Zebra Technologies. Tous droits réservés.'),
                        StringStruct(u'OriginalFilename', u'ImageLabelTool.exe'),
                        StringStruct(u'ProductName', u'Image Label Tool'),
                        StringStruct(u'ProductVersion', version),
                        StringStruct(u'Comments', u'Outil de labellisation et classification d\'images pour Aurora Focus'),
                    ]
                )
            ]
        ),
        VarFileInfo([VarStruct(u'Translation', [0x409, 1252])])
    ]
)