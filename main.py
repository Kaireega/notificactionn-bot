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
    instrumentCollection.LoadInstruments("./data")
    # instrumentCollection.CreateDB(api.get_account_instruments())
    # instrumentCollection.LoadInstrumentsDB()
    # print(instrumentCollection.instruments_dict)
    # d = DataDB()
    # d.test_connection()
    # db_tests()
    run_collection(instrumentCollection, api)
    # print(api.get_account_instruments())

