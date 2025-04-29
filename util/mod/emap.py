
# L M P
efiles: dict[str, list[str]] = {
    'Dawnguard':                ['esm'],
    'Dragonborn':               ['esm'],
    'HearthFires':              ['esm'],
    'ccbgssse001-fish':         ['bsa', 'esm'],
    'ccbgssse025-advdsgs':      ['bsa', 'esm'],
    'ccqdrsse001-survivalmode': ['bsa', 'esl'],
    'ccbgssse037-curios':       ['bsa', 'esl'],
    '_ResourcePack':            ['bsa', 'esl']
}

ehashes: dict[str, bytes] = {
    'Dawnguard':                bytes.fromhex('1bda804009a21228acf6b30aa6aa7a692b247ff8a0313fe9aa69b3617ed4a6c4'),
    'Dragonborn':               bytes.fromhex('5f44f343552688c04f73bf83de58b90f70c7376b133fbbcb56b6fe33acf8778b'),
    'HearthFires':              bytes.fromhex('ad4ca9f32c81e7ddd3e39ec95e03b07841f20712989e598778442ea69b6e6a97'),
    'ccbgssse001-fish':         bytes.fromhex('3b7693a876cd6001960e3f5e3069a79ac8c8fc5528113908bab5079b31efbb87'),
    'ccbgssse025-advdsgs':      bytes.fromhex('d4fe42062c317d2f2d1b3d590fb9afcba850efb69d3e34c86fa64442cda38781'),
    'ccqdrsse001-survivalmode': bytes.fromhex('67393c051f40317be8fa5f36019d92c081ae0aae717441b866bcc2dbbce77650'),
    'ccbgssse037-curios':       bytes.fromhex('7847bc8bc8b22e66fb36647a1f0e454e2e5fe68db0e1385c0c58fff04839dffa'),
    '_ResourcePack':            bytes.fromhex('987f002b2b85ceed0309cb120c0576b359d4ace89f1e4332ecaf1775a3e8725d')
}