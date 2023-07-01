import requests
import json
from retry import retry


@retry(tries=3, delay=1)
def get_audio_query(text, speaker):
    r = requests.post("http://localhost:50021/audio_query", 
                      params={"text": text, "speaker": speaker},
                      timeout=(10.0, 300.0))
    r.raise_for_status()
    return r.json()


@retry(tries=3, delay=1)
def audio_query_to_wav(query_data, speaker, filename):
    r = requests.post("http://localhost:50021/synthesis",
                      data=json.dumps(query_data),
                      params={"speaker": speaker},
                      timeout=(10.0, 300.0))
    r.raise_for_status()
    with open(filename, "wb") as fp:
                fp.write(r.content)


def synthesize(text, filename, speaker=1, options=None):
    query_data = get_audio_query(text, speaker)
    if options is not None:
        query_data.update(options)
    audio_query_to_wav(query_data, speaker, filename)
