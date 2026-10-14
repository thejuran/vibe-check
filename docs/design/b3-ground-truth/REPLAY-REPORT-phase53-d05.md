# Replay report — complete-output diff

- base: blob:d4f9fb14aea5f934a12dadf34e357626f7047ba5 (sha256 e22f33b0f3d4ec69425b2e0f948f774116aebe87a90e82551b3c9cab62ad048d)
- candidate: blob:5ca2ddd5cc9a7f88bab9bbdc0604477e8a3d0504 (sha256 660d09ef6753b5a987d948a69c891548898f35ce88053b0be77222a4f94f1089)
- roots: all (6 roots)
- allowances: docs/design/b3-ground-truth/ALLOWANCES-phase53-d05.json
- runs compared: 154
- runs differing: 27
- runs differing (allowed): 8
- runs with unallowed differences: 19
- allowances unused: 0
- head: 2aa339a582fe08f9bb0717866b7e8f26e42ba064
- generated: 2026-10-14T16:36:46Z

_no rounding — exact fractions_

## runs-v2.10-phase40/batch1/triggarr-secret-in-logs/run-1

changed paths: 45
allowed: no

- UNALLOWED filtered[0].line: 235 -> 233
- UNALLOWED filtered[0].title: sha256:ee0df4bffba47551df5d4522229a41f74715ea4f472c3030d06c95b152695b46 -> sha256:c187cf94b4636af8ae6fc2357a89e49751abaf25bb1688271ececba9bdfd86c0
- UNALLOWED filtered[1].title: sha256:c187cf94b4636af8ae6fc2357a89e49751abaf25bb1688271ececba9bdfd86c0 -> sha256:b0ffbfb4726ebb751a2d2534746a4d464a5e65297c517dfeb992d37310556d23
- UNALLOWED filtered[2].line: 233 -> 235
- UNALLOWED filtered[2].title: sha256:b0ffbfb4726ebb751a2d2534746a4d464a5e65297c517dfeb992d37310556d23 -> sha256:ee0df4bffba47551df5d4522229a41f74715ea4f472c3030d06c95b152695b46
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].agent: security -> architecture
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].agent_confidence: sha256:ad48ff99415b2f007dc35b7eb553fd1eb35ebfa2f2f308acd9488eeb86f71fa8 -> sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].category: sha256:8cc5192684865079dea813dcf1f24a4cac21e0e4174cc4e30a1460c44a643178 -> sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].cwe: sha256:d9bf3eb9e951563cd03de1af55fd1d83b420072b0c1578408d5f10317c0e52b7 -> sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].fix_hint: sha256:23b2464bc9a84fef1436ed281be995487c409901c3a40ae36764507f33a46d14 -> sha256:55428a32ecc4f2a54c92dd0854fd0eca19bf6ba70514224e4c32a8b3fab3193c
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].line: 235 -> 233
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].problem: sha256:4e2359f51652f344cb334be3d515b791fc22b8587de815301e15d686276eaa41 -> sha256:664da5f6b31a1280edbc5bc4a25ac25c9cc2200d465f9a07bfcd202bf205d686
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].severity: sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].source_window[0]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].source_window[1]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].source_window[2]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].source_window[3]: sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286 -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].source_window[4]: sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].title: sha256:ee0df4bffba47551df5d4522229a41f74715ea4f472c3030d06c95b152695b46 -> sha256:c187cf94b4636af8ae6fc2357a89e49751abaf25bb1688271ececba9bdfd86c0
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].why_it_matters: sha256:8ae7b293dff575421242ad6075f7216ffb1f5b1c112a1c9890cfb8622f6c7c1d -> sha256:9880f3889a8fff69c88788121834c5f0bc028b004a3020ef0d1f400d479ea46f
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[2].agent: architecture -> codex-adversarial
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[2].agent_confidence: sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763 -> sha256:ad57366865126e55649ecb23ae1d48887544976efea46a48eb5d85a6eeb4d306
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[2].category: sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2 -> sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[2].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> (absent)
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[2].cwe: sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[2].fix_hint: sha256:55428a32ecc4f2a54c92dd0854fd0eca19bf6ba70514224e4c32a8b3fab3193c -> sha256:132f6b00089c4483f09b981341948496bbb9ec979170c17a9f448424279141fb
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[2].problem: sha256:664da5f6b31a1280edbc5bc4a25ac25c9cc2200d465f9a07bfcd202bf205d686 -> sha256:e51f716a0a4fc876bcdebf001804ecdf8bbfed55907372b954c50cb72f06548d
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[2].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[2].title: sha256:c187cf94b4636af8ae6fc2357a89e49751abaf25bb1688271ececba9bdfd86c0 -> sha256:b0ffbfb4726ebb751a2d2534746a4d464a5e65297c517dfeb992d37310556d23
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[2].why_it_matters: sha256:9880f3889a8fff69c88788121834c5f0bc028b004a3020ef0d1f400d479ea46f -> sha256:50982a260ffd4dd650a1d7705b7e484829a5286eb18758da3a4c3b118a7bdeb7
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].agent: codex-adversarial -> security
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].agent_confidence: sha256:ad57366865126e55649ecb23ae1d48887544976efea46a48eb5d85a6eeb4d306 -> sha256:ad48ff99415b2f007dc35b7eb553fd1eb35ebfa2f2f308acd9488eeb86f71fa8
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].category: sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7 -> sha256:8cc5192684865079dea813dcf1f24a4cac21e0e4174cc4e30a1460c44a643178
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].current_code: (absent) -> sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> sha256:d9bf3eb9e951563cd03de1af55fd1d83b420072b0c1578408d5f10317c0e52b7
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].fix_hint: sha256:132f6b00089c4483f09b981341948496bbb9ec979170c17a9f448424279141fb -> sha256:23b2464bc9a84fef1436ed281be995487c409901c3a40ae36764507f33a46d14
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].line: 233 -> 235
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].problem: sha256:e51f716a0a4fc876bcdebf001804ecdf8bbfed55907372b954c50cb72f06548d -> sha256:4e2359f51652f344cb334be3d515b791fc22b8587de815301e15d686276eaa41
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].source_window[0]: sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].source_window[1]: sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].source_window[2]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].source_window[3]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].source_window[4]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].title: sha256:b0ffbfb4726ebb751a2d2534746a4d464a5e65297c517dfeb992d37310556d23 -> sha256:ee0df4bffba47551df5d4522229a41f74715ea4f472c3030d06c95b152695b46
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].why_it_matters: sha256:50982a260ffd4dd650a1d7705b7e484829a5286eb18758da3a4c3b118a7bdeb7 -> sha256:8ae7b293dff575421242ad6075f7216ffb1f5b1c112a1c9890cfb8622f6c7c1d

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | triggarr/clients/base.py | 233 | critical | 100 | 1b7b0aee39af |
| security | triggarr/clients/base.py | 254 | warning | 94 | 9df57cdcdad5 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | triggarr/clients/base.py | 233 | critical | 100 | 1b7b0aee39af |
| security | triggarr/clients/base.py | 254 | warning | 94 | 9df57cdcdad5 |

## runs-v2.10-phase40/batch2/triggarr-secret-in-logs/run-1

changed paths: 36
allowed: no

- UNALLOWED filtered[1].line: 232 -> 233
- UNALLOWED filtered[1].title: sha256:8bbf26086ecfaed4a137c6a350d7fcc10848d2a2324f5f5bf2c64a334a025d27 -> sha256:f95cbd6f0f5a1c3dc72f28b1256db1bdcdc000d2fc1cf178839ee258e55c999d
- UNALLOWED filtered[2].line: 233 -> 232
- UNALLOWED filtered[2].title: sha256:f95cbd6f0f5a1c3dc72f28b1256db1bdcdc000d2fc1cf178839ee258e55c999d -> sha256:8bbf26086ecfaed4a137c6a350d7fcc10848d2a2324f5f5bf2c64a334a025d27
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].agent: architecture -> codex-adversarial
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].agent_confidence: sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349 -> sha256:ad57366865126e55649ecb23ae1d48887544976efea46a48eb5d85a6eeb4d306
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].category: sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2 -> sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].current_code: sha256:090a6aaadf7cb054cdd79571045924cae0b1632ade322a8c651da3ab001f9514 -> (absent)
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].cwe: sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].fix_hint: sha256:cd12db9df007dd0b8b2fbb559040e75050e4c6a5b19b89ec38877890e90d1407 -> sha256:5c3693295366a30212edae1ae3dc6d78ccc2dd2d3a217690494568f4104848dd
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].line: 232 -> 233
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].problem: sha256:5e5945a67cdc7189e0631ed83c43e1b7a15c4fc0429cdcca5a8219634049d3f8 -> sha256:138dfe4351d0d6b71deadc4c35dd2504e524d8e14ab2fca0767dcd02b8abc75d
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].source_window[0]: sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286 -> sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].source_window[1]: sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca -> sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].source_window[2]: sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].source_window[3]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].source_window[4]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].title: sha256:8bbf26086ecfaed4a137c6a350d7fcc10848d2a2324f5f5bf2c64a334a025d27 -> sha256:f95cbd6f0f5a1c3dc72f28b1256db1bdcdc000d2fc1cf178839ee258e55c999d
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].why_it_matters: sha256:fe6d2acc6b11d851a38c81b92c68896c931c0df52bd9d6834de88add4a0ff96c -> sha256:d232fd6e18167035e68c819d2aabec81551345e2ad566d8449de6dddcb3a1afa
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].agent: codex-adversarial -> architecture
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].agent_confidence: sha256:ad57366865126e55649ecb23ae1d48887544976efea46a48eb5d85a6eeb4d306 -> sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].category: sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7 -> sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].current_code: (absent) -> sha256:090a6aaadf7cb054cdd79571045924cae0b1632ade322a8c651da3ab001f9514
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].fix_hint: sha256:5c3693295366a30212edae1ae3dc6d78ccc2dd2d3a217690494568f4104848dd -> sha256:cd12db9df007dd0b8b2fbb559040e75050e4c6a5b19b89ec38877890e90d1407
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].line: 233 -> 232
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].problem: sha256:138dfe4351d0d6b71deadc4c35dd2504e524d8e14ab2fca0767dcd02b8abc75d -> sha256:5e5945a67cdc7189e0631ed83c43e1b7a15c4fc0429cdcca5a8219634049d3f8
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].severity: sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].source_window[0]: sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca -> sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].source_window[1]: sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e -> sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].source_window[2]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].source_window[3]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].source_window[4]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].title: sha256:f95cbd6f0f5a1c3dc72f28b1256db1bdcdc000d2fc1cf178839ee258e55c999d -> sha256:8bbf26086ecfaed4a137c6a350d7fcc10848d2a2324f5f5bf2c64a334a025d27
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].why_it_matters: sha256:d232fd6e18167035e68c819d2aabec81551345e2ad566d8449de6dddcb3a1afa -> sha256:fe6d2acc6b11d851a38c81b92c68896c931c0df52bd9d6834de88add4a0ff96c

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| security | triggarr/clients/base.py | 233 | critical | 100 | 087270666450 |
| security | triggarr/clients/base.py | 252 | warning | 92 | 66cb504a179b |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| security | triggarr/clients/base.py | 233 | critical | 100 | 087270666450 |
| security | triggarr/clients/base.py | 252 | warning | 92 | 66cb504a179b |

## runs-v2.10-phase40/batch3/triggarr-secret-in-logs/run-1

changed paths: 251
allowed: no

- UNALLOWED filtered[0].line: 235 -> 233
- UNALLOWED filtered[0].reason: sha256:e791d9e68d41d2736eb554fe71d5c0a38ae446273de831455020a0832a4b43ee -> sha256:bbf812d2aebcc82b9cafd11f95a864caa7f3da78c66ab499c2abafb7890f38ca
- UNALLOWED filtered[0].title: sha256:c90bb668ab14a7a42038e77ae35f950e4b6104b847342f2d178edc1c76dfb261 -> sha256:245cb7ecccfa3c07882f094abbebd77d54ea9526ea1ce72442b3f54fddbefe61
- UNALLOWED filtered[1].line: 233 -> 235
- UNALLOWED filtered[1].reason: sha256:e791d9e68d41d2736eb554fe71d5c0a38ae446273de831455020a0832a4b43ee -> sha256:bbf812d2aebcc82b9cafd11f95a864caa7f3da78c66ab499c2abafb7890f38ca
- UNALLOWED filtered[1].title: sha256:e56e7be97a7a90821b9ff114081fdfa4eba1efc570ce2d374af0409757f13daf -> sha256:ca0a74fde3f93cb931153eac36f4c8c74a7c0e8b667e1afd337ec6a6d658d772
- UNALLOWED filtered[2].line: 233 -> 235
- UNALLOWED filtered[2].reason: sha256:e791d9e68d41d2736eb554fe71d5c0a38ae446273de831455020a0832a4b43ee -> sha256:bbf812d2aebcc82b9cafd11f95a864caa7f3da78c66ab499c2abafb7890f38ca
- UNALLOWED filtered[2].title: sha256:245cb7ecccfa3c07882f094abbebd77d54ea9526ea1ce72442b3f54fddbefe61 -> sha256:c90bb668ab14a7a42038e77ae35f950e4b6104b847342f2d178edc1c76dfb261
- UNALLOWED filtered[3].reason: sha256:e791d9e68d41d2736eb554fe71d5c0a38ae446273de831455020a0832a4b43ee -> sha256:bbf812d2aebcc82b9cafd11f95a864caa7f3da78c66ab499c2abafb7890f38ca
- UNALLOWED findings.order: sha256:b6115fd4b5be23e9e78802927b71db10bee02e58fef745e96715c9b523df61f5 -> sha256:234f9e5e7f1c2248c9aaeb3106f6368bbb6f9becb2da433813d8c314ab92a5c7
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].agent: architecture -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].agent_confidence: sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].attribution[0]: sha256:361e7b1acb6d80d7ef7f8e0aa4204fcebe6a047e57167c83979fbcdb9d37833c -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].attribution[1]: sha256:7d2a878caddd9607bc53d207b7a721b971748c3b78e5dc50f25325c50db20f2e -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].attribution[2]: sha256:96f34c94f7cf7eb0d8a8aadf48980e0ac0d131b90ee50a682424071e25f2f534 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].attribution[3]: sha256:cac9fa20faacbccf6f0e6b780fdfa8793d3bc0773ca4d5b280c4bbe9ac02cac3 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].attribution[4]: sha256:610cb42c95dd518d546a1f6603bb920b2a5e04c6c1514e84e47433dc58102d3a -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].band: critical -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].canonical_line_content: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].category: sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].cwe: sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].fix_hint: sha256:e42fb796ca01b791e33dd54abe03fc8a02e763fb7df16205bf46b8098e7608c8 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].id: sha256:21a98240a7385d1dd9cc9ec512ccf4c433457e6d5c4f0815b361d86ad5818542 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].in_diff: sha256:b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].line: 235 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].agent: architecture -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].agent_confidence: sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].category: sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].cwe: sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].fix_hint: sha256:e42fb796ca01b791e33dd54abe03fc8a02e763fb7df16205bf46b8098e7608c8 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].line: 235 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].problem: sha256:44dd0502ced01d939b5aa5a53392fe0ac7a072607de66a2c23f288413266e5b3 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].source_window[0]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].source_window[1]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].source_window[2]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].source_window[3]: sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].source_window[4]: sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].title: sha256:ca0a74fde3f93cb931153eac36f4c8c74a7c0e8b667e1afd337ec6a6d658d772 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].why_it_matters: sha256:307c9e9c23a07c23f9290aca8104565524d4343cf7a83ccfa4c04a4888418983 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].agent: impact -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].agent_confidence: sha256:48449a14a4ff7d79bb7a1b6f3d488eba397c36ef25634c111b49baf362511afc -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].cwe: sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].fix_hint: sha256:dbe84f078888d217ac84d4f6b2997f193560be755fd31df7505638c533b15058 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].line: 235 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].problem: sha256:a7a581390c403ebcb7b483a44c9df6c6085e0f483c79bd9d8b05f0f3e4be4f5e -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].source_window[0]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].source_window[1]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].source_window[2]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].source_window[3]: sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].source_window[4]: sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].title: sha256:c90bb668ab14a7a42038e77ae35f950e4b6104b847342f2d178edc1c76dfb261 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].why_it_matters: sha256:0b03bea6bf7e36e29d6ca1ee24c65241f355b198400dea7bec0d057294b9a63c -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].agent: security -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].agent_confidence: sha256:349c41201b62db851192665c504b350ff98c6b45fb62a8a2161f78b6534d8de9 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].category: sha256:8cc5192684865079dea813dcf1f24a4cac21e0e4174cc4e30a1460c44a643178 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].cwe: sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].fix_hint: sha256:9fc97451724761cefdb61715dd9c47754ffb5924cac9f196cb89adf6f2257654 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].line: 233 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].problem: sha256:3ed8125cdb4f68eb0b1e809eb3e66cfa961e5a79f93ac73f8d633e0961c230dc -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].source_window[0]: sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].source_window[1]: sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].source_window[2]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].source_window[3]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].source_window[4]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].title: sha256:e56e7be97a7a90821b9ff114081fdfa4eba1efc570ce2d374af0409757f13daf -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].why_it_matters: sha256:70359cecd8888cd23a5ff05302f638a9c7e1544e9b3fec1d5917abc626950343 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].agent: codex-adversarial -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].agent_confidence: sha256:ad57366865126e55649ecb23ae1d48887544976efea46a48eb5d85a6eeb4d306 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].category: sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].fix_hint: sha256:26dc33819d47a215d15a3cacd2769312e97b9f47f9cabae63314f36df94a10df -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].line: 233 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].problem: sha256:30c79070b89bc6b5195744bc92ca9025b2671c9823211270d400bddcbb40d79a -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].severity: sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].source_window[0]: sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].source_window[1]: sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].source_window[2]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].source_window[3]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].source_window[4]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].title: sha256:245cb7ecccfa3c07882f094abbebd77d54ea9526ea1ce72442b3f54fddbefe61 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].why_it_matters: sha256:30c79070b89bc6b5195744bc92ca9025b2671c9823211270d400bddcbb40d79a -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].agent: bugs -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].agent_confidence: sha256:d59eced1ded07f84c145592f65bdf854358e009c5cd705f5215bf18697fed103 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].category: sha256:3ef24481f8d08db74d73b250d8b5c5e8e3fdc9b6bcd339f6a6599529ce338a42 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].fix_hint: sha256:de766f7f501374adc78ddea6e80dfff4c94c78f7f7a8f540c94d79b7c61ad40e -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].line: 235 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].problem: sha256:92bd7c86b1c514d180444b96eb54a9188a7483200ae7b9b3f4690924aea798e4 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].severity: sha256:364bb7082249ee9fbc5247ee49735c4246f271b82c2745a35107ddda0d7cabcc -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].title: sha256:b1c3004018b07b1ba2835a97d3c3a52d9fc4d6bf7690c3488d42b9d372c36df2 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].why_it_matters: sha256:da5a66bdeb82e514018d98ca3163d90769f300161850e602d9a8c992a5f10f96 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].orchestrator_score: 100 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].problem: sha256:44dd0502ced01d939b5aa5a53392fe0ac7a072607de66a2c23f288413266e5b3 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].silenced_marker_nearby: sha256:fcbcf165908dd18a9e49f7ff27810176db8e9f63b4352213741664245224f8aa -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].snapshot.at_pass: 1 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].snapshot.band: critical -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].snapshot.canonical_line_content: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].snapshot.file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].snapshot.line: 235 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].source_window[0]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].source_window[1]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].source_window[2]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].source_window[3]: sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].source_window[4]: sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].stable_hash: sha256:1c6899874fd5e0f1cb3c6fad9250e9f31a4484789907dd390caa01adb836053d -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].status: new -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].title: sha256:ca0a74fde3f93cb931153eac36f4c8c74a7c0e8b667e1afd337ec6a6d658d772 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].why_it_matters: sha256:307c9e9c23a07c23f9290aca8104565524d4343cf7a83ccfa4c04a4888418983 -> (absent)
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].agent: (absent) -> security
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].agent_confidence: (absent) -> sha256:349c41201b62db851192665c504b350ff98c6b45fb62a8a2161f78b6534d8de9
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].attribution[0]: (absent) -> sha256:361e7b1acb6d80d7ef7f8e0aa4204fcebe6a047e57167c83979fbcdb9d37833c
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].attribution[1]: (absent) -> sha256:7d2a878caddd9607bc53d207b7a721b971748c3b78e5dc50f25325c50db20f2e
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].attribution[2]: (absent) -> sha256:96f34c94f7cf7eb0d8a8aadf48980e0ac0d131b90ee50a682424071e25f2f534
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].attribution[3]: (absent) -> sha256:cac9fa20faacbccf6f0e6b780fdfa8793d3bc0773ca4d5b280c4bbe9ac02cac3
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].attribution[4]: (absent) -> sha256:610cb42c95dd518d546a1f6603bb920b2a5e04c6c1514e84e47433dc58102d3a
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].band: (absent) -> critical
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].canonical_line_content: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].category: (absent) -> sha256:8cc5192684865079dea813dcf1f24a4cac21e0e4174cc4e30a1460c44a643178
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].current_code: (absent) -> sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].cwe: (absent) -> sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].fix_hint: (absent) -> sha256:9fc97451724761cefdb61715dd9c47754ffb5924cac9f196cb89adf6f2257654
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].id: (absent) -> sha256:9287869e1b50080b0e190d73e552d15b5b2ccd6e50ecc62725efb307d9540efe
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].in_diff: (absent) -> sha256:b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].line: (absent) -> 233
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].agent: (absent) -> security
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].agent_confidence: (absent) -> sha256:349c41201b62db851192665c504b350ff98c6b45fb62a8a2161f78b6534d8de9
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].category: (absent) -> sha256:8cc5192684865079dea813dcf1f24a4cac21e0e4174cc4e30a1460c44a643178
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].current_code: (absent) -> sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].cwe: (absent) -> sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].fix_hint: (absent) -> sha256:9fc97451724761cefdb61715dd9c47754ffb5924cac9f196cb89adf6f2257654
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].line: (absent) -> 233
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].problem: (absent) -> sha256:3ed8125cdb4f68eb0b1e809eb3e66cfa961e5a79f93ac73f8d633e0961c230dc
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].source_window[0]: (absent) -> sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].source_window[1]: (absent) -> sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].source_window[2]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].source_window[3]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].source_window[4]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].title: (absent) -> sha256:e56e7be97a7a90821b9ff114081fdfa4eba1efc570ce2d374af0409757f13daf
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].why_it_matters: (absent) -> sha256:70359cecd8888cd23a5ff05302f638a9c7e1544e9b3fec1d5917abc626950343
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].agent: (absent) -> codex-adversarial
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].agent_confidence: (absent) -> sha256:ad57366865126e55649ecb23ae1d48887544976efea46a48eb5d85a6eeb4d306
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].category: (absent) -> sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].fix_hint: (absent) -> sha256:26dc33819d47a215d15a3cacd2769312e97b9f47f9cabae63314f36df94a10df
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].line: (absent) -> 233
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].problem: (absent) -> sha256:30c79070b89bc6b5195744bc92ca9025b2671c9823211270d400bddcbb40d79a
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].severity: (absent) -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].source_window[0]: (absent) -> sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].source_window[1]: (absent) -> sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].source_window[2]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].source_window[3]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].source_window[4]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].title: (absent) -> sha256:245cb7ecccfa3c07882f094abbebd77d54ea9526ea1ce72442b3f54fddbefe61
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].why_it_matters: (absent) -> sha256:30c79070b89bc6b5195744bc92ca9025b2671c9823211270d400bddcbb40d79a
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].agent: (absent) -> architecture
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].agent_confidence: (absent) -> sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].category: (absent) -> sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].current_code: (absent) -> sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].cwe: (absent) -> sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].fix_hint: (absent) -> sha256:e42fb796ca01b791e33dd54abe03fc8a02e763fb7df16205bf46b8098e7608c8
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].line: (absent) -> 235
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].problem: (absent) -> sha256:44dd0502ced01d939b5aa5a53392fe0ac7a072607de66a2c23f288413266e5b3
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].source_window[0]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].source_window[1]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].source_window[2]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].source_window[3]: (absent) -> sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].source_window[4]: (absent) -> sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].title: (absent) -> sha256:ca0a74fde3f93cb931153eac36f4c8c74a7c0e8b667e1afd337ec6a6d658d772
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].why_it_matters: (absent) -> sha256:307c9e9c23a07c23f9290aca8104565524d4343cf7a83ccfa4c04a4888418983
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].agent: (absent) -> impact
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].agent_confidence: (absent) -> sha256:48449a14a4ff7d79bb7a1b6f3d488eba397c36ef25634c111b49baf362511afc
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].category: (absent) -> sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].current_code: (absent) -> sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].cwe: (absent) -> sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].fix_hint: (absent) -> sha256:dbe84f078888d217ac84d4f6b2997f193560be755fd31df7505638c533b15058
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].line: (absent) -> 235
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].problem: (absent) -> sha256:a7a581390c403ebcb7b483a44c9df6c6085e0f483c79bd9d8b05f0f3e4be4f5e
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].source_window[0]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].source_window[1]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].source_window[2]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].source_window[3]: (absent) -> sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].source_window[4]: (absent) -> sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].title: (absent) -> sha256:c90bb668ab14a7a42038e77ae35f950e4b6104b847342f2d178edc1c76dfb261
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].why_it_matters: (absent) -> sha256:0b03bea6bf7e36e29d6ca1ee24c65241f355b198400dea7bec0d057294b9a63c
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].agent: (absent) -> bugs
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].agent_confidence: (absent) -> sha256:d59eced1ded07f84c145592f65bdf854358e009c5cd705f5215bf18697fed103
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].category: (absent) -> sha256:3ef24481f8d08db74d73b250d8b5c5e8e3fdc9b6bcd339f6a6599529ce338a42
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].current_code: (absent) -> sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].fix_hint: (absent) -> sha256:de766f7f501374adc78ddea6e80dfff4c94c78f7f7a8f540c94d79b7c61ad40e
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].line: (absent) -> 235
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].problem: (absent) -> sha256:92bd7c86b1c514d180444b96eb54a9188a7483200ae7b9b3f4690924aea798e4
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].severity: (absent) -> sha256:364bb7082249ee9fbc5247ee49735c4246f271b82c2745a35107ddda0d7cabcc
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].title: (absent) -> sha256:b1c3004018b07b1ba2835a97d3c3a52d9fc4d6bf7690c3488d42b9d372c36df2
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].why_it_matters: (absent) -> sha256:da5a66bdeb82e514018d98ca3163d90769f300161850e602d9a8c992a5f10f96
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].orchestrator_score: (absent) -> 100
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].problem: (absent) -> sha256:3ed8125cdb4f68eb0b1e809eb3e66cfa961e5a79f93ac73f8d633e0961c230dc
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].silenced_marker_nearby: (absent) -> sha256:fcbcf165908dd18a9e49f7ff27810176db8e9f63b4352213741664245224f8aa
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].snapshot.at_pass: (absent) -> 1
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].snapshot.band: (absent) -> critical
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].snapshot.canonical_line_content: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].snapshot.file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].snapshot.line: (absent) -> 233
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].source_window[0]: (absent) -> sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].source_window[1]: (absent) -> sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].source_window[2]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].source_window[3]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].source_window[4]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].stable_hash: (absent) -> sha256:04b5c3d7d2eb6ecf1d00e55ad86893f14969ba2ddb343e82d07e69bb459996d7
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].status: (absent) -> new
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].title: (absent) -> sha256:e56e7be97a7a90821b9ff114081fdfa4eba1efc570ce2d374af0409757f13daf
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].why_it_matters: (absent) -> sha256:70359cecd8888cd23a5ff05302f638a9c7e1544e9b3fec1d5917abc626950343

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| architecture | triggarr/clients/base.py | 235 | critical | 100 | 1c3fbec96c05 |
| security | triggarr/clients/base.py | 252 | warning | 94 | c9cb8e9eb043 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| security | triggarr/clients/base.py | 233 | critical | 100 | a3152fbf25ef |
| security | triggarr/clients/base.py | 252 | warning | 94 | c9cb8e9eb043 |

## runs-v2.10-phase40/final/triggarr-secret-in-logs/run-1

changed paths: 301
allowed: no

- UNALLOWED filtered[0].reason: sha256:7db00e3028fec2ac766e4dc45711a3e90063329a54057b01e9264d7020c545cb -> sha256:32828f37f1e3b02eb636bf6f09675311db5bb5aa37535cba5110dc89248e5743
- UNALLOWED filtered[0].title: sha256:ed591b8471361f9e3a62b9948bb96d861973f39a83fc4379544fc2086b88c051 -> sha256:7a4996f90e7c1bfed81123ff53e9a2f1d3c2380869bcb53e9f761c01350bfac4
- UNALLOWED filtered[1].line: 235 -> 233
- UNALLOWED filtered[1].reason: sha256:7db00e3028fec2ac766e4dc45711a3e90063329a54057b01e9264d7020c545cb -> sha256:32828f37f1e3b02eb636bf6f09675311db5bb5aa37535cba5110dc89248e5743
- UNALLOWED filtered[1].title: sha256:d383512448addab243151c158647cf198c5db151b2d53938bfe9fb5c97076fe9 -> sha256:6bde2a15648b3b231286e4ff79dd29171a00ac1d7f172eb4e79c627690934ced
- UNALLOWED filtered[2].line: 233 -> 235
- UNALLOWED filtered[2].reason: sha256:7db00e3028fec2ac766e4dc45711a3e90063329a54057b01e9264d7020c545cb -> sha256:32828f37f1e3b02eb636bf6f09675311db5bb5aa37535cba5110dc89248e5743
- UNALLOWED filtered[2].title: sha256:7a4996f90e7c1bfed81123ff53e9a2f1d3c2380869bcb53e9f761c01350bfac4 -> sha256:d383512448addab243151c158647cf198c5db151b2d53938bfe9fb5c97076fe9
- UNALLOWED filtered[3].line: 233 -> 235
- UNALLOWED filtered[3].reason: sha256:7db00e3028fec2ac766e4dc45711a3e90063329a54057b01e9264d7020c545cb -> sha256:32828f37f1e3b02eb636bf6f09675311db5bb5aa37535cba5110dc89248e5743
- UNALLOWED filtered[3].title: sha256:6bde2a15648b3b231286e4ff79dd29171a00ac1d7f172eb4e79c627690934ced -> sha256:aed2ae2e8f0e452508f3549fda11e4fbf2cd686f46cb49b4769aceee5447014b
- UNALLOWED filtered[4].reason: sha256:7db00e3028fec2ac766e4dc45711a3e90063329a54057b01e9264d7020c545cb -> sha256:32828f37f1e3b02eb636bf6f09675311db5bb5aa37535cba5110dc89248e5743
- UNALLOWED findings.order: sha256:f4682b807835e174fcff9fb484d8dcc0c70883da8c9a1f5b5dda9ac40b6964bb -> sha256:983ef760437911371f03d02466cee9bdb9ecc72d3074ba3630acbbdf0dab171a
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].agent: architecture -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].agent_confidence: sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].attribution[0]: sha256:610cb42c95dd518d546a1f6603bb920b2a5e04c6c1514e84e47433dc58102d3a -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].attribution[1]: sha256:361e7b1acb6d80d7ef7f8e0aa4204fcebe6a047e57167c83979fbcdb9d37833c -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].attribution[2]: sha256:7d2a878caddd9607bc53d207b7a721b971748c3b78e5dc50f25325c50db20f2e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].attribution[3]: sha256:96f34c94f7cf7eb0d8a8aadf48980e0ac0d131b90ee50a682424071e25f2f534 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].attribution[4]: sha256:cb5935d87ff4757894d82d38506c9bc11df4c9ab49e15d1f00e6b17d1a417323 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].attribution[5]: sha256:cac9fa20faacbccf6f0e6b780fdfa8793d3bc0773ca4d5b280c4bbe9ac02cac3 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].band: critical -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].canonical_line_content: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].category: sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].fix_hint: sha256:585a09161f897e48ca627923fc58a6e0d8835888b65be042c306c147cd703f86 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].id: sha256:6543fd3c27156b114308e3810833757733001eddf92393c23326f702f9423402 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].in_diff: sha256:b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].line: 235 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].agent: architecture -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].agent_confidence: sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].category: sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].fix_hint: sha256:585a09161f897e48ca627923fc58a6e0d8835888b65be042c306c147cd703f86 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].line: 235 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].problem: sha256:de2cae87594ffeaae16753e22d0bde0edef104d52f333eba6ad1e07ebdc7a243 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].source_window[0]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].source_window[1]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].source_window[2]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].source_window[3]: sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].source_window[4]: sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].title: sha256:aed2ae2e8f0e452508f3549fda11e4fbf2cd686f46cb49b4769aceee5447014b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].why_it_matters: sha256:0d9f82c2ca8bdcc1e992efdf17918240efa21ce8b8d7e35ca9b4e8438b7ead0e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].agent: codex-adversarial -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].agent_confidence: sha256:ad57366865126e55649ecb23ae1d48887544976efea46a48eb5d85a6eeb4d306 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].category: sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].current_code: sha256:01c5ac1b042ce1cdb4dfaae6267cddb670969678b8b8c3927ef632afbb39e683 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].fix_hint: sha256:be30427871e21fea470a0b4f5a6de681c52c4c1dc2e68a1d2e1235367b3edcab -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].line: 233 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].problem: sha256:8178e03ec1855d69045294e6e688f9a18d402ed065323104862b9ab973a56d39 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].severity: sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].source_window[0]: sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].source_window[1]: sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].source_window[2]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].source_window[3]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].source_window[4]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].title: sha256:ed591b8471361f9e3a62b9948bb96d861973f39a83fc4379544fc2086b88c051 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].why_it_matters: sha256:8178e03ec1855d69045294e6e688f9a18d402ed065323104862b9ab973a56d39 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].agent: compliance -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].agent_confidence: sha256:ad48ff99415b2f007dc35b7eb553fd1eb35ebfa2f2f308acd9488eeb86f71fa8 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].category: sha256:df9420b6c4d136a808026d388318d24387a18cd204153c572e9c982b693864b9 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].current_code: sha256:f388cdae836776ffa643b71656544d68c603097a25f08f9154aeb2d84d7bb380 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].cwe: sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].fix_hint: sha256:50865b2a1a98a0259a7870dbd397508782cc924986d3e8ae83f71ef5cda7e19f -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].line: 235 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].problem: sha256:51a54239150e175a430bf99181f6ccf5ae9658f0279b0aaf2f2c15c1725147f0 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].severity: sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].source_window[0]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].source_window[1]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].source_window[2]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].source_window[3]: sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].source_window[4]: sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].title: sha256:d383512448addab243151c158647cf198c5db151b2d53938bfe9fb5c97076fe9 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].why_it_matters: sha256:e5b07fe5f1356c4d9caeaa18157f9a2d08132584673848a27892b24424fc2f16 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].agent: impact -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].agent_confidence: sha256:48449a14a4ff7d79bb7a1b6f3d488eba397c36ef25634c111b49baf362511afc -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].cwe: sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].fix_hint: sha256:e7e5a994add79c48b1ab28da0836e6c9cae7578e7f77b7ed26e853f58e20cdf6 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].line: 233 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].problem: sha256:626c16ba4d0ccbec689002de30be2323f3e4e5488053ce3e79a5fcf01219e9a1 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].source_window[0]: sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].source_window[1]: sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].source_window[2]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].source_window[3]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].source_window[4]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].title: sha256:7a4996f90e7c1bfed81123ff53e9a2f1d3c2380869bcb53e9f761c01350bfac4 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].why_it_matters: sha256:a633af169a857b6816ad2243120a7812bf60fdcc4e0e5f9acdf456d75147ed8b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].agent: security -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].agent_confidence: sha256:8241649609f88ccd2a0a5b233a07a538ec313ff6adf695aa44a969dbca39f67d -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].category: sha256:8cc5192684865079dea813dcf1f24a4cac21e0e4174cc4e30a1460c44a643178 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].cwe: sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].fix_hint: sha256:af36d18a3c5834c0f55359f08404c9785a9d9fec13dad129f13385311ac974bd -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].line: 233 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].problem: sha256:7f419a5b210ca56d4213b2e0f9f11975b12ab4e7ce8e03738b0a5d290a9a29c3 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].source_window[0]: sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].source_window[1]: sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].source_window[2]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].source_window[3]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].source_window[4]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].title: sha256:6bde2a15648b3b231286e4ff79dd29171a00ac1d7f172eb4e79c627690934ced -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].why_it_matters: sha256:09fc6f1788932b6d6389891dcf25831396d13ab44363eea6d115665d62e5e0f0 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].agent: bugs -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].agent_confidence: sha256:ff5a1ae012afa5d4c889c50ad427aaf545d31a4fac04ffc1c4d03d403ba4250a -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].fix_hint: sha256:e1bb1d26fd064a5fa1f3857c70bbd40b05ff686661c0d30c2e24cdcdb8b4e283 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].line: 233 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].problem: sha256:b14dac70a8e1462dfaae0d0e4689b4e64c33c79752e4680a8590ee8d02a12cf1 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].source_window[0]: sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].source_window[1]: sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].source_window[2]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].source_window[3]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].source_window[4]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].title: sha256:4497669488b56d56461a8b64374f3391dfcfdcd493fd99985ad6e4f67b8d4ca3 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].why_it_matters: sha256:b6affb995a32a7a8c4d4e1089862ddd3ad40b7f5e5e40c3f9f5f745de028a4b4 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].orchestrator_score: 100 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].problem: sha256:de2cae87594ffeaae16753e22d0bde0edef104d52f333eba6ad1e07ebdc7a243 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].silenced_marker_nearby: sha256:fcbcf165908dd18a9e49f7ff27810176db8e9f63b4352213741664245224f8aa -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].snapshot.at_pass: 1 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].snapshot.band: critical -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].snapshot.canonical_line_content: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].snapshot.file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].snapshot.line: 235 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].source_window[0]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].source_window[1]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].source_window[2]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].source_window[3]: sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].source_window[4]: sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].stable_hash: sha256:6c05754589c3b691b44555c1692200deac78bf55cab53a9e8d7cd69c95f85f1a -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].status: new -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].title: sha256:aed2ae2e8f0e452508f3549fda11e4fbf2cd686f46cb49b4769aceee5447014b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].why_it_matters: sha256:0d9f82c2ca8bdcc1e992efdf17918240efa21ce8b8d7e35ca9b4e8438b7ead0e -> (absent)
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].agent: (absent) -> codex-adversarial
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].agent_confidence: (absent) -> sha256:ad57366865126e55649ecb23ae1d48887544976efea46a48eb5d85a6eeb4d306
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].attribution[0]: (absent) -> sha256:610cb42c95dd518d546a1f6603bb920b2a5e04c6c1514e84e47433dc58102d3a
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].attribution[1]: (absent) -> sha256:361e7b1acb6d80d7ef7f8e0aa4204fcebe6a047e57167c83979fbcdb9d37833c
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].attribution[2]: (absent) -> sha256:7d2a878caddd9607bc53d207b7a721b971748c3b78e5dc50f25325c50db20f2e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].attribution[3]: (absent) -> sha256:96f34c94f7cf7eb0d8a8aadf48980e0ac0d131b90ee50a682424071e25f2f534
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].attribution[4]: (absent) -> sha256:cb5935d87ff4757894d82d38506c9bc11df4c9ab49e15d1f00e6b17d1a417323
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].attribution[5]: (absent) -> sha256:cac9fa20faacbccf6f0e6b780fdfa8793d3bc0773ca4d5b280c4bbe9ac02cac3
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].band: (absent) -> critical
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].canonical_line_content: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].category: (absent) -> sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].current_code: (absent) -> sha256:01c5ac1b042ce1cdb4dfaae6267cddb670969678b8b8c3927ef632afbb39e683
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].fix_hint: (absent) -> sha256:be30427871e21fea470a0b4f5a6de681c52c4c1dc2e68a1d2e1235367b3edcab
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].id: (absent) -> sha256:73ca1c8c1b1765028ee41138e76ea51dc55c913de8ba80028c40cedfc30b6369
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].line: (absent) -> 233
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].agent: (absent) -> codex-adversarial
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].agent_confidence: (absent) -> sha256:ad57366865126e55649ecb23ae1d48887544976efea46a48eb5d85a6eeb4d306
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].category: (absent) -> sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].current_code: (absent) -> sha256:01c5ac1b042ce1cdb4dfaae6267cddb670969678b8b8c3927ef632afbb39e683
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].fix_hint: (absent) -> sha256:be30427871e21fea470a0b4f5a6de681c52c4c1dc2e68a1d2e1235367b3edcab
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].line: (absent) -> 233
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].problem: (absent) -> sha256:8178e03ec1855d69045294e6e688f9a18d402ed065323104862b9ab973a56d39
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].severity: (absent) -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].source_window[0]: (absent) -> sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].source_window[1]: (absent) -> sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].source_window[2]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].source_window[3]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].source_window[4]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].title: (absent) -> sha256:ed591b8471361f9e3a62b9948bb96d861973f39a83fc4379544fc2086b88c051
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].why_it_matters: (absent) -> sha256:8178e03ec1855d69045294e6e688f9a18d402ed065323104862b9ab973a56d39
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].agent: (absent) -> impact
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].agent_confidence: (absent) -> sha256:48449a14a4ff7d79bb7a1b6f3d488eba397c36ef25634c111b49baf362511afc
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].category: (absent) -> sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].current_code: (absent) -> sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].cwe: (absent) -> sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].fix_hint: (absent) -> sha256:e7e5a994add79c48b1ab28da0836e6c9cae7578e7f77b7ed26e853f58e20cdf6
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].line: (absent) -> 233
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].problem: (absent) -> sha256:626c16ba4d0ccbec689002de30be2323f3e4e5488053ce3e79a5fcf01219e9a1
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].source_window[0]: (absent) -> sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].source_window[1]: (absent) -> sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].source_window[2]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].source_window[3]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].source_window[4]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].title: (absent) -> sha256:7a4996f90e7c1bfed81123ff53e9a2f1d3c2380869bcb53e9f761c01350bfac4
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].why_it_matters: (absent) -> sha256:a633af169a857b6816ad2243120a7812bf60fdcc4e0e5f9acdf456d75147ed8b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].agent: (absent) -> security
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].agent_confidence: (absent) -> sha256:8241649609f88ccd2a0a5b233a07a538ec313ff6adf695aa44a969dbca39f67d
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].category: (absent) -> sha256:8cc5192684865079dea813dcf1f24a4cac21e0e4174cc4e30a1460c44a643178
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].current_code: (absent) -> sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].cwe: (absent) -> sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].fix_hint: (absent) -> sha256:af36d18a3c5834c0f55359f08404c9785a9d9fec13dad129f13385311ac974bd
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].line: (absent) -> 233
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].problem: (absent) -> sha256:7f419a5b210ca56d4213b2e0f9f11975b12ab4e7ce8e03738b0a5d290a9a29c3
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].source_window[0]: (absent) -> sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].source_window[1]: (absent) -> sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].source_window[2]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].source_window[3]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].source_window[4]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].title: (absent) -> sha256:6bde2a15648b3b231286e4ff79dd29171a00ac1d7f172eb4e79c627690934ced
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].why_it_matters: (absent) -> sha256:09fc6f1788932b6d6389891dcf25831396d13ab44363eea6d115665d62e5e0f0
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].agent: (absent) -> compliance
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].agent_confidence: (absent) -> sha256:ad48ff99415b2f007dc35b7eb553fd1eb35ebfa2f2f308acd9488eeb86f71fa8
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].category: (absent) -> sha256:df9420b6c4d136a808026d388318d24387a18cd204153c572e9c982b693864b9
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].current_code: (absent) -> sha256:f388cdae836776ffa643b71656544d68c603097a25f08f9154aeb2d84d7bb380
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].cwe: (absent) -> sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].fix_hint: (absent) -> sha256:50865b2a1a98a0259a7870dbd397508782cc924986d3e8ae83f71ef5cda7e19f
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].line: (absent) -> 235
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].problem: (absent) -> sha256:51a54239150e175a430bf99181f6ccf5ae9658f0279b0aaf2f2c15c1725147f0
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].severity: (absent) -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].source_window[0]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].source_window[1]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].source_window[2]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].source_window[3]: (absent) -> sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].source_window[4]: (absent) -> sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].title: (absent) -> sha256:d383512448addab243151c158647cf198c5db151b2d53938bfe9fb5c97076fe9
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].why_it_matters: (absent) -> sha256:e5b07fe5f1356c4d9caeaa18157f9a2d08132584673848a27892b24424fc2f16
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].agent: (absent) -> architecture
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].agent_confidence: (absent) -> sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].category: (absent) -> sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].current_code: (absent) -> sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].fix_hint: (absent) -> sha256:585a09161f897e48ca627923fc58a6e0d8835888b65be042c306c147cd703f86
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].line: (absent) -> 235
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].problem: (absent) -> sha256:de2cae87594ffeaae16753e22d0bde0edef104d52f333eba6ad1e07ebdc7a243
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].source_window[0]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].source_window[1]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].source_window[2]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].source_window[3]: (absent) -> sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].source_window[4]: (absent) -> sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].title: (absent) -> sha256:aed2ae2e8f0e452508f3549fda11e4fbf2cd686f46cb49b4769aceee5447014b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].why_it_matters: (absent) -> sha256:0d9f82c2ca8bdcc1e992efdf17918240efa21ce8b8d7e35ca9b4e8438b7ead0e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].agent: (absent) -> bugs
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].agent_confidence: (absent) -> sha256:ff5a1ae012afa5d4c889c50ad427aaf545d31a4fac04ffc1c4d03d403ba4250a
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].category: (absent) -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].current_code: (absent) -> sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].fix_hint: (absent) -> sha256:e1bb1d26fd064a5fa1f3857c70bbd40b05ff686661c0d30c2e24cdcdb8b4e283
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].line: (absent) -> 233
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].problem: (absent) -> sha256:b14dac70a8e1462dfaae0d0e4689b4e64c33c79752e4680a8590ee8d02a12cf1
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].source_window[0]: (absent) -> sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].source_window[1]: (absent) -> sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].source_window[2]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].source_window[3]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].source_window[4]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].title: (absent) -> sha256:4497669488b56d56461a8b64374f3391dfcfdcd493fd99985ad6e4f67b8d4ca3
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].why_it_matters: (absent) -> sha256:b6affb995a32a7a8c4d4e1089862ddd3ad40b7f5e5e40c3f9f5f745de028a4b4
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].orchestrator_score: (absent) -> 100
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].problem: (absent) -> sha256:8178e03ec1855d69045294e6e688f9a18d402ed065323104862b9ab973a56d39
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].severity: (absent) -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].snapshot.at_pass: (absent) -> 1
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].snapshot.band: (absent) -> critical
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].snapshot.canonical_line_content: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].snapshot.file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].snapshot.line: (absent) -> 233
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].source_window[0]: (absent) -> sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].source_window[1]: (absent) -> sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].source_window[2]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].source_window[3]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].source_window[4]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].stable_hash: (absent) -> sha256:8cd676b0e27a11b6da8f70c87ee7fa7180714fc658118d726711c85594bdd1a4
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].status: (absent) -> new
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].title: (absent) -> sha256:ed591b8471361f9e3a62b9948bb96d861973f39a83fc4379544fc2086b88c051
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].why_it_matters: (absent) -> sha256:8178e03ec1855d69045294e6e688f9a18d402ed065323104862b9ab973a56d39

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| architecture | triggarr/clients/base.py | 235 | critical | 100 | 5a47a4976122 |
| compliance | triggarr/clients/base.py | 254 | warning | 94 | 0fd15b2ec9c1 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 233 | critical | 100 | 8f4d653e7115 |
| compliance | triggarr/clients/base.py | 254 | warning | 94 | 0fd15b2ec9c1 |

## runs-v2.10-phase43/first/should-quiet-4/run-2

changed paths: 3
allowed: yes

- findings[de932df74922916070143f8ba95b7766ef1b218f58b1d2f8375e96ddec9e3b8b].band: critical -> warning
- findings[de932df74922916070143f8ba95b7766ef1b218f58b1d2f8375e96ddec9e3b8b].orchestrator_score: 100 -> 94
- findings[de932df74922916070143f8ba95b7766ef1b218f58b1d2f8375e96ddec9e3b8b].snapshot.band: critical -> warning

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 107 | critical | 100 | de932df74922 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 107 | warning | 94 | de932df74922 |

## runs-v2.10-phase43/first/should-quiet-4/run-3

changed paths: 3
allowed: no

- UNALLOWED findings[fedecf9ededf1e6479cf584ae95303d7b3633e48e779d0c41d33ecf9cb4dfd39].band: critical -> warning
- UNALLOWED findings[fedecf9ededf1e6479cf584ae95303d7b3633e48e779d0c41d33ecf9cb4dfd39].orchestrator_score: 100 -> 94
- UNALLOWED findings[fedecf9ededf1e6479cf584ae95303d7b3633e48e779d0c41d33ecf9cb4dfd39].snapshot.band: critical -> warning

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 107 | critical | 100 | fedecf9ededf |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 107 | warning | 94 | fedecf9ededf |

## runs-v2.10-phase43/first/should-quiet-6/run-1

changed paths: 3
allowed: yes

- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].band: critical -> warning
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].orchestrator_score: 100 -> 94
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].snapshot.band: critical -> warning

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | critical | 100 | c93be6bfe251 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | warning | 94 | c93be6bfe251 |

## runs-v2.10-phase43/first/should-quiet-6/run-2

changed paths: 28
allowed: no

- UNALLOWED filtered[4].title: sha256:95a116e293ee571c98f0a790d55acbe42819a2899b2953546e3f80f02058ca67 -> sha256:5fbdcde1f4fe76b94e2f5983f4c7d1b2a33f11c66b836ba41f63cce915ab0949
- UNALLOWED filtered[5].title: sha256:5fbdcde1f4fe76b94e2f5983f4c7d1b2a33f11c66b836ba41f63cce915ab0949 -> sha256:95a116e293ee571c98f0a790d55acbe42819a2899b2953546e3f80f02058ca67
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].agent: impact -> architecture
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].agent_confidence: sha256:624b60c58c9d8bfb6ff1886c2fd605d2adeb6ea4da576068201b6c6958ce93f4 -> sha256:811786ad1ae74adfdd20dd0372abaaebc6246e343aebd01da0bfc4c02bf0106c
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].fix_hint: sha256:214eeab3bb5747661e213a6da286d096188b24b25e889b84fa755bc4322235ea -> sha256:851b79fc72fdb873007d03295326017857709884e1f23a96a2e8001724b35e3d
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].intent_doc_match: sha256:b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b -> (absent)
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].intent_doc_match.confidence: (absent) -> sha256:1e9d7c27c8bbc8ddf0055c93e064a62fa995d177fee28cc8fa949bc8a4db06f4
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].intent_doc_match.doc: (absent) -> sha256:2da16962ed90531c876536115ad838630da9f394ebb78961727d213fda9d1d02
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].intent_doc_match.quote: (absent) -> sha256:f854b75460a280aa5fcadec554cddb20f20c30acee932b9384e4966b06231d83
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].intent_doc_match.section: (absent) -> sha256:66f183ee8bf4b6b74d436aeed6d057b9fa506a617c35cda924a3f79c11c171d0
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].problem: sha256:a1cba18ed65962be408df88dabcbee7cb316c92630301d091034fdd1068c3d97 -> sha256:27598c58e13c44dd663ac77c5fd8d37955daac2dab21e6fb697d6311287b7c35
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].severity: sha256:364bb7082249ee9fbc5247ee49735c4246f271b82c2745a35107ddda0d7cabcc -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].title: sha256:95a116e293ee571c98f0a790d55acbe42819a2899b2953546e3f80f02058ca67 -> sha256:5fbdcde1f4fe76b94e2f5983f4c7d1b2a33f11c66b836ba41f63cce915ab0949
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].why_it_matters: sha256:ad2170918fb9d6a0b0a0ce40dd9bf86fe5c30d17c56b851dcc4caf7eec5b3e51 -> sha256:912aef3f36a67c121f6572591aabfb8e10111404f02394f9f658d0c2bbc347bf
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].agent: architecture -> impact
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].agent_confidence: sha256:811786ad1ae74adfdd20dd0372abaaebc6246e343aebd01da0bfc4c02bf0106c -> sha256:624b60c58c9d8bfb6ff1886c2fd605d2adeb6ea4da576068201b6c6958ce93f4
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].category: sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2 -> sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].fix_hint: sha256:851b79fc72fdb873007d03295326017857709884e1f23a96a2e8001724b35e3d -> sha256:214eeab3bb5747661e213a6da286d096188b24b25e889b84fa755bc4322235ea
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].intent_doc_match: (absent) -> sha256:b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].intent_doc_match.confidence: sha256:1e9d7c27c8bbc8ddf0055c93e064a62fa995d177fee28cc8fa949bc8a4db06f4 -> (absent)
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].intent_doc_match.doc: sha256:2da16962ed90531c876536115ad838630da9f394ebb78961727d213fda9d1d02 -> (absent)
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].intent_doc_match.quote: sha256:f854b75460a280aa5fcadec554cddb20f20c30acee932b9384e4966b06231d83 -> (absent)
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].intent_doc_match.section: sha256:66f183ee8bf4b6b74d436aeed6d057b9fa506a617c35cda924a3f79c11c171d0 -> (absent)
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].problem: sha256:27598c58e13c44dd663ac77c5fd8d37955daac2dab21e6fb697d6311287b7c35 -> sha256:a1cba18ed65962be408df88dabcbee7cb316c92630301d091034fdd1068c3d97
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> sha256:364bb7082249ee9fbc5247ee49735c4246f271b82c2745a35107ddda0d7cabcc
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].title: sha256:5fbdcde1f4fe76b94e2f5983f4c7d1b2a33f11c66b836ba41f63cce915ab0949 -> sha256:95a116e293ee571c98f0a790d55acbe42819a2899b2953546e3f80f02058ca67
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].why_it_matters: sha256:912aef3f36a67c121f6572591aabfb8e10111404f02394f9f658d0c2bbc347bf -> sha256:ad2170918fb9d6a0b0a0ce40dd9bf86fe5c30d17c56b851dcc4caf7eec5b3e51

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | critical | 100 | 92e9bcdf8831 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | critical | 100 | 92e9bcdf8831 |

## runs-v2.10-phase43/first/should-quiet-6/run-3

changed paths: 20
allowed: no

- UNALLOWED filtered[2].title: sha256:c10501395451d653c06ed75fd4666a40fe02f61db3e9b493a0ea67c748924453 -> sha256:2730feef10db474145f902e1e55c72cfe5ac987d8f8b0bf2c8f0c2fa1ac756b9
- UNALLOWED filtered[3].title: sha256:2730feef10db474145f902e1e55c72cfe5ac987d8f8b0bf2c8f0c2fa1ac756b9 -> sha256:c10501395451d653c06ed75fd4666a40fe02f61db3e9b493a0ea67c748924453
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].agent: impact -> bugs
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].agent_confidence: sha256:39fa9ec190eee7b6f4dff1100d6343e10918d044c75eac8f9e9a2596173f80c9 -> sha256:02d20bbd7e394ad5999a4cebabac9619732c343a4cac99470c03e23ba2bdc2bc
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].current_code: sha256:bb6973e5ee262da73b7605d3c5597adde7e61b1c2af822f55b4fef0de5256f31 -> sha256:5aa4108a4bb44ec35086473bb2ecf5a6e4a3d3349cb81c22857b28c503b8e094
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].fix_hint: sha256:3dd173238ea39a1be7f4b39b35a38490e7047bba44473257512e6828336651cb -> sha256:2cfb296ef63314e08b1171148d33276d7790100d9e36e45ff0898bd7ecf33c07
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].intent_doc_match: sha256:8ac24611cfe47c129e37108bc6adc6843c4fe8fb9c37c27fac8a1835ba660307 -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].problem: sha256:e4e787215c686defc7a0170ff8b5e4e3382fef92bee490c34742df4138f7da0e -> sha256:ae06da698e19a39cd88067a0ed01e0e21276e956f1e2550fb7ff8164c54170e5
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].title: sha256:c10501395451d653c06ed75fd4666a40fe02f61db3e9b493a0ea67c748924453 -> sha256:2730feef10db474145f902e1e55c72cfe5ac987d8f8b0bf2c8f0c2fa1ac756b9
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].why_it_matters: sha256:630797a5d869ac17de6b0662833df5f782fe9e7419157d8e50998a87171a2c0c -> sha256:4b77b3c1679b88ff111fa4f51a67625274d78a67266139f8880579e43c13298a
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].agent: bugs -> impact
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].agent_confidence: sha256:02d20bbd7e394ad5999a4cebabac9619732c343a4cac99470c03e23ba2bdc2bc -> sha256:39fa9ec190eee7b6f4dff1100d6343e10918d044c75eac8f9e9a2596173f80c9
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].current_code: sha256:5aa4108a4bb44ec35086473bb2ecf5a6e4a3d3349cb81c22857b28c503b8e094 -> sha256:bb6973e5ee262da73b7605d3c5597adde7e61b1c2af822f55b4fef0de5256f31
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].fix_hint: sha256:2cfb296ef63314e08b1171148d33276d7790100d9e36e45ff0898bd7ecf33c07 -> sha256:3dd173238ea39a1be7f4b39b35a38490e7047bba44473257512e6828336651cb
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> sha256:8ac24611cfe47c129e37108bc6adc6843c4fe8fb9c37c27fac8a1835ba660307
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].problem: sha256:ae06da698e19a39cd88067a0ed01e0e21276e956f1e2550fb7ff8164c54170e5 -> sha256:e4e787215c686defc7a0170ff8b5e4e3382fef92bee490c34742df4138f7da0e
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].title: sha256:2730feef10db474145f902e1e55c72cfe5ac987d8f8b0bf2c8f0c2fa1ac756b9 -> sha256:c10501395451d653c06ed75fd4666a40fe02f61db3e9b493a0ea67c748924453
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].why_it_matters: sha256:4b77b3c1679b88ff111fa4f51a67625274d78a67266139f8880579e43c13298a -> sha256:630797a5d869ac17de6b0662833df5f782fe9e7419157d8e50998a87171a2c0c

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | critical | 100 | c93be6bfe251 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | critical | 100 | c93be6bfe251 |

## runs-v2.10-phase43/first/should-quiet-7/run-2

changed paths: 20
allowed: no

- UNALLOWED filtered[2].title: sha256:da080c9b2f8f9e99ce51851fd3234737b6e9a8c1cfc952ba0b6ee2b965fce955 -> sha256:e93a21de80cea63b37750968a2df4fbeab5c573530fa165f4856ba4ad89f731e
- UNALLOWED filtered[3].title: sha256:e93a21de80cea63b37750968a2df4fbeab5c573530fa165f4856ba4ad89f731e -> sha256:da080c9b2f8f9e99ce51851fd3234737b6e9a8c1cfc952ba0b6ee2b965fce955
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[3].agent: impact -> bugs
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[3].agent_confidence: sha256:ff5a1ae012afa5d4c889c50ad427aaf545d31a4fac04ffc1c4d03d403ba4250a -> sha256:02d20bbd7e394ad5999a4cebabac9619732c343a4cac99470c03e23ba2bdc2bc
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[3].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[3].fix_hint: sha256:d7b074f45e4b156b99fda75dcfd303810feb2f2722cfe726598b139e4591b816 -> sha256:033b911eb236ed72912837d1763e236035ae15493e48bf4ba774a315a6b30f96
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[3].intent_doc_match: sha256:8ac24611cfe47c129e37108bc6adc6843c4fe8fb9c37c27fac8a1835ba660307 -> sha256:4266337f59b4a4787c0782e29697114968f6b95b6c6bf946bbacc5dca531716a
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[3].problem: sha256:991dae3ab61ca93d6dfba02f5c1ee8e89425f4d1276bfb58cf249f317140b788 -> sha256:60a0b8795e6771639537639c110a4cc0fb5e0ac47fde15066f9e07e6b19db3ac
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[3].severity: sha256:364bb7082249ee9fbc5247ee49735c4246f271b82c2745a35107ddda0d7cabcc -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[3].title: sha256:da080c9b2f8f9e99ce51851fd3234737b6e9a8c1cfc952ba0b6ee2b965fce955 -> sha256:e93a21de80cea63b37750968a2df4fbeab5c573530fa165f4856ba4ad89f731e
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[3].why_it_matters: sha256:f4984da12370d6d37601a8aaf372ef667d34328008732baeed6c6bb53c947455 -> sha256:ddcbf89346c40a71f5f6d60821de7203bb111538fda47834874d7f71638a05d3
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[4].agent: bugs -> impact
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[4].agent_confidence: sha256:02d20bbd7e394ad5999a4cebabac9619732c343a4cac99470c03e23ba2bdc2bc -> sha256:ff5a1ae012afa5d4c889c50ad427aaf545d31a4fac04ffc1c4d03d403ba4250a
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[4].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[4].fix_hint: sha256:033b911eb236ed72912837d1763e236035ae15493e48bf4ba774a315a6b30f96 -> sha256:d7b074f45e4b156b99fda75dcfd303810feb2f2722cfe726598b139e4591b816
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[4].intent_doc_match: sha256:4266337f59b4a4787c0782e29697114968f6b95b6c6bf946bbacc5dca531716a -> sha256:8ac24611cfe47c129e37108bc6adc6843c4fe8fb9c37c27fac8a1835ba660307
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[4].problem: sha256:60a0b8795e6771639537639c110a4cc0fb5e0ac47fde15066f9e07e6b19db3ac -> sha256:991dae3ab61ca93d6dfba02f5c1ee8e89425f4d1276bfb58cf249f317140b788
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[4].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> sha256:364bb7082249ee9fbc5247ee49735c4246f271b82c2745a35107ddda0d7cabcc
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[4].title: sha256:e93a21de80cea63b37750968a2df4fbeab5c573530fa165f4856ba4ad89f731e -> sha256:da080c9b2f8f9e99ce51851fd3234737b6e9a8c1cfc952ba0b6ee2b965fce955
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[4].why_it_matters: sha256:ddcbf89346c40a71f5f6d60821de7203bb111538fda47834874d7f71638a05d3 -> sha256:f4984da12370d6d37601a8aaf372ef667d34328008732baeed6c6bb53c947455

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/routes.py | 550 | critical | 100 | 234ca986d72e |
| codex-adversarial | triggarr/web/routes.py | 446 | warning | 94 | 30c1d8feff9e |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/routes.py | 550 | critical | 100 | 234ca986d72e |
| codex-adversarial | triggarr/web/routes.py | 446 | warning | 94 | 30c1d8feff9e |

## runs-v2.10-phase43/first/should-quiet-7/run-3

changed paths: 28
allowed: no

- UNALLOWED filtered[4].title: sha256:5ae9fd9eea7bc2153e2931649f7c29bf91a3beec305663c18a6b2c597dda6bb9 -> sha256:9998ce74438d9a1cc9e532fb9feb4c877c8941baea0dc94948f7ed0a07039052
- UNALLOWED filtered[5].title: sha256:9998ce74438d9a1cc9e532fb9feb4c877c8941baea0dc94948f7ed0a07039052 -> sha256:5ae9fd9eea7bc2153e2931649f7c29bf91a3beec305663c18a6b2c597dda6bb9
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].agent: impact -> architecture
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].agent_confidence: sha256:d59eced1ded07f84c145592f65bdf854358e009c5cd705f5215bf18697fed103 -> sha256:9f14025af0065b30e47e23ebb3b491d39ae8ed17d33739e5ff3827ffb3634953
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].current_code: sha256:113b584eb734b1ba06a4814802bf18648ab9620b5a29e05bad737eb5c12a7af3 -> sha256:435b3f5f95d1192d28520727a4401d29f28e4113a82bbc06f36be4b93d727d82
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].fix_hint: sha256:27bedc07b51cd398f39ef037375dd0d23188f8b2049716a31e788676294a2c9d -> sha256:11301202fa7456f707dded0090ddbdc98ab973364b9ae7a00d49140f166cf9d1
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].intent_doc_match: sha256:8ac24611cfe47c129e37108bc6adc6843c4fe8fb9c37c27fac8a1835ba660307 -> (absent)
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].intent_doc_match.confidence: (absent) -> sha256:b4af4e0d40391d3a00179d935c63b7e15ba8cd3dfa29f218dedc270bd3eb3e79
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].intent_doc_match.doc: (absent) -> sha256:2da16962ed90531c876536115ad838630da9f394ebb78961727d213fda9d1d02
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].intent_doc_match.quote: (absent) -> sha256:27c72c8372eba3766f6c1467970127703de9f85875d2ae539f15e8d9aee6703e
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].intent_doc_match.section: (absent) -> sha256:65d0eeb922927ba39bec6d8ed659007357fd61b3b10be2e30e9a2340022ca521
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].problem: sha256:a905c5d4c3b0cf7f4da090b3cc547b423062371b7087871a2d61ddf457b42c4d -> sha256:792b89718df61dc9efb4aca149a5fb4f9ec00272f7db23b21cfde1ef731f833f
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].title: sha256:5ae9fd9eea7bc2153e2931649f7c29bf91a3beec305663c18a6b2c597dda6bb9 -> sha256:9998ce74438d9a1cc9e532fb9feb4c877c8941baea0dc94948f7ed0a07039052
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].why_it_matters: sha256:7b31fa6faa549b6ac1c9edfe31a94dc832c72a3c63718c50207b65af4065c6cc -> sha256:76aa7f3e568ea7f616fba6ef5872125b53c30ac40c64e900e6f79706ee2bf15f
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].agent: architecture -> impact
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].agent_confidence: sha256:9f14025af0065b30e47e23ebb3b491d39ae8ed17d33739e5ff3827ffb3634953 -> sha256:d59eced1ded07f84c145592f65bdf854358e009c5cd705f5215bf18697fed103
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].category: sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2 -> sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].current_code: sha256:435b3f5f95d1192d28520727a4401d29f28e4113a82bbc06f36be4b93d727d82 -> sha256:113b584eb734b1ba06a4814802bf18648ab9620b5a29e05bad737eb5c12a7af3
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].fix_hint: sha256:11301202fa7456f707dded0090ddbdc98ab973364b9ae7a00d49140f166cf9d1 -> sha256:27bedc07b51cd398f39ef037375dd0d23188f8b2049716a31e788676294a2c9d
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].intent_doc_match: (absent) -> sha256:8ac24611cfe47c129e37108bc6adc6843c4fe8fb9c37c27fac8a1835ba660307
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].intent_doc_match.confidence: sha256:b4af4e0d40391d3a00179d935c63b7e15ba8cd3dfa29f218dedc270bd3eb3e79 -> (absent)
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].intent_doc_match.doc: sha256:2da16962ed90531c876536115ad838630da9f394ebb78961727d213fda9d1d02 -> (absent)
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].intent_doc_match.quote: sha256:27c72c8372eba3766f6c1467970127703de9f85875d2ae539f15e8d9aee6703e -> (absent)
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].intent_doc_match.section: sha256:65d0eeb922927ba39bec6d8ed659007357fd61b3b10be2e30e9a2340022ca521 -> (absent)
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].problem: sha256:792b89718df61dc9efb4aca149a5fb4f9ec00272f7db23b21cfde1ef731f833f -> sha256:a905c5d4c3b0cf7f4da090b3cc547b423062371b7087871a2d61ddf457b42c4d
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].title: sha256:9998ce74438d9a1cc9e532fb9feb4c877c8941baea0dc94948f7ed0a07039052 -> sha256:5ae9fd9eea7bc2153e2931649f7c29bf91a3beec305663c18a6b2c597dda6bb9
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].why_it_matters: sha256:76aa7f3e568ea7f616fba6ef5872125b53c30ac40c64e900e6f79706ee2bf15f -> sha256:7b31fa6faa549b6ac1c9edfe31a94dc832c72a3c63718c50207b65af4065c6cc

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | triggarr/web/routes.py | 550 | critical | 100 | 2b1a20a238c5 |
| codex-adversarial | triggarr/web/routes.py | 446 | warning | 94 | 86011a03320d |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | triggarr/web/routes.py | 550 | critical | 100 | 2b1a20a238c5 |
| codex-adversarial | triggarr/web/routes.py | 446 | warning | 94 | 86011a03320d |

## runs-v2.10-phase43/first/triggarr-autoescape/run-2

changed paths: 18
allowed: no

- UNALLOWED filtered[3].title: sha256:8244cb00270a82b4406283fffec90786ee5d9bbc5261848a6c14fd63b0de4f9e -> sha256:fa63a1f4e2ceb742be253366465aa95b443ec57e4cb9f8080b81964f71cdfd1c
- UNALLOWED filtered[4].title: sha256:fa63a1f4e2ceb742be253366465aa95b443ec57e4cb9f8080b81964f71cdfd1c -> sha256:8244cb00270a82b4406283fffec90786ee5d9bbc5261848a6c14fd63b0de4f9e
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[4].agent: impact -> bugs
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[4].agent_confidence: sha256:48449a14a4ff7d79bb7a1b6f3d488eba397c36ef25634c111b49baf362511afc -> sha256:ff5a1ae012afa5d4c889c50ad427aaf545d31a4fac04ffc1c4d03d403ba4250a
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[4].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[4].fix_hint: sha256:9f42f78c4dab7aa6d36a92b448235b8e42627b4ee00373655211384c08a85f9e -> sha256:22bf108130a4d84db9b2bc08bc635b30d2a7cbf39f215dcdb5584c64e69e0e4b
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[4].intent_doc_match: sha256:fcbcf165908dd18a9e49f7ff27810176db8e9f63b4352213741664245224f8aa -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[4].problem: sha256:7aaeeccaa038096af7c02a4fb422d5bf6b35c8e2aec1bc75bdd48523a5163ec7 -> sha256:84b98b74e2924e62e2183e7ebb6ab1956324a841b019e13ab28bc356b6f1026b
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[4].title: sha256:8244cb00270a82b4406283fffec90786ee5d9bbc5261848a6c14fd63b0de4f9e -> sha256:fa63a1f4e2ceb742be253366465aa95b443ec57e4cb9f8080b81964f71cdfd1c
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[4].why_it_matters: sha256:d73a4666e945058903a1f6dfa74f918a549d278ce1add623b46b2f3ee76979f6 -> sha256:ff0ace959760dd27ec24c7a27f6dee909fac3078ee82df0aa8d0bbaf32ba9009
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[5].agent: bugs -> impact
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[5].agent_confidence: sha256:ff5a1ae012afa5d4c889c50ad427aaf545d31a4fac04ffc1c4d03d403ba4250a -> sha256:48449a14a4ff7d79bb7a1b6f3d488eba397c36ef25634c111b49baf362511afc
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[5].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[5].fix_hint: sha256:22bf108130a4d84db9b2bc08bc635b30d2a7cbf39f215dcdb5584c64e69e0e4b -> sha256:9f42f78c4dab7aa6d36a92b448235b8e42627b4ee00373655211384c08a85f9e
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[5].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> sha256:fcbcf165908dd18a9e49f7ff27810176db8e9f63b4352213741664245224f8aa
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[5].problem: sha256:84b98b74e2924e62e2183e7ebb6ab1956324a841b019e13ab28bc356b6f1026b -> sha256:7aaeeccaa038096af7c02a4fb422d5bf6b35c8e2aec1bc75bdd48523a5163ec7
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[5].title: sha256:fa63a1f4e2ceb742be253366465aa95b443ec57e4cb9f8080b81964f71cdfd1c -> sha256:8244cb00270a82b4406283fffec90786ee5d9bbc5261848a6c14fd63b0de4f9e
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[5].why_it_matters: sha256:ff0ace959760dd27ec24c7a27f6dee909fac3078ee82df0aa8d0bbaf32ba9009 -> sha256:d73a4666e945058903a1f6dfa74f918a549d278ce1add623b46b2f3ee76979f6

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 45 | critical | 100 | 4f30f8fb283f |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/routes.py | 45 | critical | 100 | 4f30f8fb283f |

## runs-v2.10-phase43/first/triggarr-secret-in-logs/run-1

changed paths: 23
allowed: no

- UNALLOWED filtered[2].line: 233 -> 235
- UNALLOWED filtered[2].title: sha256:d625b0a4862c8d006d4f4127466faa252ee20fb2bd91dc76f60ed47824d564ef -> sha256:7134fab34db53552ed56c580651b9825e00144079247ac8ba2605e176adb48d7
- UNALLOWED filtered[3].line: 235 -> 233
- UNALLOWED filtered[3].title: sha256:7134fab34db53552ed56c580651b9825e00144079247ac8ba2605e176adb48d7 -> sha256:d625b0a4862c8d006d4f4127466faa252ee20fb2bd91dc76f60ed47824d564ef
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].band: critical -> warning
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[3].agent: impact -> bugs
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[3].agent_confidence: sha256:39fa9ec190eee7b6f4dff1100d6343e10918d044c75eac8f9e9a2596173f80c9 -> sha256:02d20bbd7e394ad5999a4cebabac9619732c343a4cac99470c03e23ba2bdc2bc
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[3].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[3].fix_hint: sha256:1e29ae017e762f65ab8d1985d30717fa1b68a20a1ec71685a02cfd0c6b2e22eb -> sha256:343edcb43004ce7d34e186a70c22f65473e52e50ea04ecf64c9956387b13b68b
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[3].line: 233 -> 235
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[3].problem: sha256:a19272eb4be1507274c41c7b1aafffde8a6fda2d851aa2e527065a024e866a64 -> sha256:89f0eb4030a51c14df2096168b5f20e30d31d01aa1c7c73d949cb78a6fa8c47d
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[3].title: sha256:d625b0a4862c8d006d4f4127466faa252ee20fb2bd91dc76f60ed47824d564ef -> sha256:7134fab34db53552ed56c580651b9825e00144079247ac8ba2605e176adb48d7
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[3].why_it_matters: sha256:ed81e27a37cc2ca0c17d6307139baa0b6382e1179f09ce7c246910d702122fb7 -> sha256:f0e76b30fcea5dc02d97598678dfe99e52f6a01a19c83df65de2656bf1eb251c
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[4].agent: bugs -> impact
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[4].agent_confidence: sha256:02d20bbd7e394ad5999a4cebabac9619732c343a4cac99470c03e23ba2bdc2bc -> sha256:39fa9ec190eee7b6f4dff1100d6343e10918d044c75eac8f9e9a2596173f80c9
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[4].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[4].fix_hint: sha256:343edcb43004ce7d34e186a70c22f65473e52e50ea04ecf64c9956387b13b68b -> sha256:1e29ae017e762f65ab8d1985d30717fa1b68a20a1ec71685a02cfd0c6b2e22eb
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[4].line: 235 -> 233
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[4].problem: sha256:89f0eb4030a51c14df2096168b5f20e30d31d01aa1c7c73d949cb78a6fa8c47d -> sha256:a19272eb4be1507274c41c7b1aafffde8a6fda2d851aa2e527065a024e866a64
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[4].title: sha256:7134fab34db53552ed56c580651b9825e00144079247ac8ba2605e176adb48d7 -> sha256:d625b0a4862c8d006d4f4127466faa252ee20fb2bd91dc76f60ed47824d564ef
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[4].why_it_matters: sha256:f0e76b30fcea5dc02d97598678dfe99e52f6a01a19c83df65de2656bf1eb251c -> sha256:ed81e27a37cc2ca0c17d6307139baa0b6382e1179f09ce7c246910d702122fb7
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].orchestrator_score: 100 -> 94
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].snapshot.band: critical -> warning

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 232 | critical | 100 | 13f543dd935e |
| compliance | triggarr/clients/base.py | 252 | warning | 94 | af2794b67712 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 232 | warning | 94 | 13f543dd935e |
| compliance | triggarr/clients/base.py | 252 | warning | 94 | af2794b67712 |

## runs-v2.10-phase43/first/triggarr-secret-in-logs/run-3

changed paths: 28
allowed: no

- UNALLOWED filtered[2].title: sha256:9bd739b43f73f863f8be988a4baacebb5d4283edf8f249fd7f043ecbaeda1c1d -> sha256:c92d07056c5e95ce361c929303f83e79c07b9ef8698a04f5a2bfd6bf114ce535
- UNALLOWED filtered[3].title: sha256:c92d07056c5e95ce361c929303f83e79c07b9ef8698a04f5a2bfd6bf114ce535 -> sha256:04509ac5c3410ff50b8b6b0ea378e45461ee60e7f225f7efb2140e6d421bc358
- UNALLOWED filtered[4].title: sha256:04509ac5c3410ff50b8b6b0ea378e45461ee60e7f225f7efb2140e6d421bc358 -> sha256:9bd739b43f73f863f8be988a4baacebb5d4283edf8f249fd7f043ecbaeda1c1d
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[3].agent: impact -> bugs
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[3].agent_confidence: sha256:a21855da08cb102d1d217c53dc5824a3a795c1c1a44e971bf01ab9da3a2acbbf -> sha256:81b8a03f97e8787c53fe1a86bda042b6f0de9b0ec9c09357e107c99ba4d6948a
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[3].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[3].fix_hint: sha256:36b9e4672f6950f144f8920fb239cc09e4db8a6b3beaac36242f9633d35e78db -> sha256:3b2ad497391437469a76025f5d695c6f74ccebcb8eba72e54d237e73f4c7c3ab
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[3].intent_doc_match: sha256:90d1ad9b8cedd78feaeb3d139fd6246e921a08b14553594cc499f1e271166b6d -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[3].problem: sha256:90c0770c76f3824edd57e639b2ccd90c03522481840ff112e3d33c3382033381 -> sha256:ae8c740fae6205b294c6de099ea380cd3f9e28f5102be3a0192cbe87187b4a10
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[3].title: sha256:9bd739b43f73f863f8be988a4baacebb5d4283edf8f249fd7f043ecbaeda1c1d -> sha256:c92d07056c5e95ce361c929303f83e79c07b9ef8698a04f5a2bfd6bf114ce535
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[3].why_it_matters: sha256:7d7c57d16bedd6865c7f52f58005bdda8b1f3778a76016f4804af6f58a5f2a2d -> sha256:40d32e69735e3334def8fb9209a5d2c72ff2835318d281edaa180e08dd1617d8
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[4].agent: bugs -> compliance
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[4].agent_confidence: sha256:81b8a03f97e8787c53fe1a86bda042b6f0de9b0ec9c09357e107c99ba4d6948a -> sha256:41cfc0d1f2d127b04555b7246d84019b4d27710a3f3aff6e7764375b1e06e05d
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[4].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> sha256:df9420b6c4d136a808026d388318d24387a18cd204153c572e9c982b693864b9
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[4].fix_hint: sha256:3b2ad497391437469a76025f5d695c6f74ccebcb8eba72e54d237e73f4c7c3ab -> sha256:a1ae37051fe4bf80d8db64c894f519516d6c6c4e79f26cd0f07b8cef29716c1d
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[4].problem: sha256:ae8c740fae6205b294c6de099ea380cd3f9e28f5102be3a0192cbe87187b4a10 -> sha256:3c85df51d1711640b4b4b6178a286c421149167a6b5d19ed9529d772be017d11
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[4].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> sha256:364bb7082249ee9fbc5247ee49735c4246f271b82c2745a35107ddda0d7cabcc
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[4].title: sha256:c92d07056c5e95ce361c929303f83e79c07b9ef8698a04f5a2bfd6bf114ce535 -> sha256:04509ac5c3410ff50b8b6b0ea378e45461ee60e7f225f7efb2140e6d421bc358
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[4].why_it_matters: sha256:40d32e69735e3334def8fb9209a5d2c72ff2835318d281edaa180e08dd1617d8 -> sha256:d1c4131920f7bdbcffb28eaad457ed68cbddb4500bf3aee7724b6cee8ed7bcee
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[5].agent: compliance -> impact
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[5].agent_confidence: sha256:41cfc0d1f2d127b04555b7246d84019b4d27710a3f3aff6e7764375b1e06e05d -> sha256:a21855da08cb102d1d217c53dc5824a3a795c1c1a44e971bf01ab9da3a2acbbf
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[5].category: sha256:df9420b6c4d136a808026d388318d24387a18cd204153c572e9c982b693864b9 -> sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[5].fix_hint: sha256:a1ae37051fe4bf80d8db64c894f519516d6c6c4e79f26cd0f07b8cef29716c1d -> sha256:36b9e4672f6950f144f8920fb239cc09e4db8a6b3beaac36242f9633d35e78db
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[5].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> sha256:90d1ad9b8cedd78feaeb3d139fd6246e921a08b14553594cc499f1e271166b6d
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[5].problem: sha256:3c85df51d1711640b4b4b6178a286c421149167a6b5d19ed9529d772be017d11 -> sha256:90c0770c76f3824edd57e639b2ccd90c03522481840ff112e3d33c3382033381
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[5].severity: sha256:364bb7082249ee9fbc5247ee49735c4246f271b82c2745a35107ddda0d7cabcc -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[5].title: sha256:04509ac5c3410ff50b8b6b0ea378e45461ee60e7f225f7efb2140e6d421bc358 -> sha256:9bd739b43f73f863f8be988a4baacebb5d4283edf8f249fd7f043ecbaeda1c1d
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[5].why_it_matters: sha256:d1c4131920f7bdbcffb28eaad457ed68cbddb4500bf3aee7724b6cee8ed7bcee -> sha256:7d7c57d16bedd6865c7f52f58005bdda8b1f3778a76016f4804af6f58a5f2a2d

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 233 | critical | 100 | 5718c2673139 |
| compliance | triggarr/clients/base.py | 252 | warning | 94 | 17ab47c4de4d |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 233 | critical | 100 | 5718c2673139 |
| compliance | triggarr/clients/base.py | 252 | warning | 94 | 17ab47c4de4d |

## runs-v2.10-phase43/retune/should-quiet-6/run-1

changed paths: 3
allowed: yes

- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].band: critical -> warning
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].orchestrator_score: 100 -> 94
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].snapshot.band: critical -> warning

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | critical | 100 | c93be6bfe251 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | warning | 94 | c93be6bfe251 |

## runs-v2.10-phase43/retune/should-quiet-6/run-2

changed paths: 3
allowed: yes

- findings[4ac803dd7f3d2d25ef8e361db8752671cd3c02eb4d284c77a2e5c4b5ad30cd0f].band: critical -> warning
- findings[4ac803dd7f3d2d25ef8e361db8752671cd3c02eb4d284c77a2e5c4b5ad30cd0f].orchestrator_score: 100 -> 94
- findings[4ac803dd7f3d2d25ef8e361db8752671cd3c02eb4d284c77a2e5c4b5ad30cd0f].snapshot.band: critical -> warning

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | critical | 100 | 4ac803dd7f3d |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | warning | 94 | 4ac803dd7f3d |

## runs-v2.10-phase43/retune/should-quiet-6/run-3

changed paths: 35
allowed: yes

- filtered[1].title: sha256:d18ca883c83e42466bf16393b6709f1753a4c107271581d69629e7632376806f -> sha256:a0bb4462d8aef8ac8bf37ee7b67c2833b5b99a3e1fdd8466a509ac03b00ed127
- filtered[2].title: sha256:a0bb4462d8aef8ac8bf37ee7b67c2833b5b99a3e1fdd8466a509ac03b00ed127 -> sha256:af16b0a1c9a23a411d700d0bc40de293b66f30823f11bb4e07698578503c6906
- filtered[3].title: sha256:4e9ee704edf12cf8f86af15c2fcefeae0fd9af171b1dad02008128a09390cc5e -> sha256:d18ca883c83e42466bf16393b6709f1753a4c107271581d69629e7632376806f
- filtered[4].title: sha256:af16b0a1c9a23a411d700d0bc40de293b66f30823f11bb4e07698578503c6906 -> sha256:4e9ee704edf12cf8f86af15c2fcefeae0fd9af171b1dad02008128a09390cc5e
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].band: critical -> warning
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[2].agent: impact -> bugs
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[2].agent_confidence: sha256:d59eced1ded07f84c145592f65bdf854358e009c5cd705f5215bf18697fed103 -> sha256:9f14025af0065b30e47e23ebb3b491d39ae8ed17d33739e5ff3827ffb3634953
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[2].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[2].current_code: sha256:bb6973e5ee262da73b7605d3c5597adde7e61b1c2af822f55b4fef0de5256f31 -> sha256:225b35956b7d7e9a7dd5117abd0f75a9a762dc2b1abc6b90422ba033611b17cb
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[2].fix_hint: sha256:c443032adf13928079fee988fb81de0e261b9c803014c3ac94f667865a3837dc -> sha256:311d3629a76d1f07a8d1c2eec33583d4bc7c764b34836620c13c48fd617fe5b4
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[2].problem: sha256:8243f8ea3d0030ea1ed63c032454d4634bb139e73fbea4c640e5b5e2d8966ac4 -> sha256:e7ce14e9d03e9d2601dda12a9762967548f18761ccf0f605745f41b0ca8ab4db
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[2].title: sha256:d18ca883c83e42466bf16393b6709f1753a4c107271581d69629e7632376806f -> sha256:a0bb4462d8aef8ac8bf37ee7b67c2833b5b99a3e1fdd8466a509ac03b00ed127
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[2].why_it_matters: sha256:4e5184d28825d2de202fa79daa91a7e2ee5cb40262b4137d938d0a33666269fc -> sha256:a0c52f24305dfe0ff34da996f9b8df15f167c379f37f4ca894c270a60af50b23
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].agent_confidence: sha256:9f14025af0065b30e47e23ebb3b491d39ae8ed17d33739e5ff3827ffb3634953 -> sha256:624b60c58c9d8bfb6ff1886c2fd605d2adeb6ea4da576068201b6c6958ce93f4
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].current_code: sha256:225b35956b7d7e9a7dd5117abd0f75a9a762dc2b1abc6b90422ba033611b17cb -> sha256:bb6973e5ee262da73b7605d3c5597adde7e61b1c2af822f55b4fef0de5256f31
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].fix_hint: sha256:311d3629a76d1f07a8d1c2eec33583d4bc7c764b34836620c13c48fd617fe5b4 -> sha256:fca1167c0d0ad15e688215729b5d64a2789a69ddbb7946e5a674e5690c52ea5e
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].problem: sha256:e7ce14e9d03e9d2601dda12a9762967548f18761ccf0f605745f41b0ca8ab4db -> sha256:e2c77c664493f6bb781826c3a32f23c01ff791133980e3c996742a6ec468cbd6
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].title: sha256:a0bb4462d8aef8ac8bf37ee7b67c2833b5b99a3e1fdd8466a509ac03b00ed127 -> sha256:af16b0a1c9a23a411d700d0bc40de293b66f30823f11bb4e07698578503c6906
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].why_it_matters: sha256:a0c52f24305dfe0ff34da996f9b8df15f167c379f37f4ca894c270a60af50b23 -> sha256:73cefb4dc42cac2f45ebecb808b6d67eb743d44978987b6693d1768c65498aab
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].agent_confidence: sha256:9f14025af0065b30e47e23ebb3b491d39ae8ed17d33739e5ff3827ffb3634953 -> sha256:d59eced1ded07f84c145592f65bdf854358e009c5cd705f5215bf18697fed103
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].current_code: sha256:98bd5c5216972428106f8543cf654e41b7b568cfeb96eda3f0f4dd554d3d3299 -> sha256:bb6973e5ee262da73b7605d3c5597adde7e61b1c2af822f55b4fef0de5256f31
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].fix_hint: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> sha256:c443032adf13928079fee988fb81de0e261b9c803014c3ac94f667865a3837dc
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].problem: sha256:9ad902c59b3a16d8e510c532648e267ae29981c54ad822a9212980a2dad3c9d7 -> sha256:8243f8ea3d0030ea1ed63c032454d4634bb139e73fbea4c640e5b5e2d8966ac4
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].title: sha256:4e9ee704edf12cf8f86af15c2fcefeae0fd9af171b1dad02008128a09390cc5e -> sha256:d18ca883c83e42466bf16393b6709f1753a4c107271581d69629e7632376806f
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].why_it_matters: sha256:f238bad9170d4c1db80fe1a8318a636402bc61f1ed1e38d79dc9ee76b679e70b -> sha256:4e5184d28825d2de202fa79daa91a7e2ee5cb40262b4137d938d0a33666269fc
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[5].agent: bugs -> impact
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[5].agent_confidence: sha256:624b60c58c9d8bfb6ff1886c2fd605d2adeb6ea4da576068201b6c6958ce93f4 -> sha256:9f14025af0065b30e47e23ebb3b491d39ae8ed17d33739e5ff3827ffb3634953
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[5].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[5].current_code: sha256:bb6973e5ee262da73b7605d3c5597adde7e61b1c2af822f55b4fef0de5256f31 -> sha256:98bd5c5216972428106f8543cf654e41b7b568cfeb96eda3f0f4dd554d3d3299
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[5].fix_hint: sha256:fca1167c0d0ad15e688215729b5d64a2789a69ddbb7946e5a674e5690c52ea5e -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[5].problem: sha256:e2c77c664493f6bb781826c3a32f23c01ff791133980e3c996742a6ec468cbd6 -> sha256:9ad902c59b3a16d8e510c532648e267ae29981c54ad822a9212980a2dad3c9d7
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[5].title: sha256:af16b0a1c9a23a411d700d0bc40de293b66f30823f11bb4e07698578503c6906 -> sha256:4e9ee704edf12cf8f86af15c2fcefeae0fd9af171b1dad02008128a09390cc5e
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[5].why_it_matters: sha256:73cefb4dc42cac2f45ebecb808b6d67eb743d44978987b6693d1768c65498aab -> sha256:f238bad9170d4c1db80fe1a8318a636402bc61f1ed1e38d79dc9ee76b679e70b
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].orchestrator_score: 100 -> 94
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].snapshot.band: critical -> warning

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | critical | 100 | c93be6bfe251 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | warning | 94 | c93be6bfe251 |

## runs-v2.10/third-organic-should-catch/run-2

changed paths: 32
allowed: no

- UNALLOWED filtered[2].line: 308 -> 307
- UNALLOWED filtered[2].title: sha256:160edb94d04f1e6d1c354d35df87ceb6fd99d977c39467d37ccd3622800e3970 -> sha256:b4810c75aa3b28b66b578be41e38f757d97121d00260717dc29cd55d6d5eb3a7
- UNALLOWED filtered[3].line: 307 -> 308
- UNALLOWED filtered[3].title: sha256:b4810c75aa3b28b66b578be41e38f757d97121d00260717dc29cd55d6d5eb3a7 -> sha256:160edb94d04f1e6d1c354d35df87ceb6fd99d977c39467d37ccd3622800e3970
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].agent: language-typescript -> bugs
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].agent_confidence: sha256:f369cb89fc627e668987007d121ed1eacdc01db9e28f8bb26f358b7d8c4f08ac -> sha256:8722616204217eddb39e7df969e0698aed8e599ba62ed2de1ce49b03ade0fede
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].category: sha256:fcc959df514120f6ef0f7625da45bc925e8a0e2a209110e986c40c366f630fc6 -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].current_code: sha256:4b9d0001d17f6ddd8d511e589e0694425f0ee70d0eacc3f29015fdb4edd27645 -> sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].fix_hint: sha256:a1193af4dcb0c98287d635d333fd16f7ae1d76c955b998536a8db084c7c980d8 -> sha256:0b6e91bc41af6b02bad74ca22d224f0216b46871e4390a1f2bda01496f146ef7
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].line: 308 -> 307
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].problem: sha256:0ea13a36dad96b265814f2b842e66d867860d90c9e8e7515de8320bc8ecc9f59 -> sha256:5aafacf1536dcd502b596ed98d1d786f7bf3d5284805cf4793cacd2fa51deb6c
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].source_window[0]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].source_window[1]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].source_window[2]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].source_window[3]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].source_window[4]: sha256:12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126 -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].title: sha256:160edb94d04f1e6d1c354d35df87ceb6fd99d977c39467d37ccd3622800e3970 -> sha256:b4810c75aa3b28b66b578be41e38f757d97121d00260717dc29cd55d6d5eb3a7
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].why_it_matters: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> sha256:f806b3cc17956b407bbb662336b4c6ef0ff20a513146ffefbd521490eb8da0b4
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].agent: bugs -> language-typescript
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].agent_confidence: sha256:8722616204217eddb39e7df969e0698aed8e599ba62ed2de1ce49b03ade0fede -> sha256:f369cb89fc627e668987007d121ed1eacdc01db9e28f8bb26f358b7d8c4f08ac
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> sha256:fcc959df514120f6ef0f7625da45bc925e8a0e2a209110e986c40c366f630fc6
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].current_code: sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56 -> sha256:4b9d0001d17f6ddd8d511e589e0694425f0ee70d0eacc3f29015fdb4edd27645
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].fix_hint: sha256:0b6e91bc41af6b02bad74ca22d224f0216b46871e4390a1f2bda01496f146ef7 -> sha256:a1193af4dcb0c98287d635d333fd16f7ae1d76c955b998536a8db084c7c980d8
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].line: 307 -> 308
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].problem: sha256:5aafacf1536dcd502b596ed98d1d786f7bf3d5284805cf4793cacd2fa51deb6c -> sha256:0ea13a36dad96b265814f2b842e66d867860d90c9e8e7515de8320bc8ecc9f59
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].source_window[0]: sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].source_window[1]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].source_window[2]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].source_window[3]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].source_window[4]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> sha256:12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].title: sha256:b4810c75aa3b28b66b578be41e38f757d97121d00260717dc29cd55d6d5eb3a7 -> sha256:160edb94d04f1e6d1c354d35df87ceb6fd99d977c39467d37ccd3622800e3970
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].why_it_matters: sha256:f806b3cc17956b407bbb662336b4c6ef0ff20a513146ffefbd521490eb8da0b4 -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | src/angular/src/app/services/files/view-file.service.ts | 307 | critical | 100 | 25b18f8a4353 |
| architecture | src/angular/src/app/pages/files/transfer-row.component.html | 33 | medium | 79 | 0146d176fdb7 |
| impact | src/angular/src/app/tests/unittests/services/files/view-file.service.spec.ts | 246 | warning | 81 | 05b574a5062b |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | src/angular/src/app/services/files/view-file.service.ts | 307 | critical | 100 | 25b18f8a4353 |
| architecture | src/angular/src/app/pages/files/transfer-row.component.html | 33 | medium | 79 | 0146d176fdb7 |
| impact | src/angular/src/app/tests/unittests/services/files/view-file.service.spec.ts | 246 | warning | 81 | 05b574a5062b |

## runs-v2.10/triggarr-secret-in-logs/run-1

changed paths: 3
allowed: no

- UNALLOWED findings[12fe298fc07e929bf6fd70047bc5e520b172a1c5329544a48022e36ce0c4be82].band: critical -> warning
- UNALLOWED findings[12fe298fc07e929bf6fd70047bc5e520b172a1c5329544a48022e36ce0c4be82].orchestrator_score: 100 -> 94
- UNALLOWED findings[12fe298fc07e929bf6fd70047bc5e520b172a1c5329544a48022e36ce0c4be82].snapshot.band: critical -> warning

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | triggarr/clients/base.py | 252 | warning | 82 | 7074d66fd289 |
| codex-adversarial | triggarr/clients/base.py | 233 | critical | 100 | 12fe298fc07e |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | triggarr/clients/base.py | 252 | warning | 82 | 7074d66fd289 |
| codex-adversarial | triggarr/clients/base.py | 233 | warning | 94 | 12fe298fc07e |

## runs-v2.11-phase49/first/should-quiet-6/run-1

changed paths: 3
allowed: yes

- findings[780e77edbe528e97f714b9c148538f93595e7e6cac04cafdb192ac8383378d4a].band: critical -> warning
- findings[780e77edbe528e97f714b9c148538f93595e7e6cac04cafdb192ac8383378d4a].orchestrator_score: 100 -> 94
- findings[780e77edbe528e97f714b9c148538f93595e7e6cac04cafdb192ac8383378d4a].snapshot.band: critical -> warning

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 135 | critical | 100 | 780e77edbe52 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 135 | warning | 94 | 780e77edbe52 |

## runs-v2.11-phase49/first/should-quiet-6/run-2

changed paths: 3
allowed: yes

- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].band: critical -> warning
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].orchestrator_score: 100 -> 94
- findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].snapshot.band: critical -> warning

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | critical | 100 | c93be6bfe251 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | warning | 94 | c93be6bfe251 |

## runs-v2.11-phase49/first/should-quiet-6/run-3

changed paths: 21
allowed: yes

- filtered[1].title: sha256:5d903bf28ed8baa23a32348e7d9b5bbacf83164733cea8e20ab7056fc4023759 -> sha256:4c0967b7043569b09668bb961bfbb34b5e6371db14e03d4f423f53b05555bf94
- filtered[2].title: sha256:4c0967b7043569b09668bb961bfbb34b5e6371db14e03d4f423f53b05555bf94 -> sha256:5d903bf28ed8baa23a32348e7d9b5bbacf83164733cea8e20ab7056fc4023759
- findings[993c32eb9391cd620527d9b63921e2f556ce66a8cd641dd81425e774e71098af].band: critical -> warning
- findings[993c32eb9391cd620527d9b63921e2f556ce66a8cd641dd81425e774e71098af].members[2].agent: impact -> bugs
- findings[993c32eb9391cd620527d9b63921e2f556ce66a8cd641dd81425e774e71098af].members[2].agent_confidence: sha256:d59eced1ded07f84c145592f65bdf854358e009c5cd705f5215bf18697fed103 -> sha256:9f14025af0065b30e47e23ebb3b491d39ae8ed17d33739e5ff3827ffb3634953
- findings[993c32eb9391cd620527d9b63921e2f556ce66a8cd641dd81425e774e71098af].members[2].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- findings[993c32eb9391cd620527d9b63921e2f556ce66a8cd641dd81425e774e71098af].members[2].fix_hint: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> sha256:dcbbbab3d8f11b4c44c88fc2f6827701b8ee4a1ecd374ee3236cedb8e19f8d53
- findings[993c32eb9391cd620527d9b63921e2f556ce66a8cd641dd81425e774e71098af].members[2].intent_doc_match: sha256:18f38fab6dc380f22b18de0e43997fc485f049b5a02e740eef573f4a4110edc0 -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- findings[993c32eb9391cd620527d9b63921e2f556ce66a8cd641dd81425e774e71098af].members[2].problem: sha256:406de08b89386b0a9752756ffb246ec5339e7db1da05aa4a3f4812050abb45f1 -> sha256:247621a95f9834d33b78eca9c71082d3518afd6f9a502d52b0d3c47284897562
- findings[993c32eb9391cd620527d9b63921e2f556ce66a8cd641dd81425e774e71098af].members[2].title: sha256:5d903bf28ed8baa23a32348e7d9b5bbacf83164733cea8e20ab7056fc4023759 -> sha256:4c0967b7043569b09668bb961bfbb34b5e6371db14e03d4f423f53b05555bf94
- findings[993c32eb9391cd620527d9b63921e2f556ce66a8cd641dd81425e774e71098af].members[2].why_it_matters: sha256:21b5ab1cc71407254d3b40f6f6c955688c915da115c7b9c197ea1cd402f21d26 -> sha256:dd3cdeaec62d06b55b7abcb51314aed70108368669846278389d063fe88ea5c7
- findings[993c32eb9391cd620527d9b63921e2f556ce66a8cd641dd81425e774e71098af].members[3].agent: bugs -> impact
- findings[993c32eb9391cd620527d9b63921e2f556ce66a8cd641dd81425e774e71098af].members[3].agent_confidence: sha256:9f14025af0065b30e47e23ebb3b491d39ae8ed17d33739e5ff3827ffb3634953 -> sha256:d59eced1ded07f84c145592f65bdf854358e009c5cd705f5215bf18697fed103
- findings[993c32eb9391cd620527d9b63921e2f556ce66a8cd641dd81425e774e71098af].members[3].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7
- findings[993c32eb9391cd620527d9b63921e2f556ce66a8cd641dd81425e774e71098af].members[3].fix_hint: sha256:dcbbbab3d8f11b4c44c88fc2f6827701b8ee4a1ecd374ee3236cedb8e19f8d53 -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- findings[993c32eb9391cd620527d9b63921e2f556ce66a8cd641dd81425e774e71098af].members[3].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> sha256:18f38fab6dc380f22b18de0e43997fc485f049b5a02e740eef573f4a4110edc0
- findings[993c32eb9391cd620527d9b63921e2f556ce66a8cd641dd81425e774e71098af].members[3].problem: sha256:247621a95f9834d33b78eca9c71082d3518afd6f9a502d52b0d3c47284897562 -> sha256:406de08b89386b0a9752756ffb246ec5339e7db1da05aa4a3f4812050abb45f1
- findings[993c32eb9391cd620527d9b63921e2f556ce66a8cd641dd81425e774e71098af].members[3].title: sha256:4c0967b7043569b09668bb961bfbb34b5e6371db14e03d4f423f53b05555bf94 -> sha256:5d903bf28ed8baa23a32348e7d9b5bbacf83164733cea8e20ab7056fc4023759
- findings[993c32eb9391cd620527d9b63921e2f556ce66a8cd641dd81425e774e71098af].members[3].why_it_matters: sha256:dd3cdeaec62d06b55b7abcb51314aed70108368669846278389d063fe88ea5c7 -> sha256:21b5ab1cc71407254d3b40f6f6c955688c915da115c7b9c197ea1cd402f21d26
- findings[993c32eb9391cd620527d9b63921e2f556ce66a8cd641dd81425e774e71098af].orchestrator_score: 100 -> 94
- findings[993c32eb9391cd620527d9b63921e2f556ce66a8cd641dd81425e774e71098af].snapshot.band: critical -> warning

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | critical | 100 | 993c32eb9391 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/models/config.py | 139 | warning | 94 | 993c32eb9391 |

## runs-v2.11-phase49/first/triggarr-secret-in-logs/run-2

changed paths: 36
allowed: no

- UNALLOWED filtered[0].line: 232 -> 233
- UNALLOWED filtered[0].title: sha256:ab2bffffabe40bf998818457b2d617a4002a75ab576bf8a9b779fda19368582c -> sha256:fc2a24fcd2f346848923394d66f4553e455a4ae0fdc83175fca80b33c3b3985c
- UNALLOWED filtered[1].title: sha256:b945310fa83d6dfd96f3f21a1474cd9c92b416a70bdf276e13e9c69b6f94aad5 -> sha256:ab2bffffabe40bf998818457b2d617a4002a75ab576bf8a9b779fda19368582c
- UNALLOWED filtered[2].line: 233 -> 232
- UNALLOWED filtered[2].title: sha256:fc2a24fcd2f346848923394d66f4553e455a4ae0fdc83175fca80b33c3b3985c -> sha256:b945310fa83d6dfd96f3f21a1474cd9c92b416a70bdf276e13e9c69b6f94aad5
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].agent: security -> architecture
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].agent_confidence: sha256:8241649609f88ccd2a0a5b233a07a538ec313ff6adf695aa44a969dbca39f67d -> sha256:b4944c6ff08dc6f43da2e9c824669b7d927dd1fa976fadc7b456881f51bf5ccc
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].category: sha256:8cc5192684865079dea813dcf1f24a4cac21e0e4174cc4e30a1460c44a643178 -> sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> sha256:4f8f4acf01981dfb513cc1eb86aa119224eded9c1408dae2502021fae2faa23b
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].cwe: sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].fix_hint: sha256:2ce7db69189316a140e3c7f19f524cee26edd3a02da5f2481213f5b2548bf4b8 -> sha256:173c347e4ea487f9f1586e67d9c574edf5d355a7dee9a504e70a3b634127a279
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].intent_doc_match: sha256:55e5dc644493646f21e6a412775acf22c8cdbd8b238db8314359792c37e2a16e -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].line: 232 -> 233
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].problem: sha256:32b2759705ccb4a12cebe4096aa81ee84c4c777635190f9e57fa00fbeb944913 -> sha256:d95298a101a9f0fa69e9c0db008b45c54d4a43378469eccbade68699d9de94b3
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].severity: sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].title: sha256:ab2bffffabe40bf998818457b2d617a4002a75ab576bf8a9b779fda19368582c -> sha256:fc2a24fcd2f346848923394d66f4553e455a4ae0fdc83175fca80b33c3b3985c
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].why_it_matters: sha256:c55cd3aeae668530c6b208b627daa814e2d40bbb04685c3e42569bb1ca362367 -> sha256:3b17cce381849b2957297a2a77df0e06858dedc0879efc3bd4d46205c674ec82
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[2].agent: compliance -> security
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[2].agent_confidence: sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349 -> sha256:8241649609f88ccd2a0a5b233a07a538ec313ff6adf695aa44a969dbca39f67d
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[2].category: sha256:df9420b6c4d136a808026d388318d24387a18cd204153c572e9c982b693864b9 -> sha256:8cc5192684865079dea813dcf1f24a4cac21e0e4174cc4e30a1460c44a643178
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[2].fix_hint: sha256:6f91d93584eb532c56a1fb70c265f04ca587f36a41f54c49204848e2caa8d8f8 -> sha256:2ce7db69189316a140e3c7f19f524cee26edd3a02da5f2481213f5b2548bf4b8
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[2].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> sha256:55e5dc644493646f21e6a412775acf22c8cdbd8b238db8314359792c37e2a16e
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[2].problem: sha256:144da007df8b4155e37f5ca51482aefeff5267b25e8913d175dc4bc6b62a2dac -> sha256:32b2759705ccb4a12cebe4096aa81ee84c4c777635190f9e57fa00fbeb944913
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[2].title: sha256:b945310fa83d6dfd96f3f21a1474cd9c92b416a70bdf276e13e9c69b6f94aad5 -> sha256:ab2bffffabe40bf998818457b2d617a4002a75ab576bf8a9b779fda19368582c
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[2].why_it_matters: sha256:c8882d480a0d730fb9c9335910a01835a5e4859a24f42eaebf20c076cfe1bfa8 -> sha256:c55cd3aeae668530c6b208b627daa814e2d40bbb04685c3e42569bb1ca362367
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[3].agent: architecture -> compliance
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[3].agent_confidence: sha256:b4944c6ff08dc6f43da2e9c824669b7d927dd1fa976fadc7b456881f51bf5ccc -> sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[3].category: sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2 -> sha256:df9420b6c4d136a808026d388318d24387a18cd204153c572e9c982b693864b9
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[3].current_code: sha256:4f8f4acf01981dfb513cc1eb86aa119224eded9c1408dae2502021fae2faa23b -> sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[3].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[3].fix_hint: sha256:173c347e4ea487f9f1586e67d9c574edf5d355a7dee9a504e70a3b634127a279 -> sha256:6f91d93584eb532c56a1fb70c265f04ca587f36a41f54c49204848e2caa8d8f8
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[3].line: 233 -> 232
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[3].problem: sha256:d95298a101a9f0fa69e9c0db008b45c54d4a43378469eccbade68699d9de94b3 -> sha256:144da007df8b4155e37f5ca51482aefeff5267b25e8913d175dc4bc6b62a2dac
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[3].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[3].title: sha256:fc2a24fcd2f346848923394d66f4553e455a4ae0fdc83175fca80b33c3b3985c -> sha256:b945310fa83d6dfd96f3f21a1474cd9c92b416a70bdf276e13e9c69b6f94aad5
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[3].why_it_matters: sha256:3b17cce381849b2957297a2a77df0e06858dedc0879efc3bd4d46205c674ec82 -> sha256:c8882d480a0d730fb9c9335910a01835a5e4859a24f42eaebf20c076cfe1bfa8

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 233 | critical | 100 | 231222c433af |
| compliance | triggarr/clients/base.py | 251 | warning | 94 | 48ab3c20fcc2 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/clients/base.py | 233 | critical | 100 | 231222c433af |
| compliance | triggarr/clients/base.py | 251 | warning | 94 | 48ab3c20fcc2 |

## runs/should-quiet-1/run-1

changed paths: 244
allowed: no

- UNALLOWED filtered[0].line: 85 -> 87
- UNALLOWED filtered[0].reason: sha256:f1244fd68e7cc828d1b8620f645fa0494032320c8c8af439320981cf14227449 -> sha256:c3d2875a36c6b2e621ce38125d1fda2c13555353fdf92d3a89f50840df0e76d4
- UNALLOWED filtered[0].title: sha256:ee0906ffe9ddb7038f84a6f1d36fd0c9c7785a3876e656298e38d4bdc380b0d2 -> sha256:c6e017fc57cd45cbe57a96af97f00116d33daee5dad01ca953c7377334f96ee3
- UNALLOWED filtered[1].line: 87 -> 85
- UNALLOWED filtered[1].reason: sha256:f1244fd68e7cc828d1b8620f645fa0494032320c8c8af439320981cf14227449 -> sha256:c3d2875a36c6b2e621ce38125d1fda2c13555353fdf92d3a89f50840df0e76d4
- UNALLOWED filtered[1].title: sha256:1921f463d437650fec91853234a158ec90828e01fd98f1b6ed2ba67e6335191f -> sha256:8d2fc74b59a42d7d602ce7c21b310dec8115786bd291324a4c13377ba9de87c3
- UNALLOWED filtered[2].line: 85 -> 87
- UNALLOWED filtered[2].reason: sha256:f1244fd68e7cc828d1b8620f645fa0494032320c8c8af439320981cf14227449 -> sha256:c3d2875a36c6b2e621ce38125d1fda2c13555353fdf92d3a89f50840df0e76d4
- UNALLOWED filtered[2].title: sha256:8d2fc74b59a42d7d602ce7c21b310dec8115786bd291324a4c13377ba9de87c3 -> sha256:1921f463d437650fec91853234a158ec90828e01fd98f1b6ed2ba67e6335191f
- UNALLOWED findings.order: sha256:ec2573fa201b5447ebac284c6edba72404d45bf693278f83475b4573c2db9508 -> sha256:a1adb5e90d4a54dd7f94a88c0f85b7917f6a8e31677e8842cd13a4ddb3db6d76
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].agent: bugs -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].agent_confidence: sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].attribution[0]: sha256:610cb42c95dd518d546a1f6603bb920b2a5e04c6c1514e84e47433dc58102d3a -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].attribution[1]: sha256:361e7b1acb6d80d7ef7f8e0aa4204fcebe6a047e57167c83979fbcdb9d37833c -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].attribution[2]: sha256:96f34c94f7cf7eb0d8a8aadf48980e0ac0d131b90ee50a682424071e25f2f534 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].attribution[3]: sha256:cac9fa20faacbccf6f0e6b780fdfa8793d3bc0773ca4d5b280c4bbe9ac02cac3 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].band: critical -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].canonical_line_content: sha256:4c3544b3e573f4cae2f0a8ee27029fe96c97df9cf442ed5697d802d7e50d84b5 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].current_code: sha256:21ecfa845b615bcabfb9870e3f30b3064da664f49f86fe57529afdcddcda594a -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].cwe: sha256:4779bc407343d916c5a4f6a996174046419bdd87ce6c609054dc8788b3dfc233 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].file: triggarr/web/validation.py -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].fix_hint: sha256:cad6e60c8f0dae8f73d82ec9cf9880ee01b5c8db04cab2405e93a39e7d1ad527 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].id: sha256:f7a33a0e52e4cd019310f1f9bca293dad2fd118a2304ea0ce7c3008a348766dd -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].in_diff: sha256:b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].line: 87 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].agent: bugs -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].agent_confidence: sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].current_code: sha256:21ecfa845b615bcabfb9870e3f30b3064da664f49f86fe57529afdcddcda594a -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].cwe: sha256:4779bc407343d916c5a4f6a996174046419bdd87ce6c609054dc8788b3dfc233 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].file: triggarr/web/validation.py -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].fix_hint: sha256:cad6e60c8f0dae8f73d82ec9cf9880ee01b5c8db04cab2405e93a39e7d1ad527 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].line: 87 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].problem: sha256:d29277d7c711873f930b3d4ecec523322a93f64485339df7ef3ba212797c09fa -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].severity: sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].source_window[0]: sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].source_window[1]: sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].source_window[2]: sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].source_window[3]: sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].source_window[4]: sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].source_window[5]: sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].source_window[6]: sha256:8441e9dc7ef6b32e165b29cc5ef7cc39cd9b9e4a7728dcc9b01331b99f116253 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].title: sha256:c6e017fc57cd45cbe57a96af97f00116d33daee5dad01ca953c7377334f96ee3 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].why_it_matters: sha256:f47254a85dabf2d27ac2a6050626b14359c7cabbaf9c63a71553649f5f6752e4 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].agent: codex-adversarial -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].agent_confidence: sha256:ad48ff99415b2f007dc35b7eb553fd1eb35ebfa2f2f308acd9488eeb86f71fa8 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].category: sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].current_code: sha256:95abd0fa465e9d41f4578e977f3ac54ad99b05118deeb0127fd6d9a4bbd1e2eb -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].file: triggarr/web/validation.py -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].fix_hint: sha256:4557baec16295212ba42d53c790c300ddcdbe12bfc1f7f94c765973855bd04f1 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].line: 85 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].problem: sha256:37ea85c141434b0e8cc5df649d0a4b5b070efe15d60ff87f99e18a7fd6e184b4 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].severity: sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].source_window[0]: sha256:fc6acc58b0d2e4b87e7f3737cb47c30b86d13acdf356020f3394a4e28c1b7477 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].source_window[1]: sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].source_window[2]: sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].source_window[3]: sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].source_window[4]: sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].source_window[5]: sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].source_window[6]: sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].title: sha256:ee0906ffe9ddb7038f84a6f1d36fd0c9c7785a3876e656298e38d4bdc380b0d2 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].why_it_matters: sha256:1d41b935172d9800e1ee3976ceddae1165522c99321d451f590ff68211ad68a6 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].agent: impact -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].agent_confidence: sha256:b4944c6ff08dc6f43da2e9c824669b7d927dd1fa976fadc7b456881f51bf5ccc -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].category: sha256:e9d2fa82c1b28de0b5f3b1a9a311c35290be120039e74565666b2eacd78a0db8 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].current_code: sha256:95abd0fa465e9d41f4578e977f3ac54ad99b05118deeb0127fd6d9a4bbd1e2eb -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].cwe: sha256:c051865328b3785824d077aa68c6c887594337a8876e6f8dde046cc48f8be749 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].file: triggarr/web/validation.py -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].fix_hint: sha256:252351e4eda92337711cbbace5af5f02864dcea6c4be018f3b456bf43a475f17 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].intent_doc_match: sha256:8ac24611cfe47c129e37108bc6adc6843c4fe8fb9c37c27fac8a1835ba660307 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].line: 87 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].problem: sha256:507f8e4ba7b0aadb6d37eb45b162b3ad5cb5b416bab5b6bc03772ac5a25b63e8 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].source_window[0]: sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].source_window[1]: sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].source_window[2]: sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].source_window[3]: sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].source_window[4]: sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].source_window[5]: sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].source_window[6]: sha256:8441e9dc7ef6b32e165b29cc5ef7cc39cd9b9e4a7728dcc9b01331b99f116253 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].title: sha256:1921f463d437650fec91853234a158ec90828e01fd98f1b6ed2ba67e6335191f -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].why_it_matters: sha256:2edd5b4f964f155da8f374a70159cbdfee4bc39a774ec4b2228164b531f2018c -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].agent: security -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].agent_confidence: sha256:ff5a1ae012afa5d4c889c50ad427aaf545d31a4fac04ffc1c4d03d403ba4250a -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].category: sha256:957cd792225924f94088800508637992ebc6cdcd9950ebff17e14c8fb598afc1 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].current_code: sha256:95abd0fa465e9d41f4578e977f3ac54ad99b05118deeb0127fd6d9a4bbd1e2eb -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].cwe: sha256:c051865328b3785824d077aa68c6c887594337a8876e6f8dde046cc48f8be749 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].file: triggarr/web/validation.py -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].fix_hint: sha256:c82e7f88d0fb6495468c03cb87ab6bf9167f18315a1baad908aa45ca42045ff3 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].line: 85 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].problem: sha256:9c81a46f569504bd0eae9fd1d872cafe7cd3a2bc8ca79bf401f43e2fbaf47eee -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].source_window[0]: sha256:fc6acc58b0d2e4b87e7f3737cb47c30b86d13acdf356020f3394a4e28c1b7477 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].source_window[1]: sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].source_window[2]: sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].source_window[3]: sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].source_window[4]: sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].source_window[5]: sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].source_window[6]: sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].title: sha256:8d2fc74b59a42d7d602ce7c21b310dec8115786bd291324a4c13377ba9de87c3 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].why_it_matters: sha256:42bd93e5a6ae97ed75d74c3a4262bec1920b1bbc360be044729c778fa4c7f7e8 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].orchestrator_score: 100 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].problem: sha256:d29277d7c711873f930b3d4ecec523322a93f64485339df7ef3ba212797c09fa -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].severity: sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].silenced_marker_nearby: sha256:fcbcf165908dd18a9e49f7ff27810176db8e9f63b4352213741664245224f8aa -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].snapshot.at_pass: 1 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].snapshot.band: critical -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].snapshot.canonical_line_content: sha256:4c3544b3e573f4cae2f0a8ee27029fe96c97df9cf442ed5697d802d7e50d84b5 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].snapshot.file: triggarr/web/validation.py -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].snapshot.line: 87 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].source_window[0]: sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].source_window[1]: sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].source_window[2]: sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].source_window[3]: sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].source_window[4]: sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].source_window[5]: sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].source_window[6]: sha256:8441e9dc7ef6b32e165b29cc5ef7cc39cd9b9e4a7728dcc9b01331b99f116253 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].stable_hash: sha256:8730351ae3e46f00b32fd22fb2bd5057bf6bfd36f7a5dd06c0eaa7f651237d44 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].status: new -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].title: sha256:c6e017fc57cd45cbe57a96af97f00116d33daee5dad01ca953c7377334f96ee3 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].why_it_matters: sha256:f47254a85dabf2d27ac2a6050626b14359c7cabbaf9c63a71553649f5f6752e4 -> (absent)
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].agent: (absent) -> codex-adversarial
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].agent_confidence: (absent) -> sha256:ad48ff99415b2f007dc35b7eb553fd1eb35ebfa2f2f308acd9488eeb86f71fa8
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].attribution[0]: (absent) -> sha256:610cb42c95dd518d546a1f6603bb920b2a5e04c6c1514e84e47433dc58102d3a
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].attribution[1]: (absent) -> sha256:361e7b1acb6d80d7ef7f8e0aa4204fcebe6a047e57167c83979fbcdb9d37833c
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].attribution[2]: (absent) -> sha256:96f34c94f7cf7eb0d8a8aadf48980e0ac0d131b90ee50a682424071e25f2f534
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].attribution[3]: (absent) -> sha256:cac9fa20faacbccf6f0e6b780fdfa8793d3bc0773ca4d5b280c4bbe9ac02cac3
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].band: (absent) -> critical
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].canonical_line_content: (absent) -> sha256:7d385043a71eca1b81988ac3c806d768705c1ce4f5b5c51e244961f0cc14f6da
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].category: (absent) -> sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].current_code: (absent) -> sha256:95abd0fa465e9d41f4578e977f3ac54ad99b05118deeb0127fd6d9a4bbd1e2eb
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].file: (absent) -> triggarr/web/validation.py
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].fix_hint: (absent) -> sha256:4557baec16295212ba42d53c790c300ddcdbe12bfc1f7f94c765973855bd04f1
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].id: (absent) -> sha256:73ca1c8c1b1765028ee41138e76ea51dc55c913de8ba80028c40cedfc30b6369
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].in_diff: (absent) -> sha256:b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].line: (absent) -> 85
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].agent: (absent) -> codex-adversarial
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].agent_confidence: (absent) -> sha256:ad48ff99415b2f007dc35b7eb553fd1eb35ebfa2f2f308acd9488eeb86f71fa8
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].category: (absent) -> sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].current_code: (absent) -> sha256:95abd0fa465e9d41f4578e977f3ac54ad99b05118deeb0127fd6d9a4bbd1e2eb
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].file: (absent) -> triggarr/web/validation.py
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].fix_hint: (absent) -> sha256:4557baec16295212ba42d53c790c300ddcdbe12bfc1f7f94c765973855bd04f1
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].line: (absent) -> 85
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].problem: (absent) -> sha256:37ea85c141434b0e8cc5df649d0a4b5b070efe15d60ff87f99e18a7fd6e184b4
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].severity: (absent) -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].source_window[0]: (absent) -> sha256:fc6acc58b0d2e4b87e7f3737cb47c30b86d13acdf356020f3394a4e28c1b7477
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].source_window[1]: (absent) -> sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].source_window[2]: (absent) -> sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].source_window[3]: (absent) -> sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].source_window[4]: (absent) -> sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].source_window[5]: (absent) -> sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].source_window[6]: (absent) -> sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].title: (absent) -> sha256:ee0906ffe9ddb7038f84a6f1d36fd0c9c7785a3876e656298e38d4bdc380b0d2
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].why_it_matters: (absent) -> sha256:1d41b935172d9800e1ee3976ceddae1165522c99321d451f590ff68211ad68a6
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].agent: (absent) -> bugs
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].agent_confidence: (absent) -> sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].category: (absent) -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].current_code: (absent) -> sha256:21ecfa845b615bcabfb9870e3f30b3064da664f49f86fe57529afdcddcda594a
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].cwe: (absent) -> sha256:4779bc407343d916c5a4f6a996174046419bdd87ce6c609054dc8788b3dfc233
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].file: (absent) -> triggarr/web/validation.py
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].fix_hint: (absent) -> sha256:cad6e60c8f0dae8f73d82ec9cf9880ee01b5c8db04cab2405e93a39e7d1ad527
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].line: (absent) -> 87
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].problem: (absent) -> sha256:d29277d7c711873f930b3d4ecec523322a93f64485339df7ef3ba212797c09fa
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].severity: (absent) -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].source_window[0]: (absent) -> sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].source_window[1]: (absent) -> sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].source_window[2]: (absent) -> sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].source_window[3]: (absent) -> sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].source_window[4]: (absent) -> sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].source_window[5]: (absent) -> sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].source_window[6]: (absent) -> sha256:8441e9dc7ef6b32e165b29cc5ef7cc39cd9b9e4a7728dcc9b01331b99f116253
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].title: (absent) -> sha256:c6e017fc57cd45cbe57a96af97f00116d33daee5dad01ca953c7377334f96ee3
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].why_it_matters: (absent) -> sha256:f47254a85dabf2d27ac2a6050626b14359c7cabbaf9c63a71553649f5f6752e4
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].agent: (absent) -> security
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].agent_confidence: (absent) -> sha256:ff5a1ae012afa5d4c889c50ad427aaf545d31a4fac04ffc1c4d03d403ba4250a
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].category: (absent) -> sha256:957cd792225924f94088800508637992ebc6cdcd9950ebff17e14c8fb598afc1
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].current_code: (absent) -> sha256:95abd0fa465e9d41f4578e977f3ac54ad99b05118deeb0127fd6d9a4bbd1e2eb
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].cwe: (absent) -> sha256:c051865328b3785824d077aa68c6c887594337a8876e6f8dde046cc48f8be749
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].file: (absent) -> triggarr/web/validation.py
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].fix_hint: (absent) -> sha256:c82e7f88d0fb6495468c03cb87ab6bf9167f18315a1baad908aa45ca42045ff3
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].line: (absent) -> 85
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].problem: (absent) -> sha256:9c81a46f569504bd0eae9fd1d872cafe7cd3a2bc8ca79bf401f43e2fbaf47eee
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].source_window[0]: (absent) -> sha256:fc6acc58b0d2e4b87e7f3737cb47c30b86d13acdf356020f3394a4e28c1b7477
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].source_window[1]: (absent) -> sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].source_window[2]: (absent) -> sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].source_window[3]: (absent) -> sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].source_window[4]: (absent) -> sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].source_window[5]: (absent) -> sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].source_window[6]: (absent) -> sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].title: (absent) -> sha256:8d2fc74b59a42d7d602ce7c21b310dec8115786bd291324a4c13377ba9de87c3
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].why_it_matters: (absent) -> sha256:42bd93e5a6ae97ed75d74c3a4262bec1920b1bbc360be044729c778fa4c7f7e8
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].agent: (absent) -> impact
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].agent_confidence: (absent) -> sha256:b4944c6ff08dc6f43da2e9c824669b7d927dd1fa976fadc7b456881f51bf5ccc
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].category: (absent) -> sha256:e9d2fa82c1b28de0b5f3b1a9a311c35290be120039e74565666b2eacd78a0db8
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].current_code: (absent) -> sha256:95abd0fa465e9d41f4578e977f3ac54ad99b05118deeb0127fd6d9a4bbd1e2eb
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].cwe: (absent) -> sha256:c051865328b3785824d077aa68c6c887594337a8876e6f8dde046cc48f8be749
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].file: (absent) -> triggarr/web/validation.py
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].fix_hint: (absent) -> sha256:252351e4eda92337711cbbace5af5f02864dcea6c4be018f3b456bf43a475f17
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].intent_doc_match: (absent) -> sha256:8ac24611cfe47c129e37108bc6adc6843c4fe8fb9c37c27fac8a1835ba660307
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].line: (absent) -> 87
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].problem: (absent) -> sha256:507f8e4ba7b0aadb6d37eb45b162b3ad5cb5b416bab5b6bc03772ac5a25b63e8
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].source_window[0]: (absent) -> sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].source_window[1]: (absent) -> sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].source_window[2]: (absent) -> sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].source_window[3]: (absent) -> sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].source_window[4]: (absent) -> sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].source_window[5]: (absent) -> sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].source_window[6]: (absent) -> sha256:8441e9dc7ef6b32e165b29cc5ef7cc39cd9b9e4a7728dcc9b01331b99f116253
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].title: (absent) -> sha256:1921f463d437650fec91853234a158ec90828e01fd98f1b6ed2ba67e6335191f
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].why_it_matters: (absent) -> sha256:2edd5b4f964f155da8f374a70159cbdfee4bc39a774ec4b2228164b531f2018c
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].orchestrator_score: (absent) -> 100
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].problem: (absent) -> sha256:37ea85c141434b0e8cc5df649d0a4b5b070efe15d60ff87f99e18a7fd6e184b4
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].severity: (absent) -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].silenced_marker_nearby: (absent) -> sha256:fcbcf165908dd18a9e49f7ff27810176db8e9f63b4352213741664245224f8aa
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].snapshot.at_pass: (absent) -> 1
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].snapshot.band: (absent) -> critical
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].snapshot.canonical_line_content: (absent) -> sha256:7d385043a71eca1b81988ac3c806d768705c1ce4f5b5c51e244961f0cc14f6da
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].snapshot.file: (absent) -> triggarr/web/validation.py
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].snapshot.line: (absent) -> 85
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].source_window[0]: (absent) -> sha256:fc6acc58b0d2e4b87e7f3737cb47c30b86d13acdf356020f3394a4e28c1b7477
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].source_window[1]: (absent) -> sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].source_window[2]: (absent) -> sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].source_window[3]: (absent) -> sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].source_window[4]: (absent) -> sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].source_window[5]: (absent) -> sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].source_window[6]: (absent) -> sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].stable_hash: (absent) -> sha256:946ae3bb78b9fe68eb04ff9099c6a981bd3dd7b736d83fc7a3fa671657ae5b28
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].status: (absent) -> new
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].title: (absent) -> sha256:ee0906ffe9ddb7038f84a6f1d36fd0c9c7785a3876e656298e38d4bdc380b0d2
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].why_it_matters: (absent) -> sha256:1d41b935172d9800e1ee3976ceddae1165522c99321d451f590ff68211ad68a6

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | triggarr/web/validation.py | 87 | critical | 100 | 37f78051c196 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/validation.py | 85 | critical | 100 | 6a3d6e71ed3f |

## runs/should-quiet-1/run-3

changed paths: 36
allowed: no

- UNALLOWED filtered[1].line: 87 -> 85
- UNALLOWED filtered[1].title: sha256:99d5d29be7b163b3f48d9c5e365783787fe79f5c6805cfd1b10851c431eeb60d -> sha256:80a12232c264dda1e6bc00ef0e716a661d8f64b98489fda45314e60bc34dfe31
- UNALLOWED filtered[2].line: 85 -> 87
- UNALLOWED filtered[2].title: sha256:80a12232c264dda1e6bc00ef0e716a661d8f64b98489fda45314e60bc34dfe31 -> sha256:99d5d29be7b163b3f48d9c5e365783787fe79f5c6805cfd1b10851c431eeb60d
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].agent: impact -> bugs
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].agent_confidence: sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763 -> sha256:8722616204217eddb39e7df969e0698aed8e599ba62ed2de1ce49b03ade0fede
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].category: sha256:ff610fb106a3a1c1cedcc6589f563a9a1da99b391e061593d0965d58ddaddceb -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].current_code: sha256:21ecfa845b615bcabfb9870e3f30b3064da664f49f86fe57529afdcddcda594a -> sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> sha256:c051865328b3785824d077aa68c6c887594337a8876e6f8dde046cc48f8be749
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].fix_hint: sha256:18a8665bcf42ce5a26bbf3534fe407d1fe4c2af210c33ec2892561c78c195c44 -> sha256:5f40e265b39d2613c98b7fe0d040481fa2a48128b9d6d118a972fd5cf826175f
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].line: 87 -> 85
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].problem: sha256:3125e8e66e71607c475052a6477513f445f3c78873fc3fbf55656874e9588099 -> sha256:6deaa30a2f6da48ea843358344080eefc91c8d4007f166164e97fca7c11055b7
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].severity: sha256:364bb7082249ee9fbc5247ee49735c4246f271b82c2745a35107ddda0d7cabcc -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].source_window[0]: sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b -> sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].source_window[1]: sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f -> sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].source_window[2]: sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55 -> sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].source_window[3]: sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f -> sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].source_window[4]: sha256:8441e9dc7ef6b32e165b29cc5ef7cc39cd9b9e4a7728dcc9b01331b99f116253 -> sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].title: sha256:99d5d29be7b163b3f48d9c5e365783787fe79f5c6805cfd1b10851c431eeb60d -> sha256:80a12232c264dda1e6bc00ef0e716a661d8f64b98489fda45314e60bc34dfe31
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].why_it_matters: sha256:4aaaf54038fe334343952580e98a55709eefc6f79b0a5f1d226391009bb7d698 -> sha256:b87f9b529b313ff37eed1e6b577cfeff9f34285e5471823afc5fbc09c1f986bc
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].agent: bugs -> impact
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].agent_confidence: sha256:8722616204217eddb39e7df969e0698aed8e599ba62ed2de1ce49b03ade0fede -> sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> sha256:ff610fb106a3a1c1cedcc6589f563a9a1da99b391e061593d0965d58ddaddceb
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].current_code: sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b -> sha256:21ecfa845b615bcabfb9870e3f30b3064da664f49f86fe57529afdcddcda594a
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].cwe: sha256:c051865328b3785824d077aa68c6c887594337a8876e6f8dde046cc48f8be749 -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].fix_hint: sha256:5f40e265b39d2613c98b7fe0d040481fa2a48128b9d6d118a972fd5cf826175f -> sha256:18a8665bcf42ce5a26bbf3534fe407d1fe4c2af210c33ec2892561c78c195c44
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].line: 85 -> 87
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].problem: sha256:6deaa30a2f6da48ea843358344080eefc91c8d4007f166164e97fca7c11055b7 -> sha256:3125e8e66e71607c475052a6477513f445f3c78873fc3fbf55656874e9588099
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> sha256:364bb7082249ee9fbc5247ee49735c4246f271b82c2745a35107ddda0d7cabcc
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].source_window[0]: sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce -> sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].source_window[1]: sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424 -> sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].source_window[2]: sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b -> sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].source_window[3]: sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f -> sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].source_window[4]: sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55 -> sha256:8441e9dc7ef6b32e165b29cc5ef7cc39cd9b9e4a7728dcc9b01331b99f116253
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].title: sha256:80a12232c264dda1e6bc00ef0e716a661d8f64b98489fda45314e60bc34dfe31 -> sha256:99d5d29be7b163b3f48d9c5e365783787fe79f5c6805cfd1b10851c431eeb60d
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].why_it_matters: sha256:b87f9b529b313ff37eed1e6b577cfeff9f34285e5471823afc5fbc09c1f986bc -> sha256:4aaaf54038fe334343952580e98a55709eefc6f79b0a5f1d226391009bb7d698

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/validation.py | 85 | critical | 100 | 0a40ea77053b |
| security | triggarr/web/validation.py | 80 | warning | 94 | 0fd4a28ca370 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | triggarr/web/validation.py | 85 | critical | 100 | 0a40ea77053b |
| security | triggarr/web/validation.py | 80 | warning | 94 | 0fd4a28ca370 |

## runs/third-organic-should-catch/run-2

changed paths: 209
allowed: no

- UNALLOWED filtered[0].reason: sha256:2674ad5367feccf89efe37d4270e6ffd44685556f909918da3a2f65372d64321 -> sha256:4b55bfc0a989ffc4e82bf563c44a171139d39696f4fd159c337a381ea7cdd900
- UNALLOWED filtered[0].title: sha256:4ad77cbe8eb444b23ebec784554d3b239c99f5511acac485637bda4cfcfd699b -> sha256:f478c3a42f7101d6bf7d7749d0e6a3ef4d33990cdd21446928c1b8515611ad77
- UNALLOWED filtered[1].reason: sha256:2674ad5367feccf89efe37d4270e6ffd44685556f909918da3a2f65372d64321 -> sha256:4b55bfc0a989ffc4e82bf563c44a171139d39696f4fd159c337a381ea7cdd900
- UNALLOWED filtered[1].title: sha256:f478c3a42f7101d6bf7d7749d0e6a3ef4d33990cdd21446928c1b8515611ad77 -> sha256:46156577598e762fd034b9236b48c54aa05ba91d56b816f55928a5c2ed1c7053
- UNALLOWED filtered[2].line: 307 -> 308
- UNALLOWED filtered[2].reason: sha256:2674ad5367feccf89efe37d4270e6ffd44685556f909918da3a2f65372d64321 -> sha256:4b55bfc0a989ffc4e82bf563c44a171139d39696f4fd159c337a381ea7cdd900
- UNALLOWED filtered[2].title: sha256:46156577598e762fd034b9236b48c54aa05ba91d56b816f55928a5c2ed1c7053 -> sha256:bfd4996ce76c5b6ffcddb9fe7a7d4dae40ceafffd8abdbb2d41a6b7b1ba223c6
- UNALLOWED findings.order: sha256:5bb613360d88b554ad4ccb5010a0dee8c6b3bb6f113be62a5ff7b9be06c11527 -> sha256:00bcd878e906380f38fb8d537257472179eb5e66a992bb199bc032d6ab57799e
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].agent: bugs -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].agent_confidence: sha256:8241649609f88ccd2a0a5b233a07a538ec313ff6adf695aa44a969dbca39f67d -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].attribution[0]: sha256:610cb42c95dd518d546a1f6603bb920b2a5e04c6c1514e84e47433dc58102d3a -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].attribution[1]: sha256:7d2a878caddd9607bc53d207b7a721b971748c3b78e5dc50f25325c50db20f2e -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].attribution[2]: sha256:96f34c94f7cf7eb0d8a8aadf48980e0ac0d131b90ee50a682424071e25f2f534 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].attribution[3]: sha256:cac9fa20faacbccf6f0e6b780fdfa8793d3bc0773ca4d5b280c4bbe9ac02cac3 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].band: critical -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].current_code: sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].fix_hint: sha256:5df4fdfb437521467fc9f175b141fb2ca4fb50a21d41739a052d0c0768a0fa5f -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].id: sha256:f7a33a0e52e4cd019310f1f9bca293dad2fd118a2304ea0ce7c3008a348766dd -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].in_diff: sha256:b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].line: 308 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].agent: bugs -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].agent_confidence: sha256:8241649609f88ccd2a0a5b233a07a538ec313ff6adf695aa44a969dbca39f67d -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].current_code: sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].fix_hint: sha256:5df4fdfb437521467fc9f175b141fb2ca4fb50a21d41739a052d0c0768a0fa5f -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].line: 308 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].problem: sha256:aa1ff19c77126b8b3c02551d26bb67abd330bf441860df50e4e159b793994959 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].source_window[0]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].source_window[1]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].source_window[2]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].source_window[3]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].source_window[4]: sha256:12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].title: sha256:bfd4996ce76c5b6ffcddb9fe7a7d4dae40ceafffd8abdbb2d41a6b7b1ba223c6 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].why_it_matters: sha256:4fcef8d0d92a115e63f49157702ff0dafb4578578af422f91ea39216a8aa9509 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].agent: codex-adversarial -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].agent_confidence: sha256:7b1a278f5abe8e9da907fc9c29dfd432d60dc76e17b0fabab659d2a508bc65c4 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].category: sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].fix_hint: sha256:953edf8d3868a97c9cfccb5d399ba889a536a505018662b9169b9d6b3cc6f0f4 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].line: 307 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].problem: sha256:d1d6222c09a22d0872e9c8981c9eb710304f1155a51513c90db72102fd81621b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].source_window[0]: sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].source_window[1]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].source_window[2]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].source_window[3]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].source_window[4]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].title: sha256:4ad77cbe8eb444b23ebec784554d3b239c99f5511acac485637bda4cfcfd699b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].why_it_matters: sha256:bde5b074f17a8d52c876a86de2f86b912d5dbb2ecf7e1c7d7db4718dd3a16ca2 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].agent: architecture -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].agent_confidence: sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].category: sha256:2b5b64f71e5ba181f65f150c8ed433facc7d0dc223cab631067d2ed40615ab86 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].line: 307 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].problem: sha256:8ac11b632cb0153f9181b09dd970ff6ca6e7efcb819cf78414ea0a617f662658 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].source_window[0]: sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].source_window[1]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].source_window[2]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].source_window[3]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].source_window[4]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].title: sha256:f478c3a42f7101d6bf7d7749d0e6a3ef4d33990cdd21446928c1b8515611ad77 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].why_it_matters: sha256:ce89de673f2b393a729892ef29f320971969d3ec2f8f08e0da921276a2d7fb0d -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].agent: impact -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].agent_confidence: sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].category: sha256:e9d2fa82c1b28de0b5f3b1a9a311c35290be120039e74565666b2eacd78a0db8 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].current_code: sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].cwe: sha256:4d616b416ea7dfb61c69c800dd3a83b4df88bf4fabcaa2451cf85ab9a8eb230e -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].fix_hint: sha256:bb6beeb721c59cfb7d6caad69b4438dd62d81aca9b5ae26843f41b7ec1c476c3 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].line: 307 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].problem: sha256:c5a70ac042c563996d84b4e97e9f24eb3f38a0f1de67808c1b1c0ac5b691af20 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].source_window[0]: sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].source_window[1]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].source_window[2]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].source_window[3]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].source_window[4]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].title: sha256:46156577598e762fd034b9236b48c54aa05ba91d56b816f55928a5c2ed1c7053 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].why_it_matters: sha256:63aabcd08104a6d5b145e1de38b41ac1bae8e3f737ce62d43ae97a8f440e14e3 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].orchestrator_score: 100 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].problem: sha256:aa1ff19c77126b8b3c02551d26bb67abd330bf441860df50e4e159b793994959 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].silenced_marker_nearby: sha256:fcbcf165908dd18a9e49f7ff27810176db8e9f63b4352213741664245224f8aa -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].snapshot.at_pass: 1 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].snapshot.band: critical -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].snapshot.canonical_line_content: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].snapshot.file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].snapshot.line: 308 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].source_window[0]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].source_window[1]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].source_window[2]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].source_window[3]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].source_window[4]: sha256:12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].stable_hash: sha256:b7db314a5fe3eafac160d0432cfff941176b462d23ed321c82a2d9ac2ff76f48 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].status: new -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].title: sha256:bfd4996ce76c5b6ffcddb9fe7a7d4dae40ceafffd8abdbb2d41a6b7b1ba223c6 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].why_it_matters: sha256:4fcef8d0d92a115e63f49157702ff0dafb4578578af422f91ea39216a8aa9509 -> (absent)
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].agent: (absent) -> codex-adversarial
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].agent_confidence: (absent) -> sha256:7b1a278f5abe8e9da907fc9c29dfd432d60dc76e17b0fabab659d2a508bc65c4
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].attribution[0]: (absent) -> sha256:610cb42c95dd518d546a1f6603bb920b2a5e04c6c1514e84e47433dc58102d3a
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].attribution[1]: (absent) -> sha256:7d2a878caddd9607bc53d207b7a721b971748c3b78e5dc50f25325c50db20f2e
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].attribution[2]: (absent) -> sha256:96f34c94f7cf7eb0d8a8aadf48980e0ac0d131b90ee50a682424071e25f2f534
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].attribution[3]: (absent) -> sha256:cac9fa20faacbccf6f0e6b780fdfa8793d3bc0773ca4d5b280c4bbe9ac02cac3
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].band: (absent) -> critical
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].category: (absent) -> sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].fix_hint: (absent) -> sha256:953edf8d3868a97c9cfccb5d399ba889a536a505018662b9169b9d6b3cc6f0f4
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].id: (absent) -> sha256:73ca1c8c1b1765028ee41138e76ea51dc55c913de8ba80028c40cedfc30b6369
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].line: (absent) -> 307
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].agent: (absent) -> codex-adversarial
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].agent_confidence: (absent) -> sha256:7b1a278f5abe8e9da907fc9c29dfd432d60dc76e17b0fabab659d2a508bc65c4
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].category: (absent) -> sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].fix_hint: (absent) -> sha256:953edf8d3868a97c9cfccb5d399ba889a536a505018662b9169b9d6b3cc6f0f4
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].line: (absent) -> 307
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].problem: (absent) -> sha256:d1d6222c09a22d0872e9c8981c9eb710304f1155a51513c90db72102fd81621b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].source_window[0]: (absent) -> sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].source_window[1]: (absent) -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].source_window[2]: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].source_window[3]: (absent) -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].source_window[4]: (absent) -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].title: (absent) -> sha256:4ad77cbe8eb444b23ebec784554d3b239c99f5511acac485637bda4cfcfd699b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].why_it_matters: (absent) -> sha256:bde5b074f17a8d52c876a86de2f86b912d5dbb2ecf7e1c7d7db4718dd3a16ca2
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].agent: (absent) -> architecture
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].agent_confidence: (absent) -> sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].category: (absent) -> sha256:2b5b64f71e5ba181f65f150c8ed433facc7d0dc223cab631067d2ed40615ab86
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].line: (absent) -> 307
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].problem: (absent) -> sha256:8ac11b632cb0153f9181b09dd970ff6ca6e7efcb819cf78414ea0a617f662658
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].source_window[0]: (absent) -> sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].source_window[1]: (absent) -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].source_window[2]: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].source_window[3]: (absent) -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].source_window[4]: (absent) -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].title: (absent) -> sha256:f478c3a42f7101d6bf7d7749d0e6a3ef4d33990cdd21446928c1b8515611ad77
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].why_it_matters: (absent) -> sha256:ce89de673f2b393a729892ef29f320971969d3ec2f8f08e0da921276a2d7fb0d
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].agent: (absent) -> impact
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].agent_confidence: (absent) -> sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].category: (absent) -> sha256:e9d2fa82c1b28de0b5f3b1a9a311c35290be120039e74565666b2eacd78a0db8
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].current_code: (absent) -> sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].cwe: (absent) -> sha256:4d616b416ea7dfb61c69c800dd3a83b4df88bf4fabcaa2451cf85ab9a8eb230e
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].fix_hint: (absent) -> sha256:bb6beeb721c59cfb7d6caad69b4438dd62d81aca9b5ae26843f41b7ec1c476c3
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].line: (absent) -> 307
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].problem: (absent) -> sha256:c5a70ac042c563996d84b4e97e9f24eb3f38a0f1de67808c1b1c0ac5b691af20
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].source_window[0]: (absent) -> sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].source_window[1]: (absent) -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].source_window[2]: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].source_window[3]: (absent) -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].source_window[4]: (absent) -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].title: (absent) -> sha256:46156577598e762fd034b9236b48c54aa05ba91d56b816f55928a5c2ed1c7053
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].why_it_matters: (absent) -> sha256:63aabcd08104a6d5b145e1de38b41ac1bae8e3f737ce62d43ae97a8f440e14e3
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].agent: (absent) -> bugs
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].agent_confidence: (absent) -> sha256:8241649609f88ccd2a0a5b233a07a538ec313ff6adf695aa44a969dbca39f67d
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].category: (absent) -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].current_code: (absent) -> sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].fix_hint: (absent) -> sha256:5df4fdfb437521467fc9f175b141fb2ca4fb50a21d41739a052d0c0768a0fa5f
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].line: (absent) -> 308
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].problem: (absent) -> sha256:aa1ff19c77126b8b3c02551d26bb67abd330bf441860df50e4e159b793994959
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].source_window[0]: (absent) -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].source_window[1]: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].source_window[2]: (absent) -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].source_window[3]: (absent) -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].source_window[4]: (absent) -> sha256:12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].title: (absent) -> sha256:bfd4996ce76c5b6ffcddb9fe7a7d4dae40ceafffd8abdbb2d41a6b7b1ba223c6
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].why_it_matters: (absent) -> sha256:4fcef8d0d92a115e63f49157702ff0dafb4578578af422f91ea39216a8aa9509
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].orchestrator_score: (absent) -> 100
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].problem: (absent) -> sha256:d1d6222c09a22d0872e9c8981c9eb710304f1155a51513c90db72102fd81621b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].snapshot.at_pass: (absent) -> 1
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].snapshot.band: (absent) -> critical
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].snapshot.canonical_line_content: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].snapshot.file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].snapshot.line: (absent) -> 307
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].source_window[0]: (absent) -> sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].source_window[1]: (absent) -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].source_window[2]: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].source_window[3]: (absent) -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].source_window[4]: (absent) -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].stable_hash: (absent) -> sha256:285c711120ebd151d747824a8d3822ec83263454a494590d70807c93a97f7b57
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].status: (absent) -> new
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].title: (absent) -> sha256:4ad77cbe8eb444b23ebec784554d3b239c99f5511acac485637bda4cfcfd699b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].why_it_matters: (absent) -> sha256:bde5b074f17a8d52c876a86de2f86b912d5dbb2ecf7e1c7d7db4718dd3a16ca2

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| bugs | src/angular/src/app/services/files/view-file.service.ts | 308 | critical | 100 | 2cb2358b0ad3 |
| impact | src/angular/src/app/tests/unittests/services/files/view-file.service.spec.ts | 246 | medium | 77 | 5b9b53868095 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | src/angular/src/app/services/files/view-file.service.ts | 307 | critical | 100 | 2d81f598f774 |
| impact | src/angular/src/app/tests/unittests/services/files/view-file.service.spec.ts | 246 | medium | 77 | 5b9b53868095 |

## runs/third-organic-should-catch/run-3

changed paths: 263
allowed: no

- UNALLOWED filtered[0].reason: sha256:cd5a63687ce45491ab73e7c71f2cea258d262005379c2366d2d1003b79de3258 -> sha256:1bd578ded95b292775ffb545d0b750ddd36698815d06609bf2c6f1a40c697605
- UNALLOWED filtered[0].title: sha256:c27d0c408f0a39339c9d667743858d13609d09be1380efebbffa9d2ae3db0ca2 -> sha256:7499492732b352fadc616cca95e97a5be55f621aed6d01b4390399cb1a682652
- UNALLOWED filtered[1].line: 308 -> 307
- UNALLOWED filtered[1].reason: sha256:cd5a63687ce45491ab73e7c71f2cea258d262005379c2366d2d1003b79de3258 -> sha256:1bd578ded95b292775ffb545d0b750ddd36698815d06609bf2c6f1a40c697605
- UNALLOWED filtered[1].title: sha256:ad3c8d9c6325552ea85b18e0a21a59d0d753457ba5923f4648ee9b72c6817b59 -> sha256:16afa0087177e845d48139b9c52687711237f672c1b26002c696abfafd9463d3
- UNALLOWED filtered[2].line: 307 -> 308
- UNALLOWED filtered[2].reason: sha256:cd5a63687ce45491ab73e7c71f2cea258d262005379c2366d2d1003b79de3258 -> sha256:1bd578ded95b292775ffb545d0b750ddd36698815d06609bf2c6f1a40c697605
- UNALLOWED filtered[2].title: sha256:7499492732b352fadc616cca95e97a5be55f621aed6d01b4390399cb1a682652 -> sha256:ad3c8d9c6325552ea85b18e0a21a59d0d753457ba5923f4648ee9b72c6817b59
- UNALLOWED filtered[3].line: 307 -> 308
- UNALLOWED filtered[3].reason: sha256:cd5a63687ce45491ab73e7c71f2cea258d262005379c2366d2d1003b79de3258 -> sha256:1bd578ded95b292775ffb545d0b750ddd36698815d06609bf2c6f1a40c697605
- UNALLOWED filtered[3].title: sha256:16afa0087177e845d48139b9c52687711237f672c1b26002c696abfafd9463d3 -> sha256:a70e59ad882d39ce6f35d14a543119ac8210921194f3b7d23628f9fb7de4a687
- UNALLOWED findings.order: sha256:c88e75a2c37e0f0b242146efa5a2dd90dff1f310b722bffcf268e2d8c158058d -> sha256:3ae04a0e8e294c0420361309fc2e892e32a178ca0e30c2eb734acc9e2a5ef0a9
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].agent: impact -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].agent_confidence: sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].attribution[0]: sha256:610cb42c95dd518d546a1f6603bb920b2a5e04c6c1514e84e47433dc58102d3a -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].attribution[1]: sha256:7d2a878caddd9607bc53d207b7a721b971748c3b78e5dc50f25325c50db20f2e -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].attribution[2]: sha256:96f34c94f7cf7eb0d8a8aadf48980e0ac0d131b90ee50a682424071e25f2f534 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].attribution[3]: sha256:b8ab7d08e15e9ae907f689cc4239ce39537c20a000625e915ccd6a0e4d027443 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].attribution[4]: sha256:cac9fa20faacbccf6f0e6b780fdfa8793d3bc0773ca4d5b280c4bbe9ac02cac3 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].band: critical -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].canonical_line_content: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].current_code: sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].cwe: sha256:4d616b416ea7dfb61c69c800dd3a83b4df88bf4fabcaa2451cf85ab9a8eb230e -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].fix_hint: sha256:fe163d1fcd8d1d9daf48b86b5dd43f28f72d837e475f4628e9064fa64a4df5f8 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].id: sha256:06bfd497fdf80ecf905506cba0fcd59d193f0aa4f2354a6b296433fb18a9e32e -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].in_diff: sha256:b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].intent_doc_match: sha256:eb8bf0d80db323992f6b634aab492b1e6d9e96a8e87a511c2a0db75ab929452c -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].line: 308 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].agent: impact -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].agent_confidence: sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].current_code: sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].cwe: sha256:4d616b416ea7dfb61c69c800dd3a83b4df88bf4fabcaa2451cf85ab9a8eb230e -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].fix_hint: sha256:fe163d1fcd8d1d9daf48b86b5dd43f28f72d837e475f4628e9064fa64a4df5f8 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].intent_doc_match: sha256:eb8bf0d80db323992f6b634aab492b1e6d9e96a8e87a511c2a0db75ab929452c -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].line: 308 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].problem: sha256:fffb6391c3fe3ab01e1703a3c26587def016157bf33518f3700a126270e71868 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].source_window[0]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].source_window[1]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].source_window[2]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].source_window[3]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].source_window[4]: sha256:12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].title: sha256:a70e59ad882d39ce6f35d14a543119ac8210921194f3b7d23628f9fb7de4a687 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].why_it_matters: sha256:4b05e754f229ec9e720a049d559dce46f5add8abf0758acee72963b24b0553ce -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].agent: codex-adversarial -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].agent_confidence: sha256:d6d824abba4afde81129c71dea75b8100e96338da5f416d2f69088f1960cb091 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].category: sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].current_code: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].fix_hint: sha256:84d7b79f6aa4abdc4cd1ea0f7908230f7854c33ae4aeec229f50cf85fe820781 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].line: 307 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].problem: sha256:4e6a84ace70c45965794815f70652082696b146f40b2606349ccee3d9e288dfb -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].severity: sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].source_window[0]: sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].source_window[1]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].source_window[2]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].source_window[3]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].source_window[4]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].title: sha256:c27d0c408f0a39339c9d667743858d13609d09be1380efebbffa9d2ae3db0ca2 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].why_it_matters: sha256:774d990c3c81786b55eec57555f75e95b6cc0ad50384945ffc53bf5b36a3436c -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].agent: bugs -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].agent_confidence: sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].current_code: sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].fix_hint: sha256:60dc48b1ca9224f608f7bd3250110c1eb3d767a48c321bfd1549928df2a9f7ee -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].line: 308 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].problem: sha256:cec3aaa956516af67f4aed9703df587ae81f2f02c4287d5d459869bf4a9295de -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].source_window[0]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].source_window[1]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].source_window[2]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].source_window[3]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].source_window[4]: sha256:12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].title: sha256:ad3c8d9c6325552ea85b18e0a21a59d0d753457ba5923f4648ee9b72c6817b59 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].why_it_matters: sha256:2808251d9dec1a6bb64f0176105cc2d51bd8f5917260a114a57d89d3cff320f1 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].agent: language-typescript -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].agent_confidence: sha256:b4944c6ff08dc6f43da2e9c824669b7d927dd1fa976fadc7b456881f51bf5ccc -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].category: sha256:a63437a8dd71536d683bcbedce42aa51a6ecaee7c407ee4868a1bdc5d2f0906a -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].current_code: sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].fix_hint: sha256:33a321b6216b5e7a1a4e720c7eda7b061862eef6a348c6c751261dd89831b4ec -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].line: 307 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].problem: sha256:77e019bdbba80ce92c789b11e74485f7c71025d9d03fff4e224153ada05c5c98 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].severity: sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].source_window[0]: sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].source_window[1]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].source_window[2]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].source_window[3]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].source_window[4]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].title: sha256:7499492732b352fadc616cca95e97a5be55f621aed6d01b4390399cb1a682652 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].why_it_matters: sha256:b466e43ee0add019e07afcdc8553c9fe19b66d54976a0e2cb51c5b3d53057ce1 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].agent: architecture -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].agent_confidence: sha256:48449a14a4ff7d79bb7a1b6f3d488eba397c36ef25634c111b49baf362511afc -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].category: sha256:2b5b64f71e5ba181f65f150c8ed433facc7d0dc223cab631067d2ed40615ab86 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].current_code: sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].fix_hint: sha256:40d3fc6659703f260a264131c7e414ed7a6a0294eff96ff00d3f8782710d859f -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].line: 307 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].problem: sha256:dd1ce5359168ccd378f42bcc15657962aadaf2bdffac819417d8af1c686185b7 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].source_window[0]: sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].source_window[1]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].source_window[2]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].source_window[3]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].source_window[4]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].title: sha256:16afa0087177e845d48139b9c52687711237f672c1b26002c696abfafd9463d3 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].why_it_matters: sha256:78368ba45dc0e7aa096873f1a2bd66717c9b60c4cd79b9a66c2279354688c779 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].orchestrator_score: 100 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].problem: sha256:fffb6391c3fe3ab01e1703a3c26587def016157bf33518f3700a126270e71868 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].silenced_marker_nearby: sha256:fcbcf165908dd18a9e49f7ff27810176db8e9f63b4352213741664245224f8aa -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].snapshot.at_pass: 1 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].snapshot.band: critical -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].snapshot.canonical_line_content: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].snapshot.file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].snapshot.line: 308 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].source_window[0]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].source_window[1]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].source_window[2]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].source_window[3]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].source_window[4]: sha256:12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].stable_hash: sha256:7eb0c8a0778a07d4514998853b40bf0f5b58f8ab9b90b0f3251e9254c96dd406 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].status: new -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].title: sha256:a70e59ad882d39ce6f35d14a543119ac8210921194f3b7d23628f9fb7de4a687 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].why_it_matters: sha256:4b05e754f229ec9e720a049d559dce46f5add8abf0758acee72963b24b0553ce -> (absent)
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].agent: (absent) -> codex-adversarial
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].agent_confidence: (absent) -> sha256:d6d824abba4afde81129c71dea75b8100e96338da5f416d2f69088f1960cb091
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].attribution[0]: (absent) -> sha256:610cb42c95dd518d546a1f6603bb920b2a5e04c6c1514e84e47433dc58102d3a
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].attribution[1]: (absent) -> sha256:7d2a878caddd9607bc53d207b7a721b971748c3b78e5dc50f25325c50db20f2e
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].attribution[2]: (absent) -> sha256:96f34c94f7cf7eb0d8a8aadf48980e0ac0d131b90ee50a682424071e25f2f534
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].attribution[3]: (absent) -> sha256:b8ab7d08e15e9ae907f689cc4239ce39537c20a000625e915ccd6a0e4d027443
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].attribution[4]: (absent) -> sha256:cac9fa20faacbccf6f0e6b780fdfa8793d3bc0773ca4d5b280c4bbe9ac02cac3
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].band: (absent) -> critical
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].canonical_line_content: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].category: (absent) -> sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].current_code: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].fix_hint: (absent) -> sha256:84d7b79f6aa4abdc4cd1ea0f7908230f7854c33ae4aeec229f50cf85fe820781
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].id: (absent) -> sha256:73ca1c8c1b1765028ee41138e76ea51dc55c913de8ba80028c40cedfc30b6369
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].line: (absent) -> 307
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].agent: (absent) -> codex-adversarial
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].agent_confidence: (absent) -> sha256:d6d824abba4afde81129c71dea75b8100e96338da5f416d2f69088f1960cb091
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].category: (absent) -> sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].current_code: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].fix_hint: (absent) -> sha256:84d7b79f6aa4abdc4cd1ea0f7908230f7854c33ae4aeec229f50cf85fe820781
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].line: (absent) -> 307
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].problem: (absent) -> sha256:4e6a84ace70c45965794815f70652082696b146f40b2606349ccee3d9e288dfb
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].severity: (absent) -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].source_window[0]: (absent) -> sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].source_window[1]: (absent) -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].source_window[2]: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].source_window[3]: (absent) -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].source_window[4]: (absent) -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].title: (absent) -> sha256:c27d0c408f0a39339c9d667743858d13609d09be1380efebbffa9d2ae3db0ca2
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].why_it_matters: (absent) -> sha256:774d990c3c81786b55eec57555f75e95b6cc0ad50384945ffc53bf5b36a3436c
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].agent: (absent) -> language-typescript
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].agent_confidence: (absent) -> sha256:b4944c6ff08dc6f43da2e9c824669b7d927dd1fa976fadc7b456881f51bf5ccc
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].category: (absent) -> sha256:a63437a8dd71536d683bcbedce42aa51a6ecaee7c407ee4868a1bdc5d2f0906a
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].current_code: (absent) -> sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].fix_hint: (absent) -> sha256:33a321b6216b5e7a1a4e720c7eda7b061862eef6a348c6c751261dd89831b4ec
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].line: (absent) -> 307
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].problem: (absent) -> sha256:77e019bdbba80ce92c789b11e74485f7c71025d9d03fff4e224153ada05c5c98
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].severity: (absent) -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].source_window[0]: (absent) -> sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].source_window[1]: (absent) -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].source_window[2]: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].source_window[3]: (absent) -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].source_window[4]: (absent) -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].title: (absent) -> sha256:7499492732b352fadc616cca95e97a5be55f621aed6d01b4390399cb1a682652
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].why_it_matters: (absent) -> sha256:b466e43ee0add019e07afcdc8553c9fe19b66d54976a0e2cb51c5b3d53057ce1
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].agent: (absent) -> architecture
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].agent_confidence: (absent) -> sha256:48449a14a4ff7d79bb7a1b6f3d488eba397c36ef25634c111b49baf362511afc
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].category: (absent) -> sha256:2b5b64f71e5ba181f65f150c8ed433facc7d0dc223cab631067d2ed40615ab86
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].current_code: (absent) -> sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].fix_hint: (absent) -> sha256:40d3fc6659703f260a264131c7e414ed7a6a0294eff96ff00d3f8782710d859f
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].line: (absent) -> 307
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].problem: (absent) -> sha256:dd1ce5359168ccd378f42bcc15657962aadaf2bdffac819417d8af1c686185b7
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].source_window[0]: (absent) -> sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].source_window[1]: (absent) -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].source_window[2]: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].source_window[3]: (absent) -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].source_window[4]: (absent) -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].title: (absent) -> sha256:16afa0087177e845d48139b9c52687711237f672c1b26002c696abfafd9463d3
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].why_it_matters: (absent) -> sha256:78368ba45dc0e7aa096873f1a2bd66717c9b60c4cd79b9a66c2279354688c779
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].agent: (absent) -> bugs
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].agent_confidence: (absent) -> sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].category: (absent) -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].current_code: (absent) -> sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].fix_hint: (absent) -> sha256:60dc48b1ca9224f608f7bd3250110c1eb3d767a48c321bfd1549928df2a9f7ee
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].line: (absent) -> 308
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].problem: (absent) -> sha256:cec3aaa956516af67f4aed9703df587ae81f2f02c4287d5d459869bf4a9295de
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].source_window[0]: (absent) -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].source_window[1]: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].source_window[2]: (absent) -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].source_window[3]: (absent) -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].source_window[4]: (absent) -> sha256:12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].title: (absent) -> sha256:ad3c8d9c6325552ea85b18e0a21a59d0d753457ba5923f4648ee9b72c6817b59
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].why_it_matters: (absent) -> sha256:2808251d9dec1a6bb64f0176105cc2d51bd8f5917260a114a57d89d3cff320f1
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].agent: (absent) -> impact
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].agent_confidence: (absent) -> sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].category: (absent) -> sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].current_code: (absent) -> sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].cwe: (absent) -> sha256:4d616b416ea7dfb61c69c800dd3a83b4df88bf4fabcaa2451cf85ab9a8eb230e
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].fix_hint: (absent) -> sha256:fe163d1fcd8d1d9daf48b86b5dd43f28f72d837e475f4628e9064fa64a4df5f8
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].intent_doc_match: (absent) -> sha256:eb8bf0d80db323992f6b634aab492b1e6d9e96a8e87a511c2a0db75ab929452c
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].line: (absent) -> 308
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].problem: (absent) -> sha256:fffb6391c3fe3ab01e1703a3c26587def016157bf33518f3700a126270e71868
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].source_window[0]: (absent) -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].source_window[1]: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].source_window[2]: (absent) -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].source_window[3]: (absent) -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].source_window[4]: (absent) -> sha256:12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].title: (absent) -> sha256:a70e59ad882d39ce6f35d14a543119ac8210921194f3b7d23628f9fb7de4a687
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].why_it_matters: (absent) -> sha256:4b05e754f229ec9e720a049d559dce46f5add8abf0758acee72963b24b0553ce
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].orchestrator_score: (absent) -> 100
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].problem: (absent) -> sha256:4e6a84ace70c45965794815f70652082696b146f40b2606349ccee3d9e288dfb
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].severity: (absent) -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].silenced_marker_nearby: (absent) -> sha256:fcbcf165908dd18a9e49f7ff27810176db8e9f63b4352213741664245224f8aa
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].snapshot.at_pass: (absent) -> 1
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].snapshot.band: (absent) -> critical
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].snapshot.canonical_line_content: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].snapshot.file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].snapshot.line: (absent) -> 307
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].source_window[0]: (absent) -> sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].source_window[1]: (absent) -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].source_window[2]: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].source_window[3]: (absent) -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].source_window[4]: (absent) -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].stable_hash: (absent) -> sha256:6e20535e4e09ae3726c8cd73a5104df2329b1adf771d97bc7002b37f2d7dad0e
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].status: (absent) -> new
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].title: (absent) -> sha256:c27d0c408f0a39339c9d667743858d13609d09be1380efebbffa9d2ae3db0ca2
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].why_it_matters: (absent) -> sha256:774d990c3c81786b55eec57555f75e95b6cc0ad50384945ffc53bf5b36a3436c

before

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| impact | src/angular/src/app/services/files/view-file.service.ts | 308 | critical | 100 | 01ed78b6a684 |
| impact | src/angular/src/app/pages/files/transfer-row.component.html | 33 | medium | 70 | 9c9ae15a8afd |
| impact | src/angular/src/app/tests/unittests/services/files/view-file.service.spec.ts | 246 | warning | 80 | ab416b2d0126 |

after

| agent | file | line | band | score | stable_hash |
|---|---|---|---|---|---|
| codex-adversarial | src/angular/src/app/services/files/view-file.service.ts | 307 | critical | 100 | 7c6faa94a2af |
| impact | src/angular/src/app/pages/files/transfer-row.component.html | 33 | medium | 70 | 9c9ae15a8afd |
| impact | src/angular/src/app/tests/unittests/services/files/view-file.service.spec.ts | 246 | warning | 80 | ab416b2d0126 |

## Fire-state check

Each of the 154 runs was scored by both scorers (`replay.load_scorer`, `replay.iter_runs(roots=replay.DIFF_ROOTS)`) and `replay.fires` compared per run.

0 runs changed fire state

All 27 differing runs fire before and after.

## Reason per differing run

Members at the changed site: agent, line, severity/agent confidence, and the member's own lone-lane score against the deep-review cutoff 70. A: critical -> warning. B: lead member switches at an unchanged critical/100. C: row unchanged, member order and absorbed list only. (protected) = a protected catch run.

- runs-v2.10-phase40/batch1/triggarr-secret-in-logs/run-1 [C]: row unchanged (impact L233 critical/100, identity 1b7b0aee39af). Credited (same-line qualifying Codex/Claude members): architecture L233 medium/90, alone 96 (clears 70); impact L233 medium/85, alone 85 (clears 70); codex L233 high/100, alone 100 (clears 70). The members outside it (security L235 high/95, alone 100 (clears 70); impact L233 low/75, alone 63 (below 70); compliance L233 low/30, alone 50 (below 70)) no longer borrow the +10 / ceiling release, so their own scores drop and the member list and the absorbed-members list (filtered[]) reorder. No band, score or fire state changes.
- runs-v2.10-phase40/batch2/triggarr-secret-in-logs/run-1 [C]: row unchanged (security L233 critical/100, identity 087270666450). Credited (same-line qualifying Codex/Claude members): security L233 medium/85, alone 97 (clears 70); impact L233 high/88, alone 93 (clears 70); compliance L233 low/55, alone 75 (clears 70); codex L233 high/100, alone 100 (clears 70). The members outside it (architecture L232 medium/88, alone 94 (clears 70); bugs L233 low/35, alone 33 (below 70)) no longer borrow the +10 / ceiling release, so their own scores drop and the member list and the absorbed-members list (filtered[]) reorder. No band, score or fire state changes.
- runs-v2.10-phase40/batch3/triggarr-secret-in-logs/run-1 [B]: before: architecture L235 led at critical/100 using the row-wide second opinion. Now only the same-line qualifying Codex/Claude members are credited (security L233 medium/78, alone 90 (clears 70); codex L233 high/100, alone 100 (clears 70)); architecture is not among them (line L235, not L233), so it is capped at 94 and the credited security L233 leads at critical/100. Band and score of the row are unchanged; the row identity changes (1c3fbec96c05 -> a3152fbf25ef).
- runs-v2.10-phase40/final/triggarr-secret-in-logs/run-1 [B] (protected): before: architecture L235 led at critical/100 using the row-wide second opinion. Now only the same-line qualifying Codex/Claude members are credited (bugs L233 medium/70, alone 80 (clears 70); security L233 medium/92, alone 100 (clears 70); impact L233 medium/80, alone 80 (clears 70); codex L233 high/100, alone 100 (clears 70)); architecture is not among them (line L235, not L233), so it is capped at 94 and the credited codex L233 leads at critical/100. Band and score of the row are unchanged; the row identity changes (5a47a4976122 -> 8f4d653e7115).
- runs-v2.10-phase43/first/should-quiet-4/run-2 [A] (pre-approved O-3): codex L107 (medium/99) led critical/100 because a co-located Claude note counted as a second opinion. Under D-05 no Claude-lane member at the site clears the cutoff on its own (bugs L108 medium/55, alone 65 (below 70); bugs L108 low/40, alone 38 (below 70); architecture L106 medium/45, alone 51 (below 70); impact L109 low/30, alone 18 (below 70); security L106 low/35, alone 35 (below 70)), so the Codex member is lone: its score above the ceiling is capped at 94 -> warning. Same row identity (de932df74922).
- runs-v2.10-phase43/first/should-quiet-4/run-3 [A]: codex L107 (medium/99) led critical/100 because a co-located Claude note counted as a second opinion. Under D-05 the Claude-lane member(s) that do clear the cutoff alone sit on another line (bugs L108 medium/60, alone 70 (clears 70)), so the same-line rule gives no pair; the ones on L107 are absent, so the Codex member is lone: its score above the ceiling is capped at 94 -> warning. Same row identity (fedecf9ededf).
- runs-v2.10-phase43/first/should-quiet-6/run-1 [A] (pre-approved O-3): codex L139 (medium/99) led critical/100 because a co-located Claude note counted as a second opinion. Under D-05 no Claude-lane member at the site clears the cutoff on its own (bugs L139 low/40, alone 38 (below 70); bugs L139 low/35, alone 33 (below 70); impact L139 low/60, alone 48 (below 70); impact L139 low/25, alone 13 (below 70)), so the Codex member is lone: its score above the ceiling is capped at 94 -> warning. Same row identity (c93be6bfe251).
- runs-v2.10-phase43/first/should-quiet-6/run-2 [C]: row unchanged (codex L139 critical/100, identity 92e9bcdf8831). Credited (same-line qualifying Codex/Claude members): codex L139 medium/99, alone 100 (clears 70); bugs L139 medium/70, alone 80 (clears 70). The members outside it (bugs L139 low/45, alone 43 (below 70); bugs L139 low/35, alone 33 (below 70); impact L139 low/30, alone 18 (below 70); architecture L139 low/65, alone 59 (below 70); architecture L139 medium/45, alone 21 (below 70)) no longer borrow the +10 / ceiling release, so their own scores drop and the member list and the absorbed-members list (filtered[]) reorder. No band, score or fire state changes.
- runs-v2.10-phase43/first/should-quiet-6/run-3 [C]: row unchanged (codex L139 critical/100, identity c93be6bfe251). Credited (same-line qualifying Codex/Claude members): codex L139 medium/99, alone 100 (clears 70); bugs L139 medium/68, alone 78 (clears 70). The members outside it (bugs L139 low/55, alone 53 (below 70); architecture L139 medium/55, alone 61 (below 70); architecture L137 low/50, alone 44 (below 70); impact L139 low/60, alone 48 (below 70); impact L139 low/30, alone 18 (below 70)) no longer borrow the +10 / ceiling release, so their own scores drop and the member list and the absorbed-members list (filtered[]) reorder. No band, score or fire state changes.
- runs-v2.10-phase43/first/should-quiet-7/run-2 [C]: row unchanged (bugs L550 critical/100, identity 234ca986d72e). Credited (same-line qualifying Codex/Claude members): bugs L550 medium/80, alone 90 (clears 70); impact L550 medium/80, alone 80 (clears 70); codex L550 medium/99, alone 100 (clears 70). The members outside it (bugs L550 low/60, alone 58 (below 70); bugs L550 medium/55, alone 65 (below 70); impact L550 low/70, alone 58 (below 70); impact L550 low/40, alone 28 (below 70)) no longer borrow the +10 / ceiling release, so their own scores drop and the member list and the absorbed-members list (filtered[]) reorder. No band, score or fire state changes.
- runs-v2.10-phase43/first/should-quiet-7/run-3 [C]: row unchanged (impact L550 critical/100, identity 2b1a20a238c5). Credited (same-line qualifying Codex/Claude members): codex L550 medium/99, alone 100 (clears 70); bugs L550 medium/85, alone 95 (clears 70); impact L550 medium/80, alone 80 (clears 70). The members outside it (bugs L550 low/60, alone 58 (below 70); bugs L550 medium/55, alone 65 (below 70); architecture L550 low/35, alone 29 (below 70); impact L550 low/40, alone 28 (below 70)) no longer borrow the +10 / ceiling release, so their own scores drop and the member list and the absorbed-members list (filtered[]) reorder. No band, score or fire state changes.
- runs-v2.10-phase43/first/triggarr-autoescape/run-2 [C]: row unchanged (codex L45 critical/100, identity 4f30f8fb283f). Credited (same-line qualifying Codex/Claude members): codex L45 high/99, alone 100 (clears 70); architecture L45 medium/80, alone 86 (clears 70); impact L45 medium/72, alone 72 (clears 70); compliance L45 medium/60, alone 92 (clears 70). The members outside it (bugs L45 low/70, alone 68 (below 70); impact L45 low/80, alone 68 (below 70); security L45 low/35, alone 35 (below 70); framework-fastapi L45 low/58, alone 58 (below 70)) no longer borrow the +10 / ceiling release, so their own scores drop and the member list and the absorbed-members list (filtered[]) reorder. No band, score or fire state changes.
- runs-v2.10-phase43/first/triggarr-secret-in-logs/run-1 [A]: codex L232 (high/99) led critical/100 because a co-located Claude note counted as a second opinion. Under D-05 the Claude-lane member(s) that do clear the cutoff alone sit on another line (architecture L233 medium/85, alone 91 (clears 70); compliance L233 high/85, alone 100 (clears 70)), so the same-line rule gives no pair; the ones on L232 are absent, so the Codex member is lone: its score above the ceiling is capped at 94 -> warning. Same row identity (13f543dd935e). Also: the members outside the credit reorder (20 member-order / absorbed-list lines; no further band or score change).
- runs-v2.10-phase43/first/triggarr-secret-in-logs/run-3 [C]: row unchanged (codex L233 critical/100, identity 5718c2673139). Credited (same-line qualifying Codex/Claude members): codex L233 high/100, alone 100 (clears 70); bugs L233 medium/62, alone 72 (clears 70); architecture L233 medium/82, alone 88 (clears 70); security L233 medium/78, alone 90 (clears 70); compliance L233 low/52, alone 72 (clears 70). The members outside it (impact L233 medium/68, alone 68 (below 70)) no longer borrow the +10 / ceiling release, so their own scores drop and the member list and the absorbed-members list (filtered[]) reorder. No band, score or fire state changes.
- runs-v2.10-phase43/retune/should-quiet-6/run-1 [A] (pre-approved O-3): codex L139 (medium/99) led critical/100 because a co-located Claude note counted as a second opinion. Under D-05 no Claude-lane member at the site clears the cutoff on its own (bugs L139 medium/55, alone 65 (below 70); bugs L139 low/30, alone 28 (below 70); impact L139 low/30, alone 18 (below 70)), so the Codex member is lone: its score above the ceiling is capped at 94 -> warning. Same row identity (c93be6bfe251).
- runs-v2.10-phase43/retune/should-quiet-6/run-2 [A] (pre-approved O-3): codex L139 (medium/99) led critical/100 because a co-located Claude note counted as a second opinion. Under D-05 no Claude-lane member at the site clears the cutoff on its own (bugs L139 low/55, alone 53 (below 70); bugs L139 low/35, alone 33 (below 70); architecture L139 low/35, alone 29 (below 70); impact L139 low/30, alone 18 (below 70)), so the Codex member is lone: its score above the ceiling is capped at 94 -> warning. Same row identity (4ac803dd7f3d).
- runs-v2.10-phase43/retune/should-quiet-6/run-3 [A] (pre-approved O-3): codex L139 (medium/99) led critical/100 because a co-located Claude note counted as a second opinion. Under D-05 no Claude-lane member at the site clears the cutoff on its own (bugs L139 low/40, alone 38 (below 70); bugs L139 low/35, alone 33 (below 70); bugs L139 low/30, alone 28 (below 70); impact L139 low/40, alone 28 (below 70); impact L139 low/35, alone 23 (below 70)), so the Codex member is lone: its score above the ceiling is capped at 94 -> warning. Same row identity (c93be6bfe251). Also: the members outside the credit reorder (32 member-order / absorbed-list lines; no further band or score change).
- runs-v2.10/third-organic-should-catch/run-2 [C] (protected): row unchanged (codex L307 critical/100, identity 25b18f8a4353). Credited (same-line qualifying Codex/Claude members): bugs L307 medium/72, alone 82 (clears 70); architecture L307 high/92, alone 100 (clears 70); impact L307 medium/95, alone 95 (clears 70); codex L307 medium/100, alone 100 (clears 70). The members outside it (language-typescript L308 medium/75, alone 87 (clears 70)) no longer borrow the +10 / ceiling release, so their own scores drop and the member list and the absorbed-members list (filtered[]) reorder. No band, score or fire state changes.
- runs-v2.10/triggarr-secret-in-logs/run-1 [A] (protected): codex L233 (high/100) led critical/100 because a co-located Claude note counted as a second opinion. Under D-05 the Claude-lane member(s) that do clear the cutoff alone sit on another line (architecture L232 medium/88, alone 94 (clears 70)), so the same-line rule gives no pair; the ones on L233 are impact L233 low/78, alone 66 (below 70), so the Codex member is lone: its score above the ceiling is capped at 94 -> warning. Same row identity (12fe298fc07e).
- runs-v2.11-phase49/first/should-quiet-6/run-1 [A] (pre-approved O-3): codex L135 (medium/99) led critical/100 because a co-located Claude note counted as a second opinion. Under D-05 no Claude-lane member at the site clears the cutoff on its own (architecture L135 low/40, alone 34 (below 70)), so the Codex member is lone: its score above the ceiling is capped at 94 -> warning. Same row identity (780e77edbe52).
- runs-v2.11-phase49/first/should-quiet-6/run-2 [A] (pre-approved O-3): codex L139 (medium/99) led critical/100 because a co-located Claude note counted as a second opinion. Under D-05 no Claude-lane member at the site clears the cutoff on its own (bugs L139 medium/55, alone 65 (below 70); bugs L139 low/35, alone 33 (below 70); impact L139 low/20, alone 8 (below 70)), so the Codex member is lone: its score above the ceiling is capped at 94 -> warning. Same row identity (c93be6bfe251).
- runs-v2.11-phase49/first/should-quiet-6/run-3 [A] (pre-approved O-3): codex L139 (medium/99) led critical/100 because a co-located Claude note counted as a second opinion. Under D-05 no Claude-lane member at the site clears the cutoff on its own (bugs L139 low/40, alone 38 (below 70); bugs L139 low/35, alone 33 (below 70); impact L139 low/40, alone 28 (below 70)), so the Codex member is lone: its score above the ceiling is capped at 94 -> warning. Same row identity (993c32eb9391). Also: the members outside the credit reorder (18 member-order / absorbed-list lines; no further band or score change).
- runs-v2.11-phase49/first/triggarr-secret-in-logs/run-2 [C]: row unchanged (codex L233 critical/100, identity 231222c433af). Credited (same-line qualifying Codex/Claude members): codex L233 high/100, alone 100 (clears 70); architecture L233 medium/85, alone 91 (clears 70); impact L233 medium/70, alone 70 (clears 70). The members outside it (bugs L235 medium/62, alone 72 (clears 70); security L232 high/92, alone 100 (clears 70); compliance L232 high/88, alone 100 (clears 70)) no longer borrow the +10 / ceiling release, so their own scores drop and the member list and the absorbed-members list (filtered[]) reorder. No band, score or fire state changes.
- runs/should-quiet-1/run-1 [B]: before: bugs L87 led at critical/100 using the row-wide second opinion. Now only the same-line qualifying Codex/Claude members are credited (security L85 medium/70, alone 82 (clears 70); codex L85 high/95, alone 100 (clears 70)); bugs is not among them (line L87, not L85), so it is capped at 94 and the credited codex L85 leads at critical/100. Band and score of the row are unchanged; the row identity changes (37f78051c196 -> 6a3d6e71ed3f).
- runs/should-quiet-1/run-3 [C]: row unchanged (codex L85 critical/100, identity 0a40ea77053b). Credited (same-line qualifying Codex/Claude members): bugs L85 medium/72, alone 82 (clears 70); codex L85 high/92, alone 100 (clears 70). The members outside it (bugs L87 high/88, alone 100 (clears 70); impact L87 low/90, alone 78 (clears 70)) no longer borrow the +10 / ceiling release, so their own scores drop and the member list and the absorbed-members list (filtered[]) reorder. No band, score or fire state changes.
- runs/third-organic-should-catch/run-2 [B] (protected): before: bugs L308 led at critical/100 using the row-wide second opinion. Now only the same-line qualifying Codex/Claude members are credited (architecture L307 medium/90, alone 96 (clears 70); impact L307 medium/90, alone 90 (clears 70); codex L307 medium/96, alone 100 (clears 70)); bugs is not among them (line L308, not L307), so it is capped at 94 and the credited codex L307 leads at critical/100. Band and score of the row are unchanged; the row identity changes (2cb2358b0ad3 -> 2d81f598f774).
- runs/third-organic-should-catch/run-3 [B] (protected): before: impact L308 led at critical/100 using the row-wide second opinion. Now only the same-line qualifying Codex/Claude members are credited (architecture L307 medium/80, alone 86 (clears 70); language-typescript L307 high/85, alone 100 (clears 70); codex L307 high/97, alone 100 (clears 70)); impact is not among them (line L308, not L307), so it is capped at 94 and the credited codex L307 leads at critical/100. Band and score of the row are unchanged; the row identity changes (01ed78b6a684 -> 7c6faa94a2af).

Totals: A 11, B 5, C 11.

## Pre-approved set (O-3)

Research expectation = RESEARCH Pattern 1 table (row-wide qualification-only prototype). Measured = this report (per-member scorer, blob 5ca2ddd).

| run | research (agent, line, before -> after) | measured (agent, line, before -> after) | changed paths | mark |
|---|---|---|---|---|
| runs-v2.10-phase43/first/should-quiet-4/run-2 | codex L107 critical/100 -> warning/94 | codex L107 critical/100 -> warning/94 | 3 | matches research |
| runs-v2.10-phase43/first/should-quiet-6/run-1 | codex L139 critical/100 -> warning/94 | codex L139 critical/100 -> warning/94 | 3 | matches research |
| runs-v2.10-phase43/retune/should-quiet-6/run-1 | codex L139 critical/100 -> warning/94 | codex L139 critical/100 -> warning/94 | 3 | matches research |
| runs-v2.10-phase43/retune/should-quiet-6/run-2 | codex L139 critical/100 -> warning/94 | codex L139 critical/100 -> warning/94 | 3 | matches research |
| runs-v2.10-phase43/retune/should-quiet-6/run-3 | codex L139 critical/100 -> warning/94 | codex L139 critical/100 -> warning/94 (also 32 member-order / absorbed-list lines in the same row; see Reason) | 35 | matches research |
| runs-v2.11-phase49/first/should-quiet-6/run-1 | codex L135 critical/100 -> warning/94 | codex L135 critical/100 -> warning/94 | 3 | matches research |
| runs-v2.11-phase49/first/should-quiet-6/run-2 | codex L139 critical/100 -> warning/94 | codex L139 critical/100 -> warning/94 | 3 | matches research |
| runs-v2.11-phase49/first/should-quiet-6/run-3 | codex L139 critical/100 -> warning/94 | codex L139 critical/100 -> warning/94 (also 18 member-order / absorbed-list lines in the same row; see Reason) | 21 | matches research |

pre-approved runs changed or absent: 0

differences beyond the pre-approved set: 19

### runs-v2.10-phase40/batch1/triggarr-secret-in-logs/run-1 [C]

- UNALLOWED filtered[0].line: 235 -> 233
- UNALLOWED filtered[0].title: sha256:ee0df4bffba47551df5d4522229a41f74715ea4f472c3030d06c95b152695b46 -> sha256:c187cf94b4636af8ae6fc2357a89e49751abaf25bb1688271ececba9bdfd86c0
- UNALLOWED filtered[1].title: sha256:c187cf94b4636af8ae6fc2357a89e49751abaf25bb1688271ececba9bdfd86c0 -> sha256:b0ffbfb4726ebb751a2d2534746a4d464a5e65297c517dfeb992d37310556d23
- UNALLOWED filtered[2].line: 233 -> 235
- UNALLOWED filtered[2].title: sha256:b0ffbfb4726ebb751a2d2534746a4d464a5e65297c517dfeb992d37310556d23 -> sha256:ee0df4bffba47551df5d4522229a41f74715ea4f472c3030d06c95b152695b46
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].agent: security -> architecture
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].agent_confidence: sha256:ad48ff99415b2f007dc35b7eb553fd1eb35ebfa2f2f308acd9488eeb86f71fa8 -> sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].category: sha256:8cc5192684865079dea813dcf1f24a4cac21e0e4174cc4e30a1460c44a643178 -> sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].cwe: sha256:d9bf3eb9e951563cd03de1af55fd1d83b420072b0c1578408d5f10317c0e52b7 -> sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].fix_hint: sha256:23b2464bc9a84fef1436ed281be995487c409901c3a40ae36764507f33a46d14 -> sha256:55428a32ecc4f2a54c92dd0854fd0eca19bf6ba70514224e4c32a8b3fab3193c
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].line: 235 -> 233
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].problem: sha256:4e2359f51652f344cb334be3d515b791fc22b8587de815301e15d686276eaa41 -> sha256:664da5f6b31a1280edbc5bc4a25ac25c9cc2200d465f9a07bfcd202bf205d686
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].severity: sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].source_window[0]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].source_window[1]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].source_window[2]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].source_window[3]: sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286 -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].source_window[4]: sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].title: sha256:ee0df4bffba47551df5d4522229a41f74715ea4f472c3030d06c95b152695b46 -> sha256:c187cf94b4636af8ae6fc2357a89e49751abaf25bb1688271ececba9bdfd86c0
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[1].why_it_matters: sha256:8ae7b293dff575421242ad6075f7216ffb1f5b1c112a1c9890cfb8622f6c7c1d -> sha256:9880f3889a8fff69c88788121834c5f0bc028b004a3020ef0d1f400d479ea46f
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[2].agent: architecture -> codex-adversarial
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[2].agent_confidence: sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763 -> sha256:ad57366865126e55649ecb23ae1d48887544976efea46a48eb5d85a6eeb4d306
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[2].category: sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2 -> sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[2].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> (absent)
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[2].cwe: sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[2].fix_hint: sha256:55428a32ecc4f2a54c92dd0854fd0eca19bf6ba70514224e4c32a8b3fab3193c -> sha256:132f6b00089c4483f09b981341948496bbb9ec979170c17a9f448424279141fb
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[2].problem: sha256:664da5f6b31a1280edbc5bc4a25ac25c9cc2200d465f9a07bfcd202bf205d686 -> sha256:e51f716a0a4fc876bcdebf001804ecdf8bbfed55907372b954c50cb72f06548d
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[2].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[2].title: sha256:c187cf94b4636af8ae6fc2357a89e49751abaf25bb1688271ececba9bdfd86c0 -> sha256:b0ffbfb4726ebb751a2d2534746a4d464a5e65297c517dfeb992d37310556d23
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[2].why_it_matters: sha256:9880f3889a8fff69c88788121834c5f0bc028b004a3020ef0d1f400d479ea46f -> sha256:50982a260ffd4dd650a1d7705b7e484829a5286eb18758da3a4c3b118a7bdeb7
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].agent: codex-adversarial -> security
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].agent_confidence: sha256:ad57366865126e55649ecb23ae1d48887544976efea46a48eb5d85a6eeb4d306 -> sha256:ad48ff99415b2f007dc35b7eb553fd1eb35ebfa2f2f308acd9488eeb86f71fa8
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].category: sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7 -> sha256:8cc5192684865079dea813dcf1f24a4cac21e0e4174cc4e30a1460c44a643178
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].current_code: (absent) -> sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> sha256:d9bf3eb9e951563cd03de1af55fd1d83b420072b0c1578408d5f10317c0e52b7
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].fix_hint: sha256:132f6b00089c4483f09b981341948496bbb9ec979170c17a9f448424279141fb -> sha256:23b2464bc9a84fef1436ed281be995487c409901c3a40ae36764507f33a46d14
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].line: 233 -> 235
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].problem: sha256:e51f716a0a4fc876bcdebf001804ecdf8bbfed55907372b954c50cb72f06548d -> sha256:4e2359f51652f344cb334be3d515b791fc22b8587de815301e15d686276eaa41
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].source_window[0]: sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].source_window[1]: sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].source_window[2]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].source_window[3]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].source_window[4]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].title: sha256:b0ffbfb4726ebb751a2d2534746a4d464a5e65297c517dfeb992d37310556d23 -> sha256:ee0df4bffba47551df5d4522229a41f74715ea4f472c3030d06c95b152695b46
- UNALLOWED findings[1b7b0aee39af82282cd2e052452deaf16cf90dfd89d7a39f939d0cdf4dadd440].members[3].why_it_matters: sha256:50982a260ffd4dd650a1d7705b7e484829a5286eb18758da3a4c3b118a7bdeb7 -> sha256:8ae7b293dff575421242ad6075f7216ffb1f5b1c112a1c9890cfb8622f6c7c1d

### runs-v2.10-phase40/batch2/triggarr-secret-in-logs/run-1 [C]

- UNALLOWED filtered[1].line: 232 -> 233
- UNALLOWED filtered[1].title: sha256:8bbf26086ecfaed4a137c6a350d7fcc10848d2a2324f5f5bf2c64a334a025d27 -> sha256:f95cbd6f0f5a1c3dc72f28b1256db1bdcdc000d2fc1cf178839ee258e55c999d
- UNALLOWED filtered[2].line: 233 -> 232
- UNALLOWED filtered[2].title: sha256:f95cbd6f0f5a1c3dc72f28b1256db1bdcdc000d2fc1cf178839ee258e55c999d -> sha256:8bbf26086ecfaed4a137c6a350d7fcc10848d2a2324f5f5bf2c64a334a025d27
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].agent: architecture -> codex-adversarial
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].agent_confidence: sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349 -> sha256:ad57366865126e55649ecb23ae1d48887544976efea46a48eb5d85a6eeb4d306
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].category: sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2 -> sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].current_code: sha256:090a6aaadf7cb054cdd79571045924cae0b1632ade322a8c651da3ab001f9514 -> (absent)
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].cwe: sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].fix_hint: sha256:cd12db9df007dd0b8b2fbb559040e75050e4c6a5b19b89ec38877890e90d1407 -> sha256:5c3693295366a30212edae1ae3dc6d78ccc2dd2d3a217690494568f4104848dd
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].line: 232 -> 233
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].problem: sha256:5e5945a67cdc7189e0631ed83c43e1b7a15c4fc0429cdcca5a8219634049d3f8 -> sha256:138dfe4351d0d6b71deadc4c35dd2504e524d8e14ab2fca0767dcd02b8abc75d
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].source_window[0]: sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286 -> sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].source_window[1]: sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca -> sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].source_window[2]: sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].source_window[3]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].source_window[4]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].title: sha256:8bbf26086ecfaed4a137c6a350d7fcc10848d2a2324f5f5bf2c64a334a025d27 -> sha256:f95cbd6f0f5a1c3dc72f28b1256db1bdcdc000d2fc1cf178839ee258e55c999d
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[2].why_it_matters: sha256:fe6d2acc6b11d851a38c81b92c68896c931c0df52bd9d6834de88add4a0ff96c -> sha256:d232fd6e18167035e68c819d2aabec81551345e2ad566d8449de6dddcb3a1afa
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].agent: codex-adversarial -> architecture
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].agent_confidence: sha256:ad57366865126e55649ecb23ae1d48887544976efea46a48eb5d85a6eeb4d306 -> sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].category: sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7 -> sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].current_code: (absent) -> sha256:090a6aaadf7cb054cdd79571045924cae0b1632ade322a8c651da3ab001f9514
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].fix_hint: sha256:5c3693295366a30212edae1ae3dc6d78ccc2dd2d3a217690494568f4104848dd -> sha256:cd12db9df007dd0b8b2fbb559040e75050e4c6a5b19b89ec38877890e90d1407
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].line: 233 -> 232
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].problem: sha256:138dfe4351d0d6b71deadc4c35dd2504e524d8e14ab2fca0767dcd02b8abc75d -> sha256:5e5945a67cdc7189e0631ed83c43e1b7a15c4fc0429cdcca5a8219634049d3f8
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].severity: sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].source_window[0]: sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca -> sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].source_window[1]: sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e -> sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].source_window[2]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].source_window[3]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].source_window[4]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].title: sha256:f95cbd6f0f5a1c3dc72f28b1256db1bdcdc000d2fc1cf178839ee258e55c999d -> sha256:8bbf26086ecfaed4a137c6a350d7fcc10848d2a2324f5f5bf2c64a334a025d27
- UNALLOWED findings[087270666450f275acceffac8e766b41d8273165c67c92559527f1198548224c].members[3].why_it_matters: sha256:d232fd6e18167035e68c819d2aabec81551345e2ad566d8449de6dddcb3a1afa -> sha256:fe6d2acc6b11d851a38c81b92c68896c931c0df52bd9d6834de88add4a0ff96c

### runs-v2.10-phase40/batch3/triggarr-secret-in-logs/run-1 [B]

- UNALLOWED filtered[0].line: 235 -> 233
- UNALLOWED filtered[0].reason: sha256:e791d9e68d41d2736eb554fe71d5c0a38ae446273de831455020a0832a4b43ee -> sha256:bbf812d2aebcc82b9cafd11f95a864caa7f3da78c66ab499c2abafb7890f38ca
- UNALLOWED filtered[0].title: sha256:c90bb668ab14a7a42038e77ae35f950e4b6104b847342f2d178edc1c76dfb261 -> sha256:245cb7ecccfa3c07882f094abbebd77d54ea9526ea1ce72442b3f54fddbefe61
- UNALLOWED filtered[1].line: 233 -> 235
- UNALLOWED filtered[1].reason: sha256:e791d9e68d41d2736eb554fe71d5c0a38ae446273de831455020a0832a4b43ee -> sha256:bbf812d2aebcc82b9cafd11f95a864caa7f3da78c66ab499c2abafb7890f38ca
- UNALLOWED filtered[1].title: sha256:e56e7be97a7a90821b9ff114081fdfa4eba1efc570ce2d374af0409757f13daf -> sha256:ca0a74fde3f93cb931153eac36f4c8c74a7c0e8b667e1afd337ec6a6d658d772
- UNALLOWED filtered[2].line: 233 -> 235
- UNALLOWED filtered[2].reason: sha256:e791d9e68d41d2736eb554fe71d5c0a38ae446273de831455020a0832a4b43ee -> sha256:bbf812d2aebcc82b9cafd11f95a864caa7f3da78c66ab499c2abafb7890f38ca
- UNALLOWED filtered[2].title: sha256:245cb7ecccfa3c07882f094abbebd77d54ea9526ea1ce72442b3f54fddbefe61 -> sha256:c90bb668ab14a7a42038e77ae35f950e4b6104b847342f2d178edc1c76dfb261
- UNALLOWED filtered[3].reason: sha256:e791d9e68d41d2736eb554fe71d5c0a38ae446273de831455020a0832a4b43ee -> sha256:bbf812d2aebcc82b9cafd11f95a864caa7f3da78c66ab499c2abafb7890f38ca
- UNALLOWED findings.order: sha256:b6115fd4b5be23e9e78802927b71db10bee02e58fef745e96715c9b523df61f5 -> sha256:234f9e5e7f1c2248c9aaeb3106f6368bbb6f9becb2da433813d8c314ab92a5c7
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].agent: architecture -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].agent_confidence: sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].attribution[0]: sha256:361e7b1acb6d80d7ef7f8e0aa4204fcebe6a047e57167c83979fbcdb9d37833c -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].attribution[1]: sha256:7d2a878caddd9607bc53d207b7a721b971748c3b78e5dc50f25325c50db20f2e -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].attribution[2]: sha256:96f34c94f7cf7eb0d8a8aadf48980e0ac0d131b90ee50a682424071e25f2f534 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].attribution[3]: sha256:cac9fa20faacbccf6f0e6b780fdfa8793d3bc0773ca4d5b280c4bbe9ac02cac3 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].attribution[4]: sha256:610cb42c95dd518d546a1f6603bb920b2a5e04c6c1514e84e47433dc58102d3a -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].band: critical -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].canonical_line_content: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].category: sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].cwe: sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].fix_hint: sha256:e42fb796ca01b791e33dd54abe03fc8a02e763fb7df16205bf46b8098e7608c8 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].id: sha256:21a98240a7385d1dd9cc9ec512ccf4c433457e6d5c4f0815b361d86ad5818542 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].in_diff: sha256:b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].line: 235 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].agent: architecture -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].agent_confidence: sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].category: sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].cwe: sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].fix_hint: sha256:e42fb796ca01b791e33dd54abe03fc8a02e763fb7df16205bf46b8098e7608c8 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].line: 235 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].problem: sha256:44dd0502ced01d939b5aa5a53392fe0ac7a072607de66a2c23f288413266e5b3 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].source_window[0]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].source_window[1]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].source_window[2]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].source_window[3]: sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].source_window[4]: sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].title: sha256:ca0a74fde3f93cb931153eac36f4c8c74a7c0e8b667e1afd337ec6a6d658d772 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[0].why_it_matters: sha256:307c9e9c23a07c23f9290aca8104565524d4343cf7a83ccfa4c04a4888418983 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].agent: impact -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].agent_confidence: sha256:48449a14a4ff7d79bb7a1b6f3d488eba397c36ef25634c111b49baf362511afc -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].cwe: sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].fix_hint: sha256:dbe84f078888d217ac84d4f6b2997f193560be755fd31df7505638c533b15058 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].line: 235 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].problem: sha256:a7a581390c403ebcb7b483a44c9df6c6085e0f483c79bd9d8b05f0f3e4be4f5e -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].source_window[0]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].source_window[1]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].source_window[2]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].source_window[3]: sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].source_window[4]: sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].title: sha256:c90bb668ab14a7a42038e77ae35f950e4b6104b847342f2d178edc1c76dfb261 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[1].why_it_matters: sha256:0b03bea6bf7e36e29d6ca1ee24c65241f355b198400dea7bec0d057294b9a63c -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].agent: security -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].agent_confidence: sha256:349c41201b62db851192665c504b350ff98c6b45fb62a8a2161f78b6534d8de9 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].category: sha256:8cc5192684865079dea813dcf1f24a4cac21e0e4174cc4e30a1460c44a643178 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].cwe: sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].fix_hint: sha256:9fc97451724761cefdb61715dd9c47754ffb5924cac9f196cb89adf6f2257654 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].line: 233 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].problem: sha256:3ed8125cdb4f68eb0b1e809eb3e66cfa961e5a79f93ac73f8d633e0961c230dc -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].source_window[0]: sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].source_window[1]: sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].source_window[2]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].source_window[3]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].source_window[4]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].title: sha256:e56e7be97a7a90821b9ff114081fdfa4eba1efc570ce2d374af0409757f13daf -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[2].why_it_matters: sha256:70359cecd8888cd23a5ff05302f638a9c7e1544e9b3fec1d5917abc626950343 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].agent: codex-adversarial -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].agent_confidence: sha256:ad57366865126e55649ecb23ae1d48887544976efea46a48eb5d85a6eeb4d306 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].category: sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].fix_hint: sha256:26dc33819d47a215d15a3cacd2769312e97b9f47f9cabae63314f36df94a10df -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].line: 233 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].problem: sha256:30c79070b89bc6b5195744bc92ca9025b2671c9823211270d400bddcbb40d79a -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].severity: sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].source_window[0]: sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].source_window[1]: sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].source_window[2]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].source_window[3]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].source_window[4]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].title: sha256:245cb7ecccfa3c07882f094abbebd77d54ea9526ea1ce72442b3f54fddbefe61 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[3].why_it_matters: sha256:30c79070b89bc6b5195744bc92ca9025b2671c9823211270d400bddcbb40d79a -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].agent: bugs -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].agent_confidence: sha256:d59eced1ded07f84c145592f65bdf854358e009c5cd705f5215bf18697fed103 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].category: sha256:3ef24481f8d08db74d73b250d8b5c5e8e3fdc9b6bcd339f6a6599529ce338a42 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].fix_hint: sha256:de766f7f501374adc78ddea6e80dfff4c94c78f7f7a8f540c94d79b7c61ad40e -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].line: 235 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].problem: sha256:92bd7c86b1c514d180444b96eb54a9188a7483200ae7b9b3f4690924aea798e4 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].severity: sha256:364bb7082249ee9fbc5247ee49735c4246f271b82c2745a35107ddda0d7cabcc -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].title: sha256:b1c3004018b07b1ba2835a97d3c3a52d9fc4d6bf7690c3488d42b9d372c36df2 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].members[4].why_it_matters: sha256:da5a66bdeb82e514018d98ca3163d90769f300161850e602d9a8c992a5f10f96 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].orchestrator_score: 100 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].problem: sha256:44dd0502ced01d939b5aa5a53392fe0ac7a072607de66a2c23f288413266e5b3 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].silenced_marker_nearby: sha256:fcbcf165908dd18a9e49f7ff27810176db8e9f63b4352213741664245224f8aa -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].snapshot.at_pass: 1 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].snapshot.band: critical -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].snapshot.canonical_line_content: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].snapshot.file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].snapshot.line: 235 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].source_window[0]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].source_window[1]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].source_window[2]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].source_window[3]: sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].source_window[4]: sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].stable_hash: sha256:1c6899874fd5e0f1cb3c6fad9250e9f31a4484789907dd390caa01adb836053d -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].status: new -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].title: sha256:ca0a74fde3f93cb931153eac36f4c8c74a7c0e8b667e1afd337ec6a6d658d772 -> (absent)
- UNALLOWED findings[1c3fbec96c0537ed8bdc2de53a96e690f70c67d94699058f81066b2bb212c9fb].why_it_matters: sha256:307c9e9c23a07c23f9290aca8104565524d4343cf7a83ccfa4c04a4888418983 -> (absent)
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].agent: (absent) -> security
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].agent_confidence: (absent) -> sha256:349c41201b62db851192665c504b350ff98c6b45fb62a8a2161f78b6534d8de9
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].attribution[0]: (absent) -> sha256:361e7b1acb6d80d7ef7f8e0aa4204fcebe6a047e57167c83979fbcdb9d37833c
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].attribution[1]: (absent) -> sha256:7d2a878caddd9607bc53d207b7a721b971748c3b78e5dc50f25325c50db20f2e
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].attribution[2]: (absent) -> sha256:96f34c94f7cf7eb0d8a8aadf48980e0ac0d131b90ee50a682424071e25f2f534
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].attribution[3]: (absent) -> sha256:cac9fa20faacbccf6f0e6b780fdfa8793d3bc0773ca4d5b280c4bbe9ac02cac3
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].attribution[4]: (absent) -> sha256:610cb42c95dd518d546a1f6603bb920b2a5e04c6c1514e84e47433dc58102d3a
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].band: (absent) -> critical
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].canonical_line_content: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].category: (absent) -> sha256:8cc5192684865079dea813dcf1f24a4cac21e0e4174cc4e30a1460c44a643178
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].current_code: (absent) -> sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].cwe: (absent) -> sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].fix_hint: (absent) -> sha256:9fc97451724761cefdb61715dd9c47754ffb5924cac9f196cb89adf6f2257654
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].id: (absent) -> sha256:9287869e1b50080b0e190d73e552d15b5b2ccd6e50ecc62725efb307d9540efe
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].in_diff: (absent) -> sha256:b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].line: (absent) -> 233
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].agent: (absent) -> security
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].agent_confidence: (absent) -> sha256:349c41201b62db851192665c504b350ff98c6b45fb62a8a2161f78b6534d8de9
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].category: (absent) -> sha256:8cc5192684865079dea813dcf1f24a4cac21e0e4174cc4e30a1460c44a643178
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].current_code: (absent) -> sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].cwe: (absent) -> sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].fix_hint: (absent) -> sha256:9fc97451724761cefdb61715dd9c47754ffb5924cac9f196cb89adf6f2257654
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].line: (absent) -> 233
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].problem: (absent) -> sha256:3ed8125cdb4f68eb0b1e809eb3e66cfa961e5a79f93ac73f8d633e0961c230dc
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].source_window[0]: (absent) -> sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].source_window[1]: (absent) -> sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].source_window[2]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].source_window[3]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].source_window[4]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].title: (absent) -> sha256:e56e7be97a7a90821b9ff114081fdfa4eba1efc570ce2d374af0409757f13daf
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[0].why_it_matters: (absent) -> sha256:70359cecd8888cd23a5ff05302f638a9c7e1544e9b3fec1d5917abc626950343
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].agent: (absent) -> codex-adversarial
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].agent_confidence: (absent) -> sha256:ad57366865126e55649ecb23ae1d48887544976efea46a48eb5d85a6eeb4d306
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].category: (absent) -> sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].fix_hint: (absent) -> sha256:26dc33819d47a215d15a3cacd2769312e97b9f47f9cabae63314f36df94a10df
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].line: (absent) -> 233
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].problem: (absent) -> sha256:30c79070b89bc6b5195744bc92ca9025b2671c9823211270d400bddcbb40d79a
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].severity: (absent) -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].source_window[0]: (absent) -> sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].source_window[1]: (absent) -> sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].source_window[2]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].source_window[3]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].source_window[4]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].title: (absent) -> sha256:245cb7ecccfa3c07882f094abbebd77d54ea9526ea1ce72442b3f54fddbefe61
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[1].why_it_matters: (absent) -> sha256:30c79070b89bc6b5195744bc92ca9025b2671c9823211270d400bddcbb40d79a
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].agent: (absent) -> architecture
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].agent_confidence: (absent) -> sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].category: (absent) -> sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].current_code: (absent) -> sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].cwe: (absent) -> sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].fix_hint: (absent) -> sha256:e42fb796ca01b791e33dd54abe03fc8a02e763fb7df16205bf46b8098e7608c8
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].line: (absent) -> 235
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].problem: (absent) -> sha256:44dd0502ced01d939b5aa5a53392fe0ac7a072607de66a2c23f288413266e5b3
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].source_window[0]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].source_window[1]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].source_window[2]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].source_window[3]: (absent) -> sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].source_window[4]: (absent) -> sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].title: (absent) -> sha256:ca0a74fde3f93cb931153eac36f4c8c74a7c0e8b667e1afd337ec6a6d658d772
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[2].why_it_matters: (absent) -> sha256:307c9e9c23a07c23f9290aca8104565524d4343cf7a83ccfa4c04a4888418983
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].agent: (absent) -> impact
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].agent_confidence: (absent) -> sha256:48449a14a4ff7d79bb7a1b6f3d488eba397c36ef25634c111b49baf362511afc
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].category: (absent) -> sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].current_code: (absent) -> sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].cwe: (absent) -> sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].fix_hint: (absent) -> sha256:dbe84f078888d217ac84d4f6b2997f193560be755fd31df7505638c533b15058
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].line: (absent) -> 235
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].problem: (absent) -> sha256:a7a581390c403ebcb7b483a44c9df6c6085e0f483c79bd9d8b05f0f3e4be4f5e
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].source_window[0]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].source_window[1]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].source_window[2]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].source_window[3]: (absent) -> sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].source_window[4]: (absent) -> sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].title: (absent) -> sha256:c90bb668ab14a7a42038e77ae35f950e4b6104b847342f2d178edc1c76dfb261
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[3].why_it_matters: (absent) -> sha256:0b03bea6bf7e36e29d6ca1ee24c65241f355b198400dea7bec0d057294b9a63c
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].agent: (absent) -> bugs
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].agent_confidence: (absent) -> sha256:d59eced1ded07f84c145592f65bdf854358e009c5cd705f5215bf18697fed103
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].category: (absent) -> sha256:3ef24481f8d08db74d73b250d8b5c5e8e3fdc9b6bcd339f6a6599529ce338a42
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].current_code: (absent) -> sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].fix_hint: (absent) -> sha256:de766f7f501374adc78ddea6e80dfff4c94c78f7f7a8f540c94d79b7c61ad40e
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].line: (absent) -> 235
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].problem: (absent) -> sha256:92bd7c86b1c514d180444b96eb54a9188a7483200ae7b9b3f4690924aea798e4
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].severity: (absent) -> sha256:364bb7082249ee9fbc5247ee49735c4246f271b82c2745a35107ddda0d7cabcc
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].title: (absent) -> sha256:b1c3004018b07b1ba2835a97d3c3a52d9fc4d6bf7690c3488d42b9d372c36df2
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].members[4].why_it_matters: (absent) -> sha256:da5a66bdeb82e514018d98ca3163d90769f300161850e602d9a8c992a5f10f96
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].orchestrator_score: (absent) -> 100
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].problem: (absent) -> sha256:3ed8125cdb4f68eb0b1e809eb3e66cfa961e5a79f93ac73f8d633e0961c230dc
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].silenced_marker_nearby: (absent) -> sha256:fcbcf165908dd18a9e49f7ff27810176db8e9f63b4352213741664245224f8aa
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].snapshot.at_pass: (absent) -> 1
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].snapshot.band: (absent) -> critical
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].snapshot.canonical_line_content: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].snapshot.file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].snapshot.line: (absent) -> 233
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].source_window[0]: (absent) -> sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].source_window[1]: (absent) -> sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].source_window[2]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].source_window[3]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].source_window[4]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].stable_hash: (absent) -> sha256:04b5c3d7d2eb6ecf1d00e55ad86893f14969ba2ddb343e82d07e69bb459996d7
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].status: (absent) -> new
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].title: (absent) -> sha256:e56e7be97a7a90821b9ff114081fdfa4eba1efc570ce2d374af0409757f13daf
- UNALLOWED findings[a3152fbf25efee7765fd6103d9f3253918a81e670cd5afc7260de47e0dae47ac].why_it_matters: (absent) -> sha256:70359cecd8888cd23a5ff05302f638a9c7e1544e9b3fec1d5917abc626950343

### runs-v2.10-phase40/final/triggarr-secret-in-logs/run-1 [B] (protected)

- UNALLOWED filtered[0].reason: sha256:7db00e3028fec2ac766e4dc45711a3e90063329a54057b01e9264d7020c545cb -> sha256:32828f37f1e3b02eb636bf6f09675311db5bb5aa37535cba5110dc89248e5743
- UNALLOWED filtered[0].title: sha256:ed591b8471361f9e3a62b9948bb96d861973f39a83fc4379544fc2086b88c051 -> sha256:7a4996f90e7c1bfed81123ff53e9a2f1d3c2380869bcb53e9f761c01350bfac4
- UNALLOWED filtered[1].line: 235 -> 233
- UNALLOWED filtered[1].reason: sha256:7db00e3028fec2ac766e4dc45711a3e90063329a54057b01e9264d7020c545cb -> sha256:32828f37f1e3b02eb636bf6f09675311db5bb5aa37535cba5110dc89248e5743
- UNALLOWED filtered[1].title: sha256:d383512448addab243151c158647cf198c5db151b2d53938bfe9fb5c97076fe9 -> sha256:6bde2a15648b3b231286e4ff79dd29171a00ac1d7f172eb4e79c627690934ced
- UNALLOWED filtered[2].line: 233 -> 235
- UNALLOWED filtered[2].reason: sha256:7db00e3028fec2ac766e4dc45711a3e90063329a54057b01e9264d7020c545cb -> sha256:32828f37f1e3b02eb636bf6f09675311db5bb5aa37535cba5110dc89248e5743
- UNALLOWED filtered[2].title: sha256:7a4996f90e7c1bfed81123ff53e9a2f1d3c2380869bcb53e9f761c01350bfac4 -> sha256:d383512448addab243151c158647cf198c5db151b2d53938bfe9fb5c97076fe9
- UNALLOWED filtered[3].line: 233 -> 235
- UNALLOWED filtered[3].reason: sha256:7db00e3028fec2ac766e4dc45711a3e90063329a54057b01e9264d7020c545cb -> sha256:32828f37f1e3b02eb636bf6f09675311db5bb5aa37535cba5110dc89248e5743
- UNALLOWED filtered[3].title: sha256:6bde2a15648b3b231286e4ff79dd29171a00ac1d7f172eb4e79c627690934ced -> sha256:aed2ae2e8f0e452508f3549fda11e4fbf2cd686f46cb49b4769aceee5447014b
- UNALLOWED filtered[4].reason: sha256:7db00e3028fec2ac766e4dc45711a3e90063329a54057b01e9264d7020c545cb -> sha256:32828f37f1e3b02eb636bf6f09675311db5bb5aa37535cba5110dc89248e5743
- UNALLOWED findings.order: sha256:f4682b807835e174fcff9fb484d8dcc0c70883da8c9a1f5b5dda9ac40b6964bb -> sha256:983ef760437911371f03d02466cee9bdb9ecc72d3074ba3630acbbdf0dab171a
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].agent: architecture -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].agent_confidence: sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].attribution[0]: sha256:610cb42c95dd518d546a1f6603bb920b2a5e04c6c1514e84e47433dc58102d3a -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].attribution[1]: sha256:361e7b1acb6d80d7ef7f8e0aa4204fcebe6a047e57167c83979fbcdb9d37833c -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].attribution[2]: sha256:7d2a878caddd9607bc53d207b7a721b971748c3b78e5dc50f25325c50db20f2e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].attribution[3]: sha256:96f34c94f7cf7eb0d8a8aadf48980e0ac0d131b90ee50a682424071e25f2f534 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].attribution[4]: sha256:cb5935d87ff4757894d82d38506c9bc11df4c9ab49e15d1f00e6b17d1a417323 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].attribution[5]: sha256:cac9fa20faacbccf6f0e6b780fdfa8793d3bc0773ca4d5b280c4bbe9ac02cac3 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].band: critical -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].canonical_line_content: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].category: sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].fix_hint: sha256:585a09161f897e48ca627923fc58a6e0d8835888b65be042c306c147cd703f86 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].id: sha256:6543fd3c27156b114308e3810833757733001eddf92393c23326f702f9423402 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].in_diff: sha256:b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].line: 235 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].agent: architecture -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].agent_confidence: sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].category: sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].fix_hint: sha256:585a09161f897e48ca627923fc58a6e0d8835888b65be042c306c147cd703f86 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].line: 235 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].problem: sha256:de2cae87594ffeaae16753e22d0bde0edef104d52f333eba6ad1e07ebdc7a243 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].source_window[0]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].source_window[1]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].source_window[2]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].source_window[3]: sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].source_window[4]: sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].title: sha256:aed2ae2e8f0e452508f3549fda11e4fbf2cd686f46cb49b4769aceee5447014b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[0].why_it_matters: sha256:0d9f82c2ca8bdcc1e992efdf17918240efa21ce8b8d7e35ca9b4e8438b7ead0e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].agent: codex-adversarial -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].agent_confidence: sha256:ad57366865126e55649ecb23ae1d48887544976efea46a48eb5d85a6eeb4d306 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].category: sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].current_code: sha256:01c5ac1b042ce1cdb4dfaae6267cddb670969678b8b8c3927ef632afbb39e683 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].fix_hint: sha256:be30427871e21fea470a0b4f5a6de681c52c4c1dc2e68a1d2e1235367b3edcab -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].line: 233 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].problem: sha256:8178e03ec1855d69045294e6e688f9a18d402ed065323104862b9ab973a56d39 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].severity: sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].source_window[0]: sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].source_window[1]: sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].source_window[2]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].source_window[3]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].source_window[4]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].title: sha256:ed591b8471361f9e3a62b9948bb96d861973f39a83fc4379544fc2086b88c051 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[1].why_it_matters: sha256:8178e03ec1855d69045294e6e688f9a18d402ed065323104862b9ab973a56d39 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].agent: compliance -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].agent_confidence: sha256:ad48ff99415b2f007dc35b7eb553fd1eb35ebfa2f2f308acd9488eeb86f71fa8 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].category: sha256:df9420b6c4d136a808026d388318d24387a18cd204153c572e9c982b693864b9 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].current_code: sha256:f388cdae836776ffa643b71656544d68c603097a25f08f9154aeb2d84d7bb380 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].cwe: sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].fix_hint: sha256:50865b2a1a98a0259a7870dbd397508782cc924986d3e8ae83f71ef5cda7e19f -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].line: 235 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].problem: sha256:51a54239150e175a430bf99181f6ccf5ae9658f0279b0aaf2f2c15c1725147f0 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].severity: sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].source_window[0]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].source_window[1]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].source_window[2]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].source_window[3]: sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].source_window[4]: sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].title: sha256:d383512448addab243151c158647cf198c5db151b2d53938bfe9fb5c97076fe9 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[2].why_it_matters: sha256:e5b07fe5f1356c4d9caeaa18157f9a2d08132584673848a27892b24424fc2f16 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].agent: impact -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].agent_confidence: sha256:48449a14a4ff7d79bb7a1b6f3d488eba397c36ef25634c111b49baf362511afc -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].cwe: sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].fix_hint: sha256:e7e5a994add79c48b1ab28da0836e6c9cae7578e7f77b7ed26e853f58e20cdf6 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].line: 233 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].problem: sha256:626c16ba4d0ccbec689002de30be2323f3e4e5488053ce3e79a5fcf01219e9a1 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].source_window[0]: sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].source_window[1]: sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].source_window[2]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].source_window[3]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].source_window[4]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].title: sha256:7a4996f90e7c1bfed81123ff53e9a2f1d3c2380869bcb53e9f761c01350bfac4 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[3].why_it_matters: sha256:a633af169a857b6816ad2243120a7812bf60fdcc4e0e5f9acdf456d75147ed8b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].agent: security -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].agent_confidence: sha256:8241649609f88ccd2a0a5b233a07a538ec313ff6adf695aa44a969dbca39f67d -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].category: sha256:8cc5192684865079dea813dcf1f24a4cac21e0e4174cc4e30a1460c44a643178 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].cwe: sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].fix_hint: sha256:af36d18a3c5834c0f55359f08404c9785a9d9fec13dad129f13385311ac974bd -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].line: 233 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].problem: sha256:7f419a5b210ca56d4213b2e0f9f11975b12ab4e7ce8e03738b0a5d290a9a29c3 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].source_window[0]: sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].source_window[1]: sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].source_window[2]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].source_window[3]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].source_window[4]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].title: sha256:6bde2a15648b3b231286e4ff79dd29171a00ac1d7f172eb4e79c627690934ced -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[4].why_it_matters: sha256:09fc6f1788932b6d6389891dcf25831396d13ab44363eea6d115665d62e5e0f0 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].agent: bugs -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].agent_confidence: sha256:ff5a1ae012afa5d4c889c50ad427aaf545d31a4fac04ffc1c4d03d403ba4250a -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].fix_hint: sha256:e1bb1d26fd064a5fa1f3857c70bbd40b05ff686661c0d30c2e24cdcdb8b4e283 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].line: 233 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].problem: sha256:b14dac70a8e1462dfaae0d0e4689b4e64c33c79752e4680a8590ee8d02a12cf1 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].source_window[0]: sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].source_window[1]: sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].source_window[2]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].source_window[3]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].source_window[4]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].title: sha256:4497669488b56d56461a8b64374f3391dfcfdcd493fd99985ad6e4f67b8d4ca3 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].members[5].why_it_matters: sha256:b6affb995a32a7a8c4d4e1089862ddd3ad40b7f5e5e40c3f9f5f745de028a4b4 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].orchestrator_score: 100 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].problem: sha256:de2cae87594ffeaae16753e22d0bde0edef104d52f333eba6ad1e07ebdc7a243 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].silenced_marker_nearby: sha256:fcbcf165908dd18a9e49f7ff27810176db8e9f63b4352213741664245224f8aa -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].snapshot.at_pass: 1 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].snapshot.band: critical -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].snapshot.canonical_line_content: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].snapshot.file: triggarr/clients/base.py -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].snapshot.line: 235 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].source_window[0]: sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].source_window[1]: sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].source_window[2]: sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].source_window[3]: sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286 -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].source_window[4]: sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].stable_hash: sha256:6c05754589c3b691b44555c1692200deac78bf55cab53a9e8d7cd69c95f85f1a -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].status: new -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].title: sha256:aed2ae2e8f0e452508f3549fda11e4fbf2cd686f46cb49b4769aceee5447014b -> (absent)
- UNALLOWED findings[5a47a49761224a3efffde4939482825f2384e17ca47579a6f876bac057dfe96d].why_it_matters: sha256:0d9f82c2ca8bdcc1e992efdf17918240efa21ce8b8d7e35ca9b4e8438b7ead0e -> (absent)
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].agent: (absent) -> codex-adversarial
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].agent_confidence: (absent) -> sha256:ad57366865126e55649ecb23ae1d48887544976efea46a48eb5d85a6eeb4d306
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].attribution[0]: (absent) -> sha256:610cb42c95dd518d546a1f6603bb920b2a5e04c6c1514e84e47433dc58102d3a
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].attribution[1]: (absent) -> sha256:361e7b1acb6d80d7ef7f8e0aa4204fcebe6a047e57167c83979fbcdb9d37833c
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].attribution[2]: (absent) -> sha256:7d2a878caddd9607bc53d207b7a721b971748c3b78e5dc50f25325c50db20f2e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].attribution[3]: (absent) -> sha256:96f34c94f7cf7eb0d8a8aadf48980e0ac0d131b90ee50a682424071e25f2f534
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].attribution[4]: (absent) -> sha256:cb5935d87ff4757894d82d38506c9bc11df4c9ab49e15d1f00e6b17d1a417323
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].attribution[5]: (absent) -> sha256:cac9fa20faacbccf6f0e6b780fdfa8793d3bc0773ca4d5b280c4bbe9ac02cac3
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].band: (absent) -> critical
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].canonical_line_content: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].category: (absent) -> sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].current_code: (absent) -> sha256:01c5ac1b042ce1cdb4dfaae6267cddb670969678b8b8c3927ef632afbb39e683
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].fix_hint: (absent) -> sha256:be30427871e21fea470a0b4f5a6de681c52c4c1dc2e68a1d2e1235367b3edcab
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].id: (absent) -> sha256:73ca1c8c1b1765028ee41138e76ea51dc55c913de8ba80028c40cedfc30b6369
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].line: (absent) -> 233
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].agent: (absent) -> codex-adversarial
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].agent_confidence: (absent) -> sha256:ad57366865126e55649ecb23ae1d48887544976efea46a48eb5d85a6eeb4d306
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].category: (absent) -> sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].current_code: (absent) -> sha256:01c5ac1b042ce1cdb4dfaae6267cddb670969678b8b8c3927ef632afbb39e683
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].fix_hint: (absent) -> sha256:be30427871e21fea470a0b4f5a6de681c52c4c1dc2e68a1d2e1235367b3edcab
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].line: (absent) -> 233
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].problem: (absent) -> sha256:8178e03ec1855d69045294e6e688f9a18d402ed065323104862b9ab973a56d39
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].severity: (absent) -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].source_window[0]: (absent) -> sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].source_window[1]: (absent) -> sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].source_window[2]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].source_window[3]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].source_window[4]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].title: (absent) -> sha256:ed591b8471361f9e3a62b9948bb96d861973f39a83fc4379544fc2086b88c051
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[0].why_it_matters: (absent) -> sha256:8178e03ec1855d69045294e6e688f9a18d402ed065323104862b9ab973a56d39
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].agent: (absent) -> impact
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].agent_confidence: (absent) -> sha256:48449a14a4ff7d79bb7a1b6f3d488eba397c36ef25634c111b49baf362511afc
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].category: (absent) -> sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].current_code: (absent) -> sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].cwe: (absent) -> sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].fix_hint: (absent) -> sha256:e7e5a994add79c48b1ab28da0836e6c9cae7578e7f77b7ed26e853f58e20cdf6
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].line: (absent) -> 233
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].problem: (absent) -> sha256:626c16ba4d0ccbec689002de30be2323f3e4e5488053ce3e79a5fcf01219e9a1
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].source_window[0]: (absent) -> sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].source_window[1]: (absent) -> sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].source_window[2]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].source_window[3]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].source_window[4]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].title: (absent) -> sha256:7a4996f90e7c1bfed81123ff53e9a2f1d3c2380869bcb53e9f761c01350bfac4
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[1].why_it_matters: (absent) -> sha256:a633af169a857b6816ad2243120a7812bf60fdcc4e0e5f9acdf456d75147ed8b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].agent: (absent) -> security
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].agent_confidence: (absent) -> sha256:8241649609f88ccd2a0a5b233a07a538ec313ff6adf695aa44a969dbca39f67d
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].category: (absent) -> sha256:8cc5192684865079dea813dcf1f24a4cac21e0e4174cc4e30a1460c44a643178
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].current_code: (absent) -> sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].cwe: (absent) -> sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].fix_hint: (absent) -> sha256:af36d18a3c5834c0f55359f08404c9785a9d9fec13dad129f13385311ac974bd
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].line: (absent) -> 233
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].problem: (absent) -> sha256:7f419a5b210ca56d4213b2e0f9f11975b12ab4e7ce8e03738b0a5d290a9a29c3
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].source_window[0]: (absent) -> sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].source_window[1]: (absent) -> sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].source_window[2]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].source_window[3]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].source_window[4]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].title: (absent) -> sha256:6bde2a15648b3b231286e4ff79dd29171a00ac1d7f172eb4e79c627690934ced
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[2].why_it_matters: (absent) -> sha256:09fc6f1788932b6d6389891dcf25831396d13ab44363eea6d115665d62e5e0f0
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].agent: (absent) -> compliance
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].agent_confidence: (absent) -> sha256:ad48ff99415b2f007dc35b7eb553fd1eb35ebfa2f2f308acd9488eeb86f71fa8
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].category: (absent) -> sha256:df9420b6c4d136a808026d388318d24387a18cd204153c572e9c982b693864b9
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].current_code: (absent) -> sha256:f388cdae836776ffa643b71656544d68c603097a25f08f9154aeb2d84d7bb380
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].cwe: (absent) -> sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].fix_hint: (absent) -> sha256:50865b2a1a98a0259a7870dbd397508782cc924986d3e8ae83f71ef5cda7e19f
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].line: (absent) -> 235
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].problem: (absent) -> sha256:51a54239150e175a430bf99181f6ccf5ae9658f0279b0aaf2f2c15c1725147f0
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].severity: (absent) -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].source_window[0]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].source_window[1]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].source_window[2]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].source_window[3]: (absent) -> sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].source_window[4]: (absent) -> sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].title: (absent) -> sha256:d383512448addab243151c158647cf198c5db151b2d53938bfe9fb5c97076fe9
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[3].why_it_matters: (absent) -> sha256:e5b07fe5f1356c4d9caeaa18157f9a2d08132584673848a27892b24424fc2f16
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].agent: (absent) -> architecture
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].agent_confidence: (absent) -> sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].category: (absent) -> sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].current_code: (absent) -> sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].fix_hint: (absent) -> sha256:585a09161f897e48ca627923fc58a6e0d8835888b65be042c306c147cd703f86
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].line: (absent) -> 235
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].problem: (absent) -> sha256:de2cae87594ffeaae16753e22d0bde0edef104d52f333eba6ad1e07ebdc7a243
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].source_window[0]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].source_window[1]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].source_window[2]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].source_window[3]: (absent) -> sha256:507ffff5bd67f4423e8aac48f152ca64fd0a6830e6ffc5160330dc186dc44286
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].source_window[4]: (absent) -> sha256:24c8bc91f92f25b4f0bbc5d6901e92384c6a55013d7b6f55afddf34c7cc570fd
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].title: (absent) -> sha256:aed2ae2e8f0e452508f3549fda11e4fbf2cd686f46cb49b4769aceee5447014b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[4].why_it_matters: (absent) -> sha256:0d9f82c2ca8bdcc1e992efdf17918240efa21ce8b8d7e35ca9b4e8438b7ead0e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].agent: (absent) -> bugs
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].agent_confidence: (absent) -> sha256:ff5a1ae012afa5d4c889c50ad427aaf545d31a4fac04ffc1c4d03d403ba4250a
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].category: (absent) -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].current_code: (absent) -> sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].fix_hint: (absent) -> sha256:e1bb1d26fd064a5fa1f3857c70bbd40b05ff686661c0d30c2e24cdcdb8b4e283
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].line: (absent) -> 233
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].problem: (absent) -> sha256:b14dac70a8e1462dfaae0d0e4689b4e64c33c79752e4680a8590ee8d02a12cf1
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].source_window[0]: (absent) -> sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].source_window[1]: (absent) -> sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].source_window[2]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].source_window[3]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].source_window[4]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].title: (absent) -> sha256:4497669488b56d56461a8b64374f3391dfcfdcd493fd99985ad6e4f67b8d4ca3
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].members[5].why_it_matters: (absent) -> sha256:b6affb995a32a7a8c4d4e1089862ddd3ad40b7f5e5e40c3f9f5f745de028a4b4
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].orchestrator_score: (absent) -> 100
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].problem: (absent) -> sha256:8178e03ec1855d69045294e6e688f9a18d402ed065323104862b9ab973a56d39
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].severity: (absent) -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].snapshot.at_pass: (absent) -> 1
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].snapshot.band: (absent) -> critical
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].snapshot.canonical_line_content: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].snapshot.file: (absent) -> triggarr/clients/base.py
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].snapshot.line: (absent) -> 233
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].source_window[0]: (absent) -> sha256:5e72b630e6abfdd4987f8bf59ae8fbdeae3266ee3a6e3305ff544d33c94b56ca
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].source_window[1]: (absent) -> sha256:1e7fe1733919b4d51b1c7534c9785ca6b5151813ce6c594643331837b492a36e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].source_window[2]: (absent) -> sha256:f37f0857bdc0354aceaac44c0398679d28d49aad75ecc523ad64721212e410e6
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].source_window[3]: (absent) -> sha256:8d0610e5a1b5844fc0a3548dbb94ac84a15812fa651615394c5e061566fc8b8e
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].source_window[4]: (absent) -> sha256:0922dc7d264a9213425322a19e9f5a2b8efdad51773d01cfff0bb5490388e737
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].stable_hash: (absent) -> sha256:8cd676b0e27a11b6da8f70c87ee7fa7180714fc658118d726711c85594bdd1a4
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].status: (absent) -> new
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].title: (absent) -> sha256:ed591b8471361f9e3a62b9948bb96d861973f39a83fc4379544fc2086b88c051
- UNALLOWED findings[8f4d653e71156e52e6d7d0050504c034a13abea362061423de930320824d88ef].why_it_matters: (absent) -> sha256:8178e03ec1855d69045294e6e688f9a18d402ed065323104862b9ab973a56d39

### runs-v2.10-phase43/first/should-quiet-4/run-3 [A]

- UNALLOWED findings[fedecf9ededf1e6479cf584ae95303d7b3633e48e779d0c41d33ecf9cb4dfd39].band: critical -> warning
- UNALLOWED findings[fedecf9ededf1e6479cf584ae95303d7b3633e48e779d0c41d33ecf9cb4dfd39].orchestrator_score: 100 -> 94
- UNALLOWED findings[fedecf9ededf1e6479cf584ae95303d7b3633e48e779d0c41d33ecf9cb4dfd39].snapshot.band: critical -> warning

### runs-v2.10-phase43/first/should-quiet-6/run-2 [C]

- UNALLOWED filtered[4].title: sha256:95a116e293ee571c98f0a790d55acbe42819a2899b2953546e3f80f02058ca67 -> sha256:5fbdcde1f4fe76b94e2f5983f4c7d1b2a33f11c66b836ba41f63cce915ab0949
- UNALLOWED filtered[5].title: sha256:5fbdcde1f4fe76b94e2f5983f4c7d1b2a33f11c66b836ba41f63cce915ab0949 -> sha256:95a116e293ee571c98f0a790d55acbe42819a2899b2953546e3f80f02058ca67
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].agent: impact -> architecture
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].agent_confidence: sha256:624b60c58c9d8bfb6ff1886c2fd605d2adeb6ea4da576068201b6c6958ce93f4 -> sha256:811786ad1ae74adfdd20dd0372abaaebc6246e343aebd01da0bfc4c02bf0106c
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].fix_hint: sha256:214eeab3bb5747661e213a6da286d096188b24b25e889b84fa755bc4322235ea -> sha256:851b79fc72fdb873007d03295326017857709884e1f23a96a2e8001724b35e3d
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].intent_doc_match: sha256:b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b -> (absent)
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].intent_doc_match.confidence: (absent) -> sha256:1e9d7c27c8bbc8ddf0055c93e064a62fa995d177fee28cc8fa949bc8a4db06f4
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].intent_doc_match.doc: (absent) -> sha256:2da16962ed90531c876536115ad838630da9f394ebb78961727d213fda9d1d02
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].intent_doc_match.quote: (absent) -> sha256:f854b75460a280aa5fcadec554cddb20f20c30acee932b9384e4966b06231d83
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].intent_doc_match.section: (absent) -> sha256:66f183ee8bf4b6b74d436aeed6d057b9fa506a617c35cda924a3f79c11c171d0
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].problem: sha256:a1cba18ed65962be408df88dabcbee7cb316c92630301d091034fdd1068c3d97 -> sha256:27598c58e13c44dd663ac77c5fd8d37955daac2dab21e6fb697d6311287b7c35
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].severity: sha256:364bb7082249ee9fbc5247ee49735c4246f271b82c2745a35107ddda0d7cabcc -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].title: sha256:95a116e293ee571c98f0a790d55acbe42819a2899b2953546e3f80f02058ca67 -> sha256:5fbdcde1f4fe76b94e2f5983f4c7d1b2a33f11c66b836ba41f63cce915ab0949
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[5].why_it_matters: sha256:ad2170918fb9d6a0b0a0ce40dd9bf86fe5c30d17c56b851dcc4caf7eec5b3e51 -> sha256:912aef3f36a67c121f6572591aabfb8e10111404f02394f9f658d0c2bbc347bf
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].agent: architecture -> impact
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].agent_confidence: sha256:811786ad1ae74adfdd20dd0372abaaebc6246e343aebd01da0bfc4c02bf0106c -> sha256:624b60c58c9d8bfb6ff1886c2fd605d2adeb6ea4da576068201b6c6958ce93f4
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].category: sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2 -> sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].fix_hint: sha256:851b79fc72fdb873007d03295326017857709884e1f23a96a2e8001724b35e3d -> sha256:214eeab3bb5747661e213a6da286d096188b24b25e889b84fa755bc4322235ea
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].intent_doc_match: (absent) -> sha256:b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].intent_doc_match.confidence: sha256:1e9d7c27c8bbc8ddf0055c93e064a62fa995d177fee28cc8fa949bc8a4db06f4 -> (absent)
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].intent_doc_match.doc: sha256:2da16962ed90531c876536115ad838630da9f394ebb78961727d213fda9d1d02 -> (absent)
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].intent_doc_match.quote: sha256:f854b75460a280aa5fcadec554cddb20f20c30acee932b9384e4966b06231d83 -> (absent)
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].intent_doc_match.section: sha256:66f183ee8bf4b6b74d436aeed6d057b9fa506a617c35cda924a3f79c11c171d0 -> (absent)
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].problem: sha256:27598c58e13c44dd663ac77c5fd8d37955daac2dab21e6fb697d6311287b7c35 -> sha256:a1cba18ed65962be408df88dabcbee7cb316c92630301d091034fdd1068c3d97
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> sha256:364bb7082249ee9fbc5247ee49735c4246f271b82c2745a35107ddda0d7cabcc
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].title: sha256:5fbdcde1f4fe76b94e2f5983f4c7d1b2a33f11c66b836ba41f63cce915ab0949 -> sha256:95a116e293ee571c98f0a790d55acbe42819a2899b2953546e3f80f02058ca67
- UNALLOWED findings[92e9bcdf883112750166ec6021bb3aa6b76879f11c0a0eff36694537861564ef].members[6].why_it_matters: sha256:912aef3f36a67c121f6572591aabfb8e10111404f02394f9f658d0c2bbc347bf -> sha256:ad2170918fb9d6a0b0a0ce40dd9bf86fe5c30d17c56b851dcc4caf7eec5b3e51

### runs-v2.10-phase43/first/should-quiet-6/run-3 [C]

- UNALLOWED filtered[2].title: sha256:c10501395451d653c06ed75fd4666a40fe02f61db3e9b493a0ea67c748924453 -> sha256:2730feef10db474145f902e1e55c72cfe5ac987d8f8b0bf2c8f0c2fa1ac756b9
- UNALLOWED filtered[3].title: sha256:2730feef10db474145f902e1e55c72cfe5ac987d8f8b0bf2c8f0c2fa1ac756b9 -> sha256:c10501395451d653c06ed75fd4666a40fe02f61db3e9b493a0ea67c748924453
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].agent: impact -> bugs
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].agent_confidence: sha256:39fa9ec190eee7b6f4dff1100d6343e10918d044c75eac8f9e9a2596173f80c9 -> sha256:02d20bbd7e394ad5999a4cebabac9619732c343a4cac99470c03e23ba2bdc2bc
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].current_code: sha256:bb6973e5ee262da73b7605d3c5597adde7e61b1c2af822f55b4fef0de5256f31 -> sha256:5aa4108a4bb44ec35086473bb2ecf5a6e4a3d3349cb81c22857b28c503b8e094
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].fix_hint: sha256:3dd173238ea39a1be7f4b39b35a38490e7047bba44473257512e6828336651cb -> sha256:2cfb296ef63314e08b1171148d33276d7790100d9e36e45ff0898bd7ecf33c07
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].intent_doc_match: sha256:8ac24611cfe47c129e37108bc6adc6843c4fe8fb9c37c27fac8a1835ba660307 -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].problem: sha256:e4e787215c686defc7a0170ff8b5e4e3382fef92bee490c34742df4138f7da0e -> sha256:ae06da698e19a39cd88067a0ed01e0e21276e956f1e2550fb7ff8164c54170e5
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].title: sha256:c10501395451d653c06ed75fd4666a40fe02f61db3e9b493a0ea67c748924453 -> sha256:2730feef10db474145f902e1e55c72cfe5ac987d8f8b0bf2c8f0c2fa1ac756b9
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[3].why_it_matters: sha256:630797a5d869ac17de6b0662833df5f782fe9e7419157d8e50998a87171a2c0c -> sha256:4b77b3c1679b88ff111fa4f51a67625274d78a67266139f8880579e43c13298a
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].agent: bugs -> impact
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].agent_confidence: sha256:02d20bbd7e394ad5999a4cebabac9619732c343a4cac99470c03e23ba2bdc2bc -> sha256:39fa9ec190eee7b6f4dff1100d6343e10918d044c75eac8f9e9a2596173f80c9
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].current_code: sha256:5aa4108a4bb44ec35086473bb2ecf5a6e4a3d3349cb81c22857b28c503b8e094 -> sha256:bb6973e5ee262da73b7605d3c5597adde7e61b1c2af822f55b4fef0de5256f31
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].fix_hint: sha256:2cfb296ef63314e08b1171148d33276d7790100d9e36e45ff0898bd7ecf33c07 -> sha256:3dd173238ea39a1be7f4b39b35a38490e7047bba44473257512e6828336651cb
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> sha256:8ac24611cfe47c129e37108bc6adc6843c4fe8fb9c37c27fac8a1835ba660307
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].problem: sha256:ae06da698e19a39cd88067a0ed01e0e21276e956f1e2550fb7ff8164c54170e5 -> sha256:e4e787215c686defc7a0170ff8b5e4e3382fef92bee490c34742df4138f7da0e
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].title: sha256:2730feef10db474145f902e1e55c72cfe5ac987d8f8b0bf2c8f0c2fa1ac756b9 -> sha256:c10501395451d653c06ed75fd4666a40fe02f61db3e9b493a0ea67c748924453
- UNALLOWED findings[c93be6bfe2511a39a1baeba372e27f4db50b5f3cacbdec3550e6fa0e8f25eb04].members[4].why_it_matters: sha256:4b77b3c1679b88ff111fa4f51a67625274d78a67266139f8880579e43c13298a -> sha256:630797a5d869ac17de6b0662833df5f782fe9e7419157d8e50998a87171a2c0c

### runs-v2.10-phase43/first/should-quiet-7/run-2 [C]

- UNALLOWED filtered[2].title: sha256:da080c9b2f8f9e99ce51851fd3234737b6e9a8c1cfc952ba0b6ee2b965fce955 -> sha256:e93a21de80cea63b37750968a2df4fbeab5c573530fa165f4856ba4ad89f731e
- UNALLOWED filtered[3].title: sha256:e93a21de80cea63b37750968a2df4fbeab5c573530fa165f4856ba4ad89f731e -> sha256:da080c9b2f8f9e99ce51851fd3234737b6e9a8c1cfc952ba0b6ee2b965fce955
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[3].agent: impact -> bugs
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[3].agent_confidence: sha256:ff5a1ae012afa5d4c889c50ad427aaf545d31a4fac04ffc1c4d03d403ba4250a -> sha256:02d20bbd7e394ad5999a4cebabac9619732c343a4cac99470c03e23ba2bdc2bc
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[3].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[3].fix_hint: sha256:d7b074f45e4b156b99fda75dcfd303810feb2f2722cfe726598b139e4591b816 -> sha256:033b911eb236ed72912837d1763e236035ae15493e48bf4ba774a315a6b30f96
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[3].intent_doc_match: sha256:8ac24611cfe47c129e37108bc6adc6843c4fe8fb9c37c27fac8a1835ba660307 -> sha256:4266337f59b4a4787c0782e29697114968f6b95b6c6bf946bbacc5dca531716a
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[3].problem: sha256:991dae3ab61ca93d6dfba02f5c1ee8e89425f4d1276bfb58cf249f317140b788 -> sha256:60a0b8795e6771639537639c110a4cc0fb5e0ac47fde15066f9e07e6b19db3ac
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[3].severity: sha256:364bb7082249ee9fbc5247ee49735c4246f271b82c2745a35107ddda0d7cabcc -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[3].title: sha256:da080c9b2f8f9e99ce51851fd3234737b6e9a8c1cfc952ba0b6ee2b965fce955 -> sha256:e93a21de80cea63b37750968a2df4fbeab5c573530fa165f4856ba4ad89f731e
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[3].why_it_matters: sha256:f4984da12370d6d37601a8aaf372ef667d34328008732baeed6c6bb53c947455 -> sha256:ddcbf89346c40a71f5f6d60821de7203bb111538fda47834874d7f71638a05d3
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[4].agent: bugs -> impact
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[4].agent_confidence: sha256:02d20bbd7e394ad5999a4cebabac9619732c343a4cac99470c03e23ba2bdc2bc -> sha256:ff5a1ae012afa5d4c889c50ad427aaf545d31a4fac04ffc1c4d03d403ba4250a
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[4].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[4].fix_hint: sha256:033b911eb236ed72912837d1763e236035ae15493e48bf4ba774a315a6b30f96 -> sha256:d7b074f45e4b156b99fda75dcfd303810feb2f2722cfe726598b139e4591b816
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[4].intent_doc_match: sha256:4266337f59b4a4787c0782e29697114968f6b95b6c6bf946bbacc5dca531716a -> sha256:8ac24611cfe47c129e37108bc6adc6843c4fe8fb9c37c27fac8a1835ba660307
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[4].problem: sha256:60a0b8795e6771639537639c110a4cc0fb5e0ac47fde15066f9e07e6b19db3ac -> sha256:991dae3ab61ca93d6dfba02f5c1ee8e89425f4d1276bfb58cf249f317140b788
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[4].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> sha256:364bb7082249ee9fbc5247ee49735c4246f271b82c2745a35107ddda0d7cabcc
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[4].title: sha256:e93a21de80cea63b37750968a2df4fbeab5c573530fa165f4856ba4ad89f731e -> sha256:da080c9b2f8f9e99ce51851fd3234737b6e9a8c1cfc952ba0b6ee2b965fce955
- UNALLOWED findings[234ca986d72e17a99ecd64c3518524e338da706b91069ac777b0be74c189b2da].members[4].why_it_matters: sha256:ddcbf89346c40a71f5f6d60821de7203bb111538fda47834874d7f71638a05d3 -> sha256:f4984da12370d6d37601a8aaf372ef667d34328008732baeed6c6bb53c947455

### runs-v2.10-phase43/first/should-quiet-7/run-3 [C]

- UNALLOWED filtered[4].title: sha256:5ae9fd9eea7bc2153e2931649f7c29bf91a3beec305663c18a6b2c597dda6bb9 -> sha256:9998ce74438d9a1cc9e532fb9feb4c877c8941baea0dc94948f7ed0a07039052
- UNALLOWED filtered[5].title: sha256:9998ce74438d9a1cc9e532fb9feb4c877c8941baea0dc94948f7ed0a07039052 -> sha256:5ae9fd9eea7bc2153e2931649f7c29bf91a3beec305663c18a6b2c597dda6bb9
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].agent: impact -> architecture
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].agent_confidence: sha256:d59eced1ded07f84c145592f65bdf854358e009c5cd705f5215bf18697fed103 -> sha256:9f14025af0065b30e47e23ebb3b491d39ae8ed17d33739e5ff3827ffb3634953
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].current_code: sha256:113b584eb734b1ba06a4814802bf18648ab9620b5a29e05bad737eb5c12a7af3 -> sha256:435b3f5f95d1192d28520727a4401d29f28e4113a82bbc06f36be4b93d727d82
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].fix_hint: sha256:27bedc07b51cd398f39ef037375dd0d23188f8b2049716a31e788676294a2c9d -> sha256:11301202fa7456f707dded0090ddbdc98ab973364b9ae7a00d49140f166cf9d1
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].intent_doc_match: sha256:8ac24611cfe47c129e37108bc6adc6843c4fe8fb9c37c27fac8a1835ba660307 -> (absent)
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].intent_doc_match.confidence: (absent) -> sha256:b4af4e0d40391d3a00179d935c63b7e15ba8cd3dfa29f218dedc270bd3eb3e79
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].intent_doc_match.doc: (absent) -> sha256:2da16962ed90531c876536115ad838630da9f394ebb78961727d213fda9d1d02
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].intent_doc_match.quote: (absent) -> sha256:27c72c8372eba3766f6c1467970127703de9f85875d2ae539f15e8d9aee6703e
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].intent_doc_match.section: (absent) -> sha256:65d0eeb922927ba39bec6d8ed659007357fd61b3b10be2e30e9a2340022ca521
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].problem: sha256:a905c5d4c3b0cf7f4da090b3cc547b423062371b7087871a2d61ddf457b42c4d -> sha256:792b89718df61dc9efb4aca149a5fb4f9ec00272f7db23b21cfde1ef731f833f
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].title: sha256:5ae9fd9eea7bc2153e2931649f7c29bf91a3beec305663c18a6b2c597dda6bb9 -> sha256:9998ce74438d9a1cc9e532fb9feb4c877c8941baea0dc94948f7ed0a07039052
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[5].why_it_matters: sha256:7b31fa6faa549b6ac1c9edfe31a94dc832c72a3c63718c50207b65af4065c6cc -> sha256:76aa7f3e568ea7f616fba6ef5872125b53c30ac40c64e900e6f79706ee2bf15f
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].agent: architecture -> impact
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].agent_confidence: sha256:9f14025af0065b30e47e23ebb3b491d39ae8ed17d33739e5ff3827ffb3634953 -> sha256:d59eced1ded07f84c145592f65bdf854358e009c5cd705f5215bf18697fed103
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].category: sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2 -> sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].current_code: sha256:435b3f5f95d1192d28520727a4401d29f28e4113a82bbc06f36be4b93d727d82 -> sha256:113b584eb734b1ba06a4814802bf18648ab9620b5a29e05bad737eb5c12a7af3
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].fix_hint: sha256:11301202fa7456f707dded0090ddbdc98ab973364b9ae7a00d49140f166cf9d1 -> sha256:27bedc07b51cd398f39ef037375dd0d23188f8b2049716a31e788676294a2c9d
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].intent_doc_match: (absent) -> sha256:8ac24611cfe47c129e37108bc6adc6843c4fe8fb9c37c27fac8a1835ba660307
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].intent_doc_match.confidence: sha256:b4af4e0d40391d3a00179d935c63b7e15ba8cd3dfa29f218dedc270bd3eb3e79 -> (absent)
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].intent_doc_match.doc: sha256:2da16962ed90531c876536115ad838630da9f394ebb78961727d213fda9d1d02 -> (absent)
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].intent_doc_match.quote: sha256:27c72c8372eba3766f6c1467970127703de9f85875d2ae539f15e8d9aee6703e -> (absent)
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].intent_doc_match.section: sha256:65d0eeb922927ba39bec6d8ed659007357fd61b3b10be2e30e9a2340022ca521 -> (absent)
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].problem: sha256:792b89718df61dc9efb4aca149a5fb4f9ec00272f7db23b21cfde1ef731f833f -> sha256:a905c5d4c3b0cf7f4da090b3cc547b423062371b7087871a2d61ddf457b42c4d
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].title: sha256:9998ce74438d9a1cc9e532fb9feb4c877c8941baea0dc94948f7ed0a07039052 -> sha256:5ae9fd9eea7bc2153e2931649f7c29bf91a3beec305663c18a6b2c597dda6bb9
- UNALLOWED findings[2b1a20a238c58b5044bf96941dfef20a52cfdae6a568a7ddef3fe2de6a251b49].members[6].why_it_matters: sha256:76aa7f3e568ea7f616fba6ef5872125b53c30ac40c64e900e6f79706ee2bf15f -> sha256:7b31fa6faa549b6ac1c9edfe31a94dc832c72a3c63718c50207b65af4065c6cc

### runs-v2.10-phase43/first/triggarr-autoescape/run-2 [C]

- UNALLOWED filtered[3].title: sha256:8244cb00270a82b4406283fffec90786ee5d9bbc5261848a6c14fd63b0de4f9e -> sha256:fa63a1f4e2ceb742be253366465aa95b443ec57e4cb9f8080b81964f71cdfd1c
- UNALLOWED filtered[4].title: sha256:fa63a1f4e2ceb742be253366465aa95b443ec57e4cb9f8080b81964f71cdfd1c -> sha256:8244cb00270a82b4406283fffec90786ee5d9bbc5261848a6c14fd63b0de4f9e
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[4].agent: impact -> bugs
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[4].agent_confidence: sha256:48449a14a4ff7d79bb7a1b6f3d488eba397c36ef25634c111b49baf362511afc -> sha256:ff5a1ae012afa5d4c889c50ad427aaf545d31a4fac04ffc1c4d03d403ba4250a
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[4].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[4].fix_hint: sha256:9f42f78c4dab7aa6d36a92b448235b8e42627b4ee00373655211384c08a85f9e -> sha256:22bf108130a4d84db9b2bc08bc635b30d2a7cbf39f215dcdb5584c64e69e0e4b
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[4].intent_doc_match: sha256:fcbcf165908dd18a9e49f7ff27810176db8e9f63b4352213741664245224f8aa -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[4].problem: sha256:7aaeeccaa038096af7c02a4fb422d5bf6b35c8e2aec1bc75bdd48523a5163ec7 -> sha256:84b98b74e2924e62e2183e7ebb6ab1956324a841b019e13ab28bc356b6f1026b
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[4].title: sha256:8244cb00270a82b4406283fffec90786ee5d9bbc5261848a6c14fd63b0de4f9e -> sha256:fa63a1f4e2ceb742be253366465aa95b443ec57e4cb9f8080b81964f71cdfd1c
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[4].why_it_matters: sha256:d73a4666e945058903a1f6dfa74f918a549d278ce1add623b46b2f3ee76979f6 -> sha256:ff0ace959760dd27ec24c7a27f6dee909fac3078ee82df0aa8d0bbaf32ba9009
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[5].agent: bugs -> impact
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[5].agent_confidence: sha256:ff5a1ae012afa5d4c889c50ad427aaf545d31a4fac04ffc1c4d03d403ba4250a -> sha256:48449a14a4ff7d79bb7a1b6f3d488eba397c36ef25634c111b49baf362511afc
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[5].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[5].fix_hint: sha256:22bf108130a4d84db9b2bc08bc635b30d2a7cbf39f215dcdb5584c64e69e0e4b -> sha256:9f42f78c4dab7aa6d36a92b448235b8e42627b4ee00373655211384c08a85f9e
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[5].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> sha256:fcbcf165908dd18a9e49f7ff27810176db8e9f63b4352213741664245224f8aa
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[5].problem: sha256:84b98b74e2924e62e2183e7ebb6ab1956324a841b019e13ab28bc356b6f1026b -> sha256:7aaeeccaa038096af7c02a4fb422d5bf6b35c8e2aec1bc75bdd48523a5163ec7
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[5].title: sha256:fa63a1f4e2ceb742be253366465aa95b443ec57e4cb9f8080b81964f71cdfd1c -> sha256:8244cb00270a82b4406283fffec90786ee5d9bbc5261848a6c14fd63b0de4f9e
- UNALLOWED findings[4f30f8fb283fbe56b16be82f8971ded0ffaace71a2ac4400de603559e13c26f6].members[5].why_it_matters: sha256:ff0ace959760dd27ec24c7a27f6dee909fac3078ee82df0aa8d0bbaf32ba9009 -> sha256:d73a4666e945058903a1f6dfa74f918a549d278ce1add623b46b2f3ee76979f6

### runs-v2.10-phase43/first/triggarr-secret-in-logs/run-1 [A]

- UNALLOWED filtered[2].line: 233 -> 235
- UNALLOWED filtered[2].title: sha256:d625b0a4862c8d006d4f4127466faa252ee20fb2bd91dc76f60ed47824d564ef -> sha256:7134fab34db53552ed56c580651b9825e00144079247ac8ba2605e176adb48d7
- UNALLOWED filtered[3].line: 235 -> 233
- UNALLOWED filtered[3].title: sha256:7134fab34db53552ed56c580651b9825e00144079247ac8ba2605e176adb48d7 -> sha256:d625b0a4862c8d006d4f4127466faa252ee20fb2bd91dc76f60ed47824d564ef
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].band: critical -> warning
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[3].agent: impact -> bugs
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[3].agent_confidence: sha256:39fa9ec190eee7b6f4dff1100d6343e10918d044c75eac8f9e9a2596173f80c9 -> sha256:02d20bbd7e394ad5999a4cebabac9619732c343a4cac99470c03e23ba2bdc2bc
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[3].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[3].fix_hint: sha256:1e29ae017e762f65ab8d1985d30717fa1b68a20a1ec71685a02cfd0c6b2e22eb -> sha256:343edcb43004ce7d34e186a70c22f65473e52e50ea04ecf64c9956387b13b68b
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[3].line: 233 -> 235
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[3].problem: sha256:a19272eb4be1507274c41c7b1aafffde8a6fda2d851aa2e527065a024e866a64 -> sha256:89f0eb4030a51c14df2096168b5f20e30d31d01aa1c7c73d949cb78a6fa8c47d
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[3].title: sha256:d625b0a4862c8d006d4f4127466faa252ee20fb2bd91dc76f60ed47824d564ef -> sha256:7134fab34db53552ed56c580651b9825e00144079247ac8ba2605e176adb48d7
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[3].why_it_matters: sha256:ed81e27a37cc2ca0c17d6307139baa0b6382e1179f09ce7c246910d702122fb7 -> sha256:f0e76b30fcea5dc02d97598678dfe99e52f6a01a19c83df65de2656bf1eb251c
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[4].agent: bugs -> impact
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[4].agent_confidence: sha256:02d20bbd7e394ad5999a4cebabac9619732c343a4cac99470c03e23ba2bdc2bc -> sha256:39fa9ec190eee7b6f4dff1100d6343e10918d044c75eac8f9e9a2596173f80c9
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[4].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[4].fix_hint: sha256:343edcb43004ce7d34e186a70c22f65473e52e50ea04ecf64c9956387b13b68b -> sha256:1e29ae017e762f65ab8d1985d30717fa1b68a20a1ec71685a02cfd0c6b2e22eb
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[4].line: 235 -> 233
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[4].problem: sha256:89f0eb4030a51c14df2096168b5f20e30d31d01aa1c7c73d949cb78a6fa8c47d -> sha256:a19272eb4be1507274c41c7b1aafffde8a6fda2d851aa2e527065a024e866a64
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[4].title: sha256:7134fab34db53552ed56c580651b9825e00144079247ac8ba2605e176adb48d7 -> sha256:d625b0a4862c8d006d4f4127466faa252ee20fb2bd91dc76f60ed47824d564ef
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].members[4].why_it_matters: sha256:f0e76b30fcea5dc02d97598678dfe99e52f6a01a19c83df65de2656bf1eb251c -> sha256:ed81e27a37cc2ca0c17d6307139baa0b6382e1179f09ce7c246910d702122fb7
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].orchestrator_score: 100 -> 94
- UNALLOWED findings[13f543dd935e677b161e80be2f9cca1a70add7bf80ab4a41a48b1b1ae431e6f8].snapshot.band: critical -> warning

### runs-v2.10-phase43/first/triggarr-secret-in-logs/run-3 [C]

- UNALLOWED filtered[2].title: sha256:9bd739b43f73f863f8be988a4baacebb5d4283edf8f249fd7f043ecbaeda1c1d -> sha256:c92d07056c5e95ce361c929303f83e79c07b9ef8698a04f5a2bfd6bf114ce535
- UNALLOWED filtered[3].title: sha256:c92d07056c5e95ce361c929303f83e79c07b9ef8698a04f5a2bfd6bf114ce535 -> sha256:04509ac5c3410ff50b8b6b0ea378e45461ee60e7f225f7efb2140e6d421bc358
- UNALLOWED filtered[4].title: sha256:04509ac5c3410ff50b8b6b0ea378e45461ee60e7f225f7efb2140e6d421bc358 -> sha256:9bd739b43f73f863f8be988a4baacebb5d4283edf8f249fd7f043ecbaeda1c1d
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[3].agent: impact -> bugs
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[3].agent_confidence: sha256:a21855da08cb102d1d217c53dc5824a3a795c1c1a44e971bf01ab9da3a2acbbf -> sha256:81b8a03f97e8787c53fe1a86bda042b6f0de9b0ec9c09357e107c99ba4d6948a
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[3].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[3].fix_hint: sha256:36b9e4672f6950f144f8920fb239cc09e4db8a6b3beaac36242f9633d35e78db -> sha256:3b2ad497391437469a76025f5d695c6f74ccebcb8eba72e54d237e73f4c7c3ab
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[3].intent_doc_match: sha256:90d1ad9b8cedd78feaeb3d139fd6246e921a08b14553594cc499f1e271166b6d -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[3].problem: sha256:90c0770c76f3824edd57e639b2ccd90c03522481840ff112e3d33c3382033381 -> sha256:ae8c740fae6205b294c6de099ea380cd3f9e28f5102be3a0192cbe87187b4a10
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[3].title: sha256:9bd739b43f73f863f8be988a4baacebb5d4283edf8f249fd7f043ecbaeda1c1d -> sha256:c92d07056c5e95ce361c929303f83e79c07b9ef8698a04f5a2bfd6bf114ce535
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[3].why_it_matters: sha256:7d7c57d16bedd6865c7f52f58005bdda8b1f3778a76016f4804af6f58a5f2a2d -> sha256:40d32e69735e3334def8fb9209a5d2c72ff2835318d281edaa180e08dd1617d8
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[4].agent: bugs -> compliance
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[4].agent_confidence: sha256:81b8a03f97e8787c53fe1a86bda042b6f0de9b0ec9c09357e107c99ba4d6948a -> sha256:41cfc0d1f2d127b04555b7246d84019b4d27710a3f3aff6e7764375b1e06e05d
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[4].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> sha256:df9420b6c4d136a808026d388318d24387a18cd204153c572e9c982b693864b9
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[4].fix_hint: sha256:3b2ad497391437469a76025f5d695c6f74ccebcb8eba72e54d237e73f4c7c3ab -> sha256:a1ae37051fe4bf80d8db64c894f519516d6c6c4e79f26cd0f07b8cef29716c1d
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[4].problem: sha256:ae8c740fae6205b294c6de099ea380cd3f9e28f5102be3a0192cbe87187b4a10 -> sha256:3c85df51d1711640b4b4b6178a286c421149167a6b5d19ed9529d772be017d11
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[4].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> sha256:364bb7082249ee9fbc5247ee49735c4246f271b82c2745a35107ddda0d7cabcc
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[4].title: sha256:c92d07056c5e95ce361c929303f83e79c07b9ef8698a04f5a2bfd6bf114ce535 -> sha256:04509ac5c3410ff50b8b6b0ea378e45461ee60e7f225f7efb2140e6d421bc358
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[4].why_it_matters: sha256:40d32e69735e3334def8fb9209a5d2c72ff2835318d281edaa180e08dd1617d8 -> sha256:d1c4131920f7bdbcffb28eaad457ed68cbddb4500bf3aee7724b6cee8ed7bcee
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[5].agent: compliance -> impact
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[5].agent_confidence: sha256:41cfc0d1f2d127b04555b7246d84019b4d27710a3f3aff6e7764375b1e06e05d -> sha256:a21855da08cb102d1d217c53dc5824a3a795c1c1a44e971bf01ab9da3a2acbbf
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[5].category: sha256:df9420b6c4d136a808026d388318d24387a18cd204153c572e9c982b693864b9 -> sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[5].fix_hint: sha256:a1ae37051fe4bf80d8db64c894f519516d6c6c4e79f26cd0f07b8cef29716c1d -> sha256:36b9e4672f6950f144f8920fb239cc09e4db8a6b3beaac36242f9633d35e78db
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[5].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> sha256:90d1ad9b8cedd78feaeb3d139fd6246e921a08b14553594cc499f1e271166b6d
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[5].problem: sha256:3c85df51d1711640b4b4b6178a286c421149167a6b5d19ed9529d772be017d11 -> sha256:90c0770c76f3824edd57e639b2ccd90c03522481840ff112e3d33c3382033381
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[5].severity: sha256:364bb7082249ee9fbc5247ee49735c4246f271b82c2745a35107ddda0d7cabcc -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[5].title: sha256:04509ac5c3410ff50b8b6b0ea378e45461ee60e7f225f7efb2140e6d421bc358 -> sha256:9bd739b43f73f863f8be988a4baacebb5d4283edf8f249fd7f043ecbaeda1c1d
- UNALLOWED findings[5718c26731398f1ac2e39e62d2c26751958290e01320f0aefde3e47ccd143194].members[5].why_it_matters: sha256:d1c4131920f7bdbcffb28eaad457ed68cbddb4500bf3aee7724b6cee8ed7bcee -> sha256:7d7c57d16bedd6865c7f52f58005bdda8b1f3778a76016f4804af6f58a5f2a2d

### runs-v2.10/third-organic-should-catch/run-2 [C] (protected)

- UNALLOWED filtered[2].line: 308 -> 307
- UNALLOWED filtered[2].title: sha256:160edb94d04f1e6d1c354d35df87ceb6fd99d977c39467d37ccd3622800e3970 -> sha256:b4810c75aa3b28b66b578be41e38f757d97121d00260717dc29cd55d6d5eb3a7
- UNALLOWED filtered[3].line: 307 -> 308
- UNALLOWED filtered[3].title: sha256:b4810c75aa3b28b66b578be41e38f757d97121d00260717dc29cd55d6d5eb3a7 -> sha256:160edb94d04f1e6d1c354d35df87ceb6fd99d977c39467d37ccd3622800e3970
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].agent: language-typescript -> bugs
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].agent_confidence: sha256:f369cb89fc627e668987007d121ed1eacdc01db9e28f8bb26f358b7d8c4f08ac -> sha256:8722616204217eddb39e7df969e0698aed8e599ba62ed2de1ce49b03ade0fede
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].category: sha256:fcc959df514120f6ef0f7625da45bc925e8a0e2a209110e986c40c366f630fc6 -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].current_code: sha256:4b9d0001d17f6ddd8d511e589e0694425f0ee70d0eacc3f29015fdb4edd27645 -> sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].fix_hint: sha256:a1193af4dcb0c98287d635d333fd16f7ae1d76c955b998536a8db084c7c980d8 -> sha256:0b6e91bc41af6b02bad74ca22d224f0216b46871e4390a1f2bda01496f146ef7
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].line: 308 -> 307
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].problem: sha256:0ea13a36dad96b265814f2b842e66d867860d90c9e8e7515de8320bc8ecc9f59 -> sha256:5aafacf1536dcd502b596ed98d1d786f7bf3d5284805cf4793cacd2fa51deb6c
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].source_window[0]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].source_window[1]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].source_window[2]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].source_window[3]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].source_window[4]: sha256:12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126 -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].title: sha256:160edb94d04f1e6d1c354d35df87ceb6fd99d977c39467d37ccd3622800e3970 -> sha256:b4810c75aa3b28b66b578be41e38f757d97121d00260717dc29cd55d6d5eb3a7
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[3].why_it_matters: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> sha256:f806b3cc17956b407bbb662336b4c6ef0ff20a513146ffefbd521490eb8da0b4
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].agent: bugs -> language-typescript
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].agent_confidence: sha256:8722616204217eddb39e7df969e0698aed8e599ba62ed2de1ce49b03ade0fede -> sha256:f369cb89fc627e668987007d121ed1eacdc01db9e28f8bb26f358b7d8c4f08ac
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> sha256:fcc959df514120f6ef0f7625da45bc925e8a0e2a209110e986c40c366f630fc6
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].current_code: sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56 -> sha256:4b9d0001d17f6ddd8d511e589e0694425f0ee70d0eacc3f29015fdb4edd27645
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].fix_hint: sha256:0b6e91bc41af6b02bad74ca22d224f0216b46871e4390a1f2bda01496f146ef7 -> sha256:a1193af4dcb0c98287d635d333fd16f7ae1d76c955b998536a8db084c7c980d8
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].line: 307 -> 308
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].problem: sha256:5aafacf1536dcd502b596ed98d1d786f7bf3d5284805cf4793cacd2fa51deb6c -> sha256:0ea13a36dad96b265814f2b842e66d867860d90c9e8e7515de8320bc8ecc9f59
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].source_window[0]: sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].source_window[1]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].source_window[2]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].source_window[3]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].source_window[4]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> sha256:12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].title: sha256:b4810c75aa3b28b66b578be41e38f757d97121d00260717dc29cd55d6d5eb3a7 -> sha256:160edb94d04f1e6d1c354d35df87ceb6fd99d977c39467d37ccd3622800e3970
- UNALLOWED findings[25b18f8a435341ff50b1c453193970ad9a7e7b12bb022ebf21d90d6da1fd331c].members[4].why_it_matters: sha256:f806b3cc17956b407bbb662336b4c6ef0ff20a513146ffefbd521490eb8da0b4 -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b

### runs-v2.10/triggarr-secret-in-logs/run-1 [A] (protected)

- UNALLOWED findings[12fe298fc07e929bf6fd70047bc5e520b172a1c5329544a48022e36ce0c4be82].band: critical -> warning
- UNALLOWED findings[12fe298fc07e929bf6fd70047bc5e520b172a1c5329544a48022e36ce0c4be82].orchestrator_score: 100 -> 94
- UNALLOWED findings[12fe298fc07e929bf6fd70047bc5e520b172a1c5329544a48022e36ce0c4be82].snapshot.band: critical -> warning

### runs-v2.11-phase49/first/triggarr-secret-in-logs/run-2 [C]

- UNALLOWED filtered[0].line: 232 -> 233
- UNALLOWED filtered[0].title: sha256:ab2bffffabe40bf998818457b2d617a4002a75ab576bf8a9b779fda19368582c -> sha256:fc2a24fcd2f346848923394d66f4553e455a4ae0fdc83175fca80b33c3b3985c
- UNALLOWED filtered[1].title: sha256:b945310fa83d6dfd96f3f21a1474cd9c92b416a70bdf276e13e9c69b6f94aad5 -> sha256:ab2bffffabe40bf998818457b2d617a4002a75ab576bf8a9b779fda19368582c
- UNALLOWED filtered[2].line: 233 -> 232
- UNALLOWED filtered[2].title: sha256:fc2a24fcd2f346848923394d66f4553e455a4ae0fdc83175fca80b33c3b3985c -> sha256:b945310fa83d6dfd96f3f21a1474cd9c92b416a70bdf276e13e9c69b6f94aad5
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].agent: security -> architecture
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].agent_confidence: sha256:8241649609f88ccd2a0a5b233a07a538ec313ff6adf695aa44a969dbca39f67d -> sha256:b4944c6ff08dc6f43da2e9c824669b7d927dd1fa976fadc7b456881f51bf5ccc
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].category: sha256:8cc5192684865079dea813dcf1f24a4cac21e0e4174cc4e30a1460c44a643178 -> sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].current_code: sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290 -> sha256:4f8f4acf01981dfb513cc1eb86aa119224eded9c1408dae2502021fae2faa23b
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].cwe: sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].fix_hint: sha256:2ce7db69189316a140e3c7f19f524cee26edd3a02da5f2481213f5b2548bf4b8 -> sha256:173c347e4ea487f9f1586e67d9c574edf5d355a7dee9a504e70a3b634127a279
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].intent_doc_match: sha256:55e5dc644493646f21e6a412775acf22c8cdbd8b238db8314359792c37e2a16e -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].line: 232 -> 233
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].problem: sha256:32b2759705ccb4a12cebe4096aa81ee84c4c777635190f9e57fa00fbeb944913 -> sha256:d95298a101a9f0fa69e9c0db008b45c54d4a43378469eccbade68699d9de94b3
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].severity: sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].title: sha256:ab2bffffabe40bf998818457b2d617a4002a75ab576bf8a9b779fda19368582c -> sha256:fc2a24fcd2f346848923394d66f4553e455a4ae0fdc83175fca80b33c3b3985c
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[1].why_it_matters: sha256:c55cd3aeae668530c6b208b627daa814e2d40bbb04685c3e42569bb1ca362367 -> sha256:3b17cce381849b2957297a2a77df0e06858dedc0879efc3bd4d46205c674ec82
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[2].agent: compliance -> security
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[2].agent_confidence: sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349 -> sha256:8241649609f88ccd2a0a5b233a07a538ec313ff6adf695aa44a969dbca39f67d
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[2].category: sha256:df9420b6c4d136a808026d388318d24387a18cd204153c572e9c982b693864b9 -> sha256:8cc5192684865079dea813dcf1f24a4cac21e0e4174cc4e30a1460c44a643178
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[2].fix_hint: sha256:6f91d93584eb532c56a1fb70c265f04ca587f36a41f54c49204848e2caa8d8f8 -> sha256:2ce7db69189316a140e3c7f19f524cee26edd3a02da5f2481213f5b2548bf4b8
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[2].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> sha256:55e5dc644493646f21e6a412775acf22c8cdbd8b238db8314359792c37e2a16e
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[2].problem: sha256:144da007df8b4155e37f5ca51482aefeff5267b25e8913d175dc4bc6b62a2dac -> sha256:32b2759705ccb4a12cebe4096aa81ee84c4c777635190f9e57fa00fbeb944913
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[2].title: sha256:b945310fa83d6dfd96f3f21a1474cd9c92b416a70bdf276e13e9c69b6f94aad5 -> sha256:ab2bffffabe40bf998818457b2d617a4002a75ab576bf8a9b779fda19368582c
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[2].why_it_matters: sha256:c8882d480a0d730fb9c9335910a01835a5e4859a24f42eaebf20c076cfe1bfa8 -> sha256:c55cd3aeae668530c6b208b627daa814e2d40bbb04685c3e42569bb1ca362367
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[3].agent: architecture -> compliance
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[3].agent_confidence: sha256:b4944c6ff08dc6f43da2e9c824669b7d927dd1fa976fadc7b456881f51bf5ccc -> sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[3].category: sha256:711fc44f9868e51658c479cb45ea19c4eb0b854b5577ce833f86f7930b936dd2 -> sha256:df9420b6c4d136a808026d388318d24387a18cd204153c572e9c982b693864b9
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[3].current_code: sha256:4f8f4acf01981dfb513cc1eb86aa119224eded9c1408dae2502021fae2faa23b -> sha256:383c007e67588c7654d36fb62c8606cfba2efb18e91f0ae7a32a55214b5ee290
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[3].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> sha256:79184a3edde16002a4bb47565e47d36892ea25eeb5116994db404eadfbc8871a
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[3].fix_hint: sha256:173c347e4ea487f9f1586e67d9c574edf5d355a7dee9a504e70a3b634127a279 -> sha256:6f91d93584eb532c56a1fb70c265f04ca587f36a41f54c49204848e2caa8d8f8
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[3].line: 233 -> 232
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[3].problem: sha256:d95298a101a9f0fa69e9c0db008b45c54d4a43378469eccbade68699d9de94b3 -> sha256:144da007df8b4155e37f5ca51482aefeff5267b25e8913d175dc4bc6b62a2dac
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[3].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[3].title: sha256:fc2a24fcd2f346848923394d66f4553e455a4ae0fdc83175fca80b33c3b3985c -> sha256:b945310fa83d6dfd96f3f21a1474cd9c92b416a70bdf276e13e9c69b6f94aad5
- UNALLOWED findings[231222c433af8108b7be04e802039184073cb715455ecabbee43e5d3a1d4e3de].members[3].why_it_matters: sha256:3b17cce381849b2957297a2a77df0e06858dedc0879efc3bd4d46205c674ec82 -> sha256:c8882d480a0d730fb9c9335910a01835a5e4859a24f42eaebf20c076cfe1bfa8

### runs/should-quiet-1/run-1 [B]

- UNALLOWED filtered[0].line: 85 -> 87
- UNALLOWED filtered[0].reason: sha256:f1244fd68e7cc828d1b8620f645fa0494032320c8c8af439320981cf14227449 -> sha256:c3d2875a36c6b2e621ce38125d1fda2c13555353fdf92d3a89f50840df0e76d4
- UNALLOWED filtered[0].title: sha256:ee0906ffe9ddb7038f84a6f1d36fd0c9c7785a3876e656298e38d4bdc380b0d2 -> sha256:c6e017fc57cd45cbe57a96af97f00116d33daee5dad01ca953c7377334f96ee3
- UNALLOWED filtered[1].line: 87 -> 85
- UNALLOWED filtered[1].reason: sha256:f1244fd68e7cc828d1b8620f645fa0494032320c8c8af439320981cf14227449 -> sha256:c3d2875a36c6b2e621ce38125d1fda2c13555353fdf92d3a89f50840df0e76d4
- UNALLOWED filtered[1].title: sha256:1921f463d437650fec91853234a158ec90828e01fd98f1b6ed2ba67e6335191f -> sha256:8d2fc74b59a42d7d602ce7c21b310dec8115786bd291324a4c13377ba9de87c3
- UNALLOWED filtered[2].line: 85 -> 87
- UNALLOWED filtered[2].reason: sha256:f1244fd68e7cc828d1b8620f645fa0494032320c8c8af439320981cf14227449 -> sha256:c3d2875a36c6b2e621ce38125d1fda2c13555353fdf92d3a89f50840df0e76d4
- UNALLOWED filtered[2].title: sha256:8d2fc74b59a42d7d602ce7c21b310dec8115786bd291324a4c13377ba9de87c3 -> sha256:1921f463d437650fec91853234a158ec90828e01fd98f1b6ed2ba67e6335191f
- UNALLOWED findings.order: sha256:ec2573fa201b5447ebac284c6edba72404d45bf693278f83475b4573c2db9508 -> sha256:a1adb5e90d4a54dd7f94a88c0f85b7917f6a8e31677e8842cd13a4ddb3db6d76
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].agent: bugs -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].agent_confidence: sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].attribution[0]: sha256:610cb42c95dd518d546a1f6603bb920b2a5e04c6c1514e84e47433dc58102d3a -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].attribution[1]: sha256:361e7b1acb6d80d7ef7f8e0aa4204fcebe6a047e57167c83979fbcdb9d37833c -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].attribution[2]: sha256:96f34c94f7cf7eb0d8a8aadf48980e0ac0d131b90ee50a682424071e25f2f534 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].attribution[3]: sha256:cac9fa20faacbccf6f0e6b780fdfa8793d3bc0773ca4d5b280c4bbe9ac02cac3 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].band: critical -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].canonical_line_content: sha256:4c3544b3e573f4cae2f0a8ee27029fe96c97df9cf442ed5697d802d7e50d84b5 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].current_code: sha256:21ecfa845b615bcabfb9870e3f30b3064da664f49f86fe57529afdcddcda594a -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].cwe: sha256:4779bc407343d916c5a4f6a996174046419bdd87ce6c609054dc8788b3dfc233 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].file: triggarr/web/validation.py -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].fix_hint: sha256:cad6e60c8f0dae8f73d82ec9cf9880ee01b5c8db04cab2405e93a39e7d1ad527 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].id: sha256:f7a33a0e52e4cd019310f1f9bca293dad2fd118a2304ea0ce7c3008a348766dd -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].in_diff: sha256:b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].line: 87 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].agent: bugs -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].agent_confidence: sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].current_code: sha256:21ecfa845b615bcabfb9870e3f30b3064da664f49f86fe57529afdcddcda594a -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].cwe: sha256:4779bc407343d916c5a4f6a996174046419bdd87ce6c609054dc8788b3dfc233 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].file: triggarr/web/validation.py -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].fix_hint: sha256:cad6e60c8f0dae8f73d82ec9cf9880ee01b5c8db04cab2405e93a39e7d1ad527 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].line: 87 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].problem: sha256:d29277d7c711873f930b3d4ecec523322a93f64485339df7ef3ba212797c09fa -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].severity: sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].source_window[0]: sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].source_window[1]: sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].source_window[2]: sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].source_window[3]: sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].source_window[4]: sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].source_window[5]: sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].source_window[6]: sha256:8441e9dc7ef6b32e165b29cc5ef7cc39cd9b9e4a7728dcc9b01331b99f116253 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].title: sha256:c6e017fc57cd45cbe57a96af97f00116d33daee5dad01ca953c7377334f96ee3 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[0].why_it_matters: sha256:f47254a85dabf2d27ac2a6050626b14359c7cabbaf9c63a71553649f5f6752e4 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].agent: codex-adversarial -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].agent_confidence: sha256:ad48ff99415b2f007dc35b7eb553fd1eb35ebfa2f2f308acd9488eeb86f71fa8 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].category: sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].current_code: sha256:95abd0fa465e9d41f4578e977f3ac54ad99b05118deeb0127fd6d9a4bbd1e2eb -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].file: triggarr/web/validation.py -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].fix_hint: sha256:4557baec16295212ba42d53c790c300ddcdbe12bfc1f7f94c765973855bd04f1 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].line: 85 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].problem: sha256:37ea85c141434b0e8cc5df649d0a4b5b070efe15d60ff87f99e18a7fd6e184b4 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].severity: sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].source_window[0]: sha256:fc6acc58b0d2e4b87e7f3737cb47c30b86d13acdf356020f3394a4e28c1b7477 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].source_window[1]: sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].source_window[2]: sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].source_window[3]: sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].source_window[4]: sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].source_window[5]: sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].source_window[6]: sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].title: sha256:ee0906ffe9ddb7038f84a6f1d36fd0c9c7785a3876e656298e38d4bdc380b0d2 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[1].why_it_matters: sha256:1d41b935172d9800e1ee3976ceddae1165522c99321d451f590ff68211ad68a6 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].agent: impact -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].agent_confidence: sha256:b4944c6ff08dc6f43da2e9c824669b7d927dd1fa976fadc7b456881f51bf5ccc -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].category: sha256:e9d2fa82c1b28de0b5f3b1a9a311c35290be120039e74565666b2eacd78a0db8 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].current_code: sha256:95abd0fa465e9d41f4578e977f3ac54ad99b05118deeb0127fd6d9a4bbd1e2eb -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].cwe: sha256:c051865328b3785824d077aa68c6c887594337a8876e6f8dde046cc48f8be749 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].file: triggarr/web/validation.py -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].fix_hint: sha256:252351e4eda92337711cbbace5af5f02864dcea6c4be018f3b456bf43a475f17 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].intent_doc_match: sha256:8ac24611cfe47c129e37108bc6adc6843c4fe8fb9c37c27fac8a1835ba660307 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].line: 87 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].problem: sha256:507f8e4ba7b0aadb6d37eb45b162b3ad5cb5b416bab5b6bc03772ac5a25b63e8 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].source_window[0]: sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].source_window[1]: sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].source_window[2]: sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].source_window[3]: sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].source_window[4]: sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].source_window[5]: sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].source_window[6]: sha256:8441e9dc7ef6b32e165b29cc5ef7cc39cd9b9e4a7728dcc9b01331b99f116253 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].title: sha256:1921f463d437650fec91853234a158ec90828e01fd98f1b6ed2ba67e6335191f -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[2].why_it_matters: sha256:2edd5b4f964f155da8f374a70159cbdfee4bc39a774ec4b2228164b531f2018c -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].agent: security -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].agent_confidence: sha256:ff5a1ae012afa5d4c889c50ad427aaf545d31a4fac04ffc1c4d03d403ba4250a -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].category: sha256:957cd792225924f94088800508637992ebc6cdcd9950ebff17e14c8fb598afc1 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].current_code: sha256:95abd0fa465e9d41f4578e977f3ac54ad99b05118deeb0127fd6d9a4bbd1e2eb -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].cwe: sha256:c051865328b3785824d077aa68c6c887594337a8876e6f8dde046cc48f8be749 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].file: triggarr/web/validation.py -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].fix_hint: sha256:c82e7f88d0fb6495468c03cb87ab6bf9167f18315a1baad908aa45ca42045ff3 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].line: 85 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].problem: sha256:9c81a46f569504bd0eae9fd1d872cafe7cd3a2bc8ca79bf401f43e2fbaf47eee -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].source_window[0]: sha256:fc6acc58b0d2e4b87e7f3737cb47c30b86d13acdf356020f3394a4e28c1b7477 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].source_window[1]: sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].source_window[2]: sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].source_window[3]: sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].source_window[4]: sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].source_window[5]: sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].source_window[6]: sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].title: sha256:8d2fc74b59a42d7d602ce7c21b310dec8115786bd291324a4c13377ba9de87c3 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].members[3].why_it_matters: sha256:42bd93e5a6ae97ed75d74c3a4262bec1920b1bbc360be044729c778fa4c7f7e8 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].orchestrator_score: 100 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].problem: sha256:d29277d7c711873f930b3d4ecec523322a93f64485339df7ef3ba212797c09fa -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].severity: sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].silenced_marker_nearby: sha256:fcbcf165908dd18a9e49f7ff27810176db8e9f63b4352213741664245224f8aa -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].snapshot.at_pass: 1 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].snapshot.band: critical -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].snapshot.canonical_line_content: sha256:4c3544b3e573f4cae2f0a8ee27029fe96c97df9cf442ed5697d802d7e50d84b5 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].snapshot.file: triggarr/web/validation.py -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].snapshot.line: 87 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].source_window[0]: sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].source_window[1]: sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].source_window[2]: sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].source_window[3]: sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].source_window[4]: sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].source_window[5]: sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].source_window[6]: sha256:8441e9dc7ef6b32e165b29cc5ef7cc39cd9b9e4a7728dcc9b01331b99f116253 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].stable_hash: sha256:8730351ae3e46f00b32fd22fb2bd5057bf6bfd36f7a5dd06c0eaa7f651237d44 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].status: new -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].title: sha256:c6e017fc57cd45cbe57a96af97f00116d33daee5dad01ca953c7377334f96ee3 -> (absent)
- UNALLOWED findings[37f78051c196a63173d068b85ccd0afe1a45d55dd80f2af160e7c43f9c54154d].why_it_matters: sha256:f47254a85dabf2d27ac2a6050626b14359c7cabbaf9c63a71553649f5f6752e4 -> (absent)
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].agent: (absent) -> codex-adversarial
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].agent_confidence: (absent) -> sha256:ad48ff99415b2f007dc35b7eb553fd1eb35ebfa2f2f308acd9488eeb86f71fa8
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].attribution[0]: (absent) -> sha256:610cb42c95dd518d546a1f6603bb920b2a5e04c6c1514e84e47433dc58102d3a
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].attribution[1]: (absent) -> sha256:361e7b1acb6d80d7ef7f8e0aa4204fcebe6a047e57167c83979fbcdb9d37833c
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].attribution[2]: (absent) -> sha256:96f34c94f7cf7eb0d8a8aadf48980e0ac0d131b90ee50a682424071e25f2f534
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].attribution[3]: (absent) -> sha256:cac9fa20faacbccf6f0e6b780fdfa8793d3bc0773ca4d5b280c4bbe9ac02cac3
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].band: (absent) -> critical
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].canonical_line_content: (absent) -> sha256:7d385043a71eca1b81988ac3c806d768705c1ce4f5b5c51e244961f0cc14f6da
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].category: (absent) -> sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].current_code: (absent) -> sha256:95abd0fa465e9d41f4578e977f3ac54ad99b05118deeb0127fd6d9a4bbd1e2eb
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].file: (absent) -> triggarr/web/validation.py
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].fix_hint: (absent) -> sha256:4557baec16295212ba42d53c790c300ddcdbe12bfc1f7f94c765973855bd04f1
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].id: (absent) -> sha256:73ca1c8c1b1765028ee41138e76ea51dc55c913de8ba80028c40cedfc30b6369
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].in_diff: (absent) -> sha256:b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].line: (absent) -> 85
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].agent: (absent) -> codex-adversarial
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].agent_confidence: (absent) -> sha256:ad48ff99415b2f007dc35b7eb553fd1eb35ebfa2f2f308acd9488eeb86f71fa8
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].category: (absent) -> sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].current_code: (absent) -> sha256:95abd0fa465e9d41f4578e977f3ac54ad99b05118deeb0127fd6d9a4bbd1e2eb
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].file: (absent) -> triggarr/web/validation.py
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].fix_hint: (absent) -> sha256:4557baec16295212ba42d53c790c300ddcdbe12bfc1f7f94c765973855bd04f1
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].line: (absent) -> 85
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].problem: (absent) -> sha256:37ea85c141434b0e8cc5df649d0a4b5b070efe15d60ff87f99e18a7fd6e184b4
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].severity: (absent) -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].source_window[0]: (absent) -> sha256:fc6acc58b0d2e4b87e7f3737cb47c30b86d13acdf356020f3394a4e28c1b7477
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].source_window[1]: (absent) -> sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].source_window[2]: (absent) -> sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].source_window[3]: (absent) -> sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].source_window[4]: (absent) -> sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].source_window[5]: (absent) -> sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].source_window[6]: (absent) -> sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].title: (absent) -> sha256:ee0906ffe9ddb7038f84a6f1d36fd0c9c7785a3876e656298e38d4bdc380b0d2
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[0].why_it_matters: (absent) -> sha256:1d41b935172d9800e1ee3976ceddae1165522c99321d451f590ff68211ad68a6
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].agent: (absent) -> bugs
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].agent_confidence: (absent) -> sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].category: (absent) -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].current_code: (absent) -> sha256:21ecfa845b615bcabfb9870e3f30b3064da664f49f86fe57529afdcddcda594a
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].cwe: (absent) -> sha256:4779bc407343d916c5a4f6a996174046419bdd87ce6c609054dc8788b3dfc233
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].file: (absent) -> triggarr/web/validation.py
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].fix_hint: (absent) -> sha256:cad6e60c8f0dae8f73d82ec9cf9880ee01b5c8db04cab2405e93a39e7d1ad527
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].line: (absent) -> 87
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].problem: (absent) -> sha256:d29277d7c711873f930b3d4ecec523322a93f64485339df7ef3ba212797c09fa
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].severity: (absent) -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].source_window[0]: (absent) -> sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].source_window[1]: (absent) -> sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].source_window[2]: (absent) -> sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].source_window[3]: (absent) -> sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].source_window[4]: (absent) -> sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].source_window[5]: (absent) -> sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].source_window[6]: (absent) -> sha256:8441e9dc7ef6b32e165b29cc5ef7cc39cd9b9e4a7728dcc9b01331b99f116253
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].title: (absent) -> sha256:c6e017fc57cd45cbe57a96af97f00116d33daee5dad01ca953c7377334f96ee3
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[1].why_it_matters: (absent) -> sha256:f47254a85dabf2d27ac2a6050626b14359c7cabbaf9c63a71553649f5f6752e4
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].agent: (absent) -> security
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].agent_confidence: (absent) -> sha256:ff5a1ae012afa5d4c889c50ad427aaf545d31a4fac04ffc1c4d03d403ba4250a
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].category: (absent) -> sha256:957cd792225924f94088800508637992ebc6cdcd9950ebff17e14c8fb598afc1
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].current_code: (absent) -> sha256:95abd0fa465e9d41f4578e977f3ac54ad99b05118deeb0127fd6d9a4bbd1e2eb
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].cwe: (absent) -> sha256:c051865328b3785824d077aa68c6c887594337a8876e6f8dde046cc48f8be749
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].file: (absent) -> triggarr/web/validation.py
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].fix_hint: (absent) -> sha256:c82e7f88d0fb6495468c03cb87ab6bf9167f18315a1baad908aa45ca42045ff3
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].line: (absent) -> 85
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].problem: (absent) -> sha256:9c81a46f569504bd0eae9fd1d872cafe7cd3a2bc8ca79bf401f43e2fbaf47eee
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].source_window[0]: (absent) -> sha256:fc6acc58b0d2e4b87e7f3737cb47c30b86d13acdf356020f3394a4e28c1b7477
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].source_window[1]: (absent) -> sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].source_window[2]: (absent) -> sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].source_window[3]: (absent) -> sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].source_window[4]: (absent) -> sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].source_window[5]: (absent) -> sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].source_window[6]: (absent) -> sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].title: (absent) -> sha256:8d2fc74b59a42d7d602ce7c21b310dec8115786bd291324a4c13377ba9de87c3
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[2].why_it_matters: (absent) -> sha256:42bd93e5a6ae97ed75d74c3a4262bec1920b1bbc360be044729c778fa4c7f7e8
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].agent: (absent) -> impact
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].agent_confidence: (absent) -> sha256:b4944c6ff08dc6f43da2e9c824669b7d927dd1fa976fadc7b456881f51bf5ccc
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].category: (absent) -> sha256:e9d2fa82c1b28de0b5f3b1a9a311c35290be120039e74565666b2eacd78a0db8
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].current_code: (absent) -> sha256:95abd0fa465e9d41f4578e977f3ac54ad99b05118deeb0127fd6d9a4bbd1e2eb
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].cwe: (absent) -> sha256:c051865328b3785824d077aa68c6c887594337a8876e6f8dde046cc48f8be749
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].file: (absent) -> triggarr/web/validation.py
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].fix_hint: (absent) -> sha256:252351e4eda92337711cbbace5af5f02864dcea6c4be018f3b456bf43a475f17
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].intent_doc_match: (absent) -> sha256:8ac24611cfe47c129e37108bc6adc6843c4fe8fb9c37c27fac8a1835ba660307
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].line: (absent) -> 87
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].problem: (absent) -> sha256:507f8e4ba7b0aadb6d37eb45b162b3ad5cb5b416bab5b6bc03772ac5a25b63e8
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].source_window[0]: (absent) -> sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].source_window[1]: (absent) -> sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].source_window[2]: (absent) -> sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].source_window[3]: (absent) -> sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].source_window[4]: (absent) -> sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].source_window[5]: (absent) -> sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].source_window[6]: (absent) -> sha256:8441e9dc7ef6b32e165b29cc5ef7cc39cd9b9e4a7728dcc9b01331b99f116253
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].title: (absent) -> sha256:1921f463d437650fec91853234a158ec90828e01fd98f1b6ed2ba67e6335191f
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].members[3].why_it_matters: (absent) -> sha256:2edd5b4f964f155da8f374a70159cbdfee4bc39a774ec4b2228164b531f2018c
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].orchestrator_score: (absent) -> 100
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].problem: (absent) -> sha256:37ea85c141434b0e8cc5df649d0a4b5b070efe15d60ff87f99e18a7fd6e184b4
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].severity: (absent) -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].silenced_marker_nearby: (absent) -> sha256:fcbcf165908dd18a9e49f7ff27810176db8e9f63b4352213741664245224f8aa
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].snapshot.at_pass: (absent) -> 1
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].snapshot.band: (absent) -> critical
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].snapshot.canonical_line_content: (absent) -> sha256:7d385043a71eca1b81988ac3c806d768705c1ce4f5b5c51e244961f0cc14f6da
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].snapshot.file: (absent) -> triggarr/web/validation.py
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].snapshot.line: (absent) -> 85
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].source_window[0]: (absent) -> sha256:fc6acc58b0d2e4b87e7f3737cb47c30b86d13acdf356020f3394a4e28c1b7477
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].source_window[1]: (absent) -> sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].source_window[2]: (absent) -> sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].source_window[3]: (absent) -> sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].source_window[4]: (absent) -> sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].source_window[5]: (absent) -> sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].source_window[6]: (absent) -> sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].stable_hash: (absent) -> sha256:946ae3bb78b9fe68eb04ff9099c6a981bd3dd7b736d83fc7a3fa671657ae5b28
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].status: (absent) -> new
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].title: (absent) -> sha256:ee0906ffe9ddb7038f84a6f1d36fd0c9c7785a3876e656298e38d4bdc380b0d2
- UNALLOWED findings[6a3d6e71ed3f68b3ab447e72a4db40e3cad79a211c6bbd9bff103f26ddceeab8].why_it_matters: (absent) -> sha256:1d41b935172d9800e1ee3976ceddae1165522c99321d451f590ff68211ad68a6

### runs/should-quiet-1/run-3 [C]

- UNALLOWED filtered[1].line: 87 -> 85
- UNALLOWED filtered[1].title: sha256:99d5d29be7b163b3f48d9c5e365783787fe79f5c6805cfd1b10851c431eeb60d -> sha256:80a12232c264dda1e6bc00ef0e716a661d8f64b98489fda45314e60bc34dfe31
- UNALLOWED filtered[2].line: 85 -> 87
- UNALLOWED filtered[2].title: sha256:80a12232c264dda1e6bc00ef0e716a661d8f64b98489fda45314e60bc34dfe31 -> sha256:99d5d29be7b163b3f48d9c5e365783787fe79f5c6805cfd1b10851c431eeb60d
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].agent: impact -> bugs
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].agent_confidence: sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763 -> sha256:8722616204217eddb39e7df969e0698aed8e599ba62ed2de1ce49b03ade0fede
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].category: sha256:ff610fb106a3a1c1cedcc6589f563a9a1da99b391e061593d0965d58ddaddceb -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].current_code: sha256:21ecfa845b615bcabfb9870e3f30b3064da664f49f86fe57529afdcddcda594a -> sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> sha256:c051865328b3785824d077aa68c6c887594337a8876e6f8dde046cc48f8be749
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].fix_hint: sha256:18a8665bcf42ce5a26bbf3534fe407d1fe4c2af210c33ec2892561c78c195c44 -> sha256:5f40e265b39d2613c98b7fe0d040481fa2a48128b9d6d118a972fd5cf826175f
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].line: 87 -> 85
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].problem: sha256:3125e8e66e71607c475052a6477513f445f3c78873fc3fbf55656874e9588099 -> sha256:6deaa30a2f6da48ea843358344080eefc91c8d4007f166164e97fca7c11055b7
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].severity: sha256:364bb7082249ee9fbc5247ee49735c4246f271b82c2745a35107ddda0d7cabcc -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].source_window[0]: sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b -> sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].source_window[1]: sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f -> sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].source_window[2]: sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55 -> sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].source_window[3]: sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f -> sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].source_window[4]: sha256:8441e9dc7ef6b32e165b29cc5ef7cc39cd9b9e4a7728dcc9b01331b99f116253 -> sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].title: sha256:99d5d29be7b163b3f48d9c5e365783787fe79f5c6805cfd1b10851c431eeb60d -> sha256:80a12232c264dda1e6bc00ef0e716a661d8f64b98489fda45314e60bc34dfe31
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[2].why_it_matters: sha256:4aaaf54038fe334343952580e98a55709eefc6f79b0a5f1d226391009bb7d698 -> sha256:b87f9b529b313ff37eed1e6b577cfeff9f34285e5471823afc5fbc09c1f986bc
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].agent: bugs -> impact
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].agent_confidence: sha256:8722616204217eddb39e7df969e0698aed8e599ba62ed2de1ce49b03ade0fede -> sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> sha256:ff610fb106a3a1c1cedcc6589f563a9a1da99b391e061593d0965d58ddaddceb
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].current_code: sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b -> sha256:21ecfa845b615bcabfb9870e3f30b3064da664f49f86fe57529afdcddcda594a
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].cwe: sha256:c051865328b3785824d077aa68c6c887594337a8876e6f8dde046cc48f8be749 -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].fix_hint: sha256:5f40e265b39d2613c98b7fe0d040481fa2a48128b9d6d118a972fd5cf826175f -> sha256:18a8665bcf42ce5a26bbf3534fe407d1fe4c2af210c33ec2892561c78c195c44
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].line: 85 -> 87
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].problem: sha256:6deaa30a2f6da48ea843358344080eefc91c8d4007f166164e97fca7c11055b7 -> sha256:3125e8e66e71607c475052a6477513f445f3c78873fc3fbf55656874e9588099
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> sha256:364bb7082249ee9fbc5247ee49735c4246f271b82c2745a35107ddda0d7cabcc
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].source_window[0]: sha256:57a48972e02808ac2ee7bbea2ab193d9bdf6196d13a619a89d69ba94f6ae08ce -> sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].source_window[1]: sha256:bc600a0e17289de9de33ab9714d61afa32ec8a80cf1d48354bcb641f702af424 -> sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].source_window[2]: sha256:6c1c57a8d3f71a3bdfc2d45d80fd87c5a20db40afa6b85943c8377b7edd66a9b -> sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].source_window[3]: sha256:ff5a713a9b4c2c66087d8ea61f19b1bac8a4526ca75dd3f7bf2304a0b10cf00f -> sha256:527e4c8b58b5a3a5b5dc7deafb18d6f58cbdd78a85ff65ae85dd1f4fd948eb5f
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].source_window[4]: sha256:06ac6677b37fe5207eea8727cea542260e370854ba4ab26003c99a79fc3aff55 -> sha256:8441e9dc7ef6b32e165b29cc5ef7cc39cd9b9e4a7728dcc9b01331b99f116253
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].title: sha256:80a12232c264dda1e6bc00ef0e716a661d8f64b98489fda45314e60bc34dfe31 -> sha256:99d5d29be7b163b3f48d9c5e365783787fe79f5c6805cfd1b10851c431eeb60d
- UNALLOWED findings[0a40ea77053b16711975e515ea5bb1abcfd361ab9ea22c634dc63c28a8ec7950].members[3].why_it_matters: sha256:b87f9b529b313ff37eed1e6b577cfeff9f34285e5471823afc5fbc09c1f986bc -> sha256:4aaaf54038fe334343952580e98a55709eefc6f79b0a5f1d226391009bb7d698

### runs/third-organic-should-catch/run-2 [B] (protected)

- UNALLOWED filtered[0].reason: sha256:2674ad5367feccf89efe37d4270e6ffd44685556f909918da3a2f65372d64321 -> sha256:4b55bfc0a989ffc4e82bf563c44a171139d39696f4fd159c337a381ea7cdd900
- UNALLOWED filtered[0].title: sha256:4ad77cbe8eb444b23ebec784554d3b239c99f5511acac485637bda4cfcfd699b -> sha256:f478c3a42f7101d6bf7d7749d0e6a3ef4d33990cdd21446928c1b8515611ad77
- UNALLOWED filtered[1].reason: sha256:2674ad5367feccf89efe37d4270e6ffd44685556f909918da3a2f65372d64321 -> sha256:4b55bfc0a989ffc4e82bf563c44a171139d39696f4fd159c337a381ea7cdd900
- UNALLOWED filtered[1].title: sha256:f478c3a42f7101d6bf7d7749d0e6a3ef4d33990cdd21446928c1b8515611ad77 -> sha256:46156577598e762fd034b9236b48c54aa05ba91d56b816f55928a5c2ed1c7053
- UNALLOWED filtered[2].line: 307 -> 308
- UNALLOWED filtered[2].reason: sha256:2674ad5367feccf89efe37d4270e6ffd44685556f909918da3a2f65372d64321 -> sha256:4b55bfc0a989ffc4e82bf563c44a171139d39696f4fd159c337a381ea7cdd900
- UNALLOWED filtered[2].title: sha256:46156577598e762fd034b9236b48c54aa05ba91d56b816f55928a5c2ed1c7053 -> sha256:bfd4996ce76c5b6ffcddb9fe7a7d4dae40ceafffd8abdbb2d41a6b7b1ba223c6
- UNALLOWED findings.order: sha256:5bb613360d88b554ad4ccb5010a0dee8c6b3bb6f113be62a5ff7b9be06c11527 -> sha256:00bcd878e906380f38fb8d537257472179eb5e66a992bb199bc032d6ab57799e
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].agent: bugs -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].agent_confidence: sha256:8241649609f88ccd2a0a5b233a07a538ec313ff6adf695aa44a969dbca39f67d -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].attribution[0]: sha256:610cb42c95dd518d546a1f6603bb920b2a5e04c6c1514e84e47433dc58102d3a -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].attribution[1]: sha256:7d2a878caddd9607bc53d207b7a721b971748c3b78e5dc50f25325c50db20f2e -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].attribution[2]: sha256:96f34c94f7cf7eb0d8a8aadf48980e0ac0d131b90ee50a682424071e25f2f534 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].attribution[3]: sha256:cac9fa20faacbccf6f0e6b780fdfa8793d3bc0773ca4d5b280c4bbe9ac02cac3 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].band: critical -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].current_code: sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].fix_hint: sha256:5df4fdfb437521467fc9f175b141fb2ca4fb50a21d41739a052d0c0768a0fa5f -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].id: sha256:f7a33a0e52e4cd019310f1f9bca293dad2fd118a2304ea0ce7c3008a348766dd -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].in_diff: sha256:b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].line: 308 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].agent: bugs -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].agent_confidence: sha256:8241649609f88ccd2a0a5b233a07a538ec313ff6adf695aa44a969dbca39f67d -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].current_code: sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].fix_hint: sha256:5df4fdfb437521467fc9f175b141fb2ca4fb50a21d41739a052d0c0768a0fa5f -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].line: 308 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].problem: sha256:aa1ff19c77126b8b3c02551d26bb67abd330bf441860df50e4e159b793994959 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].source_window[0]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].source_window[1]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].source_window[2]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].source_window[3]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].source_window[4]: sha256:12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].title: sha256:bfd4996ce76c5b6ffcddb9fe7a7d4dae40ceafffd8abdbb2d41a6b7b1ba223c6 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[0].why_it_matters: sha256:4fcef8d0d92a115e63f49157702ff0dafb4578578af422f91ea39216a8aa9509 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].agent: codex-adversarial -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].agent_confidence: sha256:7b1a278f5abe8e9da907fc9c29dfd432d60dc76e17b0fabab659d2a508bc65c4 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].category: sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].fix_hint: sha256:953edf8d3868a97c9cfccb5d399ba889a536a505018662b9169b9d6b3cc6f0f4 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].line: 307 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].problem: sha256:d1d6222c09a22d0872e9c8981c9eb710304f1155a51513c90db72102fd81621b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].source_window[0]: sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].source_window[1]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].source_window[2]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].source_window[3]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].source_window[4]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].title: sha256:4ad77cbe8eb444b23ebec784554d3b239c99f5511acac485637bda4cfcfd699b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[1].why_it_matters: sha256:bde5b074f17a8d52c876a86de2f86b912d5dbb2ecf7e1c7d7db4718dd3a16ca2 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].agent: architecture -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].agent_confidence: sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].category: sha256:2b5b64f71e5ba181f65f150c8ed433facc7d0dc223cab631067d2ed40615ab86 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].line: 307 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].problem: sha256:8ac11b632cb0153f9181b09dd970ff6ca6e7efcb819cf78414ea0a617f662658 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].source_window[0]: sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].source_window[1]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].source_window[2]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].source_window[3]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].source_window[4]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].title: sha256:f478c3a42f7101d6bf7d7749d0e6a3ef4d33990cdd21446928c1b8515611ad77 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[2].why_it_matters: sha256:ce89de673f2b393a729892ef29f320971969d3ec2f8f08e0da921276a2d7fb0d -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].agent: impact -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].agent_confidence: sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].category: sha256:e9d2fa82c1b28de0b5f3b1a9a311c35290be120039e74565666b2eacd78a0db8 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].current_code: sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].cwe: sha256:4d616b416ea7dfb61c69c800dd3a83b4df88bf4fabcaa2451cf85ab9a8eb230e -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].fix_hint: sha256:bb6beeb721c59cfb7d6caad69b4438dd62d81aca9b5ae26843f41b7ec1c476c3 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].line: 307 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].problem: sha256:c5a70ac042c563996d84b4e97e9f24eb3f38a0f1de67808c1b1c0ac5b691af20 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].source_window[0]: sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].source_window[1]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].source_window[2]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].source_window[3]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].source_window[4]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].title: sha256:46156577598e762fd034b9236b48c54aa05ba91d56b816f55928a5c2ed1c7053 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].members[3].why_it_matters: sha256:63aabcd08104a6d5b145e1de38b41ac1bae8e3f737ce62d43ae97a8f440e14e3 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].orchestrator_score: 100 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].problem: sha256:aa1ff19c77126b8b3c02551d26bb67abd330bf441860df50e4e159b793994959 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].silenced_marker_nearby: sha256:fcbcf165908dd18a9e49f7ff27810176db8e9f63b4352213741664245224f8aa -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].snapshot.at_pass: 1 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].snapshot.band: critical -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].snapshot.canonical_line_content: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].snapshot.file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].snapshot.line: 308 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].source_window[0]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].source_window[1]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].source_window[2]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].source_window[3]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].source_window[4]: sha256:12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].stable_hash: sha256:b7db314a5fe3eafac160d0432cfff941176b462d23ed321c82a2d9ac2ff76f48 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].status: new -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].title: sha256:bfd4996ce76c5b6ffcddb9fe7a7d4dae40ceafffd8abdbb2d41a6b7b1ba223c6 -> (absent)
- UNALLOWED findings[2cb2358b0ad3574b0e2ad8e743813b28d8d8097723de53d1dced65af34d933e6].why_it_matters: sha256:4fcef8d0d92a115e63f49157702ff0dafb4578578af422f91ea39216a8aa9509 -> (absent)
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].agent: (absent) -> codex-adversarial
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].agent_confidence: (absent) -> sha256:7b1a278f5abe8e9da907fc9c29dfd432d60dc76e17b0fabab659d2a508bc65c4
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].attribution[0]: (absent) -> sha256:610cb42c95dd518d546a1f6603bb920b2a5e04c6c1514e84e47433dc58102d3a
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].attribution[1]: (absent) -> sha256:7d2a878caddd9607bc53d207b7a721b971748c3b78e5dc50f25325c50db20f2e
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].attribution[2]: (absent) -> sha256:96f34c94f7cf7eb0d8a8aadf48980e0ac0d131b90ee50a682424071e25f2f534
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].attribution[3]: (absent) -> sha256:cac9fa20faacbccf6f0e6b780fdfa8793d3bc0773ca4d5b280c4bbe9ac02cac3
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].band: (absent) -> critical
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].category: (absent) -> sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].fix_hint: (absent) -> sha256:953edf8d3868a97c9cfccb5d399ba889a536a505018662b9169b9d6b3cc6f0f4
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].id: (absent) -> sha256:73ca1c8c1b1765028ee41138e76ea51dc55c913de8ba80028c40cedfc30b6369
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].line: (absent) -> 307
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].agent: (absent) -> codex-adversarial
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].agent_confidence: (absent) -> sha256:7b1a278f5abe8e9da907fc9c29dfd432d60dc76e17b0fabab659d2a508bc65c4
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].category: (absent) -> sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].fix_hint: (absent) -> sha256:953edf8d3868a97c9cfccb5d399ba889a536a505018662b9169b9d6b3cc6f0f4
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].line: (absent) -> 307
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].problem: (absent) -> sha256:d1d6222c09a22d0872e9c8981c9eb710304f1155a51513c90db72102fd81621b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].source_window[0]: (absent) -> sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].source_window[1]: (absent) -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].source_window[2]: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].source_window[3]: (absent) -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].source_window[4]: (absent) -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].title: (absent) -> sha256:4ad77cbe8eb444b23ebec784554d3b239c99f5511acac485637bda4cfcfd699b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[0].why_it_matters: (absent) -> sha256:bde5b074f17a8d52c876a86de2f86b912d5dbb2ecf7e1c7d7db4718dd3a16ca2
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].agent: (absent) -> architecture
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].agent_confidence: (absent) -> sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].category: (absent) -> sha256:2b5b64f71e5ba181f65f150c8ed433facc7d0dc223cab631067d2ed40615ab86
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].line: (absent) -> 307
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].problem: (absent) -> sha256:8ac11b632cb0153f9181b09dd970ff6ca6e7efcb819cf78414ea0a617f662658
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].source_window[0]: (absent) -> sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].source_window[1]: (absent) -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].source_window[2]: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].source_window[3]: (absent) -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].source_window[4]: (absent) -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].title: (absent) -> sha256:f478c3a42f7101d6bf7d7749d0e6a3ef4d33990cdd21446928c1b8515611ad77
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[1].why_it_matters: (absent) -> sha256:ce89de673f2b393a729892ef29f320971969d3ec2f8f08e0da921276a2d7fb0d
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].agent: (absent) -> impact
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].agent_confidence: (absent) -> sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].category: (absent) -> sha256:e9d2fa82c1b28de0b5f3b1a9a311c35290be120039e74565666b2eacd78a0db8
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].current_code: (absent) -> sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].cwe: (absent) -> sha256:4d616b416ea7dfb61c69c800dd3a83b4df88bf4fabcaa2451cf85ab9a8eb230e
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].fix_hint: (absent) -> sha256:bb6beeb721c59cfb7d6caad69b4438dd62d81aca9b5ae26843f41b7ec1c476c3
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].line: (absent) -> 307
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].problem: (absent) -> sha256:c5a70ac042c563996d84b4e97e9f24eb3f38a0f1de67808c1b1c0ac5b691af20
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].source_window[0]: (absent) -> sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].source_window[1]: (absent) -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].source_window[2]: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].source_window[3]: (absent) -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].source_window[4]: (absent) -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].title: (absent) -> sha256:46156577598e762fd034b9236b48c54aa05ba91d56b816f55928a5c2ed1c7053
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[2].why_it_matters: (absent) -> sha256:63aabcd08104a6d5b145e1de38b41ac1bae8e3f737ce62d43ae97a8f440e14e3
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].agent: (absent) -> bugs
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].agent_confidence: (absent) -> sha256:8241649609f88ccd2a0a5b233a07a538ec313ff6adf695aa44a969dbca39f67d
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].category: (absent) -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].current_code: (absent) -> sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].fix_hint: (absent) -> sha256:5df4fdfb437521467fc9f175b141fb2ca4fb50a21d41739a052d0c0768a0fa5f
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].line: (absent) -> 308
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].problem: (absent) -> sha256:aa1ff19c77126b8b3c02551d26bb67abd330bf441860df50e4e159b793994959
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].source_window[0]: (absent) -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].source_window[1]: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].source_window[2]: (absent) -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].source_window[3]: (absent) -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].source_window[4]: (absent) -> sha256:12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].title: (absent) -> sha256:bfd4996ce76c5b6ffcddb9fe7a7d4dae40ceafffd8abdbb2d41a6b7b1ba223c6
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].members[3].why_it_matters: (absent) -> sha256:4fcef8d0d92a115e63f49157702ff0dafb4578578af422f91ea39216a8aa9509
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].orchestrator_score: (absent) -> 100
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].problem: (absent) -> sha256:d1d6222c09a22d0872e9c8981c9eb710304f1155a51513c90db72102fd81621b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].snapshot.at_pass: (absent) -> 1
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].snapshot.band: (absent) -> critical
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].snapshot.canonical_line_content: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].snapshot.file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].snapshot.line: (absent) -> 307
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].source_window[0]: (absent) -> sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].source_window[1]: (absent) -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].source_window[2]: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].source_window[3]: (absent) -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].source_window[4]: (absent) -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].stable_hash: (absent) -> sha256:285c711120ebd151d747824a8d3822ec83263454a494590d70807c93a97f7b57
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].status: (absent) -> new
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].title: (absent) -> sha256:4ad77cbe8eb444b23ebec784554d3b239c99f5511acac485637bda4cfcfd699b
- UNALLOWED findings[2d81f598f7741ca8adb113d0bd7f6a44c38c960b3f46f8e629adbe2276a26d5c].why_it_matters: (absent) -> sha256:bde5b074f17a8d52c876a86de2f86b912d5dbb2ecf7e1c7d7db4718dd3a16ca2

### runs/third-organic-should-catch/run-3 [B] (protected)

- UNALLOWED filtered[0].reason: sha256:cd5a63687ce45491ab73e7c71f2cea258d262005379c2366d2d1003b79de3258 -> sha256:1bd578ded95b292775ffb545d0b750ddd36698815d06609bf2c6f1a40c697605
- UNALLOWED filtered[0].title: sha256:c27d0c408f0a39339c9d667743858d13609d09be1380efebbffa9d2ae3db0ca2 -> sha256:7499492732b352fadc616cca95e97a5be55f621aed6d01b4390399cb1a682652
- UNALLOWED filtered[1].line: 308 -> 307
- UNALLOWED filtered[1].reason: sha256:cd5a63687ce45491ab73e7c71f2cea258d262005379c2366d2d1003b79de3258 -> sha256:1bd578ded95b292775ffb545d0b750ddd36698815d06609bf2c6f1a40c697605
- UNALLOWED filtered[1].title: sha256:ad3c8d9c6325552ea85b18e0a21a59d0d753457ba5923f4648ee9b72c6817b59 -> sha256:16afa0087177e845d48139b9c52687711237f672c1b26002c696abfafd9463d3
- UNALLOWED filtered[2].line: 307 -> 308
- UNALLOWED filtered[2].reason: sha256:cd5a63687ce45491ab73e7c71f2cea258d262005379c2366d2d1003b79de3258 -> sha256:1bd578ded95b292775ffb545d0b750ddd36698815d06609bf2c6f1a40c697605
- UNALLOWED filtered[2].title: sha256:7499492732b352fadc616cca95e97a5be55f621aed6d01b4390399cb1a682652 -> sha256:ad3c8d9c6325552ea85b18e0a21a59d0d753457ba5923f4648ee9b72c6817b59
- UNALLOWED filtered[3].line: 307 -> 308
- UNALLOWED filtered[3].reason: sha256:cd5a63687ce45491ab73e7c71f2cea258d262005379c2366d2d1003b79de3258 -> sha256:1bd578ded95b292775ffb545d0b750ddd36698815d06609bf2c6f1a40c697605
- UNALLOWED filtered[3].title: sha256:16afa0087177e845d48139b9c52687711237f672c1b26002c696abfafd9463d3 -> sha256:a70e59ad882d39ce6f35d14a543119ac8210921194f3b7d23628f9fb7de4a687
- UNALLOWED findings.order: sha256:c88e75a2c37e0f0b242146efa5a2dd90dff1f310b722bffcf268e2d8c158058d -> sha256:3ae04a0e8e294c0420361309fc2e892e32a178ca0e30c2eb734acc9e2a5ef0a9
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].agent: impact -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].agent_confidence: sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].attribution[0]: sha256:610cb42c95dd518d546a1f6603bb920b2a5e04c6c1514e84e47433dc58102d3a -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].attribution[1]: sha256:7d2a878caddd9607bc53d207b7a721b971748c3b78e5dc50f25325c50db20f2e -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].attribution[2]: sha256:96f34c94f7cf7eb0d8a8aadf48980e0ac0d131b90ee50a682424071e25f2f534 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].attribution[3]: sha256:b8ab7d08e15e9ae907f689cc4239ce39537c20a000625e915ccd6a0e4d027443 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].attribution[4]: sha256:cac9fa20faacbccf6f0e6b780fdfa8793d3bc0773ca4d5b280c4bbe9ac02cac3 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].band: critical -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].canonical_line_content: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].current_code: sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].cwe: sha256:4d616b416ea7dfb61c69c800dd3a83b4df88bf4fabcaa2451cf85ab9a8eb230e -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].fix_hint: sha256:fe163d1fcd8d1d9daf48b86b5dd43f28f72d837e475f4628e9064fa64a4df5f8 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].id: sha256:06bfd497fdf80ecf905506cba0fcd59d193f0aa4f2354a6b296433fb18a9e32e -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].in_diff: sha256:b5bea41b6c623f7c09f1bf24dcae58ebab3c0cdd90ad966bc43a45b44867e12b -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].intent_doc_match: sha256:eb8bf0d80db323992f6b634aab492b1e6d9e96a8e87a511c2a0db75ab929452c -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].line: 308 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].agent: impact -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].agent_confidence: sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].category: sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].current_code: sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].cwe: sha256:4d616b416ea7dfb61c69c800dd3a83b4df88bf4fabcaa2451cf85ab9a8eb230e -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].fix_hint: sha256:fe163d1fcd8d1d9daf48b86b5dd43f28f72d837e475f4628e9064fa64a4df5f8 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].intent_doc_match: sha256:eb8bf0d80db323992f6b634aab492b1e6d9e96a8e87a511c2a0db75ab929452c -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].line: 308 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].problem: sha256:fffb6391c3fe3ab01e1703a3c26587def016157bf33518f3700a126270e71868 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].source_window[0]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].source_window[1]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].source_window[2]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].source_window[3]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].source_window[4]: sha256:12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].title: sha256:a70e59ad882d39ce6f35d14a543119ac8210921194f3b7d23628f9fb7de4a687 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[0].why_it_matters: sha256:4b05e754f229ec9e720a049d559dce46f5add8abf0758acee72963b24b0553ce -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].agent: codex-adversarial -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].agent_confidence: sha256:d6d824abba4afde81129c71dea75b8100e96338da5f416d2f69088f1960cb091 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].category: sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].current_code: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].fix_hint: sha256:84d7b79f6aa4abdc4cd1ea0f7908230f7854c33ae4aeec229f50cf85fe820781 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].line: 307 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].problem: sha256:4e6a84ace70c45965794815f70652082696b146f40b2606349ccee3d9e288dfb -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].severity: sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].source_window[0]: sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].source_window[1]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].source_window[2]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].source_window[3]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].source_window[4]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].title: sha256:c27d0c408f0a39339c9d667743858d13609d09be1380efebbffa9d2ae3db0ca2 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[1].why_it_matters: sha256:774d990c3c81786b55eec57555f75e95b6cc0ad50384945ffc53bf5b36a3436c -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].agent: bugs -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].agent_confidence: sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].category: sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].current_code: sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].fix_hint: sha256:60dc48b1ca9224f608f7bd3250110c1eb3d767a48c321bfd1549928df2a9f7ee -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].line: 308 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].problem: sha256:cec3aaa956516af67f4aed9703df587ae81f2f02c4287d5d459869bf4a9295de -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].source_window[0]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].source_window[1]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].source_window[2]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].source_window[3]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].source_window[4]: sha256:12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].title: sha256:ad3c8d9c6325552ea85b18e0a21a59d0d753457ba5923f4648ee9b72c6817b59 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[2].why_it_matters: sha256:2808251d9dec1a6bb64f0176105cc2d51bd8f5917260a114a57d89d3cff320f1 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].agent: language-typescript -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].agent_confidence: sha256:b4944c6ff08dc6f43da2e9c824669b7d927dd1fa976fadc7b456881f51bf5ccc -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].category: sha256:a63437a8dd71536d683bcbedce42aa51a6ecaee7c407ee4868a1bdc5d2f0906a -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].current_code: sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].fix_hint: sha256:33a321b6216b5e7a1a4e720c7eda7b061862eef6a348c6c751261dd89831b4ec -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].line: 307 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].problem: sha256:77e019bdbba80ce92c789b11e74485f7c71025d9d03fff4e224153ada05c5c98 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].severity: sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].source_window[0]: sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].source_window[1]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].source_window[2]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].source_window[3]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].source_window[4]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].title: sha256:7499492732b352fadc616cca95e97a5be55f621aed6d01b4390399cb1a682652 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[3].why_it_matters: sha256:b466e43ee0add019e07afcdc8553c9fe19b66d54976a0e2cb51c5b3d53057ce1 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].agent: architecture -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].agent_confidence: sha256:48449a14a4ff7d79bb7a1b6f3d488eba397c36ef25634c111b49baf362511afc -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].category: sha256:2b5b64f71e5ba181f65f150c8ed433facc7d0dc223cab631067d2ed40615ab86 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].current_code: sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].cwe: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].fix_hint: sha256:40d3fc6659703f260a264131c7e414ed7a6a0294eff96ff00d3f8782710d859f -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].intent_doc_match: sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].line: 307 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].problem: sha256:dd1ce5359168ccd378f42bcc15657962aadaf2bdffac819417d8af1c686185b7 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].source_window[0]: sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].source_window[1]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].source_window[2]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].source_window[3]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].source_window[4]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].title: sha256:16afa0087177e845d48139b9c52687711237f672c1b26002c696abfafd9463d3 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].members[4].why_it_matters: sha256:78368ba45dc0e7aa096873f1a2bd66717c9b60c4cd79b9a66c2279354688c779 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].orchestrator_score: 100 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].problem: sha256:fffb6391c3fe3ab01e1703a3c26587def016157bf33518f3700a126270e71868 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].severity: sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].silenced_marker_nearby: sha256:fcbcf165908dd18a9e49f7ff27810176db8e9f63b4352213741664245224f8aa -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].snapshot.at_pass: 1 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].snapshot.band: critical -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].snapshot.canonical_line_content: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].snapshot.file: src/angular/src/app/services/files/view-file.service.ts -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].snapshot.line: 308 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].source_window[0]: sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].source_window[1]: sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].source_window[2]: sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].source_window[3]: sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].source_window[4]: sha256:12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].stable_hash: sha256:7eb0c8a0778a07d4514998853b40bf0f5b58f8ab9b90b0f3251e9254c96dd406 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].status: new -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].title: sha256:a70e59ad882d39ce6f35d14a543119ac8210921194f3b7d23628f9fb7de4a687 -> (absent)
- UNALLOWED findings[01ed78b6a68493d35c324489c36ea094e0ef20d0b759169872ea820e76eb145e].why_it_matters: sha256:4b05e754f229ec9e720a049d559dce46f5add8abf0758acee72963b24b0553ce -> (absent)
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].agent: (absent) -> codex-adversarial
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].agent_confidence: (absent) -> sha256:d6d824abba4afde81129c71dea75b8100e96338da5f416d2f69088f1960cb091
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].attribution[0]: (absent) -> sha256:610cb42c95dd518d546a1f6603bb920b2a5e04c6c1514e84e47433dc58102d3a
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].attribution[1]: (absent) -> sha256:7d2a878caddd9607bc53d207b7a721b971748c3b78e5dc50f25325c50db20f2e
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].attribution[2]: (absent) -> sha256:96f34c94f7cf7eb0d8a8aadf48980e0ac0d131b90ee50a682424071e25f2f534
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].attribution[3]: (absent) -> sha256:b8ab7d08e15e9ae907f689cc4239ce39537c20a000625e915ccd6a0e4d027443
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].attribution[4]: (absent) -> sha256:cac9fa20faacbccf6f0e6b780fdfa8793d3bc0773ca4d5b280c4bbe9ac02cac3
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].band: (absent) -> critical
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].canonical_line_content: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].category: (absent) -> sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].current_code: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].fix_hint: (absent) -> sha256:84d7b79f6aa4abdc4cd1ea0f7908230f7854c33ae4aeec229f50cf85fe820781
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].id: (absent) -> sha256:73ca1c8c1b1765028ee41138e76ea51dc55c913de8ba80028c40cedfc30b6369
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].line: (absent) -> 307
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].agent: (absent) -> codex-adversarial
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].agent_confidence: (absent) -> sha256:d6d824abba4afde81129c71dea75b8100e96338da5f416d2f69088f1960cb091
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].category: (absent) -> sha256:6b81752dfc28be01d85492575a79a0ba07139de4cdc7bc33707ecec74f77cfc7
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].current_code: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].fix_hint: (absent) -> sha256:84d7b79f6aa4abdc4cd1ea0f7908230f7854c33ae4aeec229f50cf85fe820781
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].line: (absent) -> 307
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].problem: (absent) -> sha256:4e6a84ace70c45965794815f70652082696b146f40b2606349ccee3d9e288dfb
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].severity: (absent) -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].source_window[0]: (absent) -> sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].source_window[1]: (absent) -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].source_window[2]: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].source_window[3]: (absent) -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].source_window[4]: (absent) -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].title: (absent) -> sha256:c27d0c408f0a39339c9d667743858d13609d09be1380efebbffa9d2ae3db0ca2
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[0].why_it_matters: (absent) -> sha256:774d990c3c81786b55eec57555f75e95b6cc0ad50384945ffc53bf5b36a3436c
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].agent: (absent) -> language-typescript
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].agent_confidence: (absent) -> sha256:b4944c6ff08dc6f43da2e9c824669b7d927dd1fa976fadc7b456881f51bf5ccc
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].category: (absent) -> sha256:a63437a8dd71536d683bcbedce42aa51a6ecaee7c407ee4868a1bdc5d2f0906a
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].current_code: (absent) -> sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].fix_hint: (absent) -> sha256:33a321b6216b5e7a1a4e720c7eda7b061862eef6a348c6c751261dd89831b4ec
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].line: (absent) -> 307
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].problem: (absent) -> sha256:77e019bdbba80ce92c789b11e74485f7c71025d9d03fff4e224153ada05c5c98
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].severity: (absent) -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].source_window[0]: (absent) -> sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].source_window[1]: (absent) -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].source_window[2]: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].source_window[3]: (absent) -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].source_window[4]: (absent) -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].title: (absent) -> sha256:7499492732b352fadc616cca95e97a5be55f621aed6d01b4390399cb1a682652
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[1].why_it_matters: (absent) -> sha256:b466e43ee0add019e07afcdc8553c9fe19b66d54976a0e2cb51c5b3d53057ce1
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].agent: (absent) -> architecture
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].agent_confidence: (absent) -> sha256:48449a14a4ff7d79bb7a1b6f3d488eba397c36ef25634c111b49baf362511afc
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].category: (absent) -> sha256:2b5b64f71e5ba181f65f150c8ed433facc7d0dc223cab631067d2ed40615ab86
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].current_code: (absent) -> sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].fix_hint: (absent) -> sha256:40d3fc6659703f260a264131c7e414ed7a6a0294eff96ff00d3f8782710d859f
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].line: (absent) -> 307
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].problem: (absent) -> sha256:dd1ce5359168ccd378f42bcc15657962aadaf2bdffac819417d8af1c686185b7
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].source_window[0]: (absent) -> sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].source_window[1]: (absent) -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].source_window[2]: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].source_window[3]: (absent) -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].source_window[4]: (absent) -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].title: (absent) -> sha256:16afa0087177e845d48139b9c52687711237f672c1b26002c696abfafd9463d3
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[2].why_it_matters: (absent) -> sha256:78368ba45dc0e7aa096873f1a2bd66717c9b60c4cd79b9a66c2279354688c779
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].agent: (absent) -> bugs
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].agent_confidence: (absent) -> sha256:8b940be7fb78aaa6b6567dd7a3987996947460df1c668e698eb92ca77e425349
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].category: (absent) -> sha256:d00ee341f03fbc289f298e7ee6d6265205d2d12c2f493bc011b3cecbd28c61a0
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].current_code: (absent) -> sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].cwe: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].fix_hint: (absent) -> sha256:60dc48b1ca9224f608f7bd3250110c1eb3d767a48c321bfd1549928df2a9f7ee
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].intent_doc_match: (absent) -> sha256:74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].line: (absent) -> 308
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].problem: (absent) -> sha256:cec3aaa956516af67f4aed9703df587ae81f2f02c4287d5d459869bf4a9295de
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].source_window[0]: (absent) -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].source_window[1]: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].source_window[2]: (absent) -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].source_window[3]: (absent) -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].source_window[4]: (absent) -> sha256:12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].title: (absent) -> sha256:ad3c8d9c6325552ea85b18e0a21a59d0d753457ba5923f4648ee9b72c6817b59
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[3].why_it_matters: (absent) -> sha256:2808251d9dec1a6bb64f0176105cc2d51bd8f5917260a114a57d89d3cff320f1
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].agent: (absent) -> impact
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].agent_confidence: (absent) -> sha256:69f59c273b6e669ac32a6dd5e1b2cb63333d8b004f9696447aee2d422ce63763
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].category: (absent) -> sha256:6096986c0d519cd7673618065e964b05cab28c6b05ea06829e010f404e446ca7
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].current_code: (absent) -> sha256:d492027642445103df64397d9df1c9c9d226a95f948fb4ed0751bf9161dbcf56
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].cwe: (absent) -> sha256:4d616b416ea7dfb61c69c800dd3a83b4df88bf4fabcaa2451cf85ab9a8eb230e
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].fix_hint: (absent) -> sha256:fe163d1fcd8d1d9daf48b86b5dd43f28f72d837e475f4628e9064fa64a4df5f8
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].intent_doc_match: (absent) -> sha256:eb8bf0d80db323992f6b634aab492b1e6d9e96a8e87a511c2a0db75ab929452c
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].line: (absent) -> 308
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].problem: (absent) -> sha256:fffb6391c3fe3ab01e1703a3c26587def016157bf33518f3700a126270e71868
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].severity: (absent) -> sha256:60d4c90eee5e731df8d3ef2891de541d2e755ff8ee9db358e26bdec49f6e0db9
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].source_window[0]: (absent) -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].source_window[1]: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].source_window[2]: (absent) -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].source_window[3]: (absent) -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].source_window[4]: (absent) -> sha256:12ae32cb1ec02d01eda3581b127c1fee3b0dc53572ed6baf239721a03d82e126
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].title: (absent) -> sha256:a70e59ad882d39ce6f35d14a543119ac8210921194f3b7d23628f9fb7de4a687
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].members[4].why_it_matters: (absent) -> sha256:4b05e754f229ec9e720a049d559dce46f5add8abf0758acee72963b24b0553ce
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].orchestrator_score: (absent) -> 100
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].problem: (absent) -> sha256:4e6a84ace70c45965794815f70652082696b146f40b2606349ccee3d9e288dfb
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].severity: (absent) -> sha256:b57c4299afe3cda154124bdb96ceaf618a9d8d9cd8d2c8f6580ff26faa5fe5ca
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].silenced_marker_nearby: (absent) -> sha256:fcbcf165908dd18a9e49f7ff27810176db8e9f63b4352213741664245224f8aa
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].snapshot.at_pass: (absent) -> 1
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].snapshot.band: (absent) -> critical
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].snapshot.canonical_line_content: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].snapshot.file: (absent) -> src/angular/src/app/services/files/view-file.service.ts
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].snapshot.line: (absent) -> 307
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].source_window[0]: (absent) -> sha256:fbfb75c3cf1df4d136399cae8e9f3b61d60ef118937a967549d8d00e06db3fef
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].source_window[1]: (absent) -> sha256:cdd53e244a40695241a5705719b80acab78cb43fc31f9661b55587919f463f0c
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].source_window[2]: (absent) -> sha256:ee92d88358b6f04762035ff9fffbfa00291ff302976524e205ca2ff27e0da6a0
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].source_window[3]: (absent) -> sha256:1be615698377e231305642eb74d1062f1a4156e79a3a573887960eec86cd027a
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].source_window[4]: (absent) -> sha256:c01ac1bca86dfe9fd8d4372b443855428a2775156f68c3795926a429320ac350
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].stable_hash: (absent) -> sha256:6e20535e4e09ae3726c8cd73a5104df2329b1adf771d97bc7002b37f2d7dad0e
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].status: (absent) -> new
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].title: (absent) -> sha256:c27d0c408f0a39339c9d667743858d13609d09be1380efebbffa9d2ae3db0ca2
- UNALLOWED findings[7c6faa94a2af6cc266b96b3be146a62ce55e4950c175387e5d82f7f80d4a7c8d].why_it_matters: (absent) -> sha256:774d990c3c81786b55eec57555f75e95b6cc0ad50384945ffc53bf5b36a3436c

## Protected-catch guardrail (53-02)

`docs/design/b3-ground-truth/REPLAY-REPORT-phase53-d05-guardrail.md` (`replay.py candidate --name phase53-d05`, candidate scorer sha256 660d09ef6753b5a987d948a69c891548898f35ce88053b0be77222a4f94f1089 = this report's candidate blob): kept 25 / protected 26, AMENDED 1 (runs/triggarr-secret-in-logs/run-2, pre-existing ledger amendment 008), REGRESSED 0, UNEVALUABLE 0 — the identical split the pre-53 scorer gives. No protected catch is lost; runs-v2.10/triggarr-secret-in-logs/run-1 is kept at warning/94 instead of critical/100.

