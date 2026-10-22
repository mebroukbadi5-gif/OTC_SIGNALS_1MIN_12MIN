#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OTC Signal Engine v25.0 — Clean Multi-Expiry Scanner
=====================================================
For each of 13 OTC pairs × 7 weekdays × 12 expiries (1-12 min):
  - Binary options: close at expiry in predicted direction
  - 100% win rate filter
  - Streak pattern: 3+ consecutive green/red candles
  - Timestamps in CANDLE time (no timezone conversion)

Output: ONE file per expiry (SIGNALS_1min.txt, SIGNALS_2min.txt, ..., SIGNALS_12min.txt)
Plus per-weekday breakdown inside each file.
"""

import os, json, glob, csv
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import statistics

REPO_DIR = '/tmp/CANDAL_OTC_CANDLES'
OUTPUT_DIR = '/home/z/my-project/download/otc_signals_v25'

WEEKDAY_FULL = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
WEEKDAY_AR = ['الأحد','الإثنين','الثلاثاء','الأربعاء','الخميس','الجمعة','السبت']
WEEKDAY_DISPLAY = {WEEKDAY_FULL[i]: f'{WEEKDAY_FULL[i]} ({WEEKDAY_AR[i]})' for i in range(7)}

# All expiries: 1-12 minutes
EXPIRIES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

# Pattern: 3+ consecutive green/red candles
STREAK_SIZES = [3, 4, 5, 6]

# Filters
MIN_SAMPLES = 3
SAFE_DISTANCE_ATR_MULT = 0.3
MIN_SAFE_RATE = 50  # %


def load_candles(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    candles = data.get('candles', data) if isinstance(data, dict) else data
    return [{'time': int(c['time']), 'open': float(c['open']), 'high': float(c['high']),
             'low': float(c['low']), 'close': float(c['close'])} for c in sorted(candles, key=lambda c: c['time'])]


def compute_atr(candles, period=14):
    if len(candles) < period + 1: return 0
    tr = []
    for i in range(1, len(candles)):
        h, l = candles[i]['high'], candles[i]['low']
        pc = candles[i-1]['close']
        tr.append(max(h-l, abs(h-pc), abs(l-pc)))
    return statistics.mean(tr[-period:]) if len(tr) >= period else 0


def scan_all_expiries(candles, pair_name, atr_value):
    """Scan all expiries (1-12) at once for efficiency.
    
    Uses CANDLE timestamps directly (no timezone conversion).
    """
    safe_dist = atr_value * SAFE_DISTANCE_ATR_MULT
    max_exp = max(EXPIRIES)
    
    # results[(weekday, hour, minute, streak_size, color, expiry)] = stats
    results = defaultdict(lambda: {
        'total': 0, 'wins': 0, 'safe_wins': 0, 'move_sizes': []
    })
    
    for streak_size in STREAK_SIZES:
        for i in range(streak_size - 1, len(candles) - max_exp):
            # Check streak
            all_green = all(candles[j]['close'] > candles[j]['open'] for j in range(i-streak_size+1, i+1))
            all_red = all(candles[j]['close'] < candles[j]['open'] for j in range(i-streak_size+1, i+1))
            if not all_green and not all_red:
                continue
            
            candle = candles[i]
            # Use CANDLE timestamp directly (no timezone conversion)
            dt = datetime.fromtimestamp(candle['time'], tz=timezone.utc)
            our_wd = (dt.weekday() + 1) % 7  # Sun=0, Mon=1, ..., Sat=6
            hour = dt.hour
            minute = dt.minute
            entry = candle['close']
            color = 'GREEN' if all_green else 'RED'
            
            for exp in EXPIRIES:
                if i + exp >= len(candles):
                    continue
                exit_price = candles[i + exp]['close']
                move = (exit_price - entry) if all_green else (entry - exit_price)
                
                key = (our_wd, hour, minute, streak_size, color, exp)
                results[key]['total'] += 1
                if move > 0:
                    results[key]['wins'] += 1
                    if abs(move) >= safe_dist:
                        results[key]['safe_wins'] += 1
                        results[key]['move_sizes'].append(abs(move))
    
    # Filter 100% win rate
    signals_by_expiry = defaultdict(list)
    for (weekday_idx, hour, minute, streak_size, color, expiry), r in results.items():
        if r['total'] < MIN_SAMPLES:
            continue
        win_rate = r['wins'] / r['total'] * 100
        if win_rate < 100:
            continue
        safe_rate = r['safe_wins'] / r['total'] * 100
        if safe_rate < MIN_SAFE_RATE:
            continue
        
        avg_move = statistics.mean(r['move_sizes']) if r['move_sizes'] else 0
        max_move = max(r['move_sizes']) if r['move_sizes'] else 0
        
        weekday_full = WEEKDAY_FULL[weekday_idx]
        
        signals_by_expiry[expiry].append({
            'pair': pair_name,
            'time': f"{hour:02d}:{minute:02d}",
            'hour': hour, 'minute': minute,
            'day': weekday_full,
            'direction': 'CALL' if color == 'GREEN' else 'PUT',
            'streak_size': streak_size,
            'streak_color': color,
            'expiry_minutes': expiry,
            'win_rate': 100.0,
            'safe_rate': safe_rate,
            'avg_move': avg_move,
            'max_move': max_move,
            'samples': r['total'],
        })
    
    return signals_by_expiry


def generate_expiry_file(signals, expiry, output_dir):
    """Generate ONE file for a specific expiry."""
    output_path = os.path.join(output_dir, f'SIGNALS_{expiry}min.txt')
    
    out_lines = []
    out_lines.append('=' * 100)
    out_lines.append(f'  OTC Binary Options Signals — {expiry}-Minute Expiry')
    out_lines.append(f'  ──────────────────────────────────────────────────────────────────────')
    out_lines.append(f'  Expiry:       {expiry} minute(s)')
    out_lines.append(f'  Win rate:     100% (close at expiry in predicted direction)')
    out_lines.append(f'  Pattern:      3-6 consecutive green/red candles')
    out_lines.append(f'  Safety:       ≥{MIN_SAFE_RATE}% safe (close far from entry)')
    out_lines.append(f'  Timestamp:    Candle time (UTC)')
    out_lines.append(f'  Total signals: {len(signals)}')
    out_lines.append(f'  ──────────────────────────────────────────────────────────────────────')
    out_lines.append(f'  Format: ⭐⭐⭐ [PAIR] Day HH:MM <CALL|PUT> streak=N×🟢/🔴 win=100% safe=ZZ% move=X n=N')
    out_lines.append('=' * 100)
    
    # Per-day sections
    for day in WEEKDAY_FULL:
        day_sigs = [s for s in signals if s['day'] == day]
        day_sigs.sort(key=lambda s: (s['pair'], s['hour'], s['minute']))
        
        out_lines.append('')
        out_lines.append('━' * 100)
        out_lines.append(f'  📅 {WEEKDAY_DISPLAY[day]}  ({len(day_sigs)} signals)')
        out_lines.append('━' * 100)
        
        if not day_sigs:
            out_lines.append('  (no signals)')
            continue
        
        for s in day_sigs:
            emoji = '🟢' if s['streak_color'] == 'GREEN' else '🔴'
            out_lines.append(
                f"  ⭐⭐⭐ [{s['pair']}] {s['time']} {s['direction']:<4}  "
                f"streak={s['streak_size']}×{emoji}  "
                f"win=100%  "
                f"safe={s['safe_rate']:.0f}%  "
                f"move={s['avg_move']:.5f}  "
                f"n={s['samples']}"
            )
    
    out_lines.append('')
    out_lines.append('  ────────────────────────────────────────────────')
    out_lines.append(f'  How to use {expiry}-min signals:')
    out_lines.append(f'    1. Find today\'s weekday')
    out_lines.append(f'    2. Look up your currency pair')
    out_lines.append(f'    3. At signal time (candle time), open CALL or PUT')
    out_lines.append(f'    4. Expiry = {expiry} minute(s)')
    out_lines.append(f'    5. 100% win rate — all days closed same direction')
    out_lines.append('  ────────────────────────────────────────────────')
    out_lines.append('')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out_lines))


def main():
    print()
    print('=' * 100)
    print('  OTC Signal Engine v25.0 — Clean Multi-Expiry Scanner')
    print(f'  Expiries: {EXPIRIES}')
    print('  Timestamps: CANDLE time (no timezone conversion)')
    print('  Win rate: 100% | Pattern: 3+ consecutive candles')
    print('=' * 100)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    candle_files = sorted(glob.glob(f'{REPO_DIR}/*_1m_100d_*.json'))
    print(f"\n  Found {len(candle_files)} currency files\n")
    
    # Collect signals by expiry
    all_by_expiry = defaultdict(list)
    
    for file_idx, filepath in enumerate(candle_files, 1):
        pair = os.path.basename(filepath).split('_1m_100d_')[0]
        candles = load_candles(filepath)
        atr = compute_atr(candles, 14)
        
        signals_by_expiry = scan_all_expiries(candles, pair, atr)
        
        for exp, sigs in signals_by_expiry.items():
            all_by_expiry[exp].extend(sigs)
        
        total = sum(len(s) for s in signals_by_expiry.values())
        print(f"  [{file_idx}/{len(candle_files)}] {pair}: {total} signals")
    
    # Generate one file per expiry
    print(f"\n  Generating expiry files...")
    total_all = 0
    for exp in EXPIRIES:
        sigs = all_by_expiry[exp]
        # Sort by day, pair, time
        sigs.sort(key=lambda s: (WEEKDAY_FULL.index(s['day']), s['pair'], s['hour'], s['minute']))
        generate_expiry_file(sigs, exp, OUTPUT_DIR)
        
        # Also save JSON
        json_data = {
            'expiry_minutes': exp,
            'total_signals': len(sigs),
            'signals': sigs,
        }
        with open(os.path.join(OUTPUT_DIR, f'SIGNALS_{exp}min.json'), 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"    ✓ SIGNALS_{exp}min.txt — {len(sigs)} signals")
        total_all += len(sigs)
    
    # Summary file
    summary_path = os.path.join(OUTPUT_DIR, 'SUMMARY.txt')
    out_lines = []
    out_lines.append('=' * 100)
    out_lines.append(f'  OTC Signal Engine v25.0 — Summary')
    out_lines.append(f'  ──────────────────────────────────────────────────────────────────────')
    out_lines.append(f'  13 OTC Currency Pairs × 7 Weekdays × 12 Expiries (1-12 min)')
    out_lines.append(f'  Win rate: 100% | Pattern: 3+ consecutive green/red candles')
    out_lines.append(f'  Timestamp: Candle time (no conversion)')
    out_lines.append(f'  ──────────────────────────────────────────────────────────────────────')
    out_lines.append(f'  Per-expiry signal counts:')
    out_lines.append('  Expiry     Signals')
    out_lines.append('  ---------- ----------')
    for exp in EXPIRIES:
        count = len(all_by_expiry[exp])
        out_lines.append(f'  {exp}min       {count}')
    out_lines.append('  ---------- ----------')
    out_lines.append(f'  TOTAL       {total_all}')
    out_lines.append('')
    out_lines.append(f'  Per-day breakdown (all expiries combined):')
    out_lines.append('  Day                      Signals')
    out_lines.append('  ------------------------- ----------')
    for day in WEEKDAY_FULL:
        count = sum(1 for exp in EXPIRIES for s in all_by_expiry[exp] if s['day'] == day)
        out_lines.append(f'  {WEEKDAY_DISPLAY[day]:<25} {count}')
    out_lines.append('')
    out_lines.append(f'  Files:')
    for exp in EXPIRIES:
        out_lines.append(f'    SIGNALS_{exp}min.txt  +  SIGNALS_{exp}min.json')
    out_lines.append('')
    out_lines.append('  ────────────────────────────────────────────────')
    out_lines.append('  How to use:')
    out_lines.append('    1. Choose your preferred expiry (1-12 min)')
    out_lines.append('    2. Open the corresponding SIGNALS_Nmin.txt file')
    out_lines.append('    3. Find today\'s weekday section')
    out_lines.append('    4. Look up your currency pair')
    out_lines.append('    5. At signal time, open CALL or PUT')
    out_lines.append('    6. Expiry = N minutes')
    out_lines.append('    7. 100% win rate based on 100 days of data')
    out_lines.append('  ────────────────────────────────────────────────')
    out_lines.append('')
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out_lines))
    print(f"\n  ✓ SUMMARY.txt")
    
    print()
    print('  ' + '=' * 96)
    print(f'  v25.0 Done — {total_all} total signals across {len(EXPIRIES)} expiry files')
    print('  ' + '=' * 96)
    for exp in EXPIRIES:
        count = len(all_by_expiry[exp])
        print(f'    {exp:>2}min: {count:>6} signals')
    print(f'    {"":>5} {"─"*20}')
    print(f'    ALL: {total_all:>6} signals')
    print('  ' + '=' * 96)


if __name__ == '__main__':
    main()
