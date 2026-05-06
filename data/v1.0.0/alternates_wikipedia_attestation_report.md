# Alternates Wikipedia attestation — ADM1 v1.0.0

For each `name_alternates_en` entry, queries Wikipedia for: (1) title match or redirect resolution to the canonical article, (2) intitle search prefix match, (3) literal substring in the canonical article wikitext (lead or infobox name fields).

- Alternates checked: 71
- Attested via redirect/title resolution: 20
- Attested via intitle search: 36
- Attested via wikitext substring only: 2
- Unattested (flagged): 13

## Flagged alternates (no Wikipedia attestation)

Each flagged alternate failed all three checks. Most flags are expected for systematically generated spacing variants (the canonical Wikipedia title spaces words but a no-space variant was added to support consumers that strip whitespace) and for diacritic or apostrophe-form historical spellings carried for completeness. Each entry is preserved on its data-engineering merit; this report makes the lack of Wikipedia attestation visible to data consumers.

| TIS-1099 | Province | Alternate | Redirect resolved to | Search hits |
|---|---|---|---|---|
| 10 | Bangkok | `Sia-Yut'hia` | — (missing) | — |
| 14 | Phra Nakhon Si Ayutthaya | `PhraNakhonSiAyutthaya` | — (missing) | — |
| 16 | Lopburi | `Loburi` | — (missing) | — |
| 26 | Nakhon Nayok | `NakhonNayok` | — (missing) | — |
| 30 | Nakhon Ratchasima | `Nakhon Rachisima` | — (missing) | — |
| 31 | Buri Ram | `Burirum` | — (missing) | — |
| 38 | Bueng Kan | `BuengKan` | — (missing) | — |
| 45 | Roi Et | `RoiEt` | — (missing) | — |
| 52 | Lampang | `Lambang` | — (missing) | Lampang province |
| 76 | Phetchaburi | `Phet Buri` | — (missing) | — |
| 77 | Prachuap Khiri Khan | `PrachuapKhiriKhan` | — (missing) | — |
| 80 | Nakhon Si Thammarat | `NakhonSiThammarat` | — (missing) | — |
| 86 | Chumphon | `Chumpon` | — (missing) | Chumphon province |

## All alternates — full table

| TIS-1099 | Province | Alternate | Attested | Method |
|---|---|---|---|---|
| 10 | Bangkok | `Bang Makok` | ✓ | redirect |
| 10 | Bangkok | `Bangkok Special Governed District` | ✓ | redirect |
| 10 | Bangkok | `Krung Thep` | ✓ | redirect |
| 10 | Bangkok | `Krung Thep Maha Nakhon` | ✓ | redirect |
| 10 | Bangkok | `Krung Thep Mahanakhon` | ✓ | redirect |
| 10 | Bangkok | `KrungThepMahaNakhon` | ✓ | redirect |
| 10 | Bangkok | `Sia-Yut'hia` | ✗ | none |
| 11 | Samut Prakan | `SamutPrakan` | ✓ | search |
| 12 | Nonthaburi | `Nontha Buri` | ✓ | search |
| 13 | Pathum Thani | `PathumThani` | ✓ | search |
| 14 | Phra Nakhon Si Ayutthaya | `Ayutthaya` | ✓ | search |
| 14 | Phra Nakhon Si Ayutthaya | `PhraNakhonSiAyutthaya` | ✗ | none |
| 15 | Ang Thong | `AngThong` | ✓ | search |
| 16 | Lopburi | `Loburi` | ✗ | none |
| 16 | Lopburi | `Lop Buri` | ✓ | redirect |
| 17 | Sing Buri | `SingBuri` | ✓ | search |
| 18 | Chai Nat | `ChaiNat` | ✓ | search |
| 19 | Saraburi | `Sara Buri` | ✓ | redirect |
| 20 | Chon Buri | `ChonBuri` | ✓ | search |
| 22 | Chanthaburi | `Chantha Buri` | ✓ | search |
| 25 | Prachin Buri | `PrachinBuri` | ✓ | search |
| 26 | Nakhon Nayok | `NakhonNayok` | ✗ | none |
| 27 | Sa Kaeo | `SaKaeo` | ✓ | search |
| 30 | Nakhon Ratchasima | `Khorat` | ✓ | redirect |
| 30 | Nakhon Ratchasima | `Korat` | ✓ | search |
| 30 | Nakhon Ratchasima | `Nakhon Rachisima` | ✗ | none |
| 30 | Nakhon Ratchasima | `NakhonRatchasima` | ✓ | search |
| 31 | Buri Ram | `BuriRam` | ✓ | search |
| 31 | Buri Ram | `Burirum` | ✗ | none |
| 33 | Si Sa Ket | `Si Saket` | ✓ | redirect |
| 33 | Si Sa Ket | `SiSaKet` | ✓ | search |
| 34 | Ubon Ratchathani | `UbonRatchathani` | ✓ | redirect |
| 37 | Amnat Charoen | `AmnatCharoen` | ✓ | search |
| 38 | Bueng Kan | `BuengKan` | ✗ | none |
| 38 | Bueng Kan | `Bung Kan` | ✓ | redirect |
| 39 | Nong Bua Lam Phu | `Nong Bua Lamphu` | ✓ | redirect |
| 39 | Nong Bua Lam Phu | `NongBuaLamPhu` | ✓ | wikitext |
| 40 | Khon Kaen | `KhonKaen` | ✓ | search |
| 41 | Udon Thani | `UdonThani` | ✓ | search |
| 43 | Nong Khai | `NongKhai` | ✓ | search |
| 44 | Maha Sarakham | `MahaSarakham` | ✓ | search |
| 45 | Roi Et | `RoiEt` | ✗ | none |
| 47 | Sakon Nakhon | `SakonNakhon` | ✓ | search |
| 48 | Nakhon Phanom | `NakhonPhanom` | ✓ | search |
| 50 | Chiang Mai | `ChiangMai` | ✓ | search |
| 52 | Lampang | `Lambang` | ✗ | none |
| 57 | Chiang Rai | `ChiangRai` | ✓ | search |
| 58 | Mae Hong Son | `MaeHongSon` | ✓ | search |
| 60 | Nakhon Sawan | `NakhonSawan` | ✓ | search |
| 60 | Nakhon Sawan | `Nakhorn Sawan` | ✓ | redirect |
| 61 | Uthai Thani | `UthaiThani` | ✓ | search |
| 62 | Kamphaeng Phet | `Chang Wat Kamphaeng Phet` | ✓ | redirect |
| 62 | Kamphaeng Phet | `KamphaengPhet` | ✓ | search |
| 70 | Ratchaburi | `Ratcha Buri` | ✓ | search |
| 71 | Kanchanaburi | `Kanchana Buri` | ✓ | search |
| 72 | Suphan Buri | `SuphanBuri` | ✓ | search |
| 73 | Nakhon Pathom | `NakhonPathom` | ✓ | search |
| 74 | Samut Sakhon | `SamutSakhon` | ✓ | wikitext |
| 75 | Samut Songkhram | `SamutSongkhram` | ✓ | search |
| 76 | Phetchaburi | `Phet Buri` | ✗ | none |
| 76 | Phetchaburi | `Phetcha Buri` | ✓ | search |
| 77 | Prachuap Khiri Khan | `PrachuapKhiriKhan` | ✗ | none |
| 80 | Nakhon Si Thammarat | `NakhonSiThammarat` | ✗ | none |
| 82 | Phangnga | `Phang Nga` | ✓ | redirect |
| 82 | Phangnga | `Phang-nga` | ✓ | redirect |
| 84 | Surat Thani | `SuratThani` | ✓ | search |
| 86 | Chumphon | `Chum Phon` | ✓ | search |
| 86 | Chumphon | `Chumpon` | ✗ | none |
| 86 | Chumphon | `Chumporn` | ✓ | redirect |
| 90 | Songkhla | `Songkla` | ✓ | redirect |
| 96 | Narathiwat | `Bangnara` | ✓ | redirect |
