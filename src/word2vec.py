from gensim.models.word2vec import Word2Vec
from gensim.models import word2vec
import pandas as pd
import copy

# get vector for each job listing based on 'tokens" column
def get_vector(df, model):
    words = df["tokens"]
    wd_result = None
    for word in words:
        if word in model.wv.index_to_key:
            wd_vector = copy.deepcopy(model.wv.get_vector(word))
        else:
            continue
        if wd_vector is None:
            continue
        # else:
        #     print(word)
        if wd_result is None:
            wd_result = wd_vector
        else:
            wd_result += wd_vector
    return wd_result


# choose data source
df_data = pd.read_csv("/Users/cx/Documents/JobsDB.csv")
sentences=word2vec.Text8Corpus('/Users/cx/Documents/data.txt')
# build and save w2v model
model = Word2Vec(sentences, min_count=1, vector_size=200)
model.save("words200.model")

# add one more column "job_vector" to store each job listing's vector information
df_data["job_vector"] = df_data.apply(lambda x: get_vector(x, model), axis=1)

# store the data into a csv file
df_data.to_csv('vector_added200.csv', index=False)






