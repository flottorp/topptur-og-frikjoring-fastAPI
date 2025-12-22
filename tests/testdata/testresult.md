# Test Scenario - Member Sync Over 3 Days

## 🔎 Resultat etter dag 1 (Initial state)

- **Jonas** → TF ✅ + NTNUI ✅ (begge gyldige til 2026)
- **Lars** → NTNUI ✅ (gyldig til 2025-12-31), TF ❌
- **Maja** → TF ✅ (gyldig til 2026), NTNUI ❌
- **Kari** → ingen gyldige medlemskap

## 🔎 Resultat etter dag 2 (New memberships added)

- **Jonas** → fortsatt fullt gyldig (TF ✅ + NTNUI ✅)
- **Lars** → fortsatt NTNUI ✅ (men utløper snart - 2025-12-22)
- **Maja** → fortsatt TF ✅
- **Kari** → **får begge** (ny!) TF ✅ + NTNUI ✅

## 🔎 Resultat etter dag 3 (Natural expiration)

- **Jonas** → fortsatt fullt gyldig (TF ✅ + NTNUI ✅)
- **Lars** → NTNUI utløper/utløpt ❌ (2025-12-22), fortsatt ingen TF
- **Maja** → fortsatt TF ✅
- **Kari** → fortsatt begge gyldige (TF ✅ + NTNUI ✅)
- **Erik** → **ny person!** Fullt gyldig (TF ✅ + NTNUI ✅)

## Notater
- Gyldige medlemskap forsvinner ikke, de utløper naturlig når datoen passerer
- Nye personer kan få medlemskap
- Personer uten medlemskap kan få nye medlemskap