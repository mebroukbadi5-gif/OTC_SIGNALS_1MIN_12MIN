# OTC_SIGNALS_1MIN_12MIN — Binary Options Signals

> **13 OTC Currency Pairs × 7 Weekdays × 12 Expiries**
> **100% Win Rate** (close at expiry in predicted direction)
> **Pattern**: 3+ consecutive green/red candles
> **Timestamps**: Candle time (no timezone conversion)

## 📁 Files

| File | Expiry | Signals |
|------|--------|---------|
| SIGNALS_1min.txt | 1 min | 6,135 |
| SIGNALS_2min.txt | 2 min | 7,076 |
| SIGNALS_3min.txt | 3 min | 7,443 |
| SIGNALS_4min.txt | 4 min | 7,660 |
| SIGNALS_5min.txt | 5 min | 7,752 |
| SIGNALS_6min.txt | 6 min | 7,640 |
| SIGNALS_7min.txt | 7 min | 7,678 |
| SIGNALS_8min.txt | 8 min | 7,748 |
| SIGNALS_9min.txt | 9 min | 7,817 |
| SIGNALS_10min.txt | 10 min | 7,791 |
| SIGNALS_11min.txt | 11 min | 7,807 |
| SIGNALS_12min.txt | 12 min | 7,837 |
| **TOTAL** | | **90,384** |

## 📐 Signal Format

```
⭐⭐⭐ [PAIR] HH:MM <CALL|PUT> streak=N×🟢/🔴 win=100% safe=ZZ% move=X n=N
```

- **[PAIR]**: Currency pair name
- **HH:MM**: Signal time (candle time, no conversion)
- **CALL/PUT**: Direction
- **streak=N×🟢/🔴**: N consecutive green (CALL) or red (PUT) candles
- **win=100%**: ALL same-weekday days closed in this direction
- **safe=ZZ%**: % of days where close was far from entry
- **move=X**: Average price movement
- **n=N**: Number of historical samples

## 📊 13 OTC Currency Pairs

BRLUSD, USDARS, USDBDT, USDCOP, USDDZD, USDEGP, USDIDR, USDINR, USDMXN, USDNGN, USDPHP, USDPKR, USDZAR

## 📊 Per-Day Breakdown

Each file contains sections for all 7 weekdays:
- Sunday (الأحد)
- Monday (الإثنين)
- Tuesday (الثلاثاء)
- Wednesday (الأربعاء)
- Thursday (الخميس)
- Friday (الجمعة)
- Saturday (السبت)

## 📈 Data Source

- 13 OTC currency pairs
- 1-minute candles, 100 days each (~144,000 candles per pair)
- Source: Quotex via candal.py fetcher
