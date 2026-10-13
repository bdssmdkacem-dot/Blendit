# Moroccan Parliament Satire — Real-Public-Figure Character Roster

**Status:** casting and likeness-reference brief; not a completed 3D likeness pack.  
**Reference date:** 13 October 2026.  
**Creative format:** clearly labelled political satire using stylized caricatures, not documentary footage.

## Production rule

Use each person's publicly documented appearance as the visual reference for a recognizable, exaggerated caricature. Do not treat the current generic archetypes as likenesses. Before modeling, collect a legally usable official/public portrait and record its source URL, access date, and license/usage status in the asset manifest. Compare the rendered head from front, three-quarter, and profile views against the reference. Keep the exaggeration artistic (head shape, brow, cheeks, hairline, posture and wardrobe), while preserving recognizable identity.

Scenes, dialogue and gestures are fictional satire. Do not present invented statements, misconduct, votes, or events as real footage or verified fact. Add an opening/end-card notice such as: **"عمل ساخر خيالي — الشخصيات كاريكاتيرية والمواقف تمثيلية"**.

## Priority cast

| Priority | Person | Public role / why included | Modeling direction |
|---|---|---|---|
| P0 | **Ahmed Touizi — أحمد التويزي** | Elected President of the House of Representatives on 13 October 2026. | Lead presiding figure; formal suit, seated/standing podium variants, controlled hand gestures. Build likeness only from a verified portrait. |
| P0 | **Idriss El Azami El Idrissi — إدريس الأزمي الإدريسي** | Opponent in the 13 October 2026 House presidency vote; useful for a cross-bloc debate scene. | Distinct facial silhouette and glasses/hair details only if confirmed by reference; emphatic speaking pose. |
| P0 | **Mohamed Ould Errachid — محمد ولد الرشيد** | President of the House of Councillors for the second half of the 2021–2027 legislature; include only in a scene set in that chamber or clearly dated period. | Formal presiding-chair variant; keep chamber identity and timeline explicit. |
| P1 | **Fatima Ezzahra El Mansouri — فاطمة الزهراء المنصوري** | Prominent PAM leader; current head-of-government appointment reported in October 2026. | Recognizable female caricature with reference-accurate hairstyle, face shape and formal wardrobe; create a separate female base mesh rather than adapting a male base. |
| P1 | **Mohamed Chouki — محمد شوكي** | RNI leader associated with the 2026 political transition. | Party-leader character; distinguish by reference-verified facial features, not party-color stereotypes alone. |
| P1 | **Nizar Baraka — نزار بركة** | Istiqlal leader and major national political figure. | Distinct head/face profile from official reference; formal parliamentary pose. |
| P1 | **Idriss Lachgar — إدريس لشكر** | USFP leader and established parliamentary/political figure. | Mature leader caricature; verify hairline, facial hair and eyewear from source images before sculpting. |
| P1 | **Mohamed Ouzzine — محمد أوزين** | Popular Movement leader and parliamentary figure. | Speaking/reaction variants based on verified public portraits. |
| P2 | **Nabil Benabdallah — نبيل بنعبد الله** | PPS leader; useful for a wider multi-party scene. | Add after P0/P1 likeness and rigging quality is accepted. |
| P2 | **Abdelilah Benkirane — عبد الإله بنكيران** | PJD leader and former head of government; useful for recognizable political satire if the script needs him. | Build from verified public references; do not invent quotes attributed to him. |

## Source register

- Official Maroc.ma announcement of Ahmed Touizi's election, 13 October 2026: https://www.maroc.ma/ar/الأخبار/انتخاب-السيد-أحمد-التويزي-رئيسا-لمجلس-النواب
- Official Maroc.ma parliament page (two chambers and the House of Councillors presidency information): https://www.maroc.ma/ar/المغرب/البرلمان
- Reuters report on the October 2026 coalition / Fatima Ezzahra El Mansouri appointment: https://www.reuters.com/world/africa/moroccan-centrist-party-agrees-form-coalition-government-with-three-other-2026-10-12/
- IFES Election Guide, 2026 Moroccan House of Representatives election context and party leaders: https://electionguide.org/elections/id/5083/

The source register establishes casting context only. It is not a substitute for a per-person likeness reference sheet.

## Per-character acceptance checklist

- [ ] Reference image and source/license status recorded.
- [ ] Front, three-quarter and profile sculpt previews rendered.
- [ ] Face silhouette, hairline, facial hair, eyewear and age impression reviewed against references.
- [ ] Neutral expression and two expressive caricature variants reviewed.
- [ ] Female and male body/face bases use appropriate proportions; no simple head swap on a generic body.
- [ ] Name and public role appear in the internal manifest; on-screen labels are used only when helpful.
- [ ] Rig test passes: blink, jaw, head turn, shoulder, elbow, wrist and hand gestures.
- [ ] GLB import, scale, materials, shadows and floor contact checked in the target renderer.
- [ ] The final scene is clearly marked as fictional satire.

## Important current limitation

The script at tools/blender/generate_parliament_satire_characters.py currently creates six generic archetypes, not the named people above. Do not rename those files and claim likeness. The next implementation step is a reference-led character profile/config system and actual facial sculpt adjustments, followed by rendered previews and human visual review.
