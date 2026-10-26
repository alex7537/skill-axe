# Worked example: 2D-material mechanocoupling, 2021–2026

Snapshot date: **2026-10-26**. This is a worked discovery example, not a full-text systematic review. Re-run all live checks before using the list in a thesis.

## Request

```text
使用 $literature-discovery，围绕“二维材料的力电耦合”检索 2021–2026 年核心论文，
输出候选矩阵并筛选最多 15 篇。
```

## Frozen scope

- **Research question:** Which primary studies from 2021–2026 materially advance measurement, mechanism, engineering, or device demonstration of mechanical–electrical coupling in atomically thin or layered 2D materials?
- **Included mechanisms:** direct/inverse piezoelectricity, flexoelectricity, strain-gradient photovoltaic coupling, and stacking/interface mechanisms with an explicit electromechanical response.
- **Included evidence:** peer-reviewed English primary research; experimental and first-principles/mechanistic work; online-first year accepted when it is the version of record.
- **Excluded:** reviews as core evidence, polymer/composite devices whose coupling is not attributed to the 2D phase, bulk or merely “quasi-2D” systems without an atomically thin/layered mechanism, ordinary strain engineering without polarization/electromechanical coupling, and pure ferroelectric-memory work lacking a mechanical/electromechanical link.
- **Target:** no more than 15 papers, with measurement, mechanism, interface/stacking, and device coverage. Citation signal is secondary to relevance and evidence diversity.

## Query log

| Source | Query / route | Filters | Result handling |
|---|---|---|---|
| Publisher web search | `2D material piezoelectric electromechanical coupling` | 2021–2026 where supported | Result count not exposed; primary landing pages inspected |
| Publisher web search | `two-dimensional flexoelectric MoS2` | 2021–2026 | Result count not exposed; primary landing pages inspected |
| Publisher web search | `2D ferroelectric piezoelectric heterobilayer` | 2021–2026 | Result count not exposed; primary landing pages inspected |
| Publisher web search | `inverse piezoelectricity 2D TMD` | 2021–2026 | Result count not exposed; primary landing pages inspected |
| Crossref API | `query.title=two-dimensional piezoelectricity` | journal article; 2021-01-01 to 2026-12-31 | API reported 410,379 fuzzy matches; only the first 50 were screened, so this is not a relevant-paper count |
| Citation chaining | 2025 review DOI `10.1002/advs.202411422` | references limited to 2021–2026 primary papers | Used for vocabulary and candidate discovery only |
| DOI verification | Exact DOI lookup in Crossref plus publisher landing page | version of record | 21 candidate records checked; selected and excluded versions deduplicated |

## Selected core set

| # | Year | Paper | Mechanism / evidence role | Why selected |
|---:|---:|---|---|---|
| 1 | 2021 | [Quantitative probe for in-plane piezoelectric coupling in 2D materials](https://doi.org/10.1038/s41598-021-86252-9) | Measurement methodology | Calibrated lateral PFM route for sub-pm/V in-plane coupling in suspended MoS2 and layer-parity behavior. |
| 2 | 2021 | [Flexible Piezoelectricity of Two-Dimensional Materials Governed by Effective Berry Curvature](https://doi.org/10.1021/acs.jpclett.1c02054) | Mechanism / high-throughput theory | Links atomistic/electronic descriptors to 2D piezoelectricity and supplies design variables beyond material listing. |
| 3 | 2021 | [Flexo-photovoltaic effect in MoS2](https://doi.org/10.1038/s41565-021-00919-y) | Experimental flexoelectric coupling | Directly demonstrates strain-gradient-enabled photovoltaic response in a representative 2D semiconductor. |
| 4 | 2022 | [Interfacial ferroelectricity in rhombohedral-stacked bilayer transition metal dichalcogenides](https://doi.org/10.1038/s41565-021-01059-z) | Stacking/interface mechanism | Establishes switchable out-of-plane polarization tied to interlayer sliding in bilayer TMDs and anchors the stacking route. |
| 5 | 2022 | [Piezoelectricity across 2D Phase Boundaries](https://doi.org/10.1002/adma.202206425) | Phase-boundary engineering | Combines PFM and modeling to show enhanced coupling at a 2H–1T′ MoTe2 metal–semiconductor boundary. |
| 6 | 2022 | [Direct observation of ferroelectricity in two-dimensional MoS2](https://doi.org/10.1038/s41699-022-00298-5) | Mechanical switching / flexoelectric field | Connects tip-induced strain gradients with stable polarization switching in 1T″-MoS2. |
| 7 | 2022 | [Ferroelectricity in untwisted heterobilayers of transition metal dichalcogenides](https://doi.org/10.1126/science.abm5734) | Out-of-plane piezoelectricity / scalable heterobilayer | Reports switchable polarization and measured d33 in epitaxial MoS2/WS2 without requiring moiré twist. |
| 8 | 2022 | [Mechanical Stress Modulation of Resistance in MoS2 Junctions](https://doi.org/10.1021/acs.nanolett.1c04019) | Stress-gradient device response | Shows combined strain and flexoelectric modulation of transport and photovoltaic response in MoS2 junctions. |
| 9 | 2023 | [Two-Dimensional Ultrahigh Unconventional Piezoelectricity Driven by Charge Screening](https://doi.org/10.1021/acs.jpclett.3c00397) | Unconventional mechanism | Represents the charge-screening route to transverse/unconventional coupling and tests the limits of conventional tensor intuition. |
| 10 | 2023 | [In-Plane Flexoelectricity in Two-Dimensional D3d Crystals](https://doi.org/10.1103/PhysRevLett.131.236203) | First-principles flexoelectricity | Defines and computes in-plane flexoelectric coefficients across representative centrosymmetric 2D crystals; the 2024 erratum must accompany it. |
| 11 | 2023 | [Unraveling Piezoelectricity of Two-Dimensional Ferroelectric Metal 1T″-MoS2](https://doi.org/10.1021/acsmaterialslett.3c01051) | Experiment/theory reconciliation | Focuses on the electromechanical response of the unusual polar metallic MoS2 phase and follows the 2022 discovery. |
| 12 | 2024 | [Unconventional Piezoelectricity of Two-Dimensional Materials Driven by the Hall Effect](https://doi.org/10.1021/acs.nanolett.3c03709) | Berry-curvature/Hall-like mechanism | Extends coupling beyond the conventional polarization direction and connects it to asymmetric Berry curvature. |
| 13 | 2024 | [Twist piezoelectricity: giant electromechanical coupling in magic-angle twisted bilayer LiNbO3](https://doi.org/10.1038/s41467-024-49321-x) | Twist-engineered device coupling | Demonstrates twist angle as a direct control knob for effective electromechanical coupling. |
| 14 | 2025 | [Unveiling inverse piezoelectricity and field induced nonvolatile strain in 2D TMDs](https://doi.org/10.1038/s41699-025-00564-2) | Inverse response / reliability | Connects electrically induced strain to persistent transport instability in operational MoSe2 devices. |
| 15 | 2026 | [Converse flexoelectric two-dimensional MoS2 actuator](https://doi.org/10.1038/s41467-026-69271-w) | Actuator demonstration | Provides a recent device-level test of converse flexoelectric actuation in monolayer/bilayer MoS2. |

## Coverage balance

- Quantitative measurement and metrology: 1, 5, 7, 11.
- Piezoelectric/inverse-piezoelectric mechanisms: 2, 9, 12, 14.
- Flexoelectric and strain-gradient coupling: 3, 6, 8, 10, 15.
- Stacking, phase-boundary, and twist engineering: 4, 5, 7, 13.
- Device-level consequences: 3, 7, 8, 13, 14, 15.

## Important exclusions

The accompanying CSV preserves all screened examples. Notable exclusions include a 2025 review used only for vocabulary/chaining; two strong sliding-ferroelectric studies that did not add enough direct electromechanical evidence to the capped set; and several prediction-only material searches displaced by papers offering broader mechanism or experimental coverage.

## Limitations

- This was a bounded discovery exercise, not PRISMA-complete systematic review. Subscription databases such as Web of Science and Scopus were not queried directly.
- Crossref `is-referenced-by-count` is a source-specific, incomplete citation signal retrieved on 2026-10-26; it is not comparable to Google Scholar and was not the sole ranking rule.
- Full text was not uniformly accessible. Final thesis claims require `$paper-deep-analysis` and locator-level checking.
- The topic label is broad. A thesis focused only on intrinsic monolayer piezoelectric coefficients, only flexoelectric devices, or only sliding ferroelectrics should rerun the search with a narrower protocol.
- New 2026 records and corrections may appear after this snapshot. In particular, the 2023 PRL flexoelectric paper has a 2024 erratum that must be read with the original.
