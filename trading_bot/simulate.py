#!/usr/bin/env python3
import asyncio
from pathlib import Path
import sys

# Ensure repo root is on sys.path so 'trading_bot' package resolves
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from trading_bot.src.utils.config import Config
from trading_bot.src.core.models import TimeFrame
from trading_bot.src.simulation.feeds import HistoricalDataFeed
from trading_bot.src.simulation.feeds_oanda import OandaHistoricalFeed
from trading_bot.src.simulation.feeds_db import DBHistoricalFeed
from trading_bot.src.simulation.engine import SimulationEngine


async def main():
    cfg = Config()
    # Force dry-run for simulation
    cfg.notifications.live_trade_enabled = False
    # Auto-disable outbound notifications during simulation to avoid polling warnings
    cfg.notifications.telegram_enabled = False
    cfg.notifications.email_enabled = False
    cfg.notifications.send_charts = False
    # Choose data source: local pickle or OANDA historical
    source = getattr(cfg.simulation, 'data_source', 'csv')
    if source == 'oanda':
        feed = OandaHistoricalFeed()
        feed.load_last_3y_until_prev_week(cfg.trading_pairs, cfg.timeframes[:3])
    elif source == 'db':
        feed = DBHistoricalFeed()
        # Limit to M5/M15 initially for speed
        tfs = [tf for tf in cfg.timeframes if tf.value in ('M5', 'M15')]
        if not tfs:
            tfs = cfg.timeframes[:2]
        feed.load_last_3y_until_prev_week(cfg.trading_pairs, tfs)
    else:
        data_dir = cfg.simulation.csv_dir or str(Path(__file__).parent.parent / 'data')
        feed = HistoricalDataFeed(data_dir)
    engine = SimulationEngine(cfg, feed)
    await engine.start()
    try:
        pairs = cfg.trading_pairs
        tfs = cfg.timeframes[:3]  # limit to faster timeframes
        await engine.run(pairs, tfs)
    finally:
        await engine.stop()
    # TODO: add by-pair/timeframe breakdown printing here once collected in tracker


if __name__ == "__main__":
    asyncio.run(main())


