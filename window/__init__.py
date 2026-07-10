"""Package de gestion des fenêtres pour l'assistant Whisp.

L'implémentation est répartie en modules thématiques :
- ``_common`` : en-tête partagé (imports, globals, imports OS conditionnels).
- ``commands`` : dispatcher principal de commandes fenêtre.
- ``monitors`` : détection et gestion multi-écrans.
- ``focus`` : activation/bascule vers une fenêtre ou une application.
- ``enumeration`` : listage des fenêtres et applications ouvertes.
- ``active_app`` : détection de l'application/fenêtre/navigateur actif.
"""
