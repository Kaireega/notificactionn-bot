from api.oanda_api import OandaApi
from infrastructure.instrument_collection import instrumentCollection 
from stream_bot.stream_bot import run_bot
from stream_example.streamer import run_streamer
from db.db import DataDB
from infrastructure.collect_data import run_collection


def db_tests():
    d = DataDB()

    #d.add_one(DataDB.SAMPLE_COLL, dict(age=12, name='paddy', street='elm'))
    #print(d.query_single(DataDB.SAMPLE_COLL, age=34))
    print(d.query_distinct(DataDB.SAMPLE_COLL, 'age'))

if __name__ == '__main__':
    api = OandaApi()
    
    # Validate API credentials before proceeding
    print("🔍 Validating OANDA API credentials...")
    if not api.validate_credentials():
        print("\n❌ Invalid OANDA API credentials!")
        print("Please update your API credentials in config.env or set environment variables:")
        print("  OANDA_API_KEY=your_api_key_here")
        print("  OANDA_ACCOUNT_ID=your_account_id_here")
        print("\nTo get your API credentials:")
        print("1. Log into your OANDA account at https://www.oanda.com/")
        print("2. Go to Account > API Access")
        print("3. Generate a new API key")
        print("4. Copy your Account ID")
        exit(1)
    
    print("✅ API credentials validated successfully!")
    
    instrumentCollection.LoadInstruments("./data")
    # instrumentCollection.CreateDB(api.get_account_instruments())
    # instrumentCollection.LoadInstrumentsDB()
    # print(instrumentCollection.instruments_dict)
    # d = DataDB()
    # d.test_connection()
    # db_tests()
    run_collection(instrumentCollection, api)
    # print(api.get_account_instruments())

