#!/usr/bin/env python3
"""
Check Excel File Contents
Shows what data was recorded in the Excel file.
"""

import pandas as pd
import os

def check_excel_contents():
    """Check the contents of the Excel file."""
    
    excel_file = "logs/trades/complete_trading_records.xlsx"
    
    if not os.path.exists(excel_file):
        print("❌ Excel file not found!")
        return
    
    print("📊 Excel File Analysis")
    print("=" * 50)
    print(f"📁 File: {excel_file}")
    print(f"📏 Size: {os.path.getsize(excel_file):,} bytes")
    print()
    
    try:
        # Read all sheets
        excel_data = pd.read_excel(excel_file, sheet_name=None)
        
        print("📋 Available Sheets:")
        for sheet_name, df in excel_data.items():
            print(f"  📄 {sheet_name}: {len(df)} rows, {len(df.columns)} columns")
        
        print()
        
        # Show sample data from each sheet
        for sheet_name, df in excel_data.items():
            if len(df) > 0:
                print(f"📊 {sheet_name} - Sample Data:")
                print(f"   Columns: {list(df.columns)}")
                print(f"   First 3 rows:")
                print(df.head(3).to_string(index=False))
                print("-" * 50)
                print()
        
        # Summary statistics
        if 'Trades' in excel_data and len(excel_data['Trades']) > 0:
            trades_df = excel_data['Trades']
            print("📈 Trading Summary:")
            print(f"   Total Decisions: {len(trades_df)}")
            if 'signal' in trades_df.columns:
                signals = trades_df['signal'].value_counts()
                print(f"   Signals: {dict(signals)}")
            if 'pair' in trades_df.columns:
                pairs = trades_df['pair'].value_counts()
                print(f"   Pairs: {dict(pairs)}")
            print()
        
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")

if __name__ == "__main__":
    check_excel_contents()
