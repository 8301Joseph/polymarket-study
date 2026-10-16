# Pre-registration: Polymarket calibration study
Date written: 12 Oct 2026 (before any data pulled)

## Question
Are Polymarket prices well calibrated, and are long shots overpriced?

## Markets
Resolved Polymarket markets in two categories: politics and sports.
Chosen before looking at data. Excluding markets with volume under $10,000
and markets that resolved 50/50 or were cancelled.

## What I will measure
- Price 7 days, 1 day and 1 hour before the market ended
- Whether the event happened (1) or not (0)

## Method
- Group by price bucket (10 buckets of 10 percentage points)
- Compare average price to actual outcome rate in each bucket
- Compute Brier score
- Compare politics vs sports

## What would count as a result
- "Bias exists": longshot buckets (below 30%) have actual rates clearly below
  their prices, AND favourite buckets (above 70%) have actual rates above
  their prices, consistently across horizons.
- "No bias": gaps are small and inconsistent in sign.
- I will not claim a bias from any single bucket or from fewer than 30
  markets in a bucket.

## Costs
I will test whether any bias would survive trading costs of 0, 1, 2 and 4
cents per share.

## What I will NOT do
I will not add or remove categories after seeing results.