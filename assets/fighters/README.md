# Fighter photo library

Real, freely licensed photos of fighters, used by the result cards
(`post_live_result.py`, `ig_content_generator.py`). A result card only posts
when the winner has a photo here. Otherwise the card is skipped and logged.

**Rules**
- Wikimedia Commons or public-domain photos only (CC BY, CC BY-SA, CC0, public domain).
  No AI-generated likenesses, no NC/ND licenses, no unattributed uploads.
- One fighter per photo, face clearly visible. No mugshots.
- Every photo has a `<slug>.json` with `credit` (printed on the card, Latin
  characters only), `license`, `artist` and `source`.
- Slug = full name, lowercase, hyphens, no accents: `charles-oliveira.jpg`.
- Nicknames and alternate spellings go in `aliases.json`.
- A last-name match also works when the library fighter's first name appears in the
  incoming name, so "Saul Canelo Alvarez" finds `canelo-alvarez.jpg` but a different
  "Jones" never gets Jon Jones's photo.

**Not found on Commons yet (Nov 2026):** Joshua Buatsi, Willy Hutchinson, Waldo
Cortes-Acosta, Johnny Walker, Carlos Adames, Gerome Warburton, Anthony Olascuaga,
Diego Pacheco, Jai Opetaia, Zhang Weili, Terence Crawford, Jaron Ennis, Teofimo Lopez,
Daniel Dubois, Amanda Serrano, Katie Taylor, Cheavon Clarke and Agit Kabayel (only
two-person photos), Floyd Schofield.

| Fighter | File | License | Year | Source |
|---|---|---|---|---|
| Alex Pereira | `alex-pereira.jpg` | CC BY 3.0 | 2024 | [Commons](https://commons.wikimedia.org/wiki/File:Alex_Pereira_UFC_300.png) |
| Amanda Nunes | `amanda-nunes.jpg` | CC BY 3.0 | 2021 | [Commons](https://commons.wikimedia.org/wiki/File:Ceremonial_weigh_ins_-_Amanda_Nunes_vs_Julianna_Pe%C3%B1a_UFC_269_(cropped_2).jpg) |
| Anthony Joshua | `anthony-joshua.jpg` | CC BY-SA 4.0 | 2019 | [Commons](https://commons.wikimedia.org/wiki/File:Anthony_Joshua_Press_Conference_(cropped).jpg) |
| Artur Beterbiev | `artur-beterbiev.jpg` | CC BY 3.0 | 2019 | [Commons](https://commons.wikimedia.org/wiki/File:Artur_Beterbiev,_December_2019.jpg) |
| canelo-alvarez | `canelo-alvarez.jpg` | CC BY 3.0 |  | [Commons](https://commons.wikimedia.org/wiki/File:Canelo_%C3%81lvarez%27s_cross_2017.png) |
| Charles Oliveira | `charles-oliveira.jpg` | CC BY-SA 4.0 | 2023 | [Commons](https://commons.wikimedia.org/wiki/File:Charles_Oliveira_do_Bronxs_Champs.jpg) |
| Chris Billam-Smith | `chris-billam-smith.jpg` | CC BY 3.0 | 2024 | [Commons](https://commons.wikimedia.org/wiki/File:Chris_Billam_Smith_2024.png) |
| Christian Mbilli | `christian-mbilli.jpg` | CC BY-SA 2.0 | 2016 | [Commons](https://commons.wikimedia.org/wiki/File:Christian_Mbilli_Assomo_Rio2016.jpg) |
| Ciryl Gane | `ciryl-gane.jpg` | Public domain | 2026 | [Commons](https://commons.wikimedia.org/wiki/File:UFC_Freedom_250_Ceremonial_Weigh_In_(9748626)(cropped).jpg) |
| Conor McGregor | `conor-mcgregor.jpg` | CC BY-SA 2.0 | Take | [Commons](https://commons.wikimedia.org/wiki/File:Conor_McGregor,_UFC_189_World_Tour_London.jpg) |
| Deontay Wilder | `deontay-wilder.jpg` | CC BY-SA 2.0 | 2018 | [Commons](https://commons.wikimedia.org/wiki/File:Deontay_Wilder_2018_(cropped).jpg) |
| Devin Haney | `devin-haney.jpg` | CC BY 3.0 | 2024 | [Commons](https://commons.wikimedia.org/wiki/File:Devin_Haney_in_2024.jpg) |
| Diego Lopes | `diego-lopes.jpg` | CC BY 3.0 | 2026 | [Commons](https://commons.wikimedia.org/wiki/File:Diego_Lopes_2026.jpg) |
| Dmitry Bivol | `dmitry-bivol.jpg` | CC BY-SA 3.0 | 2023 | [Commons](https://commons.wikimedia.org/wiki/File:Dmitry_Bivol_in_2023.jpg) |
| Dricus du Plessis | `dricus-du-plessis.jpg` | CC0 | 2023 | [Commons](https://commons.wikimedia.org/wiki/File:IMG-Dricus-Duplessis(cropped).jpg) |
| Gervonta Davis | `gervonta-davis.jpg` | CC BY 3.0 | 2023 | [Commons](https://commons.wikimedia.org/wiki/File:Gervonta_Davis_in_2023.jpg) |
| Ilia Topuria | `ilia-topuria.jpg` | Public domain | Take | [Commons](https://commons.wikimedia.org/wiki/File:UFC_Freedom_250_Ceremonial_Weigh_In_(9748627)(cropped).jpg) |
| Islam Makhachev | `islam-makhachev.jpg` | CC BY 3.0 | 2022 | [Commons](https://commons.wikimedia.org/wiki/File:Islam_Makhachev_2022_UFC_belt.png) |
| Jake Paul | `jake-paul.jpg` | CC BY 2.0 | 2023 | [Commons](https://commons.wikimedia.org/wiki/File:Jake_Paul_(53116882732).jpg) |
| Jiří Procházka | `jiri-prochazka.jpg` | CC BY 3.0 | 2022 | [Commons](https://commons.wikimedia.org/wiki/File:JiriProchazka2022.png) |
| Jon Jones | `jon-jones.jpg` | CC BY-SA 4.0 | 2024 | [Commons](https://commons.wikimedia.org/wiki/File:JonBonesJones.jpg) |
| Josh Hokit | `josh-hokit.jpg` | Public domain | 2026 | [Commons](https://commons.wikimedia.org/wiki/File:UFC_Freedom_250_Press_Conference_(9747953)_(cropped).jpg) |
| Kayla Harrison | `kayla-harrison.jpg` | CC BY 2.0 | 2016 | [Commons](https://commons.wikimedia.org/wiki/File:Kayla_Harrison_Rio_2016c.jpg) |
| Max Holloway | `max-holloway.jpg` | Public domain | 2022 | [Commons](https://commons.wikimedia.org/wiki/File:Blue_Angels%27_VIP_Rider_Max_Holloway_(1)_(cropped).jpg) |
| Merab Dvalishvili | `merab-dvalishvili.jpg` | Public domain | 2025 | [Commons](https://commons.wikimedia.org/wiki/File:Merab_Dvalishvili_at_UFC_316_(cropped).jpg) |
| Naoya Inoue | `naoya-inoue.jpg` | CC BY 4.0 | 2 Ma | [Commons](https://commons.wikimedia.org/wiki/File:Naoya_Inoue_20230302suports_03.jpg) |
| Oleksandr Usyk | `oleksandr-usyk.jpg` | CC BY-SA 4.0 | 2025 | [Commons](https://commons.wikimedia.org/wiki/File:Oleksandr_Usyk_at_TIFF_2025.jpg) |
| Ryan Garcia | `ryan-garcia.jpg` | CC BY 3.0 | 2017 | [Commons](https://commons.wikimedia.org/wiki/File:Ryan_Garc%C3%ADa.png) |
| Sean Strickland | `sean-strickland.jpg` | CC BY-SA 4.0 | 2022 | [Commons](https://commons.wikimedia.org/wiki/File:Sean_Strickland_at_UFN_200.png) |
| Shakur Stevenson | `shakur-stevenson.jpg` | CC BY 3.0 | 2023 | [Commons](https://commons.wikimedia.org/wiki/File:Shakur_Stevenson_in_2023.jpg) |
| Tyson Fury | `tyson-fury.jpg` | CC BY-SA 4.0 | 2017 | [Commons](https://commons.wikimedia.org/wiki/File:Tyson_Fury_at_Place_Bell,_Laval_Quebec,_Canada_-_Dec_16_2017_(cropped).jpg) |
| Valentina Shevchenko | `valentina-shevchenko.jpg` | CC BY 3.0 | 2018 | [Commons](https://commons.wikimedia.org/wiki/File:Valentina_Shevchenko.jpg) |
